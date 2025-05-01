import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from scheduler_service.app.core.config import settings
from scheduler_service.app.jobs import order_updates, promotions

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = AsyncIOScheduler(timezone="UTC") # Use UTC timezone

def setup_scheduler():
    """Adds jobs to the scheduler."""
    logger.info("Setting up scheduler jobs...")

    try:
        # Add Order Update Job
        scheduler.add_job(
            order_updates.check_order_statuses_job,
            trigger=IntervalTrigger(seconds=settings.ORDER_UPDATE_JOB_INTERVAL_SECONDS),
            id="order_update_job",
            name="Check Mock Order Statuses",
            replace_existing=True,
            max_instances=1, # Ensure only one instance runs at a time
            coalesce=True, # Run once if multiple trigger times were missed
            misfire_grace_time=30 # Allow 30 seconds tolerance for misfires
        )
        logger.info(f"Added job 'order_update_job' with interval {settings.ORDER_UPDATE_JOB_INTERVAL_SECONDS} seconds.")

        # Add Promotion Job
        scheduler.add_job(
            promotions.send_promotional_notifications_job,
            trigger=IntervalTrigger(seconds=settings.PROMOTION_JOB_INTERVAL_SECONDS),
            id="promotion_job",
            name="Send Promotional Notifications",
            replace_existing=True,
            max_instances=1,
            coalesce=True,
            misfire_grace_time=60
        )
        logger.info(f"Added job 'promotion_job' with interval {settings.PROMOTION_JOB_INTERVAL_SECONDS} seconds.")

    except Exception as e:
        logger.error(f"Error setting up scheduler jobs: {e}", exc_info=True)
        # Depending on severity, might want to raise exception or exit


def start_scheduler():
    """Starts the scheduler if it's not already running."""
    if not scheduler.running:
        logger.info("Starting APScheduler...")
        scheduler.start()
        logger.info("APScheduler started.")
    else:
        logger.info("APScheduler is already running.")

def stop_scheduler():
    """Stops the scheduler."""
    if scheduler.running:
        logger.info("Shutting down APScheduler...")
        # wait=False makes it non-blocking, True waits for running jobs to complete
        scheduler.shutdown(wait=False)
        logger.info("APScheduler shut down.")
    else:
        logger.info("APScheduler is not running.")