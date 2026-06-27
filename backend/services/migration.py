from __future__ import annotations

import asyncio
import os

from alembic.config import Config
from alembic.command import upgrade as alembic_upgrade


def _get_alembic_config() -> Config:
    alembic_root = os.path.join(os.path.dirname(__file__), "..", "alembic.ini")
    cfg = Config(os.path.abspath(alembic_root))
    env_url = os.environ.get("DATABASE_URL", "").strip()
    if env_url:
        cfg.set_main_option("sqlalchemy.url", env_url)
    return cfg


async def run_migrations() -> None:
    """Run Alembic migrations up to the latest revision."""
    cfg = _get_alembic_config()
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, alembic_upgrade, cfg, "head")
