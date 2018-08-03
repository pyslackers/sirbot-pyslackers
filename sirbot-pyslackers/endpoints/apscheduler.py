import logging
import datetime

from slack import methods

LOG = logging.getLogger(__name__)


def create_jobs(scheduler, bot):
    scheduler.scheduler.add_job(
        slack_channel_list,
        "date",
        kwargs={"bot": bot},
        run_date=datetime.datetime.now() + datetime.timedelta(minutes=2),
    )
    scheduler.scheduler.add_job(
        slack_users_list,
        "date",
        kwargs={"bot": bot},
        run_date=datetime.datetime.now() + datetime.timedelta(minutes=4),
    )

    scheduler.scheduler.add_job(slack_channel_list, "cron", hour=1, kwargs={"bot": bot})
    scheduler.scheduler.add_job(slack_users_list, "cron", hour=2, kwargs={"bot": bot})


async def slack_channel_list(bot):
    LOG.info("Updating list of slack channels...")
    async with bot["plugins"]["pg"].connection() as pg_con:
        async for channel in bot["plugins"]["slack"].api.iter(
            methods.CHANNELS_LIST, minimum_time=3, data={"exclude_members": True}
        ):
            await pg_con.execute(
                """INSERT INTO slack.channels (id, raw) VALUES ($1, $2)
                                    ON CONFLICT (id) DO UPDATE SET raw = $2""",
                channel["id"],
                channel,
            )
    LOG.info("List of slack channels up to date.")


async def slack_users_list(bot):
    LOG.info("Updating list of slack users...")
    async with bot["plugins"]["pg"].connection() as pg_con:
        async for user in bot["plugins"]["slack"].api.iter(
            methods.USERS_LIST, minimum_time=12
        ):
            await pg_con.execute(
                """INSERT INTO slack.users (id, name, deleted, admin, bot, raw) VALUES
                                    ($1, $2, $3, $4, $5, $6) ON CONFLICT (id) DO UPDATE SET
                                    name = $2, deleted = $3, admin = $4, bot = $5, raw = $6""",
                user["id"],
                user["profile"]["display_name"],
                user.get("deleted", False),
                user.get("is_admin", False),
                user.get("is_bot", False),
                user,
            )
    LOG.info("List of slack users up to date")
