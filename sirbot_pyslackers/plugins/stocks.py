import os
import datetime
import dataclasses
from typing import Optional
from decimal import Decimal


@dataclasses.dataclass(frozen=True)
class StockQuote:
    symbol: str
    company: str
    price: Decimal
    change: Decimal
    change_percent: Decimal
    market_open: Decimal
    market_close: Decimal
    high: Decimal
    low: Decimal
    volume: Decimal
    time: datetime.datetime
    logo: Optional[str] = None


class StocksPlugin:
    __name__ = "stocks"

    def __init__(self):
        self.session = None  # set lazily on plugin load

    def load(self, sirbot):
        self.session = sirbot.http_session

    async def price(self, symbol: str) -> StockQuote:
        async with self.session.get(
            "https://query1.finance.yahoo.com/v7/finance/quote",
            params={"symbols": symbol},
        ) as r:
            r.raise_for_status()
            body = (await r.json())["quoteResponse"]["result"]
            if len(body) < 1:
                return None

            quote = body[0]

            return StockQuote(
                symbol=quote["symbol"],
                company=quote.get("longName", quote.get("shortName", "")),
                price=Decimal(quote.get("regularMarketPrice", 0)),
                change=Decimal(quote.get("regularMarketChange", 0)),
                change_percent=Decimal(quote.get("regularMarketChangePercent", 0)),
                market_open=Decimal(quote.get("regularMarketOpen", 0)),
                market_close=Decimal(quote.get("regularMarketPreviousClose", 0)),
                high=Decimal(quote.get("regularMarketDayHigh", 0)),
                low=Decimal(quote.get("regularMarketDayLow", 0)),
                volume=Decimal(quote.get("regularMarketVolume", 0)),
                time=datetime.datetime.fromtimestamp(quote.get("regularMarketTime", 0)),
                logo=quote.get("coinImageUrl"),
            )
