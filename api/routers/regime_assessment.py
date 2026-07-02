from fastapi import APIRouter, HTTPException

from src.engines.crisis_taxonomy import CrisisRegimeAssessmentEngine
from src.storage.database import get_latest_risk_index

router = APIRouter(prefix="/regime-assessment", tags=["regime-assessment"])


@router.get("/latest")
def latest_regime_assessment():
    risk_index = get_latest_risk_index()
    if not risk_index:
        raise HTTPException(status_code=404, detail="No risk index data available")

    ehs_scores = _latest_ehs_scores()
    engine = CrisisRegimeAssessmentEngine()
    return engine.assess(risk_index, ehs_scores)


def _latest_ehs_scores():
    try:
        from src.engines.ehs.storage import get_latest_ehs_scores
        return get_latest_ehs_scores()
    except Exception:
        return []
