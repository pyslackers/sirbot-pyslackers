import os
import asyncio
import logging

from slack import methods
from slack.events import Message

LOG = logging.getLogger(__name__)
ANNOUCEMENTS_CHANNEL = os.environ.get('SLACK_ANNOUCEMENTS_CHANNEL') or 'annoucements'


def create_endpoints(plugin):
    plugin.on_event('team_join', team_join, wait=False)
    plugin.on_event('reaction_added', start_recording)
    plugin.on_event('reaction_added', stop_recording)


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


async def start_recording(event, app):

    if event['reaction'] == 'start_recording' and 'item' in event and event['item']['type'] == 'message':

        async with app['plugins']['pg'].connection() as pg_con:
            recording_id = await pg_con.fetchval(
                '''INSERT INTO slack.recordings (start, "user", channel) VALUES ($1, $2, $3) RETURNING id''',
                event['item']['ts'], event['user'], event['item']['channel']
            )

        message = Message()
        message['text'] = 'Would you like to record this conversation ?'
        message['attachments'] = [
            {
                'fallback': 'start recording',
                'callback_id': 'recording',
                'actions': [
                    {
                        'name': 'message',
                        'text': 'Yes, Until this message',
                        'style': 'primary',
                        'type': 'button',
                        'value': recording_id
                    },
                    {
                        'name': 'emoji',
                        'text': 'Yes, Until the :stop_recording: emoji',
                        'style': 'primary',
                        'type': 'button',
                        'value': recording_id
                    },
                    {
                        'name': 'cancel',
                        'text': 'Cancel',
                        'style': 'danger',
                        'type': 'button',
                        'value': recording_id
                    }
                ]
            },
        ]

        message['channel'] = event['item']['channel']
        message['user'] = event['user']

        await app.plugins['slack'].api.query(url=methods.CHAT_POST_EPHEMERAL, data=message)


async def stop_recording(event, app):

    if event['reaction'] == 'stop_recording' and 'item' in event and event['item']['type'] == 'message':
        async with app['plugins']['pg'].connection() as pg_con:
            await pg_con.execute(
                '''UPDATE slack.recordings SET "end" = $1 WHERE id = (SELECT id FROM slack.recordings WHERE "user" = $2
                AND channel = $3 AND "end" is NULL ORDER BY created ASC LIMIT 1)''',
                event['item']['ts'], event['user'], event['item']['channel']
            )
