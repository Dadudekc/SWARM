import time
import yaml
from trade_manager import TradeManager

cfg = yaml.safe_load(open('options_bot/config.yaml'))
tm = TradeManager(cfg)

while True:
    try:
        tm.run_cycle()
    except Exception as e:
        tm.log.error('options_bot', f'Bot error: {e}')
    time.sleep(60 * 15)
