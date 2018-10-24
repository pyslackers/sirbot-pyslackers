import re
import json
import pprint
import logging
import datetime

from slack import methods
from aiohttp import ClientResponseError
from slack.events import Message
from slack.exceptions import SlackAPIError
from asyncpg.exceptions import UniqueViolationError

from .utils import ADMIN_CHANNEL

LOG = logging.getLogger(__name__)
STOCK_REGEX = re.compile(r"\$\b(?P<symbol>[A-Z.]{1,5})\b")
TELL_REGEX = re.compile("tell (<(#|@)(?P<to_id>[A-Z0-9]*)(|.*)?>) (?P<msg>.*)")


def create_endpoints(plugin):
    plugin.on_message("hello", hello, flags=re.IGNORECASE, mention=True)
    plugin.on_message("^tell", tell, flags=re.IGNORECASE, mention=True, admin=True)
    plugin.on_message(".*", mention, flags=re.IGNORECASE, mention=True)
    plugin.on_message(".*", save_in_database, wait=False)
    plugin.on_message(".*", channel_topic, subtype="channel_topic")
    plugin.on_message("g#", github_repo_link)
    plugin.on_message(
        "^inspect", inspect, flags=re.IGNORECASE, mention=True, admin=True
    )
    plugin.on_message("^help", help_message, flags=re.IGNORECASE, mention=True)
    # stock tickers are 1-5 capital characters, with a dot allowed. To keep
    # this from triggering with random text we require a leading '$'
    plugin.on_message("s\$[A-Z\.]{1,5}", stock_quote, wait=False)


async def stock_quote(message, app):
    match = STOCK_REGEX.search(message.get("text", ""))
    if not match:
        return

    symbol = match.group("symbol")
    LOG.debug("Fetching stock quotes for symbol %s", symbol)

    response = message.response()
    try:
        stocks = app["plugins"]["stocks"]
        quote = (await stocks.book(symbol))["quote"]
        logo = (await stocks.logo(symbol))["url"]
        LOG.debug("Quote from IEX API: %s", quote)
    except ClientResponseError as e:
        if e.status == 404:
            response["text"] = f"The symbol `{symbol}` could not be found."
        else:
            LOG.error("Error retrieving stock quotes: %s", e)
            response["text"] = "Unable to retrieve quotes right now."
    else:
        # Sometimes the API returns None records. We remove them here.
        quote = {k: v for k, v in quote.items() if v is not None}
        change = quote.get("change", 0)
        color = "gray"
        if change > 0:
            color = "good"
        elif change < 0:
            color = "danger"

        response.update(
            attachments=[
                {
                    "color": color,
                    "thumb_url": logo,
                    "title": f'{quote["symbol"]} ({quote["companyName"]}): '
                    f'${quote["latestPrice"]:,.4f}',
                    "title_link": f"https://finance.yahoo.com/quote/{symbol}",
                    "fields": [
                        {
                            "title": "Change",
                            "value": f'${quote.get("change", 0):,.4f} (%{quote.get("changePercent", 0) * 100:,.4f})',
                            "short": True,
                        },
                        {
                            "title": "Volume",
                            "value": f'{quote["latestVolume"]:,}',
                            "short": True,
                        },
                        {
                            "title": "Open",
                            "value": f'${quote["open"]:,.4f}',
                            "short": True,
                        },
                        {
                            "title": "Close",
                            "value": f'${quote.get("close", 0):,.4f}',
                            "short": True,
                        },
                        {
                            "title": "Low",
                            "value": f'${quote["low"]:,.4f}',
                            "short": True,
                        },
                        {
                            "title": "High",
                            "value": f'${quote["high"]:,.4f}',
                            "short": True,
                        },
                    ],
                    "footer": f"Data provided for free by "
                    f"<https://iextrading.com/developer|IEX>. View "
                    f"<https://iextrading.com/api-exhibit-a/|"
                    f"IEX's Terms of Use>.",
                    "footer_icon": "https://iextrading.com/apple-touch-icon.png",  # noqa
                    "ts": quote.get("latestUpdate", 0) / 1000,
                }
            ]
        )
    await app["plugins"]["slack"].api.query(
        url=methods.CHAT_POST_MESSAGE, data=response
    )


async def hello(message, app):
    response = message.response()
    response["text"] = "Hello <@{user}>".format(user=message["user"])
    await app["plugins"]["slack"].api.query(
        url=methods.CHAT_POST_MESSAGE, data=response
    )


async def help_message(message, app):
    response = message.response()
    response["text"] = "Sir Bot-a-lot help"
    response["attachments"] = [
        {
            "color": "good",
            "fields": [
                {
                    "title": "@sir_botalot hello",
                    "value": f"Say hello to sir_botalot.",
                    "short": True,
                },
                {
                    "title": "/report",
                    "value": "Report an offending user to the admin team.",
                    "short": True,
                },
                {
                    "title": "/gif search terms",
                    "value": "Search for a gif on giphy.com .",
                    "short": True,
                },
                {
                    "title": "/pypi search terms",
                    "value": "Search for packages on pypi.org .",
                    "short": True,
                },
                {
                    "title": "/sponsors",
                    "value": "Referal links from our sponsors.",
                    "short": True,
                },
                {
                    "title": "/snippet",
                    "value": "Instruction on creating a slack code snippet.",
                    "short": True,
                },
                {
                    "title": "g#user/repo",
                    "value": "Share the link to that github repo. User default to `pyslackers`.",
                },
                {
                    "title": "s$TICKER",
                    "value": "Retrieve today's prices for the provided stock ticker.",
                },
            ],
        }
    ]

    await app["plugins"]["slack"].api.query(
        url=methods.CHAT_POST_MESSAGE, data=response
    )


