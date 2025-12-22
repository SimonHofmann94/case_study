"""
Analytics schemas for procurement dashboard.

Pydantic models for analytics API responses.
"""

from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class RequestAnalytics(BaseModel):
    """Analytics summary for procurement requests."""

    open_count: int = Field(..., description="Number of open requests")
    in_progress_count: int = Field(..., description="Number of in-progress requests")
    closed_count: int = Field(..., description="Number of closed requests")
    total_open_value: Decimal = Field(..., description="Total value of open requests")
    total_in_progress_value: Decimal = Field(..., description="Total value of in-progress requests")
    total_closed_value: Decimal = Field(..., description="Total value of closed requests")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "open_count": 15,
                "in_progress_count": 8,
                "closed_count": 42,
                "total_open_value": "125000.00",
                "total_in_progress_value": "75000.00",
                "total_closed_value": "350000.00",
            }
        }
    )


class RequestorInfo(BaseModel):
    """Basic requestor information for filter options."""

    id: UUID = Field(..., description="User ID")
    full_name: str = Field(..., description="User's full name")
    email: str = Field(..., description="User's email")

    model_config = ConfigDict(from_attributes=True)


class FilterOptions(BaseModel):
    """Available filter options for the procurement dashboard."""

    departments: List[str] = Field(default=[], description="List of unique departments")
    vendors: List[str] = Field(default=[], description="List of unique vendor names")
    requestors: List[RequestorInfo] = Field(default=[], description="List of requestors")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "departments": ["IT", "HR", "Finance", "Marketing"],
                "vendors": ["Dell Technologies", "Microsoft", "Adobe"],
                "requestors": [
                    {"id": "550e8400-e29b-41d4-a716-446655440000", "full_name": "John Doe", "email": "john@example.com"}
                ],
            }
        }
    )
