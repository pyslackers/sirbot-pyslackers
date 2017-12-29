import os
import yaml
import logging.config

from sirbot import SirBot
from sirbot.plugins.slack import SlackPlugin
from sirbot.plugins.github import GithubPlugin

from . import endpoints
from .plugins import PypiPlugin, GiphyPlugin, DeployPlugin

PORT = 9000
HOST = '127.0.0.1'

if __name__ == '__main__':
    try:
        with open(os.path.join(os.getcwd(), 'logging.yml')) as log_configfile:
            logging.config.dictConfig(yaml.load(log_configfile.read()))
    except Exception as e:
        logging.basicConfig(level=logging.DEBUG)
        LOG = logging.getLogger(__name__)
        LOG.exception(e)

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

    deploy = DeployPlugin()
    bot.load_plugin(deploy)

    bot.start(host=HOST, port=PORT, print=False)
