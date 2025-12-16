"""
Tests for TOON (Token Oriented Object Notation) utilities.
"""

import pytest
from app.utils.toon import (
    json_to_toon,
    toon_to_json,
    estimate_token_savings,
    encode_value,
    decode_value,
)


class TestToonEncode:
    """Tests for TOON encoding."""

    def test_encode_simple_dict(self):
        """Test encoding a simple dictionary."""
        data = {"name": "Dell", "price": 999}
        result = json_to_toon(data)
        assert "name:Dell" in result
        assert "price:999" in result
        assert "|" in result

    def test_encode_nested_dict(self):
        """Test encoding nested dictionaries."""
        data = {"vendor": {"name": "Dell", "country": "US"}}
        result = json_to_toon(data)
        assert "vendor:{name:Dell|country:US}" in result

    def test_encode_list(self):
        """Test encoding lists."""
        data = {"items": ["laptop", "monitor", "keyboard"]}
        result = json_to_toon(data)
        assert "items:[laptop;monitor;keyboard]" in result

    def test_encode_list_of_objects(self):
        """Test encoding list of objects."""
        data = {
            "order_lines": [
                {"description": "Laptop", "price": 999},
                {"description": "Monitor", "price": 299},
            ]
        }
        result = json_to_toon(data)
        assert "order_lines:[" in result
        assert "description:Laptop" in result
        assert "price:999" in result

    def test_encode_special_characters(self):
        """Test encoding strings with special characters."""
        data = {"description": "Item with | special : chars"}
        result = json_to_toon(data)
        # Should be quoted
        assert '"' in result

    def test_encode_null_and_bool(self):
        """Test encoding null and boolean values."""
        data = {"active": True, "deleted": False, "notes": None}
        result = json_to_toon(data)
        assert "active:true" in result
        assert "deleted:false" in result
        assert "notes:null" in result

    def test_encode_decimal(self):
        """Test encoding decimal numbers."""
        data = {"price": 1299.99, "quantity": 5}
        result = json_to_toon(data)
        assert "price:1299.99" in result
        assert "quantity:5" in result


class TestToonDecode:
    """Tests for TOON decoding."""

    def test_decode_simple_dict(self):
        """Test decoding a simple TOON string."""
        toon = "name:Dell|price:999"
        result = toon_to_json(toon)
        assert result["name"] == "Dell"
        assert result["price"] == 999

    def test_decode_nested_dict(self):
        """Test decoding nested structures."""
        toon = "vendor:{name:Dell|country:US}"
        result = toon_to_json(toon)
        assert result["vendor"]["name"] == "Dell"
        assert result["vendor"]["country"] == "US"

    def test_decode_list(self):
        """Test decoding lists."""
        toon = "items:[laptop;monitor;keyboard]"
        result = toon_to_json(toon)
        assert result["items"] == ["laptop", "monitor", "keyboard"]

    def test_decode_list_of_objects(self):
        """Test decoding list of objects."""
        toon = "order_lines:[{description:Laptop|price:999};{description:Monitor|price:299}]"
        result = toon_to_json(toon)
        assert len(result["order_lines"]) == 2
        assert result["order_lines"][0]["description"] == "Laptop"
        assert result["order_lines"][0]["price"] == 999

    def test_decode_quoted_string(self):
        """Test decoding quoted strings."""
        toon = 'description:"Item with | special chars"'
        result = toon_to_json(toon)
        assert result["description"] == "Item with | special chars"

    def test_decode_null_and_bool(self):
        """Test decoding null and boolean values."""
        toon = "active:true|deleted:false|notes:null"
        result = toon_to_json(toon)
        assert result["active"] is True
        assert result["deleted"] is False
        assert result["notes"] is None

    def test_decode_floats(self):
        """Test decoding decimal numbers."""
        toon = "price:1299.99|quantity:5"
        result = toon_to_json(toon)
        assert result["price"] == 1299.99
        assert result["quantity"] == 5


class TestToonRoundtrip:
    """Tests for encoding and decoding roundtrip."""

    def test_roundtrip_simple(self):
        """Test simple roundtrip conversion."""
        original = {"name": "Test", "value": 123}
        encoded = json_to_toon(original)
        decoded = toon_to_json(encoded)
        assert decoded == original

    def test_roundtrip_complex(self):
        """Test complex roundtrip conversion."""
        original = {
            "vendor_name": "Dell Technologies",
            "vat_id": "DE123456789",
            "order_lines": [
                {"description": "Laptop XPS", "price": 1299.99, "quantity": 5},
                {"description": "Monitor", "price": 449.00, "quantity": 10},
            ],
        }
        encoded = json_to_toon(original)
        decoded = toon_to_json(encoded)

        assert decoded["vendor_name"] == original["vendor_name"]
        assert decoded["vat_id"] == original["vat_id"]
        assert len(decoded["order_lines"]) == len(original["order_lines"])

    def test_roundtrip_with_nulls(self):
        """Test roundtrip with null values."""
        original = {"name": "Test", "optional": None, "active": True}
        encoded = json_to_toon(original)
        decoded = toon_to_json(encoded)
        assert decoded == original


class TestTokenSavings:
    """Tests for token savings estimation."""

    def test_estimate_savings(self):
        """Test token savings estimation."""
        data = {
            "vendor_name": "Dell Technologies GmbH",
            "vat_id": "DE123456789",
            "order_lines": [
                {"description": "Laptop", "unit_price": 1299.99, "amount": 5},
                {"description": "Monitor", "unit_price": 449.00, "amount": 10},
            ],
        }
        result = estimate_token_savings(data)

        assert "json_chars" in result
        assert "toon_chars" in result
        assert "savings_percent" in result
        assert result["toon_chars"] < result["json_chars"]
        assert result["savings_percent"] > 0

    def test_savings_from_json_string(self):
        """Test token savings from JSON string input."""
        json_str = '{"name": "Test", "value": 123}'
        result = estimate_token_savings(json_str)

        assert result["json_chars"] > 0
        assert result["toon_chars"] > 0


class TestEdgeCases:
    """Tests for edge cases."""

    def test_empty_dict(self):
        """Test encoding/decoding empty dict."""
        data = {}
        encoded = json_to_toon(data)
        decoded = toon_to_json(encoded)
        assert decoded == {}

    def test_empty_list(self):
        """Test encoding/decoding empty list."""
        data = {"items": []}
        encoded = json_to_toon(data)
        decoded = toon_to_json(encoded)
        assert decoded["items"] == []

    def test_string_with_colon(self):
        """Test string containing colons."""
        data = {"url": "http://example.com:8080"}
        encoded = json_to_toon(data)
        decoded = toon_to_json(encoded)
        assert "http" in decoded["url"]

    def test_nested_special_chars(self):
        """Test deeply nested structures with special characters."""
        data = {
            "level1": {
                "level2": {
                    "value": "test"
                }
            }
        }
        encoded = json_to_toon(data)
        decoded = toon_to_json(encoded)
        assert decoded["level1"]["level2"]["value"] == "test"
