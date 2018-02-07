import os
import asyncio
import logging

from slack import methods
from slack.events import Message

LOG = logging.getLogger(__name__)
ANNOUCEMENTS_CHANNEL = os.environ.get('SLACK_ANNOUCEMENTS_CHANNEL') or 'annoucements'


def create_endpoints(plugin):
    plugin.on_event('team_join', team_join, wait=False)


async def team_join(event, app):
    await asyncio.sleep(60)

    message = Message()
    message['text'] = f'''Welcome to the community <@{event["user"]["id"]}> :tada: !\n''' \
                      '''We are glad that you have decided to join us.\n\n''' \
                      '''We have documented a few things in the ''' \
                      '''<https://github.com/pyslackers/community/blob/master/introduction.md|intro doc> to help ''' \
                      '''you along from the beginning because we are grand believers in the Don't Repeat Yourself ''' \
                      '''principle, and it just seems so professional!\n\n''' \
                      '''If you wish you can tell us a bit about yourself in this channel.\n\n''' \
                      '''May your :taco:s be plentiful!'''

    message['channel'] = 'introductions'
    message['user'] = event['user']['id']

    await app.plugins['slack'].api.query(url=methods.CHAT_POST_EPHEMERAL, data=message)
