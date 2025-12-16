"""
Offer Parsing Service.

This service uses LangChain and OpenAI to extract structured data
from vendor offer documents (PDFs). It supports TOON format for
token optimization with fallback to JSON.
"""

import json
import logging
from decimal import Decimal
from typing import List, Optional, Tuple

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI

from app.config import settings
from app.schemas.offer import ParsedOrderLine, ParsedVendorOffer
from app.utils.toon import json_to_toon, toon_to_json, estimate_token_savings

logger = logging.getLogger(__name__)


# System prompt for offer parsing
OFFER_PARSING_SYSTEM_PROMPT = """You are an expert at extracting structured data from vendor offer documents.
Your task is to extract the following information from vendor offers:

1. Vendor name (company name)
2. VAT ID (German format: DE followed by 9 digits, e.g., DE123456789)
3. Order lines (items being offered):
   - Description of item/service
   - Unit price (numeric, in EUR)
   - Quantity/Amount
   - Unit of measurement (e.g., "pcs", "hours", "kg", "m")

IMPORTANT RULES:
- Extract ALL order lines/items from the document
- VAT IDs must be in format DE + 9 digits (e.g., DE123456789)
- Prices should be numeric values without currency symbols
- If a field is not found, use null
- Be thorough - don't miss any line items

{format_instructions}
"""

TOON_FORMAT_INSTRUCTIONS = """
Output your response in TOON format (Token Oriented Object Notation):
- Use | to separate key:value pairs
- Use ; to separate array items
- Use {} for nested objects
- Use [] for arrays

Example TOON output:
vendor_name:Dell Technologies GmbH|vat_id:DE123456789|order_lines:[{description:Laptop XPS 15|unit_price:1299.99|amount:5|unit:pcs};{description:Docking Station|unit_price:249.00|amount:5|unit:pcs}]

ONLY output the TOON formatted data, nothing else.
"""

JSON_FORMAT_INSTRUCTIONS = """
Output your response as valid JSON with this structure:
{
  "vendor_name": "Company Name",
  "vat_id": "DE123456789",
  "order_lines": [
    {"description": "Item 1", "unit_price": 100.00, "amount": 5, "unit": "pcs"},
    {"description": "Item 2", "unit_price": 50.00, "amount": 10, "unit": "hours"}
  ]
}

ONLY output valid JSON, nothing else.
"""


class OfferParsingError(Exception):
    """Raised when offer parsing fails."""
    pass


class OpenAIUnavailableError(OfferParsingError):
    """Raised when OpenAI API is unavailable."""
    pass


