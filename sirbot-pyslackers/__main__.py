import os
import yaml
import raven
import logging.config

from raven.conf import setup_logging
from raven.processors import SanitizePasswordsProcessor
from raven.handlers.logging import SentryHandler

from sirbot import SirBot
from sirbot.plugins.slack import SlackPlugin
from sirbot.plugins.github import GithubPlugin
from sirbot.plugins.postgres import PgPlugin
from sirbot.plugins.apscheduler import APSchedulerPlugin
from sirbot.plugins.readthedocs import RTDPlugin

from . import endpoints
from .plugins import PypiPlugin, GiphyPlugin, DeployPlugin

PORT = os.environ.get('SIRBOT_PORT', 9000)
HOST = os.environ.get('SIRBOT_ADDR', '127.0.0.1')
VERSION = '0.0.11'
LOG = logging.getLogger(__name__)


def make_sentry_logger():
    client = raven.Client(
        dsn=os.environ['SENTRY_DSN'],
        release=raven.fetch_git_sha(os.path.join(os.path.dirname(__file__), os.pardir)),
        processor=SanitizePasswordsProcessor
    )
    handler = SentryHandler(client)
    handler.setLevel(logging.WARNING)
    setup_logging(handler)


if __name__ == '__main__':
    try:
        with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../logging.yml')) as log_configfile:
            logging.config.dictConfig(yaml.load(log_configfile.read()))

    except Exception as e:
        logging.basicConfig(level=logging.DEBUG)
        LOG.exception(e)

    if 'SENTRY_DSN' in os.environ:
        make_sentry_logger()

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

    scheduler = APSchedulerPlugin(timezone='UTC')
    endpoints.apscheduler.create_jobs(scheduler, bot)
    bot.load_plugin(scheduler)

    readthedocs = RTDPlugin()
    endpoints.readthedocs.register(readthedocs)
    bot.load_plugin(readthedocs)

    if 'POSTGRES_DSN' in os.environ:
        postgres = PgPlugin(
            version=VERSION,
            sql_migration_directory=os.path.join(os.path.dirname(os.path.realpath(__file__)), '../sql'),
            dsn=os.environ['POSTGRES_DSN']
        )
        bot.load_plugin(postgres)

    bot.start(host=HOST, port=PORT, print=False)
