"""
Economy Health Score (EHS) - Database storage.

Persists indicator data and scores to PostgreSQL.
"""

from __future__ import annotations

from typing import Optional
from datetime import date

from psycopg2.extras import Json, RealDictCursor, execute_values
from loguru import logger

from src.storage.database import get_connection


def save_market_data_batch(rows: list[tuple]):
    """Save batch of (ticker, trade_date, close_price, volume) tuples."""
    if not rows:
        return
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            execute_values(
                cur,
                """
                INSERT INTO market_data_daily (ticker, trade_date, close_price, volume)
                VALUES %s
                ON CONFLICT (ticker, trade_date) DO UPDATE SET
                    close_price = EXCLUDED.close_price,
                    volume = EXCLUDED.volume
                """,
                rows,
            )
        conn.commit()
        logger.info(f"Saved {len(rows)} market data rows")
    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to save market data: {e}")
    finally:
        conn.close()


def save_indicator_data_batch(rows: list[tuple]):
    """Save batch of (economy_code, indicator_code, reference_date, raw_value, transformed_value, z_score, data_source)."""
    if not rows:
        return
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            execute_values(
                cur,
                """
                INSERT INTO ehs_indicator_data
                    (economy_code, indicator_code, reference_date, raw_value, transformed_value, z_score, data_source)
                VALUES %s
                ON CONFLICT (economy_code, indicator_code, reference_date) DO UPDATE SET
                    raw_value = EXCLUDED.raw_value,
                    transformed_value = EXCLUDED.transformed_value,
                    z_score = EXCLUDED.z_score
                """,
                rows,
            )
        conn.commit()
        logger.info(f"Saved {len(rows)} indicator data rows")
    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to save indicator data: {e}")
    finally:
        conn.close()


def save_ehs_score(
    economy_code: str,
    score_date: str,
    ehs_score: float,
    growth_score: float,
    labor_score: float,
    price_score: float,
    external_score: float,
    financial_score: float,
    cycle_phase: str,
    score_change_1m: Optional[float] = None,
    indicator_details: Optional[dict] = None,
):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO ehs_scores
                    (economy_code, score_date, ehs_score, growth_score, labor_score,
                     price_score, external_score, financial_score, cycle_phase,
                     score_change_1m, indicator_details)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (economy_code, score_date) DO UPDATE SET
                    ehs_score = EXCLUDED.ehs_score,
                    growth_score = EXCLUDED.growth_score,
                    labor_score = EXCLUDED.labor_score,
                    price_score = EXCLUDED.price_score,
                    external_score = EXCLUDED.external_score,
                    financial_score = EXCLUDED.financial_score,
                    cycle_phase = EXCLUDED.cycle_phase,
                    score_change_1m = EXCLUDED.score_change_1m,
                    indicator_details = EXCLUDED.indicator_details
                """,
                (
                    economy_code, score_date, ehs_score, growth_score, labor_score,
                    price_score, external_score, financial_score, cycle_phase,
                    score_change_1m, Json(indicator_details),
                ),
            )
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Failed to save EHS score for {economy_code}: {e}")
    finally:
        conn.close()


def get_latest_ehs_scores() -> list[dict]:
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT DISTINCT ON (economy_code)
                    economy_code, score_date, ehs_score, growth_score, labor_score,
                    price_score, external_score, financial_score, cycle_phase,
                    score_change_1m, indicator_details
                FROM ehs_scores
                ORDER BY economy_code, score_date DESC
            """)
            return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()


def get_ehs_score_history(economy_code: str, limit: int = 30) -> list[dict]:
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT score_date, ehs_score, growth_score, labor_score,
                       price_score, external_score, financial_score, cycle_phase, score_change_1m
                FROM ehs_scores
                WHERE economy_code = %s
                ORDER BY score_date DESC
                LIMIT %s
                """,
                (economy_code, limit),
            )
            return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()


def get_indicator_history(
    economy_code: str, indicator_code: str, limit: int = 36
) -> list[dict]:
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT reference_date, raw_value, transformed_value, z_score
                FROM ehs_indicator_data
                WHERE economy_code = %s AND indicator_code = %s
                ORDER BY reference_date DESC
                LIMIT %s
                """,
                (economy_code, indicator_code, limit),
            )
            return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()
