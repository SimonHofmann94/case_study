"""
Commodity Classification Service.

This service uses LangChain and OpenAI to suggest appropriate
commodity groups for procurement requests based on their content.
"""

import json
import logging
from typing import List, Optional, Tuple
from uuid import UUID

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from sqlalchemy.orm import Session

from app.config import settings
from app.models import CommodityGroup
from app.schemas.commodity_group import CommodityGroupSuggestion
from app.utils.toon import json_to_toon, toon_to_json

logger = logging.getLogger(__name__)


# System prompt for commodity classification
CLASSIFICATION_SYSTEM_PROMPT = """You are an expert procurement specialist who classifies purchase requests into the correct commodity groups.

You will be given:
1. A request title
2. Order line descriptions
3. A catalog of available commodity groups

Your task is to:
1. Analyze the request and order lines
2. Select the MOST appropriate commodity group from the catalog
3. Provide a confidence score (0.0 to 1.0)
4. Explain your reasoning

IMPORTANT RULES:
- ONLY use commodity groups from the provided catalog
- Choose the SINGLE best match
- Consider both the request title AND individual order line descriptions
- Higher confidence (>0.8) means strong match
- Medium confidence (0.5-0.8) means reasonable match
- Low confidence (<0.5) means uncertain, best guess

{format_instructions}
"""

TOON_FORMAT_INSTRUCTIONS = """
Output your response in TOON format:
category:A|name:Commodity Name|confidence:0.85|explanation:Brief reason for selection

ONLY output the TOON formatted data, nothing else.
"""

JSON_FORMAT_INSTRUCTIONS = """
Output your response as valid JSON:
{
  "category": "A",
  "name": "Commodity Name",
  "confidence": 0.85,
  "explanation": "Brief reason for selection"
}

ONLY output valid JSON, nothing else.
"""


class ClassificationError(Exception):
    """Raised when commodity classification fails."""
    pass


