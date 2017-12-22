import logging

from aiohttp_xmlrpc.client import ServerProxy
from distance import levenshtein
from operator import itemgetter

LOG = logging.getLogger(__name__)


class PypiPlugin:
    __name__ = 'pypi'
    ROOT_URL = 'https://pypi.python.org/pypi'
    SEARCH_PATH = '?%3Aaction=search&term={0}&submit=search'

    def __init__(self):
        self.api = None

    def load(self, sirbot):
        self.api = ServerProxy(self.ROOT_URL, client=sirbot.http_session)

    async def search(self, search):
        results = await self.api.search({'name': search})
        for item in results:
            item['distance'] = levenshtein(str(search), item['name'])
        results.sort(key=itemgetter('distance'))
        return results
