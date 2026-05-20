"""Read-only regulatory pathway library — industry-benchmark gate sequences."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from ..data.regulatory_pathways import get_pathway, list_pathways
from ..deps import get_current_user
from ..models import User


router = APIRouter(prefix="/regulatory", tags=["regulatory"])


@router.get("/pathways")
def pathways(_: User = Depends(get_current_user)):
    return list_pathways()


@router.get("/pathways/{key}")
def pathway(key: str, _: User = Depends(get_current_user)):
    p = get_pathway(key)
    if not p:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Pathway {key} not found")
    return p
