import os
import json
import asyncio
import logging
import datetime

from slack import methods
from aiohttp.web import json_response
from slack.events import Message
from slack.exceptions import SlackAPIError
from slack.io.aiohttp import SlackAPI

from .utils import ADMIN_CHANNEL

LOG = logging.getLogger(__name__)


def create_endpoints(plugin):
    plugin.on_action("topic_change", topic_change_revert, name="revert")
    plugin.on_action("topic_change", topic_change_validate, name="validate")

    plugin.on_action("pin_added", pin_added_validate, name="validate")
    plugin.on_action("pin_added", pin_added_revert, name="revert")

    plugin.on_action("report", report)
    plugin.on_action("tell_admin", tell_admin)
    plugin.on_action("make_snippet", make_snippet)

    plugin.on_action("user_cleanup", user_cleanup_cancel, name="cancel")
    plugin.on_action("user_cleanup", user_cleanup_confirm, name="confirm")


async def topic_change_revert(action, app):
    response = Message()
    response["channel"] = action["channel"]["id"]
    response["ts"] = action["message_ts"]
    response["attachments"] = action["original_message"]["attachments"]
    response["attachments"][0]["color"] = "danger"
    response["attachments"][0]["text"] = f'Change reverted by <@{action["user"]["id"]}>'
    del response["attachments"][0]["actions"]

    data = json.loads(action["actions"][0]["value"])
    await app.plugins["slack"].api.query(
        url=methods.CHANNELS_SET_TOPIC,
        data={"channel": data["channel"], "topic": data["old_topic"]},
    )

    await app.plugins["slack"].api.query(url=action["response_url"], data=response)


async def topic_change_validate(action, app):
    response = Message()
    response["channel"] = action["channel"]["id"]
    response["ts"] = action["message_ts"]
    response["attachments"] = action["original_message"]["attachments"]
    response["attachments"][0]["color"] = "good"
    response["attachments"][0][
        "text"
    ] = f'Change validated by <@{action["user"]["id"]}>'
    del response["attachments"][0]["actions"]

    await app.plugins["slack"].api.query(url=action["response_url"], data=response)


async def pin_added_validate(action, app):
    response = Message()
    response["channel"] = action["channel"]["id"]
    response["ts"] = action["message_ts"]
    response["attachments"] = action["original_message"]["attachments"]
    response["attachments"][0]["color"] = "good"
    response["attachments"][0][
        "pretext"
    ] = f'Pin validated by <@{action["user"]["id"]}>'
    del response["attachments"][0]["actions"]

    await app.plugins["slack"].api.query(url=action["response_url"], data=response)


async def pin_added_revert(action, app):
    response = Message()

    response["channel"] = action["channel"]["id"]
    response["ts"] = action["message_ts"]
    response["attachments"] = action["original_message"]["attachments"]
    response["attachments"][0]["color"] = "danger"
    response["attachments"][0]["pretext"] = f'Pin reverted by <@{action["user"]["id"]}>'
    del response["attachments"][0]["actions"]

    action_data = json.loads(action["actions"][0]["value"])
    remove_data = {"channel": action_data["channel"]}

    if action_data["item_type"] == "message":
        remove_data["timestamp"] = action_data["item_id"]
    elif action_data["item_type"] == "file":
        remove_data["file"] = action_data["item_id"]
    elif action_data["item_type"] == "file_comment":
        remove_data["file_comment"] = action_data["item_id"]
    else:
        raise TypeError(f'Unknown pin type: {action_data["type"]}')

    try:
        await app.plugins["slack"].api.query(url=methods.PINS_REMOVE, data=remove_data)
    except SlackAPIError as e:
        if e.error != "no_pin":
            raise

    await app.plugins["slack"].api.query(url=action["response_url"], data=response)


async def report(action, app):
    admin_msg = Message()
    admin_msg["channel"] = ADMIN_CHANNEL
    admin_msg["attachments"] = [
        {
            "fallback": f'Report from {action["user"]["name"]}',
            "title": f'Report from <@{action["user"]["id"]}>',
            "color": "danger",
            "fields": [
                {
                    "title": "User",
                    "value": f'<@{action["submission"]["user"]}>',
                    "short": True,
                }
            ],
        }
    ]

    if action["submission"]["channel"]:
        admin_msg["attachments"][0]["fields"].append(
            {
                "title": "Channel",
                "value": f'<#{action["submission"]["channel"]}>',
                "short": True,
            }
        )

    admin_msg["attachments"][0]["fields"].append(
        {"title": "Comment", "value": action["submission"]["comment"], "short": False}
    )

    await app.plugins["slack"].api.query(url=methods.CHAT_POST_MESSAGE, data=admin_msg)

    async with app["plugins"]["pg"].connection() as pg_con:
        await pg_con.execute(
            """INSERT INTO slack.reports ("user", channel, comment, by) VALUES ($1, $2, $3, $4)""",
            action["submission"]["user"],
            action["submission"]["channel"],
            action["submission"]["comment"],
            action["user"]["id"],
        )

    response = Message()
    response["response_type"] = "ephemeral"
    response["text"] = "Thank you for your report. An admin will look into it soon."

    await app.plugins["slack"].api.query(url=action["response_url"], data=response)


