"""
WeChat Official Account publisher.

Publishes articles via the WeChat MP API:
  1. Get access_token (cached 2h)
  2. Upload thumb image
  3. Add draft
  4. Submit for publishing
"""

from __future__ import annotations

import os
import time
from typing import Optional, TYPE_CHECKING

import requests
from loguru import logger

if TYPE_CHECKING:
    from src.config import Settings

_BASE = "https://api.weixin.qq.com/cgi-bin"

_token_cache: dict = {"token": "", "expires_at": 0}
_thumb_cache: dict = {"media_id": ""}


class WechatPublisher:
    def __init__(self, settings: "Settings") -> None:
        self.app_id = settings.wechat_app_id
        self.app_secret = settings.wechat_app_secret

    def _get_access_token(self) -> str:
        now = time.time()
        if _token_cache["token"] and _token_cache["expires_at"] > now + 60:
            return _token_cache["token"]

        resp = requests.get(
            f"{_BASE}/token",
            params={
                "grant_type": "client_credential",
                "appid": self.app_id,
                "secret": self.app_secret,
            },
            timeout=10,
        )
        data = resp.json()
        if "access_token" not in data:
            raise RuntimeError(f"Failed to get access_token: {data}")

        _token_cache["token"] = data["access_token"]
        _token_cache["expires_at"] = now + data.get("expires_in", 7200)
        logger.info("WeChat access_token refreshed")
        return _token_cache["token"]

    def _get_thumb_media_id(self) -> str:
        if _thumb_cache["media_id"]:
            return _thumb_cache["media_id"]

        token = self._get_access_token()

        thumb_path = None
        output_dir = os.environ.get("OUTPUT_DIR", "/app/output")
        import glob
        cards = sorted(glob.glob(os.path.join(output_dir, "gfcri_card_*.png")), reverse=True)
        if cards:
            thumb_path = cards[0]

        if not thumb_path or not os.path.exists(thumb_path):
            thumb_path = self._generate_default_thumb()

        with open(thumb_path, "rb") as f:
            resp = requests.post(
                f"{_BASE}/material/add_material",
                params={"access_token": token, "type": "image"},
                files={"media": ("cover.png", f, "image/png")},
                timeout=30,
            )
        data = resp.json()
        if "media_id" not in data:
            raise RuntimeError(f"Failed to upload thumb: {data}")

        _thumb_cache["media_id"] = data["media_id"]
        logger.info(f"WeChat thumb uploaded: {data['media_id']}")
        return data["media_id"]

    def _generate_default_thumb(self) -> str:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(figsize=(2.1, 1.0), dpi=200)
        fig.patch.set_facecolor("#071018")
        ax.set_facecolor("#071018")
        ax.axis("off")
        ax.text(0.5, 0.5, "GFCRI", fontsize=24, color="#58a6ff", ha="center", va="center", fontweight="bold", transform=ax.transAxes)

        path = "/tmp/gfcri_thumb.png"
        plt.savefig(path, dpi=200, bbox_inches="tight", facecolor="#071018")
        plt.close(fig)
        return path

    def _add_draft(self, title: str, content: str, author: str = "GFCRI") -> str:
        import json as _json

        token = self._get_access_token()
        thumb_media_id = self._get_thumb_media_id()

        body = {
            "articles": [
                {
                    "title": title,
                    "author": author,
                    "content": content,
                    "thumb_media_id": thumb_media_id,
                    "content_source_url": "",
                    "need_open_comment": 0,
                    "only_fans_can_comment": 0,
                }
            ]
        }
        resp = requests.post(
            f"{_BASE}/draft/add",
            params={"access_token": token},
            data=_json.dumps(body, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json; charset=utf-8"},
            timeout=30,
        )
        data = resp.json()
        if "media_id" not in data:
            raise RuntimeError(f"Failed to add draft: {data}")

        media_id = data["media_id"]
        logger.info(f"WeChat draft created: media_id={media_id}")
        return media_id

    def _publish_draft(self, media_id: str) -> str:
        token = self._get_access_token()
        resp = requests.post(
            f"{_BASE}/freepublish/submit",
            params={"access_token": token},
            json={"media_id": media_id},
            timeout=30,
        )
        data = resp.json()
        if data.get("errcode", 0) != 0:
            raise RuntimeError(f"Failed to publish: {data}")

        publish_id = data.get("publish_id", "")
        logger.info(f"WeChat publish submitted: publish_id={publish_id}")
        return publish_id

    def publish_article(
        self,
        title: str,
        content: str,
        author: str = "GFCRI",
    ) -> Optional[str]:
        try:
            media_id = self._add_draft(title, content, author)
            logger.info(f"WeChat draft created: title={title}, media_id={media_id}")

            try:
                publish_id = self._publish_draft(media_id)
                logger.info(f"WeChat article published: publish_id={publish_id}")
                return publish_id
            except RuntimeError as e:
                if "48001" in str(e):
                    logger.info("WeChat freepublish not authorized (个人号限制), draft saved to 草稿箱")
                else:
                    logger.warning(f"WeChat publish step failed: {e}")
                return media_id

        except Exception as e:
            logger.error(f"WeChat publish failed: {e}")
            return None
