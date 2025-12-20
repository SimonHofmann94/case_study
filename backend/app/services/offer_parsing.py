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
3. Currency (default EUR if not specified)

4. Order lines (items being offered):
   For EACH item, extract:
   - line_type: "standard" if included in the total price, "alternative" if it's an alternative option not in total, "optional" if it's an optional add-on not in total
   - description: Short title/header of the item
   - detailed_description: Detailed specifications, features, or additional information (if available)
   - unit_price_net: Price per unit BEFORE tax (numeric, no currency symbols)
   - amount: Quantity
   - unit: Unit of measurement (e.g., "pcs", "hours", "kg", "m")
   - discount_percent: Discount percentage for this line (if applicable)
   - discount_amount: Calculated discount amount (if applicable)
   - line_total_net: Line total after discount, before tax

5. Totals section:
   - subtotal_net: Sum of all STANDARD line totals (before tax, excluding alternatives/optionals)
   - discount_total: Offer-wide discount amount (if any)
   - delivery_cost_net: Delivery/shipping cost before tax
   - delivery_tax_amount: Tax amount on delivery (usually 19%)
   - tax_rate: Tax rate percentage (usually 19 in Germany)
   - tax_amount: Tax amount on items (not including delivery tax)
   - total_gross: Final total including all taxes

IMPORTANT RULES:
- Extract ALL order lines/items from the document
- Mark items as "alternative" if they are presented as alternatives not included in the final price
- Mark items as "optional" if they are optional add-ons not included in the final price
- VAT IDs must be in format DE + 9 digits (e.g., DE123456789)
- Prices should be numeric values without currency symbols
- If a field is not found, use null
- Be thorough - don't miss any line items or specifications
- Extract detailed_description from product specifications, features lists, or item details

{format_instructions}
"""

TOON_FORMAT_INSTRUCTIONS = """
Output your response in TOON format (Token Oriented Object Notation):
- Use | to separate key:value pairs
- Use ; to separate array items
- Use {} for nested objects
- Use [] for arrays

Example TOON output:
vendor_name:Dell Technologies GmbH|vat_id:DE123456789|currency:EUR|order_lines:[{line_type:standard|description:Laptop XPS 15|detailed_description:Intel i7, 32GB RAM, 1TB SSD|unit_price_net:1299.99|amount:5|unit:pcs|discount_percent:10|line_total_net:5849.96};{line_type:alternative|description:Laptop XPS 17|detailed_description:Intel i9, 64GB RAM|unit_price_net:2499.99|amount:5|unit:pcs|line_total_net:12499.95}]|subtotal_net:5849.96|delivery_cost_net:49.99|delivery_tax_amount:9.50|tax_rate:19|tax_amount:1111.49|total_gross:7020.94