class OfferParsingService:
    """Service for parsing vendor offers using LangChain and OpenAI."""

    def __init__(self):
        """Initialize the service with OpenAI client."""
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not configured")

        self.llm = ChatOpenAI(
            api_key=settings.OPENAI_API_KEY,
            model=settings.OPENAI_MODEL,
            temperature=settings.OPENAI_TEMPERATURE,
            max_tokens=settings.OPENAI_MAX_TOKENS,
        )
        self.parser = StrOutputParser()
        self.use_toon = settings.AI_USE_TOON_FORMAT
        self.fallback_to_json = settings.AI_FALLBACK_TO_JSON

    def _get_system_prompt(self, use_toon: bool) -> str:
        """Get the system prompt with appropriate format instructions."""
        format_instructions = (
            TOON_FORMAT_INSTRUCTIONS if use_toon else JSON_FORMAT_INSTRUCTIONS
        )
        return OFFER_PARSING_SYSTEM_PROMPT.format(
            format_instructions=format_instructions
        )

    def _parse_toon_response(self, response: str) -> dict:
        """Parse TOON formatted response to dictionary."""
        try:
            # Clean up response
            response = response.strip()
            # Remove any markdown code blocks if present
            if response.startswith("```"):
                lines = response.split("\n")
                response = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])

            return toon_to_json(response)
        except Exception as e:
            logger.warning(f"Failed to parse TOON response: {e}")
            raise ValueError(f"Invalid TOON format: {e}")

    def _parse_json_response(self, response: str) -> dict:
        """Parse JSON formatted response to dictionary."""
        try:
            # Clean up response
            response = response.strip()
            # Remove any markdown code blocks if present
            if response.startswith("```"):
                lines = response.split("\n")
                # Remove first line (```json) and last line (```)
                response = "\n".join(lines[1:-1] if lines[-1].startswith("```") else lines[1:])

            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON response: {e}")
            raise ValueError(f"Invalid JSON format: {e}")

    def _validate_and_convert(self, data: dict) -> ParsedVendorOffer:
        """Validate parsed data and convert to Pydantic model."""
        order_lines = []
        raw_lines = data.get("order_lines", [])

        for line in raw_lines:
            try:
                # Handle various formats of amount/quantity
                amount = line.get("amount") or line.get("quantity") or 1
                if isinstance(amount, str):
                    amount = Decimal(amount.replace(",", "."))
                else:
                    amount = Decimal(str(amount))

                # Handle price
                price = line.get("unit_price") or line.get("price") or 0
                if isinstance(price, str):
                    # Remove currency symbols and convert
                    price = price.replace("€", "").replace("EUR", "").strip()
                    price = Decimal(price.replace(",", "."))
                else:
                    price = Decimal(str(price))

                order_lines.append(
                    ParsedOrderLine(
                        description=str(line.get("description", "Unknown item")),
                        unit_price=price,
                        amount=amount,
                        unit=str(line.get("unit", "pcs")),
                    )
                )
            except Exception as e:
                logger.warning(f"Failed to parse order line {line}: {e}")
                continue

        if not order_lines:
            raise ValueError("No valid order lines could be extracted")

        return ParsedVendorOffer(
            vendor_name=data.get("vendor_name") or "Unknown Vendor",
            vat_id=data.get("vat_id"),
            order_lines=order_lines,
        )

    async def parse_offer(
        self,
        document_text: str,
        use_toon: Optional[bool] = None,
    ) -> Tuple[ParsedVendorOffer, dict]:
        """
        Parse a vendor offer document and extract structured data.

        Args:
            document_text: The text content of the vendor offer
            use_toon: Override default TOON setting (None uses config default)

        Returns:
            Tuple of (ParsedVendorOffer, metadata dict with token info)

        Raises:
            OfferParsingError: If parsing fails
            OpenAIUnavailableError: If OpenAI is unavailable
        """
        if use_toon is None:
            use_toon = self.use_toon

        metadata = {
            "format_used": "toon" if use_toon else "json",
            "fallback_used": False,
            "token_savings": None,
        }

        # Try with preferred format
        try:
            result = await self._call_llm(document_text, use_toon)
            parsed_data = (
                self._parse_toon_response(result)
                if use_toon
                else self._parse_json_response(result)
            )

            # Estimate token savings if TOON was used
            if use_toon:
                json_equivalent = json.dumps(parsed_data)
                metadata["token_savings"] = estimate_token_savings(parsed_data)

            offer = self._validate_and_convert(parsed_data)
            return offer, metadata

        except (ValueError, KeyError) as e:
            # If TOON parsing fails and fallback is enabled, try JSON
            if use_toon and self.fallback_to_json:
                logger.info("TOON parsing failed, falling back to JSON format")
                metadata["fallback_used"] = True
                metadata["format_used"] = "json"

                try:
                    result = await self._call_llm(document_text, use_toon=False)
                    parsed_data = self._parse_json_response(result)
                    offer = self._validate_and_convert(parsed_data)
                    return offer, metadata
                except Exception as fallback_error:
                    logger.error(f"JSON fallback also failed: {fallback_error}")
                    raise OfferParsingError(
                        f"Failed to parse offer with both TOON and JSON formats: {e}"
                    )

            raise OfferParsingError(f"Failed to parse offer: {e}")

        except Exception as e:
            error_msg = str(e).lower()
            if "api" in error_msg or "openai" in error_msg or "rate" in error_msg:
                logger.error(f"OpenAI API error: {e}")
                raise OpenAIUnavailableError(f"OpenAI API error: {e}")
            raise OfferParsingError(f"Unexpected error parsing offer: {e}")

    async def _call_llm(self, document_text: str, use_toon: bool) -> str:
        """Make the actual LLM call."""
        system_prompt = self._get_system_prompt(use_toon)

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Extract data from this vendor offer:\n\n{document_text}"),
        ]

        try:
            response = await self.llm.ainvoke(messages)
            return response.content
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise


# Convenience function for synchronous usage
def create_offer_parsing_service() -> OfferParsingService:
    """Factory function to create an OfferParsingService instance."""
    return OfferParsingService()
