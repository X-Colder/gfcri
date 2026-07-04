from fastapi import APIRouter

from api.models.commercial_readiness import CommercialReadinessResponse
from src.engines.causal_validation import causal_validation_report
from src.engines.commercial_readiness import commercial_readiness
from src.engines.data_quality import data_quality_assessment
from src.engines.private_deployment import private_deployment_readiness
from src.engines.product_packaging import product_packaging

router = APIRouter(prefix="/commercial-readiness", tags=["commercial-readiness"])


@router.get("/latest", response_model=CommercialReadinessResponse)
def latest_commercial_readiness():
    return commercial_readiness()


@router.get("/data-quality")
def data_quality():
    return data_quality_assessment()


@router.get("/causal-validation")
def causal_validation(limit: int = 50):
    return causal_validation_report(limit=limit)


@router.get("/packaging")
def packaging():
    return product_packaging()


@router.get("/private-deployment")
def private_deployment():
    return private_deployment_readiness()
