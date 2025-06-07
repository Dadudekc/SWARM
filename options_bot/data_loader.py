from broker import Broker


def fetch_history(broker: Broker, symbol: str, timeframe: str = '1h', limit: int = 400):
    return broker.get_history(symbol, timeframe, limit)


def fetch_option_chain(broker: Broker, symbol: str):
    return broker.get_option_chain(symbol)
