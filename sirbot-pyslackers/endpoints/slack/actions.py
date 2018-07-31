import json
import logging
import datetime


from slack import methods
from slack.events import Message
from slack.exceptions import SlackAPIError
from aiohttp.web import json_response

from .utils import ADMIN_CHANNEL

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

    plugin.on_action('pin_added', pin_added_validate, name='validate')
    plugin.on_action('pin_added', pin_added_revert, name='revert')

    plugin.on_action('report', report)
    plugin.on_action('tell_admin', tell_admin)
    plugin.on_action('save_conversation', save_conversation)


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


async def pin_added_validate(action, app):
    response = Message()
    response['channel'] = action['channel']['id']
    response['ts'] = action['message_ts']
    response['attachments'] = action['original_message']['attachments']
    response['attachments'][0]['color'] = 'good'
    response['attachments'][0]['pretext'] = f'Pin validated by <@{action["user"]["id"]}>'
    del response['attachments'][0]['actions']

    await app.plugins['slack'].api.query(url=action['response_url'], data=response)


async def pin_added_revert(action, app):
    response = Message()

    response['channel'] = action['channel']['id']
    response['ts'] = action['message_ts']
    response['attachments'] = action['original_message']['attachments']
    response['attachments'][0]['color'] = 'danger'
    response['attachments'][0]['pretext'] = f'Pin reverted by <@{action["user"]["id"]}>'
    del response['attachments'][0]['actions']

    action_data = json.loads(action['actions'][0]['value'])
    remove_data = {'channel': action_data['channel']}

    if action_data['item_type'] == 'message':
        remove_data['timestamp'] = action_data['item_id']
    elif action_data['item_type'] == 'file':
        remove_data['file'] = action_data['item_id']
    elif action_data['item_type'] == 'file_comment':
        remove_data['file_comment'] = action_data['item_id']
    else:
        raise TypeError(f'Unknown pin type: {action_data["type"]}')

    try:
        await app.plugins['slack'].api.query(
            url=methods.PINS_REMOVE,
            data=remove_data
        )
    except SlackAPIError as e:
        if e.error != 'no_pin':
            raise

    await app.plugins['slack'].api.query(url=action['response_url'], data=response)


async def report(action, app):
    admin_msg = Message()
    admin_msg['channel'] = ADMIN_CHANNEL
    admin_msg['attachments'] = [
        {
            'fallback': f'Report from {action["user"]["name"]}',
            'title': f'Report from <@{action["user"]["id"]}>',
            'color': 'danger',
            'fields': [
                {
                    'title': 'User',
                    'value': f'<@{action["submission"]["user"]}>',
                    'short': True
                },
            ]
        }
    ]

    if action['submission']['channel']:
        admin_msg['attachments'][0]['fields'].append(
            {
                'title': 'Channel',
                'value': f'<#{action["submission"]["channel"]}>',
                'short': True
            }
        )

    admin_msg['attachments'][0]['fields'].append(
        {
            'title': 'Comment',
            'value': action["submission"]["comment"],
            'short': False
        }
    )

    await app.plugins['slack'].api.query(url=methods.CHAT_POST_MESSAGE, data=admin_msg)

    async with app['plugins']['pg'].connection() as pg_con:
        await pg_con.execute(
            '''INSERT INTO slack.reports ("user", channel, comment, by) VALUES ($1, $2, $3, $4)''',
            action['submission']['user'], action['submission']['channel'], action['submission']['comment'],
            action['user']['id']
        )

    response = Message()
    response['response_type'] = 'ephemeral'
    response['text'] = 'Thank you for your report. An admin will look into it soon.'

    await app.plugins['slack'].api.query(url=action['response_url'], data=response)


async def tell_admin(action, app):
    admin_msg = Message()
    admin_msg['channel'] = ADMIN_CHANNEL
    admin_msg['attachments'] = [
        {
            'fallback': f'Message from {action["user"]["name"]}',
            'title': f'Message from <@{action["user"]["id"]}>',
            'color': 'good',
            'text': action['submission']['message']
        }
    ]

    await app.plugins['slack'].api.query(url=methods.CHAT_POST_MESSAGE, data=admin_msg)

    response = Message()
    response['response_type'] = 'ephemeral'
    response['text'] = 'Thank you for your message.'

    await app.plugins['slack'].api.query(url=action['response_url'], data=response)


async def save_conversation(action, app):

    now = datetime.datetime.now()
    end_delay = datetime.timedelta(seconds=int(action['submission']['end']))
    start_delay = datetime.timedelta(seconds=int(action['submission']['start']))

    if end_delay >= start_delay:
        errors = [
            {
                'name': 'start',
                'error': 'Start time must be superior than end time'
            },
            {
                'name': 'end',
                'error': 'End time must be inferior than start time'
            }
        ]
        return json_response(data={'errors': errors}, status=200)

    end = now - end_delay
    start = now - start_delay

    async with app['plugins']['pg'].connection() as pg_con:
        await pg_con.execute(
            '''INSERT INTO slack.recordings (start, "end", "user", channel, comment, title)
               VALUES ($1, $2, $3, $4, $5, $6)''',
            start, end, action['user']['id'], action['submission']['channel'], action['submission']['comment'],
            action['submission']['title']
        )

    response = Message()
    response['text'] = f'Conversation from {start.strftime("%H:%M")} to {end.strftime("%H:%M")} ' \
                       f'saved by <@{action["user"]["id"]}>'
    response['channel'] = action['submission']['channel']

    await app.plugins['slack'].api.query(url=methods.CHAT_POST_MESSAGE, data=response)
