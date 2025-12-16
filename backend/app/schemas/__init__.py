"""
Pydantic schemas for the Procurement AI application.

This module exports all API schemas for easy importing.
"""

from app.schemas.commodity_group import (
    CommodityGroupBase,
    CommodityGroupCreate,
    CommodityGroupUpdate,
    CommodityGroupResponse,
    CommodityGroupSuggestion,
)
from app.schemas.order_line import (
    OrderLineBase,
    OrderLineCreate,
    OrderLineUpdate,
    OrderLineResponse,
)
from app.schemas.request import (
    RequestBase,
    RequestCreate,
    RequestUpdate,
    RequestStatusUpdate,
    RequestResponse,
    RequestDetailResponse,
    RequestListResponse,
)
from app.schemas.status_history import (
    StatusHistoryBase,
    StatusHistoryCreate,
    StatusHistoryResponse,
)
from app.schemas.attachment import (
    AttachmentBase,
    AttachmentCreate,
    AttachmentResponse,
)
from app.schemas.offer import (
    ParsedOrderLine,
    ParsedVendorOffer,
    OfferParseRequest,
    OfferParseResponse,
)

__all__ = [
    # Commodity Group
    "CommodityGroupBase",
    "CommodityGroupCreate",
    "CommodityGroupUpdate",
    "CommodityGroupResponse",
    "CommodityGroupSuggestion",
    # Order Line
    "OrderLineBase",
    "OrderLineCreate",
    "OrderLineUpdate",
    "OrderLineResponse",
    # Request
    "RequestBase",
    "RequestCreate",
    "RequestUpdate",
    "RequestStatusUpdate",
    "RequestResponse",
    "RequestDetailResponse",
    "RequestListResponse",
    # Status History
    "StatusHistoryBase",
    "StatusHistoryCreate",
    "StatusHistoryResponse",
    # Attachment
    "AttachmentBase",
    "AttachmentCreate",
    "AttachmentResponse",
    # Offer Parsing
    "ParsedOrderLine",
    "ParsedVendorOffer",
    "OfferParseRequest",
    "OfferParseResponse",
]
