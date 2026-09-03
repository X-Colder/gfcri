import time
import asyncio
from functools import partial

from fastapi import APIRouter, Depends, Query, HTTPException

from api.access import require_deep_analysis
from src.storage.database import get_inference_history
from api.dependencies import get_reasoning_engine
from api.models.inference import (
    InferenceRequest,
    ObservationalRequest,
    InterventionalRequest,
    InferenceResponse,
)

router = APIRouter(prefix="/inference", tags=["inference"])


@router.post("/path-analysis", response_model=InferenceResponse)
async def path_analysis(req: InferenceRequest, user=Depends(require_deep_analysis)):
    start = time.time()
    loop = asyncio.get_event_loop()
    try:
        engine = await loop.run_in_executor(None, get_reasoning_engine)
        result = await loop.run_in_executor(
            None, partial(engine.path_analysis, req.source, req.target)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    elapsed = int((time.time() - start) * 1000)
    return InferenceResponse(
        inference_type="path_analysis",
        source=req.source,
        target=req.target,
        result=result,
        computation_time_ms=elapsed,
    )


@router.post("/observational", response_model=InferenceResponse)
async def observational(req: ObservationalRequest, user=Depends(require_deep_analysis)):
    start = time.time()
    loop = asyncio.get_event_loop()
    try:
        engine = await loop.run_in_executor(None, get_reasoning_engine)
        result = await loop.run_in_executor(
            None,
            partial(engine.observational_inference, req.source, req.target, req.source_value),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    elapsed = int((time.time() - start) * 1000)
    return InferenceResponse(
        inference_type="observational",
        source=req.source,
        target=req.target,
        result=result,
        computation_time_ms=elapsed,
    )


@router.post("/interventional", response_model=InferenceResponse)
async def interventional(req: InterventionalRequest, user=Depends(require_deep_analysis)):
    start = time.time()
    loop = asyncio.get_event_loop()
    try:
        engine = await loop.run_in_executor(None, get_reasoning_engine)
        result = await loop.run_in_executor(
            None,
            partial(engine.interventional_inference, req.source, req.target, req.intervention_value),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    elapsed = int((time.time() - start) * 1000)
    return InferenceResponse(
        inference_type="interventional",
        source=req.source,
        target=req.target,
        result=result,
        computation_time_ms=elapsed,
    )


@router.post("/confounding", response_model=InferenceResponse)
async def confounding(req: InferenceRequest, user=Depends(require_deep_analysis)):
    start = time.time()
    loop = asyncio.get_event_loop()
    try:
        engine = await loop.run_in_executor(None, get_reasoning_engine)
        result = await loop.run_in_executor(
            None,
            partial(engine.confounding_detection, req.source, req.target),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    elapsed = int((time.time() - start) * 1000)
    return InferenceResponse(
        inference_type="confounding",
        source=req.source,
        target=req.target,
        result=result,
        computation_time_ms=elapsed,
    )


@router.get("/history")
def inference_history(
    source: str = Query(default=None),
    target: str = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    user=Depends(require_deep_analysis),
):
    return get_inference_history(source_node=source, target_node=target, limit=limit)
