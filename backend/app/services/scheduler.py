"""Nightly parser cron — runs every source across every city, off-peak.

Opt-in via PARSER_CRON_ENABLED (default off) so a live fetch never surprises a demo.
The job is sequential and guarded by parse_runner's lock; `max_instances=1` + `coalesce`
mean a long run is never stacked on top of itself.
"""

import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import settings
from app.services.parse_runner import run_all_cities

logger = logging.getLogger(__name__)


def _job() -> None:
    logger.info("cron: starting daily all-cities parse")
    ran = run_all_cities()
    logger.info("cron: parse %s", "finished" if ran else "skipped (already running)")


def create_scheduler() -> BackgroundScheduler | None:
    """Start and return the scheduler, or None when the cron is disabled."""
    if not settings.PARSER_CRON_ENABLED:
        logger.info("parser cron disabled (PARSER_CRON_ENABLED=false)")
        return None

    scheduler = BackgroundScheduler(timezone=settings.PARSER_CRON_TIMEZONE)
    scheduler.add_job(
        _job,
        CronTrigger(hour=settings.PARSER_CRON_HOUR, minute=settings.PARSER_CRON_MINUTE),
        id="parse_all_cities",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    scheduler.start()
    logger.info(
        "parser cron scheduled daily at %02d:%02d %s",
        settings.PARSER_CRON_HOUR,
        settings.PARSER_CRON_MINUTE,
        settings.PARSER_CRON_TIMEZONE,
    )
    return scheduler
