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
    response['text'] = 'pouet'
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
