from collections import Counter

from fastapi import APIRouter, HTTPException

from api.models.model_foundation import (
    ModelFoundationResponse,
    NodeDataDictionaryEntry,
    SubIndexNodeReceipt,
    SubIndexReceipt,
)
from src.engines.risk_index import SUB_INDEX_CONFIG
from src.models.data_dictionary import NODE_DATA_DICTIONARY
from src.storage.database import get_latest_risk_index

router = APIRouter(prefix="/model-foundation", tags=["model-foundation"])


SUB_INDEX_FORMULA = (
    "raw_stress = 0.4 * mean_stress + 0.6 * mean_abs_stress; "
    "score = 100 * (0.6 * raw_stress + 0.4 * transmission)"
)

CREDIT_FORMULA = (
    "dimension_score = 100 * (0.35 * mean_stress + 0.45 * mean_abs_stress + 0.20 * transmission); "
    "SI_CREDIT = weighted average of credit dimensions, then + transmission overlay"
)


def _build_receipt(si_id: str, details: dict, node_contrib: dict) -> SubIndexReceipt:
    config = SUB_INDEX_CONFIG.get(si_id, {})
    node_ids = list((details or {}).get("node_scores", {}).keys() or config.get("nodes", []))
    source_counter: Counter[str] = Counter()
    nodes: list[SubIndexNodeReceipt] = []
    limitations: list[str] = []

    for node_id in node_ids:
        dictionary = NODE_DATA_DICTIONARY.get(node_id, {})
        contribution = node_contrib.get(node_id, {})
        tier = str(dictionary.get("source_tier") or "D")
        source_counter[tier] += 1
        limitation = dictionary.get("known_limitations")
        if limitation and limitation not in limitations:
            limitations.append(str(limitation))
        nodes.append(
            SubIndexNodeReceipt(
                node_id=node_id,
                display_name=str(contribution.get("display_name") or dictionary.get("display_name") or node_id),
                current_value=contribution.get("current_value"),
                zscore=contribution.get("zscore"),
                anomaly_score=contribution.get("anomaly_score"),
                abs_score=contribution.get("abs_score"),
                source_tier=tier,
                data_source=str(dictionary.get("declared_data_source") or "unknown"),
                raw_formula=str(dictionary.get("raw_formula") or "not documented"),
                known_limitations=str(dictionary.get("known_limitations") or "not documented"),
            )
        )

    return SubIndexReceipt(
        sub_index_id=si_id,
        name=str((details or {}).get("name") or config.get("name") or si_id),
        score=float((details or {}).get("score") or 0),
        formula=CREDIT_FORMULA if (details or {}).get("formula_type") == "dimension_weighted" else SUB_INDEX_FORMULA,
        mean_stress=float((details or {}).get("mean_stress") or 0),
        mean_abs_stress=float((details or {}).get("mean_abs_stress") or 0),
        transmission=float((details or {}).get("transmission") or 0),
        top_driver=(details or {}).get("top_driver"),
        node_count=len(nodes),
        source_tier_summary=dict(source_counter),
        nodes=nodes,
        limitations=limitations[:8],
        formula_type=(details or {}).get("formula_type"),
        dimension_details=(details or {}).get("dimension_details"),
        dimension_weights=(details or {}).get("dimension_weights"),
        config=config or None,
    )


@router.get("/latest", response_model=ModelFoundationResponse)
def latest_model_foundation():
    data = get_latest_risk_index()
    if not data:
        raise HTTPException(status_code=404, detail="No risk index data available")

    sub_details = data.get("sub_index_details") or {}
    node_contrib = data.get("node_contributions") or {}
    receipts = {
        si_id: _build_receipt(si_id, details, node_contrib)
        for si_id, details in sub_details.items()
        if isinstance(details, dict)
    }

    dictionary = {
        node_id: NodeDataDictionaryEntry(**entry)
        for node_id, entry in NODE_DATA_DICTIONARY.items()
    }

    return ModelFoundationResponse(
        index_date=str(data["index_date"]),
        sub_index_receipts=receipts,
        data_dictionary=dictionary,
    )
