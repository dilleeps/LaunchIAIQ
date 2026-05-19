from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import Country, User
from ..schemas import CountryOut


router = APIRouter(prefix="/lookups", tags=["lookups"])


_PHASES = ["Pre-launch", "Launch", "Post-launch"]
_TYPES = ["NCE", "New Indication", "Line Extension", "Biosimilar", "Combination"]
_RAG = ["Green", "Amber", "Red"]
_HTA = ["Pending", "Positive", "Restricted", "Negative", "Not Applicable"]
_REGIONS = ["North America", "Europe", "LATAM", "APAC", "MEA", "China", "Japan"]
_TAS = [
    "Oncology", "Immunology", "Cardiovascular", "Neurology", "Rare Disease",
    "Infectious Disease", "Respiratory", "Metabolic", "Ophthalmology", "Vaccines",
]
_LINK_TYPES = ["blocks", "informs", "references_price", "shares_supply", "shares_evidence"]


@router.get("/static")
def static_lookups():
    return {
        "launch_phase": _PHASES,
        "launch_type": _TYPES,
        "rag": _RAG,
        "hta_decision": _HTA,
        "region": _REGIONS,
        "therapeutic_area": _TAS,
        "dependency_link_type": _LINK_TYPES,
    }


@router.get("/countries", response_model=list[CountryOut])
def countries(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(Country).order_by(Country.name).all()
