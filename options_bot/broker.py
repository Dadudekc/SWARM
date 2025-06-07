from typing import Optional
import pandas as pd
from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.trading.requests import GetAssetsRequest, OrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce


class Broker:
    def __init__(self, cfg: dict):
        key = cfg.get('key')
        secret = cfg.get('secret')
        paper = cfg.get('paper', True)
        self.trading = TradingClient(key, secret, paper=paper)
        self.data = StockHistoricalDataClient(key, secret)

    def get_history(self, symbol: str, tf: str, limit: int = 400) -> pd.DataFrame:
        timeframe = TimeFrame.Hour if tf == '1h' else TimeFrame.Day
        req = StockBarsRequest(symbol_or_symbols=symbol, timeframe=timeframe, limit=limit)
        bars = self.data.get_stock_bars(req).df
        return bars.reset_index()

    def get_option_chain(self, symbol: str) -> Optional[pd.DataFrame]:
        try:
            chain = self.trading.get_option_chain(symbol)
        except Exception:
            return None
        rows = []
        for opt in chain:
            rows.append({
                'symbol': opt.symbol,
                'strike': float(opt.strike_price),
                'type': opt.type,
                'mark': float(opt.mark_price),
                'bid': float(opt.bid_price),
                'ask': float(opt.ask_price),
                'spread': float(opt.ask_price) - float(opt.bid_price)
            })
        return pd.DataFrame(rows)

    def send_order(self, symbol: str, qty: int, order_type: str, side: str = 'buy'):
        req = OrderRequest(
            symbol=symbol,
            qty=qty,
            side=OrderSide.BUY if side == 'buy' else OrderSide.SELL,
            type=order_type,
            time_in_force=TimeInForce.DAY,
        )
        self.trading.submit_order(req)

    def get_equity(self) -> float:
        acct = self.trading.get_account()
        return float(acct.equity)
