import re
import logging

from slack import methods

LOG = logging.getLogger(__name__)
TELL_REGEX = re.compile('tell (<(#|@)(?P<to_id>[A-Z0-9]*)(|.*)?>) (?P<msg>.*)')


def create_endpoints(plugin):
    plugin.on_message('hello', hello, flags=re.IGNORECASE, mention=True)
    plugin.on_message('^tell', tell, flags=re.IGNORECASE, mention=True, admin=True)
    plugin.on_message('.*', mention, flags=re.IGNORECASE, mention=True)


async def hello(message, app):
    response = message.response()
    response['text'] = 'Hello <@{user}>'.format(user=message['user'])
    await app.plugins['slack'].api.query(url=methods.CHAT_POST_MESSAGE, data=response)


async def tell(message, app):
    match = TELL_REGEX.match(message['text'])
    response = message.response()

    if match:
        to_id = match.group('to_id')
        msg = match.group('msg')

        if to_id.startswith(('C', 'U')):
            response['text'] = msg
            response['channel'] = to_id
        else:
            response['text'] = 'Sorry I can not understand the destination.'
    else:
        response['text'] = 'Sorry I can not understand'

    await app.plugins['slack'].api.query(url=methods.CHAT_POST_MESSAGE, data=response)


async def mention(message, app):
    await app.plugins['slack'].api.query(url=methods.REACTIONS_ADD, data={
        'name': 'sirbot',
        'channel': message['channel'],
        'timestamp': message['ts']
    })