ONLY output the TOON formatted data, nothing else.
"""

JSON_FORMAT_INSTRUCTIONS = """
Output your response as valid JSON with this structure:
{
  "vendor_name": "Company Name",
  "vat_id": "DE123456789",
  "currency": "EUR",
  "order_lines": [
    {
      "line_type": "standard",
      "description": "Item title",
      "detailed_description": "Detailed specs and features",
      "unit_price_net": 100.00,
      "amount": 5,
      "unit": "pcs",
      "discount_percent": 10,
      "discount_amount": 50.00,
      "line_total_net": 450.00
    },
    {
      "line_type": "alternative",
      "description": "Alternative Item",
      "detailed_description": "Alternative specs",
      "unit_price_net": 150.00,
      "amount": 5,
      "unit": "pcs",
      "line_total_net": 750.00
    }
  ],
  "subtotal_net": 450.00,
  "discount_total": null,
  "delivery_cost_net": 25.00,
  "delivery_tax_amount": 4.75,
  "tax_rate": 19,
  "tax_amount": 85.50,
  "total_gross": 565.25
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

    def _parse_decimal(self, value, default=None) -> Optional[Decimal]:
        """Parse a value to Decimal, handling various formats."""
        if value is None:
            return default
        try:
            if isinstance(value, str):
                # Remove currency symbols and whitespace
                value = value.replace("€", "").replace("EUR", "").replace(" ", "").strip()
                # Handle German number format (1.234,56)
                if "," in value and "." in value:
                    value = value.replace(".", "").replace(",", ".")
                elif "," in value:
                    value = value.replace(",", ".")
                return Decimal(value)
            return Decimal(str(value))
        except Exception:
            return default

    def _validate_and_convert(self, data: dict) -> ParsedVendorOffer:
        """Validate parsed data and convert to Pydantic model."""
        order_lines = []
        raw_lines = data.get("order_lines", [])

        for line in raw_lines:
            try:
                # Handle various formats of amount/quantity
                amount = line.get("amount") or line.get("quantity") or 1
                amount = self._parse_decimal(amount, Decimal("1"))

                # Handle price (support both old and new field names)
                price = line.get("unit_price_net") or line.get("unit_price") or line.get("price") or 0
                price = self._parse_decimal(price, Decimal("0"))

                # Handle line total
                line_total = line.get("line_total_net") or line.get("total_price")
                line_total = self._parse_decimal(line_total)

                # Handle discount fields
                discount_percent = self._parse_decimal(line.get("discount_percent"))
                discount_amount = self._parse_decimal(line.get("discount_amount"))

                # Determine line type
                line_type = line.get("line_type", "standard")
                if line_type not in ("standard", "alternative", "optional"):
                    line_type = "standard"

                order_lines.append(
                    ParsedOrderLine(
                        line_type=line_type,
                        description=str(line.get("description", "Unknown item")),
                        detailed_description=line.get("detailed_description"),
                        unit_price_net=price,
                        amount=amount,
                        unit=str(line.get("unit", "pcs")),
                        discount_percent=discount_percent,
                        discount_amount=discount_amount,
                        line_total_net=line_total,
                    )
                )
            except Exception as e:
                logger.warning(f"Failed to parse order line {line}: {e}")
                continue

        if not order_lines:
            raise ValueError("No valid order lines could be extracted")

        # Parse totals
        subtotal_net = self._parse_decimal(data.get("subtotal_net"))
        discount_total = self._parse_decimal(data.get("discount_total"))
        delivery_cost_net = self._parse_decimal(data.get("delivery_cost_net"))
        delivery_tax_amount = self._parse_decimal(data.get("delivery_tax_amount"))
        tax_rate = self._parse_decimal(data.get("tax_rate"), Decimal("19.00"))
        tax_amount = self._parse_decimal(data.get("tax_amount"))
        total_gross = self._parse_decimal(data.get("total_gross") or data.get("total_amount"))

        return ParsedVendorOffer(
            vendor_name=data.get("vendor_name") or "Unknown Vendor",
            vat_id=data.get("vat_id"),
            currency=data.get("currency", "EUR"),
            order_lines=order_lines,
            subtotal_net=subtotal_net,
            discount_total=discount_total,
            delivery_cost_net=delivery_cost_net,
            delivery_tax_amount=delivery_tax_amount,
            tax_rate=tax_rate,
            tax_amount=tax_amount,
            total_gross=total_gross,
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
            logger.info(f"Raw LLM response: {result[:500]}...")  # Log first 500 chars

            parsed_data = (
                self._parse_toon_response(result)
                if use_toon
                else self._parse_json_response(result)
            )
            logger.info(f"Parsed data: {json.dumps(parsed_data, default=str)}")

            # Estimate token savings if TOON was used
            if use_toon:
                json_equivalent = json.dumps(parsed_data)
                metadata["token_savings"] = estimate_token_savings(parsed_data)

            offer = self._validate_and_convert(parsed_data)
            logger.info(f"Validated offer - vendor: {offer.vendor_name}, lines: {len(offer.order_lines)}")
            if offer.order_lines:
                logger.info(f"First order line: unit_price_net={offer.order_lines[0].unit_price_net}, amount={offer.order_lines[0].amount}")
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
