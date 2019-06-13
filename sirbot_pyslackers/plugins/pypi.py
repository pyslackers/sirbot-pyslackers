import logging
from operator import itemgetter

from distance import levenshtein
from aiohttp_xmlrpc.client import ServerProxy

LOG = logging.getLogger(__name__)


class PypiPlugin:
    __name__ = "pypi"
    SEARCH_URL = "https://pypi.python.org/pypi"
    ROOT_URL = "https://pypi.org"
    PROJECT_URL = ROOT_URL + "/project/{0}"
    RESULT_URL = ROOT_URL + "/search/?q={0}"

    def __init__(self):
        self.api = None

    def load(self, sirbot):
        self.api = ServerProxy(self.SEARCH_URL, client=sirbot.http_session)

    async def search(self, search):
        results = await self.api.search({"name": search})
        for item in results:
            item["distance"] = levenshtein(str(search), item["name"])
        results.sort(key=itemgetter("distance"))
        return results
