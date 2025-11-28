from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from core.models.udm import Listing
from core.database import get_db
from core.database.repository import ListingRepository

router = APIRouter()


class CreateListingRequest(BaseModel):
    listing: Listing


class PaginatedResponse(BaseModel):
    """Paginated response with metadata."""
    items: List[Listing]
    total: int
    page: int = Field(description="Current page number (1-indexed)")
    page_size: int = Field(description="Items per page")
    total_pages: int = Field(description="Total number of pages")


class ListingResponse(BaseModel):
    """Single listing response."""
    data: Listing


class DeleteResponse(BaseModel):
    """Delete operation response."""
    listing_id: str
    deleted: bool


@router.get("/", response_model=PaginatedResponse)
def list_listings(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    city: Optional[str] = Query(None, description="Filter by city"),
    price_min: Optional[float] = Query(None, ge=0, description="Minimum price"),
    price_max: Optional[float] = Query(None, ge=0, description="Maximum price"),
    fraud_score_min: Optional[float] = Query(None, ge=0, le=1, description="Minimum fraud score"),
    fraud_score_max: Optional[float] = Query(None, ge=0, le=1, description="Maximum fraud score"),
) -> PaginatedResponse:
    """List listings with pagination and filters."""
    repo = ListingRepository(db)
    
    # Apply filters
    skip = (page - 1) * page_size
    
    # Get filtered results and count with same filters
    if fraud_score_min is not None or fraud_score_max is not None:
        min_score = fraud_score_min if fraud_score_min is not None else 0.0
        max_score = fraud_score_max if fraud_score_max is not None else 1.0
        items = repo.get_by_fraud_score_range(min_score, max_score, skip=skip, limit=page_size)
        # Count with fraud score filter
        total = repo.count_by_fraud_score_range(min_score, max_score)
    elif price_min is not None or price_max is not None:
        items = repo.get_by_price_range(
            min_price=price_min,
            max_price=price_max,
            city=city,
            skip=skip,
            limit=page_size
        )
        # Count with price filter
        total = repo.count_by_price_range(min_price=price_min, max_price=price_max, city=city)
    else:
        items = repo.get_all(skip=skip, limit=page_size, city=city)
        total = repo.count(city=city)
    
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.post("/", response_model=ListingResponse, status_code=201)
def create_listing(
    req: CreateListingRequest,
    db: Session = Depends(get_db)
) -> ListingResponse:
    """Create a new listing."""
    repo = ListingRepository(db)
    
    # Check if listing already exists
    existing = repo.get_by_id(req.listing.listing_id)
    if existing:
        raise HTTPException(status_code=400, detail="Listing already exists")
    
    created = repo.create(req.listing)
    return ListingResponse(data=created)


@router.get("/{listing_id}", response_model=ListingResponse)
def get_listing(
    listing_id: str,
    db: Session = Depends(get_db)
) -> ListingResponse:
    """Get a listing by ID."""
    repo = ListingRepository(db)
    listing = repo.get_by_id(listing_id)
    
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    
    return ListingResponse(data=listing)


@router.delete("/{listing_id}", response_model=DeleteResponse)
def delete_listing(
    listing_id: str,
    db: Session = Depends(get_db)
) -> DeleteResponse:
    """Delete a listing by ID."""
    repo = ListingRepository(db)
    deleted = repo.delete(listing_id)
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Listing not found")
    
    return DeleteResponse(listing_id=listing_id, deleted=True)
