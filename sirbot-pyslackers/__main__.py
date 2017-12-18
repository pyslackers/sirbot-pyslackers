import logging

from sirbot import SirBot
from sirbot.plugins.slack import SlackPlugin

from . import endpoints

logging.basicConfig(level=logging.DEBUG)

if __name__ == '__main__':
    bot = SirBot()

    sp = SlackPlugin()
    endpoints.slack.create_endpoints(sp)
    bot.load_plugin(sp)

    bot.start(host='127.0.0.1', port=9000)
