from fastapi import APIRouter, HTTPException

from api.dependencies import get_graph
from src.engines.causal_expansion import CausalExpansionEngine
from src.engines.crisis_taxonomy import CrisisRegimeAssessmentEngine
from src.storage.database import get_latest_risk_index

router = APIRouter(prefix="/causal-discovery", tags=["causal-discovery"])


@router.get("/current")
def current_causal_discovery():
    risk_index = get_latest_risk_index()
    if not risk_index:
        raise HTTPException(status_code=404, detail="No risk index data available")

    regime = CrisisRegimeAssessmentEngine().assess(risk_index, _latest_ehs_scores())
    engine = CausalExpansionEngine(get_graph())
    return engine.assess_current(risk_index, regime)


def _latest_ehs_scores():
    try:
        from src.engines.ehs.storage import get_latest_ehs_scores
        return get_latest_ehs_scores()
    except Exception:
        return []
