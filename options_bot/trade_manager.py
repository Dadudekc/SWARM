from datetime import datetime, timedelta
import json
from pathlib import Path
from broker import Broker
from monte_carlo import batch_pop
from strategy_core import tech_signal
from dreamos.social.utils.log_manager import LogManager


class TradeManager:
    def __init__(self, cfg):
        self.log = LogManager()
        self.broker = Broker(cfg['alpaca'])
        self.cfg = cfg['trade']
        self.outbox = Path('runtime/bridge_outbox')
        self.outbox.mkdir(parents=True, exist_ok=True)

    def run_cycle(self):
        self.log.info('options_bot', 'Running trade cycle')
        hist = self.broker.get_history(self.cfg['symbol'], '1h', 400)
        long_sig, short_sig, atr = tech_signal(hist)
        self.log.info('options_bot', f'Signal L:{long_sig} S:{short_sig}')

        chain = self.broker.get_option_chain(self.cfg['symbol'])
        if chain is None:
            self.log.error('options_bot', 'No option chain data')
            return

        calls = chain[chain['type'] == 'call']
        puts = chain[chain['type'] == 'put']

        if long_sig:
            pops = batch_pop(hist, calls.strike.unique(), True)
            self._try_execute(calls, pops, True)
        elif short_sig:
            pops = batch_pop(hist, puts.strike.unique(), False)
            self._try_execute(puts, pops, False)

    def _try_execute(self, df_opts, pops, is_call):
        df_opts = df_opts.copy()
        df_opts['pop'] = df_opts.strike.map(pops)
        df = df_opts[
            (df_opts.pop >= self.cfg['min_pop']) &
            (df_opts.spread <= self.cfg['max_spread'])
        ].sort_values('pop', ascending=False)

        if df.empty:
            self.log.info('options_bot', 'No trade meets criteria')
            return

        tgt = df.iloc[0]
        qty = self._size_position(tgt.mark)
        side = 'buy' if is_call else 'sell'
        self.log.info('options_bot', f'Placing order {tgt.symbol} qty {qty} side {side}')
        self.broker.send_order(tgt.symbol, qty, self.cfg['order_type'], side=side)
        self._log_trade({
            'symbol': tgt.symbol,
            'qty': qty,
            'side': side,
            'pop': tgt.pop,
            'timestamp': datetime.utcnow().isoformat()
        })

    def _size_position(self, premium):
        equity = self.broker.get_equity()
        risk = equity * self.cfg['risk_per_trade_pct'] / 100
        return max(1, int(risk / (premium + self.cfg['slippage'])))

    def _log_trade(self, info):
        fname = self.outbox / f"trade-{datetime.utcnow().timestamp()}.json"
        with open(fname, 'w') as f:
            json.dump(info, f)
        self.log.info('options_bot', f'Logged trade {fname}')
