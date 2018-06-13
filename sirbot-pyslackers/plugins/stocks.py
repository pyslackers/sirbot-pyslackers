import os


class StocksPlugin:
    __name__ = 'stocks'

    API_ROOT = 'https://www.alphavantage.co/query'

    def __init__(self, api_key=None):
        self.session = None
        self.api_key = api_key
        if api_key is None:
            self.api_key = os.getenv('ALPHAVANTAGE_API_KEY')
        if self.api_key is None:
            raise ValueError('Improperly configured, missing '
                             'ALPHAVANTAGE_API_KEY')

    async def __call__(self, function: str, params=None):
        params = params or {}
        params.update(
            function=function,
            apikey=self.api_key
        )

        async with self.session.get(self.API_ROOT, params=params) as r:
            r.raise_for_status()
            return await r.json()

    def load(self, sirbot):
        self.session = sirbot.http_session

    async def quote_daily(self, ticker):
        return await self('TIME_SERIES_DAILY', params={'symbol': ticker})

    async def quote(self, ticker):
        return await self('TIME_SERIES_INTRADAY', params={
            'symbol': ticker,
            'interval': '1min',
        })