async def tell_admin(action, app):
    admin_msg = Message()
    admin_msg["channel"] = ADMIN_CHANNEL
    admin_msg["attachments"] = [
        {
            "fallback": f'Message from {action["user"]["name"]}',
            "title": f'Message from <@{action["user"]["id"]}>',
            "color": "good",
            "text": action["submission"]["message"],
        }
    ]

    await app.plugins["slack"].api.query(url=methods.CHAT_POST_MESSAGE, data=admin_msg)

    response = Message()
    response["response_type"] = "ephemeral"
    response["text"] = "Thank you for your message."

    await app.plugins["slack"].api.query(url=action["response_url"], data=response)


async def make_snippet(action, app):

    if not action["message"]["text"].startswith("```"):
        response = Message()
        response["channel"] = action["channel"]["id"]
        response["text"] = f"""```{action["message"]["text"]}```"""

        tip_message = Message()
        tip_message["channel"] = action["channel"]["id"]
        tip_message["user"] = action["message"]["user"]
        tip_message["text"] = (
            "Please use the snippet feature, or backticks, when sharing code. You can do so by "
            "clicking on the :heavy_plus_sign: on the left of the input box for a snippet.\n"
            "For more information on snippets click "
            "<https://get.slack.help/hc/en-us/articles/204145658-Create-a-snippet|here>.\n"
            "For more information on inline code formatting with backticks click "
            "<https://get.slack.help/hc/en-us/articles/202288908-Format-your-messages#inline-code|here>."
        )

        await asyncio.gather(
            app.plugins["slack"].api.query(
                url=methods.CHAT_POST_EPHEMERAL, data=tip_message
            ),
            app.plugins["slack"].api.query(
                url=methods.CHAT_POST_MESSAGE, data=response
            ),
        )
    else:
        response = Message()
        response["text"] = "Sorry I'm unable to format that message"
        await app.plugins["slack"].api.query(url=action["response_url"], data=response)


async def user_cleanup_cancel(action, app):
    response = Message()
    response["channel"] = action["channel"]["id"]
    response["ts"] = action["message_ts"]
    response["attachments"] = action["original_message"]["attachments"]
    response["attachments"][0]["color"] = "good"
    response["attachments"][0]["text"] = f'Cancelled by <@{action["user"]["id"]}>'
    del response["attachments"][0]["actions"]

    await app.plugins["slack"].api.query(url=action["response_url"], data=response)


async def user_cleanup_confirm(action, app):
    response = Message()
    response["channel"] = action["channel"]["id"]
    response["ts"] = action["message_ts"]
    response["attachments"] = action["original_message"]["attachments"]
    response["attachments"][0]["color"] = "good"
    response["attachments"][0][
        "text"
    ] = f'Cleanup confirmed by <@{action["user"]["id"]}>'
    del response["attachments"][0]["actions"]

    await app.plugins["slack"].api.query(url=action["response_url"], data=response)

    user_id = action["actions"][0]["value"]
    asyncio.create_task(_cleanup_user(app, user_id))


async def _cleanup_user(app, user):
    try:
        async with app["plugins"]["pg"].connection() as pg_con:
            messages = await pg_con.fetch(
                """SELECT id, channel FROM slack.messages WHERE "user" = $1""", user
            )

        api = SlackAPI(
            session=app["http_session"], token=os.environ["SLACK_ADMIN_TOKEN"]
        )
        for message in messages:
            try:
                data = {"channel": message["channel"], "ts": message["id"]}
                await api.query(url=methods.CHAT_DELETE, data=data)
            except SlackAPIError as e:
                if e.error == "message_not_found":
                    continue
                else:
                    LOG.exception(
                        "Failed to cleanup message %s in channel %s",
                        message["id"],
                        message["channel"],
                    )
            except Exception:
                LOG.exception(
                    "Failed to cleanup message %s in channel %s",
                    message["id"],
                    message["channel"],
                )
    except Exception:
        LOG.exception("Unexpected exception cleaning up user %s", user)
