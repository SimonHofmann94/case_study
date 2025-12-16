"""
Tests for OfferParsingService.

Uses mocked LLM responses for deterministic testing.
"""

import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.offer_parsing import (
    OfferParsingService,
    OfferParsingError,
    OpenAIUnavailableError,
)


# Sample vendor offer text
SAMPLE_OFFER_TEXT = """
Dell Technologies GmbH
Angebot Nr. 2024-001234

Sehr geehrte Damen und Herren,

wir unterbreiten Ihnen folgendes Angebot:

1. Dell XPS 15 Laptop
   Stückpreis: 1.299,99 EUR
   Menge: 5 Stück

2. Dell UltraSharp Monitor 27"
   Stückpreis: 449,00 EUR
   Menge: 5 Stück

Gesamtsumme: 8.744,95 EUR

USt-IdNr: DE123456789

Mit freundlichen Grüßen
Dell Technologies GmbH
"""


# Mock TOON response from LLM
MOCK_TOON_RESPONSE = """vendor_name:Dell Technologies GmbH|vat_id:DE123456789|order_lines:[{description:Dell XPS 15 Laptop|unit_price:1299.99|amount:5|unit:pcs};{description:Dell UltraSharp Monitor 27"|unit_price:449.00|amount:5|unit:pcs}]"""

# Mock JSON response from LLM
MOCK_JSON_RESPONSE = """{
  "vendor_name": "Dell Technologies GmbH",
  "vat_id": "DE123456789",
  "order_lines": [
    {"description": "Dell XPS 15 Laptop", "unit_price": 1299.99, "amount": 5, "unit": "pcs"},
    {"description": "Dell UltraSharp Monitor 27", "unit_price": 449.00, "amount": 5, "unit": "pcs"}
  ]
}"""


@pytest.fixture
def mock_llm_toon():
    """Mock LLM that returns TOON format."""
    with patch("app.services.offer_parsing.ChatOpenAI") as mock:
        instance = mock.return_value
        instance.ainvoke = AsyncMock(
            return_value=MagicMock(content=MOCK_TOON_RESPONSE)
        )
        yield instance


@pytest.fixture
def mock_llm_json():
    """Mock LLM that returns JSON format."""
    with patch("app.services.offer_parsing.ChatOpenAI") as mock:
        instance = mock.return_value
        instance.ainvoke = AsyncMock(
            return_value=MagicMock(content=MOCK_JSON_RESPONSE)
        )
        yield instance


@pytest.fixture
def mock_settings():
    """Mock settings with API key."""
    with patch("app.services.offer_parsing.settings") as mock:
        mock.OPENAI_API_KEY = "test-api-key"
        mock.OPENAI_MODEL = "gpt-4o-mini"
        mock.OPENAI_TEMPERATURE = 0.1
        mock.OPENAI_MAX_TOKENS = 2000
        mock.AI_USE_TOON_FORMAT = True
        mock.AI_FALLBACK_TO_JSON = True
        yield mock


