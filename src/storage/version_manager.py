from datetime import datetime
from typing import Optional

from psycopg2.extras import Json, RealDictCursor
from loguru import logger

from src.storage.database import get_connection


class GraphVersionManager:
    def save_new_version(
        self,
        graph_dict: dict,
        change_type: str,
        change_summary: str,
        created_by: str = "system",
        parent_version: Optional[str] = None,
        auto_activate: bool = True,
    ) -> str:
        version_id = f"v{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                if auto_activate and parent_version:
                    cur.execute(
                        "UPDATE causal_graph_versions SET is_active = FALSE WHERE is_active = TRUE"
                    )
                cur.execute(
                    """
                    INSERT INTO causal_graph_versions
                        (version_id, parent_version, created_by, change_type,
                         change_summary, is_active, graph_snapshot)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        version_id,
                        parent_version,
                        created_by,
                        change_type,
                        change_summary,
                        auto_activate,
                        Json(graph_dict),
                    ),
                )
            conn.commit()
            logger.info(f"Graph version {version_id} saved ({change_type})")
            return version_id
        finally:
            conn.close()

    def get_active_version(self) -> Optional[dict]:
        conn = get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT * FROM causal_graph_versions WHERE is_active = TRUE LIMIT 1"
                )
                row = cur.fetchone()
                return dict(row) if row else None
        finally:
            conn.close()

    def get_version(self, version_id: str) -> Optional[dict]:
        conn = get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    "SELECT * FROM causal_graph_versions WHERE version_id = %s",
                    (version_id,),
                )
                row = cur.fetchone()
                return dict(row) if row else None
        finally:
            conn.close()

    def list_versions(self, limit: int = 20) -> list[dict]:
        conn = get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT version_id, parent_version, created_at, created_by,
                           change_type, change_summary, is_active
                    FROM causal_graph_versions
                    ORDER BY created_at DESC LIMIT %s
                    """,
                    (limit,),
                )
                return [dict(row) for row in cur.fetchall()]
        finally:
            conn.close()
