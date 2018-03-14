import json
import logging

from slack import methods
from slack.events import Message

LOG = logging.getLogger(__name__)


def create_endpoints(plugin):
    plugin.on_action('gif_search', gif_search_ok, name='ok')
    plugin.on_action('gif_search', gif_search_next, name='next')
    plugin.on_action('gif_search', gif_search_cancel, name='cancel')
    plugin.on_action('gif_search', gif_search_previous, name='previous')
    plugin.on_action('topic_change', topic_change_revert, name='revert')
    plugin.on_action('topic_change', topic_change_validate, name='validate')
    plugin.on_action('recording', recording_cancel, name='cancel')
    plugin.on_action('recording', recording_message, name='message')
    plugin.on_action('recording', recording_emoji, name='emoji')


async def gif_search_ok(action, app):
    response = Message()
    response['channel'] = action['channel']['id']
    data = json.loads(action['actions'][0]['value'])

    response['attachments'] = [
        {
            'title': f'<@{action["user"]["id"]}> Searched giphy for: `{data["search"]}`',
            'fallback': f'<@{action["user"]["id"]}> Searched giphy for: `{data["search"]}`',
            'image_url': data['urls'][data['index']]
        }
    ]

    await app.plugins['slack'].api.query(url=methods.CHAT_POST_MESSAGE, data=response)

    confirm = Message()
    confirm['text'] = 'Gif successfully sent'
    confirm['attachments'] = []
    confirm['channel'] = action['channel']['id']
    confirm['ts'] = action['message_ts']
    await app.plugins['slack'].api.query(url=action['response_url'], data=confirm)


async def gif_search_next(action, app):
    response = _gif_search_next_previous(action, 1)
    await app.plugins['slack'].api.query(url=action['response_url'], data=response)


async def gif_search_previous(action, app):
    response = _gif_search_next_previous(action, -1)
    await app.plugins['slack'].api.query(url=action['response_url'], data=response)


def _gif_search_next_previous(action, index):
    response = Message()
    response['channel'] = action['channel']['id']
    response['ts'] = action['message_ts']

    data = json.loads(action['actions'][0]['value'])
    data['index'] += index
    url = data['urls'][data['index']]
    data_json = json.dumps(data)
    response['attachments'] = [
        {
            'title': f'<@{action["user"]["id"]}> Searched giphy for: `{data["search"]}`',
            'fallback': f'<@{action["user"]["id"]}> Searched giphy for: `{data["search"]}`',
            'image_url': url,
            'callback_id': 'gif_search',
            'actions': [
                {
                    'name': 'ok',
                    'text': 'Send',
                    'style': 'primary',
                    'value': data_json,
                    'type': 'button'
                },
                {
                    'name': 'cancel',
                    'text': 'Cancel',
                    'style': 'danger',
                    'value': data_json,
                    'type': 'button'
                },
            ]
        }
    ]

    if len(data['urls']) > data['index'] + 1:
        response['attachments'][0]['actions'].insert(1, {
            'name': 'next',
            'text': 'Next',
            'value': data_json,
            'type': 'button'
        })

    if data['index'] != 0:
        response['attachments'][0]['actions'].insert(1, {
            'name': 'previous',
            'text': 'Previous',
            'value': data_json,
            'type': 'button'
        })

    return response


async def gif_search_cancel(action, app):
    response = Message()
    response['channel'] = action['channel']['id']
    response['ts'] = action['message_ts']
    response['text'] = 'Cancelled'

    await app.plugins['slack'].api.query(url=action['response_url'], data=response)


async def topic_change_revert(action, app):
    response = Message()
    response['channel'] = action['channel']['id']
    response['ts'] = action['message_ts']
    response['attachments'] = action['original_message']['attachments']
    response['attachments'][0]['color'] = 'danger'
    response['attachments'][0]['text'] = f'Change reverted by <@{action["user"]["id"]}>'
    del response['attachments'][0]['actions']

    data = json.loads(action['actions'][0]['value'])
    await app.plugins['slack'].api.query(
        url=methods.CHANNELS_SET_TOPIC,
        data={'channel': data['channel'], 'topic': data['old_topic']}
    )

    await app.plugins['slack'].api.query(url=action['response_url'], data=response)


async def topic_change_validate(action, app):
    response = Message()
    response['channel'] = action['channel']['id']
    response['ts'] = action['message_ts']
    response['attachments'] = action['original_message']['attachments']
    response['attachments'][0]['color'] = 'good'
    response['attachments'][0]['text'] = f'Change validated by <@{action["user"]["id"]}>'
    del response['attachments'][0]['actions']

    await app.plugins['slack'].api.query(url=action['response_url'], data=response)


async def recording_cancel(action, app):
    recording_id = int(action['actions'][0]['value'])
    response = Message()
    response['channel'] = action['channel']['id']
    response['ts'] = action['message_ts']
    response['text'] = 'Cancelled'

    async with app['plugins']['pg'].connection() as pg_con:
        await pg_con.execute('''DELETE FROM slack.recordings WHERE id = $1''', recording_id)

    await app.plugins['slack'].api.query(url=action['response_url'], data=response)


async def recording_message(action, app):
    recording_id = int(action['actions'][0]['value'])

    response = Message()
    response['channel'] = action['channel']['id']
    response['ts'] = action['message_ts']

    async with app['plugins']['pg'].connection() as pg_con:
        result = await pg_con.fetchval(
            '''UPDATE slack.recordings SET "end" = (
            SELECT id FROM slack.messages WHERE id < $1 ORDER BY id DESC LIMIT 1
            ), commit = TRUE WHERE id = $2 RETURNING id''', action['message_ts'], recording_id)

    if result:
        response['text'] = 'Conversation successfully recorded.'
    else:
        response['text'] = 'Conversation not recorded. Please try again.'

    await app.plugins['slack'].api.query(url=action['response_url'], data=response)


async def recording_emoji(action, app):
    recording_id = int(action['actions'][0]['value'])
    async with app['plugins']['pg'].connection() as pg_con:
        created = await pg_con.fetchval(
            '''UPDATE slack.recordings SET commit = TRUE WHERE id = $1 AND "end" is NOT NULL RETURNING id''',
            recording_id)

    response = Message()
    response['channel'] = action['channel']['id']
    response['ts'] = action['message_ts']

    if created:
        response['text'] = 'Conversation successfully recorded.'
    else:
        async with app['plugins']['pg'].connection() as pg_con:
            exist = await pg_con.fetchval('''SELECT id FROM slack.recordings WHERE id = $1''', recording_id)

        if not exist:
            response['text'] = 'Conversation not recorded. Please try again.'
        else:
            response['text'] = '''*Could not find message with :stop_recording:*. \n\n''' \
                               '''Would you like to record this conversation ?'''
            response['attachments'] = [
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

    await app.plugins['slack'].api.query(url=action['response_url'], data=response)
