import logging
import datetime
import random

import pytz
from slack import methods
from slack.events import Message

LOG = logging.getLogger(__name__)


def create_jobs(scheduler, bot):
    scheduler.scheduler.add_job(slack_channel_list, "cron", hour=1, kwargs={"bot": bot})
    scheduler.scheduler.add_job(slack_users_list, "cron", hour=2, kwargs={"bot": bot})
    scheduler.scheduler.add_job(
        etc_finance_bell,
        "cron",
        day_of_week="0-4",
        hour=9,
        minute=30,
        timezone="America/New_York",
        kwargs={"bot": bot, "state": "open"},
    )
    scheduler.scheduler.add_job(
        etc_finance_bell,
        "cron",
        day_of_week="0-4",
        hour=16,
        timezone="America/New_York",
        kwargs={"bot": bot, "state": "closed"},
    )
    scheduler.scheduler.add_job(
        advent_of_code,
        "cron",
        month=12,
        day="1-25",
        hour=0,
        minute=5,
        second=0,
        timezone="America/New_York",
        kwargs={"bot": bot},
    )


async def advent_of_code(bot):
    LOG.info("Creating Advent Of Code threads...")
    for_day = datetime.datetime.now(tz=pytz.timezone("America/New_York"))
    year, day = for_day.year, for_day.day

    # megathread for all solutions at once (most solutions tend to use similar logic)
    message = Message()
    message["channel"] = "advent_of_code"
    message["attachments"] = [
        {
            "fallback": f"Advent Of Code {year} thread for Day {day}",
            "color": random.choice(["#ff0000", "#378b29"]),
            "title": f":santa: :christmas_tree: Advent of Code {year}: Day {day} :christmas_tree: :santa:",
            "title_link": f"https://adventofcode.com/{year}/day/{day}",
            "text": f"Post solutions to day {day} in this thread, in any language!",
            "footer": "Advent of Code",
            "footer_icon": "https://adventofcode.com/favicon.ico",
            "ts": int(for_day.timestamp()),
        }
    ]

    await bot["plugins"]["slack"].api.query(
        url=methods.CHAT_POST_MESSAGE, data=message
    )

    # threads for the part1/2 broken out
    for part in range(1, 3):
        message = Message()
        message["channel"] = "advent_of_code"
        message["attachments"] = [
            {
                "fallback": f"Advent Of Code {year} Thread for Day {day} Part {part}",
                "color": ["#ff0000", "#378b29"][  # red  # green
                    (part - 1) // 1
                ],  # red=part 1, green=part 2
                "title": f"Advent of Code {year}: Day {day} Part {part}",
                "title_link": f"https://adventofcode.com/{year}/day/{day}",
                "text": f"Post solutions to part {part} in this thread, in any language!",
                "footer": "Advent of Code",
                "footer_icon": "https://adventofcode.com/favicon.ico",
                "ts": int(for_day.timestamp()),
            }
        ]

        await bot["plugins"]["slack"].api.query(
            url=methods.CHAT_POST_MESSAGE, data=message
        )


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


async def etc_finance_bell(bot, state):
    LOG.info("Posting %s bell to #etc_finance", state)

    holidays = [
        datetime.date(2019, 2, 18),
        datetime.date(2019, 4, 19),
        datetime.date(2019, 5, 27),
        datetime.date(2019, 7, 4),
        datetime.date(2019, 9, 2),
        datetime.date(2019, 11, 28),
        datetime.date(2019, 12, 25),
    ]

    message = Message()

    message["channel"] = "etc_finance"

    if datetime.date.today() in holidays:
        message[
            "text"
        ] = """:bell: :bell: :bell: The US Stock Market is *CLOSED for holiday*. :bell: :bell: :bell:"""

        state = "holiday"

    elif state == "open":
        message[
            "text"
        ] = """:bell: :bell: :bell: The US Stock Market is now *OPEN* for trading. :bell: :bell: :bell:"""

    elif state == "closed":
        message[
            "text"
        ] = """:bell: :bell: :bell: The US Stock Market is now *CLOSED* for trading. :bell: :bell: :bell:"""

    await bot["plugins"]["slack"].api.query(url=methods.CHAT_POST_MESSAGE, data=message)
