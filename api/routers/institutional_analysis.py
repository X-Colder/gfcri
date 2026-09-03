from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from psycopg2.extras import Json

from api.models.institutional_analysis import AnalysisRunRequest
from api.routers.auth import require_institutional_user
from api.security import institutional_context, require_permission
from src.data.institutional.contracts import (
    ACTIVE_ENTITY_TYPES,
    MODEL_VERSION,
    summarize_quality,
)
from src.data.institutional.value_tiers import (
    normalize_product_tier,
    value_layer_manifest,
)
from src.engines.institutional_analysis import analyze_target_observations
from src.storage.database import get_connection, get_latest_risk_index
from src.storage.institutional_schema import ensure_institutional_schema

router = APIRouter(prefix="/v1/institutional", tags=["institutional-analysis"])


@router.get("/value-layer-manifest")
def get_value_layer_manifest():
    return value_layer_manifest()


def _context(user: dict) -> dict:
    return institutional_context(user)


def _run_analysis(
    *,
    user: dict,
    entity_type: str,
    entity_id: str,
    snapshot_id: str | None,
    product_tier: str,
    parameters: dict,
) -> dict:
    if entity_type not in ACTIVE_ENTITY_TYPES:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "ENTITY_TYPE_NOT_ACTIVE",
                "message": f"{entity_type} is reserved for a later model adapter.",
            },
        )
    try:
        normalized_tier = normalize_product_tier(product_tier)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    context = _context(user)
    require_permission(context, "analysis:run")
    tenant_id = str(context["tenant_id"])
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            ensure_institutional_schema(conn)
            if snapshot_id:
                cur.execute(
                    """
                    SELECT metric_id, value, quality_status, source_id,
                           source_tier, as_of
                    FROM institutional_observations
                    WHERE tenant_id = %s AND entity_type = %s AND entity_id = %s
                      AND snapshot_id = %s
                    ORDER BY as_of DESC
                    """,
                    (tenant_id, entity_type, entity_id, snapshot_id),
                )
            else:
                cur.execute(
                    """
                    SELECT metric_id, value, quality_status, source_id,
                           source_tier, as_of
                    FROM institutional_observations
                    WHERE tenant_id = %s AND entity_type = %s AND entity_id = %s
                    ORDER BY as_of DESC
                    """,
                    (tenant_id, entity_type, entity_id),
                )
            rows = [
                {
                    "metric_id": row[0],
                    "value": row[1],
                    "quality_status": row[2],
                    "source_id": row[3],
                    "source_tier": row[4],
                    "as_of": row[5].isoformat()
                    if hasattr(row[5], "isoformat")
                    else str(row[5]),
                }
                for row in cur.fetchall()
            ]

            quality = summarize_quality(
                rows,
                as_of=datetime.now(timezone.utc).date().isoformat(),
            )
            core = get_latest_risk_index() or {}
            result = analyze_target_observations(
                target={"entity_type": entity_type, "entity_id": entity_id},
                core_score=float(core.get("gfcri_value") or core.get("gfcri") or 0),
                observations=rows,
                data_quality=quality,
                core_risk=core,
                product_tier=normalized_tier,
                parameters=parameters,
            )
            run_id = f"{tenant_id}:{uuid.uuid4()}"
            result["run_id"] = run_id
            result["generated_at"] = datetime.now(timezone.utc).isoformat()
            result["parameters"] = {
                **parameters,
                "product_tier": normalized_tier,
            }

            cur.execute(
                """
                INSERT INTO institutional_analysis_runs
                    (run_id, tenant_id, target_type, target_id, model_version,
                     snapshot_id, request)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    run_id,
                    tenant_id,
                    entity_type,
                    entity_id,
                    MODEL_VERSION,
                    snapshot_id,
                    Json(
                        {
                            **parameters,
                            "product_tier": normalized_tier,
                        }
                    ),
                ),
            )
            cur.execute(
                """
                INSERT INTO institutional_analysis_results (run_id, tenant_id, result)
                VALUES (%s, %s, %s)
                """,
                (run_id, tenant_id, Json(result)),
            )
            conn.commit()
            return result
    finally:
        conn.close()


@router.post("/analysis-runs")
def create_analysis_run(
    req: AnalysisRunRequest,
    user=Depends(require_institutional_user),
):
    return _run_analysis(
        user=user,
        entity_type=req.entity_type,
        entity_id=req.entity_id,
        snapshot_id=req.snapshot_id,
        product_tier=req.product_tier,
        parameters=req.parameters,
    )


@router.get("/analysis-runs/{run_id}")
def get_analysis_run(
    run_id: str = Path(min_length=3, max_length=200),
    user=Depends(require_institutional_user),
):
    context = _context(user)
    require_permission(context, "analysis:read")
    tenant_id = str(context["tenant_id"])
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            ensure_institutional_schema(conn)
            cur.execute(
                """
                SELECT result
                FROM institutional_analysis_results
                WHERE tenant_id = %s AND run_id = %s
                """,
                (tenant_id, run_id),
            )
            row = cur.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Analysis run not found")
            return row[0]
    finally:
        conn.close()


@router.get("/entities/{entity_type}/{entity_id}/risk")
def get_entity_risk(
    entity_type: str,
    entity_id: str,
    product_tier: str = Query(default="research", max_length=30),
    user=Depends(require_institutional_user),
):
    return _run_analysis(
        user=user,
        entity_type=entity_type,
        entity_id=entity_id,
        snapshot_id=None,
        product_tier=product_tier,
        parameters={"source": "entity_risk_endpoint"},
    )
