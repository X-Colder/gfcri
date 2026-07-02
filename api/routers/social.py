import glob
import os

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from api.models.social import SocialContentResponse

router = APIRouter(prefix="/social", tags=["social"])

OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "/app/output")


def _find_latest_file(pattern: str) -> str | None:
    files = sorted(glob.glob(os.path.join(OUTPUT_DIR, pattern)), reverse=True)
    return files[0] if files else None


@router.get("/wechat/latest", response_model=SocialContentResponse)
def latest_wechat():
    path = _find_latest_file("wechat_*.html")
    if not path:
        raise HTTPException(status_code=404, detail="No WeChat content available")
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    date_str = os.path.basename(path).replace("wechat_", "").replace(".html", "")
    return SocialContentResponse(date=date_str, content=content, content_type="html")


@router.get("/zsxq/latest", response_model=SocialContentResponse)
def latest_zsxq():
    path = _find_latest_file("zsxq_*.txt")
    if not path:
        raise HTTPException(status_code=404, detail="No Zsxq content available")
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    date_str = os.path.basename(path).replace("zsxq_", "").replace(".txt", "")
    return SocialContentResponse(date=date_str, content=content, content_type="text")


@router.get("/card/latest")
def latest_card():
    path = _find_latest_file("gfcri_card_*.png")
    if not path:
        raise HTTPException(status_code=404, detail="No share card available")
    return FileResponse(path, media_type="image/png")


@router.get("/charts/{chart_type}")
def get_chart(chart_type: str):
    path = _find_latest_file(f"{chart_type}_*.png")
    if not path:
        raise HTTPException(status_code=404, detail=f"No {chart_type} chart available")
    return FileResponse(path, media_type="image/png")
