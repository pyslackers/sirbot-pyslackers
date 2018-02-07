import os
import json
import logging

from slack import methods
from slack.events import Message

LOG = logging.getLogger(__name__)
ADMIN_CHANNEL = os.environ.get('SLACK_ADMIN_CHANNEL') or 'G1DRT62UC'


def create_endpoints(plugin):
    plugin.on_command('/admin', tell_admin)
    plugin.on_command('/gif', gif_search)
    plugin.on_command('/pypi', pypi_search)
    plugin.on_command('/sponsors', sponsors)
    plugin.on_command('/do', sponsors)
    plugin.on_command('/snippet', snippet)


async def sponsors(command, app):
    slack = app.plugins['slack']
    response = Message()
    response['channel'] = command['channel_id']

    response['text'] = 'Thanks to our sponsors, <https://digitalocean.com|Digital Ocean> and ' \
                       '<https://sentry.io|Sentry> for providing hosting & services helping us ' \
                       'host our <https://www.pyslackers.com|website> and Sir Bot-a-lot. ' \
                       'If you are planning on using one of those services please use our referral codes: \n' \
                       '1. <https://m.do.co/c/457f0988c477|DO referral code>\n' \
                       '2. <https://sentry.io/?utm_source=referral&utm_content=pyslackers&utm_campaign=community|' \
                       'Sentry referral code>.'

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
            response['attachments'] = [
                {
                    'title': f'<@{command["user_id"]}> Searched PyPi for `{command["text"]}`',
                    'fallback': f'Pypi search of {command["text"]}',
                    'fields': []
                }
            ]

            for result in results[:3]:
                response['attachments'][0]['fields'].append(
                    {
                        'title': result['name'],
                        'value': f'<{app.plugins["pypi"].PROJECT_URL.format(result["name"])}|{result["summary"]}>'
                    }
                )

            if len(results) == 4:
                response['attachments'][0]['fields'].append(
                    {
                        'title': results[3]["name"],
                        'value':
                            f'<{app.plugins["pypi"].PROJECT_URL.format(results[3]["name"])}|{results[3]["summary"]}>'
                    }
                )
            elif len(results) > 3:
                response['attachments'][0]['fields'].append(
                    {
                        'title': f'More results',
                        'value':
                            f'<{app.plugins["pypi"].RESULT_URL.format(command["text"])}|'
                            f'{len(results) - 3} more results..>',
                    }
                )

        else:
            response['response_type'] = 'ephemeral'
            response['text'] = f"Could not find anything on PyPi matching `{command['text']}`"

    await app.plugins['slack'].api.query(url=methods.CHAT_POST_MESSAGE, data=response)


async def snippet(command, app):
    response = Message()
    response['channel'] = command['channel_id']

    response['text'] = 'Please use the snippet feature when sharing code :slightly_smiling_face: you can do so by ' \
                       'clicking on the :heavy_plus_sign: on the left of the input box. For more information click ' \
                       '<https://get.slack.help/hc/en-us/articles/204145658-Create-a-snippet|here>.'

    await app.plugins['slack'].api.query(url=methods.CHAT_POST_MESSAGE, data=response)
