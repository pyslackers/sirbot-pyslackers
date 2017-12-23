import os
import asyncio
import logging

from slack import methods
from slack.events import Message

LOG = logging.getLogger(__name__)
ANNOUCEMENTS_CHANNEL = os.environ.get('SLACK_ANNOUCEMENTS_CHANNEL') or 'annoucements'


def create_endpoints(plugin):
    plugin.on_event('team_join', team_join)
    plugin.on_event('team_joinr', total_members)


async def team_join(event, app):
    await asyncio.sleep(60)

    conversation = await app.plugin['slack'].api.query(url='conversations.open', date={'users': event['user']['id']})
    message = Message()
    message['text'] = '''Welcome to the community :tada:''' \
                      '''''' \
                      '''We are glad that you have decided to join us. We have documented a few things in the''' \
                      '''<{https://github.com/pyslackers/community/blob/master/introduction.md}|intro doc> to help''' \
                      '''you along from the beginning because we are grand believers in the Don't Repeat Yourself''' \
                      '''principle, and it just seems so professional!''' \
                      '''''' \
                      '''May your :taco:s be plentiful!'''

    message['channel'] = conversation['channel']['id']

    await app.plugin['slack'].api.query(url=methods.CHAT_POST_MESSAGE, data=message)


async def total_members(event, app):
    total_users = 0
    async for user in app.plugin['slack'].api.iter(url=methods.USERS_LIST, limit=500,
                                                   data={'presence': False, 'include_locale': False}):
        if not user['is_bot']:
            total_users += 1

    if total_users % 1000 == 0:
        message = Message()
        message['channel'] = ANNOUCEMENTS_CHANNEL
        message['text'] = f''':tada: Everyone give a warm welcome to <@{event['user']['id']}>  our {total_users}''' \
                          '''members ! :tada:'''
        await app.plugin['slack'].api.query(url=methods.CHAT_POST_MESSAGE, data=message)
