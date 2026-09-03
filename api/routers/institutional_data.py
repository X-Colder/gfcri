from __future__ import annotations

import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from psycopg2.extras import Json

from api.models.institutional_data import (
    DataSourceRequest,
    EntityRequest,
    ObservationBatchRequest,
)
from api.routers.auth import require_institutional_user
from api.security import institutional_context, require_permission
from src.data.institutional.contracts import (
    MODEL_VERSION,
    model_manifest,
    normalize_observation,
    summarize_quality,
)
from src.storage.database import get_connection
from src.storage.institutional_schema import ensure_institutional_schema

router = APIRouter(prefix="/v1/institutional", tags=["institutional-data"])


def _context(user: dict) -> dict:
    return institutional_context(user)


@router.get("/model-manifest")
def get_model_manifest():
    return model_manifest()


@router.post("/entities")
def create_entity(req: EntityRequest, user=Depends(require_institutional_user)):
    context = _context(user)
    require_permission(context, "data:write")
    tenant_id = str(context["tenant_id"])
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            ensure_institutional_schema(conn)
            cur.execute(
                """
                INSERT INTO institutional_entities (tenant_id, entity_type, entity_id, name, metadata)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (tenant_id, entity_type, entity_id)
                DO UPDATE SET name = EXCLUDED.name, metadata = EXCLUDED.metadata
                RETURNING id, tenant_id, entity_type, entity_id, name, metadata
                """,
                (tenant_id, req.entity_type, req.entity_id, req.name, Json(req.metadata)),
            )
            row = cur.fetchone()
            conn.commit()
            return {
                "id": row[0],
                "tenant_id": row[1],
                "entity_type": row[2],
                "entity_id": row[3],
                "name": row[4],
                "metadata": row[5],
            }
    finally:
        conn.close()


@router.post("/data-sources")
def create_data_source(req: DataSourceRequest, user=Depends(require_institutional_user)):
    context = _context(user)
    require_permission(context, "data:write")
    tenant_id = str(context["tenant_id"])
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            ensure_institutional_schema(conn)
            cur.execute(
                """
                INSERT INTO institutional_data_sources
                    (tenant_id, source_id, name, source_tier, license_status, metadata)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (tenant_id, source_id)
                DO UPDATE SET name = EXCLUDED.name, source_tier = EXCLUDED.source_tier,
                              license_status = EXCLUDED.license_status, metadata = EXCLUDED.metadata
                RETURNING id, tenant_id, source_id, name, source_tier, license_status, metadata
                """,
                (
                    tenant_id,
                    req.source_id,
                    req.name,
                    req.source_tier,
                    req.license_status,
                    Json(req.metadata),
                ),
            )
            row = cur.fetchone()
            conn.commit()
            return {
                "id": row[0],
                "tenant_id": row[1],
                "source_id": row[2],
                "name": row[3],
                "source_tier": row[4],
                "license_status": row[5],
                "metadata": row[6],
            }
    finally:
        conn.close()


@router.post("/observations:batch")
def ingest_observations(req: ObservationBatchRequest, user=Depends(require_institutional_user)):
    context = _context(user)
    require_permission(context, "data:write")
    tenant_id = str(context["tenant_id"])
    snapshot_id = req.snapshot_id or f"{tenant_id}:{uuid.uuid4()}"
    normalized: list[dict] = []
    try:
        for observation in req.observations:
            payload = observation.model_dump()
            payload["tenant_id"] = tenant_id
            normalized.append(normalize_observation(payload))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    quality = summarize_quality(normalized, as_of=date.today().isoformat())
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            ensure_institutional_schema(conn)
            cur.execute(
                """
                INSERT INTO institutional_data_snapshots (snapshot_id, tenant_id, observation_count, quality)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (snapshot_id) DO UPDATE SET
                    observation_count = EXCLUDED.observation_count,
                    quality = EXCLUDED.quality
                """,
                (snapshot_id, tenant_id, len(normalized), Json(quality)),
            )
            for item in normalized:
                cur.execute(
                    """
                    INSERT INTO institutional_observations (
                        tenant_id, entity_type, entity_id, metric_id, value, unit, as_of,
                        frequency, source_id, source_tier, quality_status, snapshot_id, ingested_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (tenant_id, entity_type, entity_id, metric_id, as_of, source_id)
                    DO UPDATE SET value = EXCLUDED.value, unit = EXCLUDED.unit,
                                  frequency = EXCLUDED.frequency, source_tier = EXCLUDED.source_tier,
                                  quality_status = EXCLUDED.quality_status,
                                  snapshot_id = EXCLUDED.snapshot_id, ingested_at = EXCLUDED.ingested_at
                    """,
                    (
                        tenant_id,
                        item["entity_type"],
                        item["entity_id"],
                        item["metric_id"],
                        item["value"],
                        item["unit"],
                        item["as_of"],
                        item["frequency"],
                        item["source_id"],
                        item["source_tier"],
                        item["quality_status"],
                        snapshot_id,
                        item["ingested_at"],
                    ),
                )
            conn.commit()
            return {
                "snapshot_id": snapshot_id,
                "model_version": MODEL_VERSION,
                "observation_count": len(normalized),
                "quality": quality,
            }
    finally:
        conn.close()


@router.get("/data-quality")
def get_data_quality(
    snapshot_id: str | None = Query(default=None, max_length=160),
    user=Depends(require_institutional_user),
):
    context = _context(user)
    require_permission(context, "data:read")
    tenant_id = str(context["tenant_id"])
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            ensure_institutional_schema(conn)
            if snapshot_id:
                cur.execute(
                    """
                    SELECT snapshot_id, observation_count, quality, created_at
                    FROM institutional_data_snapshots
                    WHERE tenant_id = %s AND snapshot_id = %s
                    """,
                    (tenant_id, snapshot_id),
                )
            else:
                cur.execute(
                    """
                    SELECT snapshot_id, observation_count, quality, created_at
                    FROM institutional_data_snapshots
                    WHERE tenant_id = %s
                    ORDER BY created_at DESC
                    LIMIT 1
                    """,
                    (tenant_id,),
                )
            row = cur.fetchone()
            if not row:
                return {
                    "status": "empty",
                    "tenant_id": tenant_id,
                    "snapshot_id": None,
                    "observation_count": 0,
                }
            return {
                "status": row[2].get("status", "degraded"),
                "tenant_id": tenant_id,
                "snapshot_id": row[0],
                "observation_count": row[1],
                "quality": row[2],
                "created_at": row[3],
            }
    finally:
        conn.close()
