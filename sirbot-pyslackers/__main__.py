import logging

from sirbot import SirBot
from sirbot.plugins.slack import SlackPlugin
from sirbot.plugins.github import GithubPlugin

from . import endpoints

logging.basicConfig(level=logging.DEBUG)

if __name__ == '__main__':
    bot = SirBot()

    slack = SlackPlugin()
    endpoints.slack.create_endpoints(slack)
    bot.load_plugin(slack)

    github = GithubPlugin()
    endpoints.github.create_endpoints(github)
    bot.load_plugin(github)

    bot.start(host='127.0.0.1', port=9000)