class CommodityClassificationService:
    """Service for AI-powered commodity group classification."""

    def __init__(self, db: Session):
        """Initialize the service."""
        self.db = db
        self.use_toon = settings.AI_USE_TOON_FORMAT

        if settings.OPENAI_API_KEY:
            self.llm = ChatOpenAI(
                api_key=settings.OPENAI_API_KEY,
                model=settings.OPENAI_MODEL,
                temperature=settings.OPENAI_TEMPERATURE,
                max_tokens=500,  # Classification needs fewer tokens
            )
            self.parser = StrOutputParser()
            self.ai_enabled = True
        else:
            self.llm = None
            self.ai_enabled = False
            logger.warning("OpenAI API key not configured - AI classification disabled")

    def _get_commodity_catalog(self) -> str:
        """Get formatted commodity group catalog for the prompt."""
        groups = self.db.query(CommodityGroup).order_by(
            CommodityGroup.category, CommodityGroup.name
        ).all()

        if self.use_toon:
            # Compact TOON format
            lines = []
            for g in groups:
                lines.append(f"{g.category}:{g.name}")
            return "\n".join(lines)
        else:
            # JSON format
            return json.dumps([
                {"category": g.category, "name": g.name, "description": g.description}
                for g in groups
            ], indent=2)

    def _get_system_prompt(self) -> str:
        """Get the system prompt with format instructions."""
        format_instructions = (
            TOON_FORMAT_INSTRUCTIONS if self.use_toon else JSON_FORMAT_INSTRUCTIONS
        )
        return CLASSIFICATION_SYSTEM_PROMPT.format(
            format_instructions=format_instructions
        )

    def _build_request_description(
        self,
        title: str,
        order_lines: List[dict],
        vendor_name: Optional[str] = None,
    ) -> str:
        """Build a description of the request for classification."""
        parts = [f"Request Title: {title}"]

        if vendor_name:
            parts.append(f"Vendor: {vendor_name}")

        if order_lines:
            parts.append("Order Lines:")
            for i, line in enumerate(order_lines, 1):
                desc = line.get("description", "Unknown")
                parts.append(f"  {i}. {desc}")

        return "\n".join(parts)

    def _parse_response(self, response: str) -> dict:
        """Parse the LLM response."""
        response = response.strip()

        # Remove markdown code blocks if present
        if response.startswith("```"):
            lines = response.split("\n")
            response = "\n".join(lines[1:-1] if lines[-1].startswith("```") else lines[1:])

        try:
            if self.use_toon:
                return toon_to_json(response)
            else:
                return json.loads(response)
        except Exception as e:
            logger.warning(f"Failed to parse classification response: {e}")
            # Try JSON as fallback
            try:
                return json.loads(response)
            except:
                raise ValueError(f"Could not parse response: {response[:100]}")

    def _find_commodity_group(
        self,
        category: str,
        name: str,
    ) -> Optional[CommodityGroup]:
        """Find a commodity group by category and name."""
        # Try exact match first
        group = self.db.query(CommodityGroup).filter(
            CommodityGroup.category == category.upper(),
            CommodityGroup.name.ilike(name)
        ).first()

        if group:
            return group

        # Try category only
        group = self.db.query(CommodityGroup).filter(
            CommodityGroup.category == category.upper()
        ).first()

        return group

    async def suggest_commodity_group(
        self,
        title: str,
        order_lines: List[dict],
        vendor_name: Optional[str] = None,
    ) -> CommodityGroupSuggestion:
        """
        Suggest the most appropriate commodity group for a request.

        Args:
            title: Request title
            order_lines: List of order line dicts with 'description' key
            vendor_name: Optional vendor name for context

        Returns:
            CommodityGroupSuggestion with group, confidence, and explanation

        Raises:
            ClassificationError: If classification fails
        """
        if not self.ai_enabled:
            # Return a default suggestion when AI is disabled
            default_group = self.db.query(CommodityGroup).first()
            return CommodityGroupSuggestion(
                commodity_group_id=default_group.id if default_group else None,
                category=default_group.category if default_group else "A",
                name=default_group.name if default_group else "General",
                confidence=0.0,
                explanation="AI classification is not available. Please select manually.",
            )

        try:
            # Get commodity catalog
            catalog = self._get_commodity_catalog()

            # Build request description
            request_desc = self._build_request_description(
                title, order_lines, vendor_name
            )

            # Create messages
            system_prompt = self._get_system_prompt()
            user_message = f"""Classify this procurement request:

{request_desc}

Available Commodity Groups:
{catalog}"""

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_message),
            ]

            # Call LLM
            response = await self.llm.ainvoke(messages)
            parsed = self._parse_response(response.content)

            # Find the commodity group
            category = parsed.get("category", "A")
            name = parsed.get("name", "")
            confidence = float(parsed.get("confidence", 0.5))
            explanation = parsed.get("explanation", "")

            group = self._find_commodity_group(category, name)

            return CommodityGroupSuggestion(
                commodity_group_id=group.id if group else None,
                category=category,
                name=name if name else (group.name if group else "Unknown"),
                confidence=min(max(confidence, 0.0), 1.0),  # Clamp to 0-1
                explanation=explanation,
            )

        except Exception as e:
            logger.error(f"Commodity classification failed: {e}")
            raise ClassificationError(f"Failed to classify request: {e}")

    def suggest_commodity_group_sync(
        self,
        title: str,
        order_lines: List[dict],
        vendor_name: Optional[str] = None,
    ) -> CommodityGroupSuggestion:
        """
        Synchronous version of suggest_commodity_group.
        Uses a simple heuristic when AI is not available.
        """
        import asyncio

        if self.ai_enabled:
            # Run async version
            loop = asyncio.new_event_loop()
            try:
                return loop.run_until_complete(
                    self.suggest_commodity_group(title, order_lines, vendor_name)
                )
            finally:
                loop.close()

        # Fallback: keyword-based matching
        return self._keyword_based_suggestion(title, order_lines)

    def _keyword_based_suggestion(
        self,
        title: str,
        order_lines: List[dict],
    ) -> CommodityGroupSuggestion:
        """Simple keyword-based commodity suggestion as fallback."""
        # Combine all text for keyword matching
        all_text = title.lower()
        for line in order_lines:
            all_text += " " + line.get("description", "").lower()

        # Simple keyword mapping
        keyword_map = {
            "laptop": ("A", "IT Hardware"),
            "computer": ("A", "IT Hardware"),
            "software": ("A", "IT Software"),
            "office supplies": ("B", "Office Supplies"),
            "furniture": ("B", "Office Furniture"),
            "consulting": ("C", "Consulting Services"),
            "marketing": ("D", "Marketing Services"),
            "travel": ("E", "Travel Services"),
        }

        for keyword, (category, name) in keyword_map.items():
            if keyword in all_text:
                group = self.db.query(CommodityGroup).filter(
                    CommodityGroup.category == category
                ).first()

                return CommodityGroupSuggestion(
                    commodity_group_id=group.id if group else None,
                    category=category,
                    name=name,
                    confidence=0.3,
                    explanation=f"Keyword match: '{keyword}' found in request",
                )

        # Default
        default_group = self.db.query(CommodityGroup).first()
        return CommodityGroupSuggestion(
            commodity_group_id=default_group.id if default_group else None,
            category=default_group.category if default_group else "A",
            name=default_group.name if default_group else "General",
            confidence=0.1,
            explanation="No strong match found. Please review and select manually.",
        )


def create_classification_service(db: Session) -> CommodityClassificationService:
    """Factory function to create a CommodityClassificationService."""
    return CommodityClassificationService(db)