class TestOfferParsingService:
    """Tests for OfferParsingService."""

    @pytest.mark.asyncio
    async def test_parse_offer_toon_format(self, mock_settings, mock_llm_toon):
        """Test parsing with TOON format."""
        service = OfferParsingService()
        result, metadata = await service.parse_offer(SAMPLE_OFFER_TEXT, use_toon=True)

        assert result.vendor_name == "Dell Technologies GmbH"
        assert result.vat_id == "DE123456789"
        assert len(result.order_lines) == 2
        assert result.order_lines[0].description == "Dell XPS 15 Laptop"
        assert result.order_lines[0].unit_price == Decimal("1299.99")
        assert result.order_lines[0].amount == Decimal("5")
        assert metadata["format_used"] == "toon"

    @pytest.mark.asyncio
    async def test_parse_offer_json_format(self, mock_settings, mock_llm_json):
        """Test parsing with JSON format."""
        service = OfferParsingService()
        result, metadata = await service.parse_offer(SAMPLE_OFFER_TEXT, use_toon=False)

        assert result.vendor_name == "Dell Technologies GmbH"
        assert result.vat_id == "DE123456789"
        assert len(result.order_lines) == 2
        assert metadata["format_used"] == "json"

    @pytest.mark.asyncio
    async def test_parse_offer_fallback_to_json(self, mock_settings):
        """Test fallback to JSON when TOON parsing fails."""
        with patch("app.services.offer_parsing.ChatOpenAI") as mock:
            instance = mock.return_value
            # First call fails (invalid TOON), second succeeds (JSON)
            instance.ainvoke = AsyncMock(
                side_effect=[
                    MagicMock(content="invalid toon format"),
                    MagicMock(content=MOCK_JSON_RESPONSE),
                ]
            )

            service = OfferParsingService()
            result, metadata = await service.parse_offer(
                SAMPLE_OFFER_TEXT, use_toon=True
            )

            assert result.vendor_name == "Dell Technologies GmbH"
            assert metadata["fallback_used"] is True
            assert metadata["format_used"] == "json"

    @pytest.mark.asyncio
    async def test_parse_offer_api_error(self, mock_settings):
        """Test handling of OpenAI API errors."""
        with patch("app.services.offer_parsing.ChatOpenAI") as mock:
            instance = mock.return_value
            instance.ainvoke = AsyncMock(
                side_effect=Exception("OpenAI API rate limit exceeded")
            )

            service = OfferParsingService()
            with pytest.raises(OpenAIUnavailableError) as exc_info:
                await service.parse_offer(SAMPLE_OFFER_TEXT)

            assert "API" in str(exc_info.value)

    def test_parse_toon_response(self, mock_settings):
        """Test TOON response parsing."""
        service = OfferParsingService()
        result = service._parse_toon_response(MOCK_TOON_RESPONSE)

        assert result["vendor_name"] == "Dell Technologies GmbH"
        assert result["vat_id"] == "DE123456789"
        assert len(result["order_lines"]) == 2

    def test_parse_json_response(self, mock_settings):
        """Test JSON response parsing."""
        service = OfferParsingService()
        result = service._parse_json_response(MOCK_JSON_RESPONSE)

        assert result["vendor_name"] == "Dell Technologies GmbH"
        assert result["vat_id"] == "DE123456789"
        assert len(result["order_lines"]) == 2

    def test_parse_json_with_markdown_wrapper(self, mock_settings):
        """Test parsing JSON wrapped in markdown code blocks."""
        service = OfferParsingService()
        wrapped_response = f"```json\n{MOCK_JSON_RESPONSE}\n```"
        result = service._parse_json_response(wrapped_response)

        assert result["vendor_name"] == "Dell Technologies GmbH"

    def test_validate_and_convert(self, mock_settings):
        """Test data validation and conversion."""
        service = OfferParsingService()
        data = {
            "vendor_name": "Test Vendor",
            "vat_id": "DE987654321",
            "order_lines": [
                {
                    "description": "Test Item",
                    "unit_price": "100.00",
                    "amount": "10",
                    "unit": "hours",
                }
            ],
        }
        result = service._validate_and_convert(data)

        assert result.vendor_name == "Test Vendor"
        assert result.vat_id == "DE987654321"
        assert len(result.order_lines) == 1
        assert result.order_lines[0].unit_price == Decimal("100.00")
        assert result.order_lines[0].amount == Decimal("10")

    def test_validate_empty_order_lines(self, mock_settings):
        """Test validation fails with empty order lines."""
        service = OfferParsingService()
        data = {
            "vendor_name": "Test Vendor",
            "vat_id": "DE987654321",
            "order_lines": [],
        }

        with pytest.raises(ValueError) as exc_info:
            service._validate_and_convert(data)

        assert "order lines" in str(exc_info.value).lower()


class TestOfferParsingServiceInit:
    """Tests for service initialization."""

    def test_init_without_api_key(self):
        """Test initialization without API key raises error."""
        with patch("app.services.offer_parsing.settings") as mock:
            mock.OPENAI_API_KEY = ""

            with pytest.raises(ValueError) as exc_info:
                OfferParsingService()

            assert "OPENAI_API_KEY" in str(exc_info.value)
