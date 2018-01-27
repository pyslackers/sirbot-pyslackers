import logging
import datetime

from slack import methods

LOG = logging.getLogger(__name__)


def create_jobs(scheduler, bot):
    scheduler.scheduler.add_job(slack_channel_list, 'date', kwargs={'bot': bot},
                                run_date=datetime.datetime.now() + datetime.timedelta(minutes=2))
    scheduler.scheduler.add_job(slack_channel_list, 'cron', hour=1, kwargs={'bot': bot})


async def slack_channel_list(bot):
    LOG.info('Updating list of slack channels...')
    async with bot['plugins']['pg'].connection() as pg_con:
        async for channel in bot['plugins']['slack'].api.iter(methods.CHANNELS_LIST, minimum_time=3):
            await pg_con.execute('''INSERT INTO slack.channels (id, raw) VALUES ($1, $2)
                                    ON CONFLICT (id) DO UPDATE SET raw = $2''', channel['id'], channel)
    LOG.info('List of slack channels up to date.')
