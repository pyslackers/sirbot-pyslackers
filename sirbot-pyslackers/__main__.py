import logging

from sirbot import SirBot
from sirbot.plugins.slack import SlackPlugin
from sirbot.plugins.github import GithubPlugin

from . import endpoints
from .plugins import PypiPlugin, GiphyPlugin

logging.basicConfig(level=logging.DEBUG)

PORT = 9000
HOST = '127.0.0.1'

if __name__ == '__main__':
    bot = SirBot()

    slack = SlackPlugin()
    endpoints.slack.create_endpoints(slack)
    bot.load_plugin(slack)

    github = GithubPlugin()
    endpoints.github.create_endpoints(github)
    bot.load_plugin(github)

    pypi = PypiPlugin()
    bot.load_plugin(pypi)

    giphy = GiphyPlugin()
    bot.load_plugin(giphy)

    bot.start(host=HOST, port=PORT, print=False)
