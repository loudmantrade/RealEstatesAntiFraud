from typing import List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.models.udm import Listing

router = APIRouter()

# Simple in-memory store for MVP
_LISTINGS: dict[str, Listing] = {}


class CreateListingRequest(BaseModel):
    listing: Listing


@router.get("/")
def list_listings() -> List[Listing]:
    return list(_LISTINGS.values())


@router.post("/")
def create_listing(req: CreateListingRequest) -> Listing:
    listing = req.listing
    if listing.listing_id in _LISTINGS:
        raise HTTPException(status_code=400, detail="Listing already exists")
    _LISTINGS[listing.listing_id] = listing
    return listing


@router.get("/{listing_id}")
def get_listing(listing_id: str) -> Listing:
    l = _LISTINGS.get(listing_id)
    if not l:
        raise HTTPException(status_code=404, detail="Listing not found")
    return l


@router.delete("/{listing_id}")
def delete_listing(listing_id: str):
    if listing_id in _LISTINGS:
        del _LISTINGS[listing_id]
        return {"listing_id": listing_id, "deleted": True}
    raise HTTPException(status_code=404, detail="Listing not found")
