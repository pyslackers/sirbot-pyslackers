import logging

from slack import methods
from slack.events import Message

LOG = logging.getLogger(__name__)


def register(readthedocs):
    readthedocs.register_project('sir-bot-a-lot', handlers=[build_failure, ],)
    readthedocs.register_project('slack-sansio', handlers=[build_failure, ],)


async def build_failure(data, app):
    msg = Message()
    msg['channel'] = 'community_projects'
    msg['text'] = f'''Building of {data["name"]} documentation failed ! :cry:'''
    await app.plugins['slack'].api.query(methods.CHAT_POST_MESSAGE, data=msg)
