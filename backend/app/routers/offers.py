"""
Offer parsing API router.

This module provides API endpoints for uploading and parsing
vendor offer documents using AI.
"""

import logging
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.config import settings
from app.database import get_db
from app.schemas.offer import OfferParseResponse, ParsedOrderLine
from app.schemas.commodity_group import CommodityGroupSuggestion, CommoditySuggestionRequest
from app.services.offer_parsing import (
    OfferParsingService,
    OfferParsingError,
    OpenAIUnavailableError,
)
from app.services.commodity_classification import (
    CommodityClassificationService,
    ClassificationError,
)
from app.utils.pdf_extractor import extract_text_from_pdf, extract_text_from_file
from app.utils.rate_limit import limiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/offers", tags=["Offers"])


def validate_file(file: UploadFile) -> None:
    """Validate uploaded file type and size."""
    # Check content type
    if file.content_type not in settings.ALLOWED_FILE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type: {file.content_type}. Allowed: {settings.ALLOWED_FILE_TYPES}",
        )

    # We can't check size before reading for streaming uploads
    # Size validation happens during read


@router.post(
    "/parse",
    response_model=OfferParseResponse,
    summary="Parse vendor offer document",
    description="Upload a PDF or text file containing a vendor offer and extract structured data using AI.",
)
@limiter.limit("20/hour")
async def parse_offer(
    request: Request,
    file: UploadFile = File(..., description="Vendor offer document (PDF or TXT)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Parse a vendor offer document and extract structured data.

    - Accepts PDF or plain text files
    - Uses AI to extract vendor info and order lines
    - Returns structured data for form auto-fill

    Rate limit: 20 requests per hour (AI-intensive operation)
    """
    validate_file(file)

    try:
        # Read file content
        content = await file.read()

        # Check file size
        if len(content) > settings.max_upload_size_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File too large. Maximum size: {settings.MAX_UPLOAD_SIZE_MB}MB",
            )

        # Extract text based on file type
        if file.content_type == "application/pdf":
            try:
                document_text = extract_text_from_pdf(content)
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Failed to read PDF: {e}",
                )
        else:
            # Plain text
            try:
                document_text = content.decode("utf-8")
            except UnicodeDecodeError:
                document_text = content.decode("latin-1")

        if not document_text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No text content could be extracted from the document",
            )

        # Parse with AI
        try:
            service = OfferParsingService()
            parsed_offer, metadata = await service.parse_offer(document_text)
        except OpenAIUnavailableError as e:
            logger.error(f"OpenAI unavailable: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI service is temporarily unavailable. Please try again later or enter data manually.",
            )
        except OfferParsingError as e:
            logger.warning(f"Offer parsing failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Could not parse offer document: {e}",
            )

        logger.info(
            f"Parsed offer for user {current_user.id}: "
            f"vendor={parsed_offer.vendor_name}, "
            f"lines={len(parsed_offer.order_lines)}, "
            f"format={metadata.get('format_used')}"
        )

        return OfferParseResponse(
            vendor_name=parsed_offer.vendor_name,
            vat_id=parsed_offer.vat_id,
            offer_date=parsed_offer.offer_date,
            offer_number=parsed_offer.offer_number,
            currency=parsed_offer.currency,
            order_lines=parsed_offer.order_lines,
            subtotal_net=parsed_offer.subtotal_net,
            discount_total=parsed_offer.discount_total,
            delivery_cost_net=parsed_offer.delivery_cost_net,
            delivery_tax_amount=parsed_offer.delivery_tax_amount,
            tax_rate=parsed_offer.tax_rate,
            tax_amount=parsed_offer.tax_amount,
            total_gross=parsed_offer.total_gross,
            # Terms and conditions
            payment_terms=parsed_offer.payment_terms,
            delivery_terms=parsed_offer.delivery_terms,
            validity_period=parsed_offer.validity_period,
            warranty_terms=parsed_offer.warranty_terms,
            other_terms=parsed_offer.other_terms,
            # Metadata
            token_savings=metadata.get("token_savings"),
            format_used=metadata.get("format_used", "json"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error parsing offer: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while parsing the document",
        )


@router.post(
    "/suggest-commodity",
    response_model=CommodityGroupSuggestion,
    summary="Suggest commodity group for request",
    description="Use AI to suggest the most appropriate commodity group based on request data.",
)
@limiter.limit("50/hour")
async def suggest_commodity_group(
    request: Request,
    body: CommoditySuggestionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Suggest the most appropriate commodity group for a procurement request.

    - Analyzes request title and order line descriptions
    - Returns suggested group with confidence score and explanation
    - Use this to help users select the right commodity group

    Rate limit: 50 requests per hour
    """
    try:
        service = CommodityClassificationService(db)
        suggestion = await service.suggest_commodity_group(
            title=body.title,
            order_lines=body.order_lines,
            vendor_name=body.vendor_name,
        )

        logger.info(
            f"Commodity suggestion for user {current_user.id}: "
            f"category={suggestion.category}, "
            f"confidence={suggestion.confidence}"
        )

        return suggestion

    except ClassificationError as e:
        logger.warning(f"Classification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Could not classify request: {e}",
        )
    except Exception as e:
        logger.exception(f"Unexpected error in classification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during classification",
        )
