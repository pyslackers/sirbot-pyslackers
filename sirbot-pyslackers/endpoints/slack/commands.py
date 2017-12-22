import os
import json
import logging

from slack import methods
from slack.events import Message

LOG = logging.getLogger(__name__)
ADMIN_CHANNEL = os.environ.get('SLACK_ADMIN_CHANNEL') or 'G1DRT62UC'


def create_endpoints(plugin):
    plugin.on_command('/do', digital_ocean)
    plugin.on_command('/admin', tell_admin)
    plugin.on_command('/gif', gif_search)
    plugin.on_command('/pypi', pypi_search)


async def digital_ocean(command, app):
    slack = app.plugins['slack']
    response = Message()
    response['channel'] = command['channel_id']
    response['text'] = 'Here at Python Developers we host our website and Slack bot on <https://digitalocean.com|' \
                       'Digital Ocean>. If you are planning on using Digital Ocean, please use our ' \
                       '<https://m.do.co/c/457f0988c477|referral code>. You get 10 USD, while helping support the ' \
                       'community by contributing to hosting fees for our site and <@{}>!'.format(slack.bot_user_id)
    await slack.api.query(url=methods.CHAT_POST_MESSAGE, data=response)


async def tell_admin(command, app):
    response = Message()
    response['channel'] = ADMIN_CHANNEL
    response['attachments'] = [
        {
            'fallback': f'admin message from {command["user_name"]}',
            'text': command['text'],
            'title': f'Message to the admin team by <@{command["user_id"]}>'
        }
    ]

    await app.plugins['slack'].api.query(url=methods.CHAT_POST_MESSAGE, data=response)


async def gif_search(command, app):
    response = Message()
    response['channel'] = command['channel_id']

    if command['text']:
        response['user'] = command['user_id']
        urls = await app.plugins['giphy'].search(command['text'])
        urls = [url.split('?')[0] for url in urls]
        data = json.dumps({'urls': urls, 'search': command['text'], 'index': 0})

        response['attachments'] = [
            {
                'title': f'You searched for `{command["text"]}`',
                'fallback': f'You searched for `{command["text"]}`',
                'image_url': urls[0],
                'callback_id': 'gif_search',
                'actions': [
                    {
                        'name': 'ok',
                        'text': 'Send',
                        'style': 'primary',
                        'value': data,
                        'type': 'button'
                    },
                    {
                        'name': 'next',
                        'text': 'Next',
                        'value': data,
                        'type': 'button'
                    },
                    {
                        'name': 'cancel',
                        'text': 'Cancel',
                        'style': 'danger',
                        'value': data,
                        'type': 'button'
                    },
                ]
            }
        ]
        await app.plugins['slack'].api.query(url=methods.CHAT_POST_EPHEMERAL, data=response)

    else:
        url = await app.plugins['giphy'].trending()

        response['attachments'] = [
            {
                'title': 'Trending gif on Giphy',
                'fallback': 'Trending gif on Giphy',
                'image_url': url
            }
        ]

        await app.plugins['slack'].api.query(url=methods.CHAT_POST_MESSAGE, data=response)


async def pypi_search(command, app):
    response = Message()
    response['channel'] = command['channel_id']

    if not command['text']:
        response['response_type'] = 'ephemeral'
        response['text'] = 'Please enter the package name you wish to find'
    else:
        results = await app.plugins['pypi'].search(command['text'])
        if results:
            response['response_type'] = 'in_channel'
            response['attachments'] = list()
            for result in results[:3]:
                response['attachments'].append(
                    {
                        'title': result['name'],
                        'fallback': result['name'],
                        'text': result['summary'],
                        'title_link': f'{app.plugins["pypi"].ROOT_URL}/{result["name"]}'
                    }
                )

            if len(results) == 4:
                response['attachments'].append(
                    {
                        'title': results[3]['name'],
                        'fallback': results[3]['name'],
                        'text': results[3]['summary'],
                        'title_link': f'{app.plugins["pypi"].ROOT_URL}/{results[3]["name"]}'
                    }
                )
            elif len(results) > 3:
                path = app.plugins["pypi"].SEARCH_PATH.format(command['text'])
                response['attachments'].append(
                    {
                        'title': f'{len(results) - 3} more results..',
                        'fallback': f'{len(results) - 3} more results..',
                        'title_link': f'{app.plugins["pypi"].ROOT_URL}/{path}'
                    }
                )
            response['text'] = f"<@{command['user_id']}> Searched PyPi for `{command['text']}`"

        else:
            response['response_type'] = 'ephemeral'
            response['text'] = f"Could not find anything on PyPi matching `{command['text']}`"

    await app.plugins['slack'].api.query(url=methods.CHAT_POST_MESSAGE, data=response)
