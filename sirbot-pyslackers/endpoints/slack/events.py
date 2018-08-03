import json
import asyncio
import logging

from slack import methods
from slack.events import Message

from .utils import ADMIN_CHANNEL

LOG = logging.getLogger(__name__)


def create_endpoints(plugin):
    plugin.on_event("team_join", team_join, wait=False)
    plugin.on_event("pin_added", pin_added)


async def team_join(event, app):
    await asyncio.sleep(60)

    message = Message()
    message[
        "text"
    ] = f"""Welcome to the community <@{event["user"]["id"]}> :tada: !\n""" """We are glad that you have decided to join us.\n\n""" """We have documented a few things in the """ """<https://github.com/pyslackers/community/blob/master/introduction.md|intro doc> to help """ """you along from the beginning because we are grand believers in the Don't Repeat Yourself """ """principle, and it just seems so professional!\n\n""" """If you wish you can tell us a bit about yourself in this channel.\n\n""" """May your :taco:s be plentiful!"""

    message["channel"] = "introductions"
    message["user"] = event["user"]["id"]

    await app.plugins["slack"].api.query(url=methods.CHAT_POST_EPHEMERAL, data=message)


async def pin_added(event, app):

    if event["user"] not in app["plugins"]["slack"].admins:

        message = Message()
        message["channel"] = ADMIN_CHANNEL
        message["attachments"] = [
            {
                "fallback": "Pin added notice",
                "title": f'Pin added in channel <#{event["channel_id"]}> by <@{event["user"]}>',
                "callback_id": "pin_added",
            }
        ]

        if event["item"]["type"] == "message":
            message["attachments"][0]["text"] = event["item"]["message"]["text"]
            item_id = event["item"]["message"]["ts"]
        elif event["item"]["type"] == "file":
            file = await app["plugins"]["slack"].api.query(
                url=methods.FILES_INFO, data={"file": event["item"]["file_id"]}
            )
            message["attachments"][0]["text"] = f'File: {file["file"]["title"]}'
            item_id = event["item"]["file_id"]
        elif event["item"]["type"] == "file_comment":
            message["attachments"][0]["text"] = event["item"]["comment"]["comment"]
            item_id = event["item"]["comment"]["id"]
        else:
            message["attachments"][0]["text"] = "Unknown pin type"
            await app.plugins["slack"].api.query(
                url=methods.CHAT_POST_MESSAGE, data=message
            )
            return

        message["attachments"][0]["actions"] = [
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
                    {
                        "channel": event["channel_id"],
                        "item_type": event["item"]["type"],
                        "item_id": item_id,
                    }
                ),
                "type": "button",
            },
        ]

        await app.plugins["slack"].api.query(
            url=methods.CHAT_POST_MESSAGE, data=message
        )
