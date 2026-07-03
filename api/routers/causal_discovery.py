from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from api.dependencies import get_graph
from src.engines.causal_expansion import CausalExpansionEngine
from src.engines.crisis_taxonomy import CrisisRegimeAssessmentEngine
from src.storage.database import (
    get_causal_candidates,
    get_latest_risk_index,
    save_causal_candidates,
    update_causal_candidate_review,
)

router = APIRouter(prefix="/causal-discovery", tags=["causal-discovery"])


class CandidateReviewUpdate(BaseModel):
    review_status: str
    review_note: str = ""
    reviewed_by: str = "local"


@router.get("/current")
def current_causal_discovery():
    risk_index = get_latest_risk_index()
    if not risk_index:
        raise HTTPException(status_code=404, detail="No risk index data available")

    regime = CrisisRegimeAssessmentEngine().assess(risk_index, _latest_ehs_scores())
    engine = CausalExpansionEngine(get_graph())
    result = engine.assess_current(risk_index, regime)
    save_causal_candidates(
        run_date=str(risk_index.get("index_date")),
        trigger=result.get("trigger") or {},
        candidates=result.get("candidate_mechanisms") or [],
    )
    result["registry"] = {
        "persisted": True,
        "candidate_count": len(result.get("candidate_mechanisms") or []),
    }
    return result


@router.get("/candidates")
def causal_candidates(limit: int = 50):
    return get_causal_candidates(limit=limit)


@router.patch("/candidates/{candidate_id}")
def update_candidate(candidate_id: str, update: CandidateReviewUpdate):
    try:
        row = update_causal_candidate_review(
            candidate_id=candidate_id,
            review_status=update.review_status,
            review_note=update.review_note,
            reviewed_by=update.reviewed_by,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    if not row:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return row


def _latest_ehs_scores():
    try:
        from src.engines.ehs.storage import get_latest_ehs_scores
        return get_latest_ehs_scores()
    except Exception:
        return []
