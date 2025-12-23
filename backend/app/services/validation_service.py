"""
Validation service for procurement requests.

This module provides validation utilities for:
- VAT ID format validation (German VAT numbers)
- Order line total calculations
- Request total cost validation
- Status transition validation
"""

import re
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Optional, Tuple

from app.models.request import RequestStatus, VALID_STATUS_TRANSITIONS
from app.schemas.order_line import OrderLineCreate


class ValidationError(Exception):
    """Custom exception for validation errors."""

    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")


class ValidationService:
    """Service for validating procurement request data."""

    # German VAT ID pattern: DE followed by exactly 9 digits
    VAT_ID_PATTERN = re.compile(r"^DE\d{9}$")

    @classmethod
    def validate_vat_id(cls, vat_id: str) -> Tuple[bool, Optional[str]]:
        """
        Validate German VAT ID format.

        German VAT IDs (USt-IdNr.) follow the format: DE + 9 digits
        Example: DE123456789

        Args:
            vat_id: The VAT ID to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not vat_id:
            return False, "VAT ID is required"

        # Remove whitespace
        vat_id = vat_id.strip().upper()

        if not cls.VAT_ID_PATTERN.match(vat_id):
            return False, "Invalid VAT ID format. Expected format: DE + 9 digits (e.g., DE123456789)"

        return True, None

    @classmethod
    def calculate_order_line_total(
        cls,
        unit_price: Decimal,
        amount: Decimal,
        discount_percent: Optional[Decimal] = None,
    ) -> Decimal:
        """
        Calculate total price for an order line.

        Args:
            unit_price: Price per unit
            amount: Quantity
            discount_percent: Optional discount percentage (0-100)

        Returns:
            Total price rounded to 2 decimal places
        """
        total = Decimal(str(unit_price)) * Decimal(str(amount))
        if discount_percent:
            discount_multiplier = Decimal("1") - (Decimal(str(discount_percent)) / Decimal("100"))
            total = total * discount_multiplier
        return total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @classmethod
    def validate_order_line_total(
        cls,
        unit_price: Decimal,
        amount: Decimal,
        provided_total: Decimal,
        tolerance: Decimal = Decimal("0.01"),
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate that the provided total matches calculated total.

        Args:
            unit_price: Price per unit
            amount: Quantity
            provided_total: The total provided by the user
            tolerance: Allowed difference (default: 0.01)

        Returns:
            Tuple of (is_valid, error_message)
        """
        calculated = cls.calculate_order_line_total(unit_price, amount)
        difference = abs(calculated - Decimal(str(provided_total)))

        if difference > tolerance:
            return (
                False,
                f"Total mismatch: expected {calculated}, got {provided_total}",
            )

        return True, None

    @classmethod
    def calculate_request_total(cls, order_lines: List[OrderLineCreate]) -> Decimal:
        """
        Calculate total cost for a request from its order lines.

        Only includes "standard" line types in the total.
        Alternative and optional lines are excluded.

        Args:
            order_lines: List of order lines

        Returns:
            Total cost rounded to 2 decimal places
        """
        total = Decimal("0.00")
        for line in order_lines:
            # Only include standard lines in total
            if line.line_type == "standard":
                line_total = cls.calculate_order_line_total(
                    line.unit_price, line.amount, line.discount_percent
                )
                total += line_total

        return total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @classmethod
    def validate_request_total(
        cls,
        order_lines: List[OrderLineCreate],
        provided_total: Decimal,
        tolerance: Decimal = Decimal("0.01"),
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate that the provided request total matches calculated total.

        Args:
            order_lines: List of order lines
            provided_total: The total provided
            tolerance: Allowed difference

        Returns:
            Tuple of (is_valid, error_message)
        """
        calculated = cls.calculate_request_total(order_lines)
        difference = abs(calculated - Decimal(str(provided_total)))

        if difference > tolerance:
            return (
                False,
                f"Request total mismatch: expected {calculated}, got {provided_total}",
            )

        return True, None

    @classmethod
    def validate_status_transition(
        cls, current_status: RequestStatus, new_status: RequestStatus
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate that a status transition is allowed.

        Args:
            current_status: Current status of the request
            new_status: Requested new status

        Returns:
            Tuple of (is_valid, error_message)
        """
        if current_status == new_status:
            return False, f"Request is already in '{new_status.value}' status"

        allowed_transitions = VALID_STATUS_TRANSITIONS.get(current_status, [])

        if new_status not in allowed_transitions:
            allowed_str = ", ".join([s.value for s in allowed_transitions]) if allowed_transitions else "none"
            return (
                False,
                f"Cannot transition from '{current_status.value}' to '{new_status.value}'. "
                f"Allowed transitions: {allowed_str}",
            )

        return True, None

    @classmethod
    def validate_order_lines(
        cls, order_lines: List[OrderLineCreate]
    ) -> Tuple[bool, List[str]]:
        """
        Validate a list of order lines.

        Args:
            order_lines: List of order lines to validate

        Returns:
            Tuple of (all_valid, list_of_errors)
        """
        errors = []

        if not order_lines:
            errors.append("At least one order line is required")
            return False, errors

        for i, line in enumerate(order_lines, 1):
            # Validate unit price
            if line.unit_price < 0:
                errors.append(f"Order line {i}: Unit price cannot be negative")

            # Validate amount
            if line.amount <= 0:
                errors.append(f"Order line {i}: Amount must be greater than 0")

            # Validate description
            if not line.description or not line.description.strip():
                errors.append(f"Order line {i}: Description is required")

        return len(errors) == 0, errors

    @classmethod
    def validate_request_data(
        cls,
        vat_id: str,
        order_lines: List[OrderLineCreate],
    ) -> Tuple[bool, List[str]]:
        """
        Perform comprehensive validation of request data.

        Args:
            vat_id: VAT ID to validate
            order_lines: Order lines to validate

        Returns:
            Tuple of (all_valid, list_of_errors)
        """
        errors = []

        # Validate VAT ID
        vat_valid, vat_error = cls.validate_vat_id(vat_id)
        if not vat_valid:
            errors.append(vat_error)

        # Validate order lines
        lines_valid, line_errors = cls.validate_order_lines(order_lines)
        if not lines_valid:
            errors.extend(line_errors)

        return len(errors) == 0, errors
