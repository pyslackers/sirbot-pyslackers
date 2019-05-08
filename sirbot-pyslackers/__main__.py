import os
import sys
import asyncio
import logging.config

import yaml
import raven
import platformshconfig
from sirbot import SirBot
from raven.processors import SanitizePasswordsProcessor
from sirbot.plugins.slack import SlackPlugin
from sirbot.plugins.github import GithubPlugin
from raven.handlers.logging import SentryHandler
from sirbot.plugins.postgres import PgPlugin
from sirbot.plugins.apscheduler import APSchedulerPlugin
from sirbot.plugins.readthedocs import RTDPlugin

from . import endpoints
from .plugins import PypiPlugin, GiphyPlugin, StocksPlugin

PORT = os.environ.get("SIRBOT_PORT", os.environ.get("PORT", 9000))
HOST = os.environ.get("SIRBOT_ADDR", "127.0.0.1")
VERSION = "0.0.11"
LOG = logging.getLogger(__name__)
PSH_CONFIG = platformshconfig.Config()


def make_sentry_logger(dsn):

    if PSH_CONFIG.is_valid_platform():
        version = PSH_CONFIG.treeID
    else:
        version = VERSION

    client = raven.Client(
        dsn=dsn, release=version, processor=SanitizePasswordsProcessor
    )
    handler = SentryHandler(client)
    handler.setLevel(logging.WARNING)
    raven.conf.setup_logging(handler)


def setup_logging():
    try:
        with open(
            os.path.join(os.path.dirname(os.path.realpath(__file__)), "../logging.yml")
        ) as log_configfile:
            logging.config.dictConfig(yaml.safe_load(log_configfile.read()))

    except Exception as e:
        logging.basicConfig(level=logging.DEBUG)
        LOG.exception(e)

    sentry_dsn = os.environ.get("SENTRY_DSN")
    if sentry_dsn:
        make_sentry_logger(sentry_dsn)


def configure_postgresql_plugin():

    if "POSTGRES_DSN" in os.environ:
        dsn = os.environ["POSTGRES_DSN"]
    elif PSH_CONFIG.is_valid_platform():
        dsn = PSH_CONFIG.formatted_credentials("database", "postgresql_dsn")
    else:
        dsn = None

    if dsn:
        return PgPlugin(
            version=VERSION,
            sql_migration_directory=os.path.join(
                os.path.dirname(os.path.realpath(__file__)), "../sql"
            ),
            dsn=dsn,
        )
    else:
        raise RuntimeError(
            "No postgresql configuration available. Use POSTGRES_DSN environment variable"
        )


if __name__ == "__main__":

    setup_logging()

    if len(sys.argv) > 1 and sys.argv[1] == "migrate":
        postgres = configure_postgresql_plugin()
        loop = asyncio.get_event_loop()
        loop.run_until_complete(postgres.migrate())
        sys.exit(0)

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

    stocks = StocksPlugin()
    bot.load_plugin(stocks)

    scheduler = APSchedulerPlugin(timezone="UTC")
    endpoints.apscheduler.create_jobs(scheduler, bot)
    bot.load_plugin(scheduler)

    readthedocs = RTDPlugin()
    endpoints.readthedocs.register(readthedocs)
    bot.load_plugin(readthedocs)

    postgres = configure_postgresql_plugin()
    bot.load_plugin(postgres)

    bot.start(host=HOST, port=PORT, print=False)
