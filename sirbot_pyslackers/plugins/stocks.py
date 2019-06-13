import os
import decimal
import datetime
import dataclasses
from typing import Optional


@dataclasses.dataclass(frozen=True)
class StockQuote:
    symbol: str
    company: str
    price: decimal.Decimal
    change: decimal.Decimal
    change_percent: decimal.Decimal
    market_open: decimal.Decimal
    market_close: decimal.Decimal
    high: decimal.Decimal
    low: decimal.Decimal
    volume: decimal.Decimal
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
                price=decimal.Decimal.from_float(quote["regularMarketPrice"]),
                change=decimal.Decimal.from_float(quote["regularMarketChange"]),
                change_percent=decimal.Decimal.from_float(
                    quote["regularMarketChangePercent"]
                ),
                market_open=decimal.Decimal.from_float(quote["regularMarketOpen"]),
                market_close=decimal.Decimal.from_float(
                    quote["regularMarketPreviousClose"]
                ),
                high=decimal.Decimal.from_float(quote["regularMarketDayHigh"]),
                low=decimal.Decimal.from_float(quote["regularMarketDayLow"]),
                volume=decimal.Decimal.from_float(quote["regularMarketVolume"]),
                time=datetime.datetime.fromtimestamp(quote["regularMarketTime"]),
                logo=quote.get("coinImageUrl"),
            )