async def tell(message, app):
    match = TELL_REGEX.match(message["text"])
    response = message.response()

    if match:
        to_id = match.group("to_id")
        msg = match.group("msg")

        if to_id.startswith(("C", "U")):
            response["text"] = msg
            response["channel"] = to_id
        else:
            response["text"] = "Sorry I can not understand the destination."
    else:
        response["text"] = "Sorry I can not understand"

    await app["plugins"]["slack"].api.query(
        url=methods.CHAT_POST_MESSAGE, data=response
    )


async def mention(message, app):
    try:
        if message["user"] != app["plugins"]["slack"].bot_user_id:
            await app["plugins"]["slack"].api.query(
                url=methods.REACTIONS_ADD,
                data={
                    "name": "sirbot",
                    "channel": message["channel"],
                    "timestamp": message["ts"],
                },
            )
    except SlackAPIError as e:
        if e.error != "already_reacted":
            raise


async def save_in_database(message, app):
    if "pg" in app["plugins"]:
        LOG.debug('Saving message "%s" to database.', message["ts"])

        if message["ts"]:  # We sometimes receive message without a timestamp. See #45
            try:
                async with app["plugins"]["pg"].connection() as pg_con:
                    await pg_con.execute(
                        """INSERT INTO slack.messages (id, text, "user", channel, raw, time)
                        VALUES ($1, $2, $3, $4, $5, $6)""",
                        message["ts"],
                        message.get("text"),
                        message.get("user"),
                        message.get("channel"),
                        dict(message),
                        datetime.datetime.fromtimestamp(
                            int(message["ts"].split(".")[0])
                        ),
                    )
            except UniqueViolationError:
                LOG.debug('Message "%s" already in database.', message["ts"])


async def channel_topic(message, app):

    if (
        message["user"] not in app["plugins"]["slack"].admins
        and message["user"] != app["plugins"]["slack"].bot_user_id
    ):

        async with app["plugins"]["pg"].connection() as pg_con:
            channel = await pg_con.fetchrow(
                """SELECT raw FROM slack.channels WHERE id = $1""", message["channel"]
            )
            LOG.debug(channel)
            if channel:
                old_topic = channel["raw"]["topic"]["value"]
            else:
                old_topic = "Original topic not found"

        response = Message()
        response["channel"] = ADMIN_CHANNEL
        response["attachments"] = [
            {
                "fallback": "Channel topic changed notice: old topic",
                "title": f'<@{message["user"]}> changed <#{message["channel"]}> topic.',
                "fields": [
                    {"title": "Previous topic", "value": old_topic},
                    {"title": "New topic", "value": message["topic"]},
                ],
            }
        ]

        if channel:
            response["attachments"][0]["callback_id"] = "topic_change"
            response["attachments"][0]["actions"] = [
                {
                    "name": "validate",
                    "text": "Validate",
                    "style": "primary",
                    "type": "button",
                },
                {
                    "name": "revert",
                    "text": "Revert",
                    "style": "danger",
                    "value": json.dumps(
                        {"channel": message["channel"], "old_topic": old_topic}
                    ),
                    "type": "button",
                },
            ]

        await app["plugins"]["slack"].api.query(
            url=methods.CHAT_POST_MESSAGE, data=response
        )


async def github_repo_link(message, app):
    if "text" in message and message["text"]:
        response = message.response()

        for i in range(0, message["text"].count("g#")):
            start = message["text"].find("g#") + 2
            repo = message["text"][start:].split()[0]

            # Remove occurrence so we don't use it again
            len_to_remove = (start + len(repo)) + 2
            message["text"] = message["text"][len_to_remove:]

            if "/" not in repo:
                repo = "pyslackers/" + repo

            url = f"https://github.com/{repo}"
            r = await app["http_session"].request("GET", url)

            if r.status == 200:
                response["text"] = url
                await app["plugins"]["slack"].api.query(
                    url=methods.CHAT_POST_MESSAGE, data=response
                )


async def inspect(message, app):
    if message["channel"] == ADMIN_CHANNEL and "text" in message and message["text"]:
        response = message.response()
        match = re.search("<@(.*)>", message["text"])

        if match:
            user_id = match.group(1)

            async with app["plugins"]["pg"].connection() as pg_con:
                data = await pg_con.fetchrow(
                    """SELECT raw, join_date FROM slack.users WHERE id = $1""", user_id
                )

            if data:
                user = data["raw"]
                user["join_date"] = data["join_date"].isoformat()
            else:
                data = await app["plugins"]["slack"].api.query(
                    url=methods.USERS_INFO, data={"user": user_id}
                )
                user = data["user"]

            response[
                "text"
            ] = f"<@{user_id}> profile information \n```{pprint.pformat(user)}```"
        else:
            response["text"] = f"Sorry I couldn't figure out which user to inspect"

        await app["plugins"]["slack"].api.query(
            url=methods.CHAT_POST_MESSAGE, data=response
        )
