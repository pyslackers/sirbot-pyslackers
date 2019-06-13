import os
import random
import logging

LOG = logging.getLogger(__name__)


class GiphyPlugin:
    __name__ = "giphy"
    ROOT_URL = "http://api.giphy.com/v1/{}"
    SEARCH_TERM_URL = ROOT_URL.format("gifs/search?q={terms}")
    TRENDING_URL = ROOT_URL.format("gifs/trending?")
    RANDOM_URL = ROOT_URL.format("gifs/random?")
    BY_ID_URL = ROOT_URL.format("gifs/{gif_id}?")

    def __init__(self):
        self.session = None
        self._token = os.environ.get("GIPHY_TOKEN") or "dc6zaTOxFJmzC"

    def load(self, sirbot):
        self.session = sirbot.http_session

    async def _query(self, url):
        if url.endswith("?"):
            url += "api_key={}".format(self._token)
        else:
            url += "&api_key={}".format(self._token)

        LOG.debug("Query giphy api with url: %s", url)
        rep = await self.session.request("GET", url)
        data = await rep.json()

        if "meta" not in data or "status" not in data["meta"]:
            raise ConnectionError("Invalid response: {}".format(data))
        elif data["meta"]["status"] != 200:
            raise ConnectionError("Giphy response: {}".format(data))
        return data

    async def search(self, *terms):
        data = await self._query(self.SEARCH_TERM_URL.format(terms="+".join(terms)))
        urls = [result["images"]["original"]["url"] for result in data["data"]]
        return urls

    async def trending(self):
        data = await self._query(self.TRENDING_URL)
        num = random.randint(0, len(data["data"]) - 1)
        return data["data"][num]["images"]["original"]["url"]
