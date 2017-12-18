import re
import logging

from slack import methods
from slack.events import Message

LOG = logging.getLogger(__name__)


def create_endpoints(plugin):
    plugin.on_message('hello', hello, flags=re.IGNORECASE, mention=True)
    plugin.on_command('/do', digital_ocean)


async def hello(msg, app):
    rep = msg.response()
    rep['text'] = 'Hello <@{user}>'.format(user=msg['user'])
    await app.plugins['slack'].api.query(url=methods.CHAT_POST_MESSAGE, data=rep)


async def digital_ocean(cmd, app):
    slack = app.plugins['slack']
    rep = Message()
    rep['channel'] = cmd['channel_id']
    rep['text'] = 'Here at Python Developers we host our website and Slack bot on <https://digitalocean.com|Digital' \
                  'Ocean>. If you are planning on using Digital Ocean, please use our ' \
                  '<https://m.do.co/c/457f0988c477|referral code>. You get 10 USD, while helping support the ' \
                  'community by contributing to hosting fees for our site and <@{}>!'.format(slack.bot_user_id)
    await slack.api.query(url=methods.CHAT_POST_MESSAGE, data=rep)
