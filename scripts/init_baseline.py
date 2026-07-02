"""
首次运行：初始化因果图基线。
运行方式：docker compose exec app python scripts/init_baseline.py
"""
import sys

sys.path.insert(0, "/app")

from loguru import logger

from src.config import settings
from src.storage.database import wait_for_db
from src.storage.version_manager import GraphVersionManager
from src.models.graph import build_initial_causal_graph


def main():
    logger.info("=== Initializing Baseline Causal Graph ===")

    wait_for_db()

    graph = build_initial_causal_graph()
    logger.info(f"Built initial graph: {len(graph.nodes)} nodes, {len(graph.edges)} edges")

    vm = GraphVersionManager()

    existing = vm.get_active_version()
    if existing:
        logger.warning(f"Active graph version already exists: {existing['version_id']}")
        logger.info("Skipping initialization. Use --force to overwrite.")
        return

    version_id = vm.save_new_version(
        graph_dict=graph.to_dict(),
        change_type="initialization",
        change_summary="Initial causal graph with 17 nodes and 15+ edges based on macro risk design doc",
        created_by="init_script",
        auto_activate=True,
    )

    logger.info(f"Baseline graph saved as version: {version_id}")
    logger.info("Initialization complete. The daily scheduler will now track changes.")


if __name__ == "__main__":
    main()
