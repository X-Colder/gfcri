from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.dependencies import init_cache, shutdown_cache
from api.middleware import ResilienceMiddleware
from api.routers import notifications
from api.routers import institutional_data, institutional_analysis, institutional_workspace
from api.routers import health, risk_index, daily_state, reports, inference, graph, social, alerts, ehs, industry, stress_test, crisis_distance, intraday, auth, billing, regime_assessment, causal_discovery, model_foundation, institutional_radar, core_themes, commercial_readiness, trade_risk, data_sources


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_cache()
    yield
    shutdown_cache()


app = FastAPI(
    title="GFCRI API",
    description="Global Financial Crisis Risk Index REST API",
    version="0.1.2",
    lifespan=lifespan,
)

app.add_middleware(ResilienceMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api")
app.include_router(risk_index.router, prefix="/api")
app.include_router(daily_state.router, prefix="/api")
app.include_router(reports.router, prefix="/api")
app.include_router(inference.router, prefix="/api")
app.include_router(graph.router, prefix="/api")
app.include_router(social.router, prefix="/api")
app.include_router(alerts.router, prefix="/api")
app.include_router(ehs.router, prefix="/api")
app.include_router(industry.router, prefix="/api")
app.include_router(stress_test.router, prefix="/api")
app.include_router(crisis_distance.router, prefix="/api")
app.include_router(intraday.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(billing.router, prefix="/api")
app.include_router(regime_assessment.router, prefix="/api")
app.include_router(causal_discovery.router, prefix="/api")
app.include_router(model_foundation.router, prefix="/api")
app.include_router(institutional_radar.router, prefix="/api")
app.include_router(core_themes.router, prefix="/api")
app.include_router(commercial_readiness.router, prefix="/api")
app.include_router(trade_risk.router, prefix="/api")
app.include_router(data_sources.router, prefix="/api")
app.include_router(institutional_data.router, prefix="/api")
app.include_router(institutional_analysis.router, prefix="/api")
app.include_router(institutional_workspace.router, prefix="/api")
app.include_router(notifications.router, prefix="/api")
