import os
import json
from fastapi import APIRouter

router = APIRouter(prefix="/intraday", tags=["intraday"])

OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "/app/output")


@router.get("/latest")
def get_latest():
    path = os.path.join(OUTPUT_DIR, "intraday_check.json")
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {"values": {}, "alerts": [], "timestamp": None}


@router.get("/narrative-en")
def get_narrative_en():
    """Get the latest English narrative."""
    import glob
    pattern = os.path.join(OUTPUT_DIR, "narrative_en_*.md")
    files = sorted(glob.glob(pattern), reverse=True)
    if files:
        with open(files[0], encoding="utf-8") as f:
            return {"content": f.read(), "date": os.path.basename(files[0]).replace("narrative_en_", "").replace(".md", "")}
    return {"content": "", "date": ""}
def get_hidden_risk():
    path = os.path.join(OUTPUT_DIR, "hidden_risk_cache.json")
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {"total_boost": 0, "signals": [], "risk_narrative": ""}
