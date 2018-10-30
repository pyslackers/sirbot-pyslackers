class StocksPlugin:
    __name__ = "stocks"

    API_ROOT = "https://api.iextrading.com/1.0"

    def __init__(self):
        self.session = None  # set lazily on plugin load

    def load(self, sirbot):
        self.session = sirbot.http_session

    async def book(self, symbol: str):
        """https://iextrading.com/developer/docs/#book"""
        url = self.API_ROOT + f"/stock/{symbol}/book"
        async with self.session.get(url) as r:
            r.raise_for_status()
            return await r.json()

    async def logo(self, symbol: str):
        """https://iextrading.com/developer/docs/#logo"""
        url = self.API_ROOT + f"/stock/{symbol}/logo"
        async with self.session.get(url) as r:
            r.raise_for_status()
            return await r.json()

    async def crypto(self):
        """https://iextrading.com/developer/docs/#crypto"""
        url = self.API_ROOT + "/stock/market/crypto"
        async with self.session.get(url) as r:
            r.raise_for_status()
            return await r.json()
