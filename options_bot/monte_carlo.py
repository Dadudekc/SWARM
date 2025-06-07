import numpy as np
import pandas as pd


def simulate_prices(returns, paths=5000, days=5):
    mu, sigma = returns.mean(), returns.std()
    rand = np.random.normal(mu, sigma, (days, paths))
    paths = returns.iloc[-1] * np.exp(np.cumsum(rand, axis=0))
    return paths


def pop_above(price_paths, strike, is_call=True):
    final_prices = price_paths[-1]
    if is_call:
        wins = final_prices > strike
    else:
        wins = final_prices < strike
    return wins.mean()


def batch_pop(df_hist, strikes, is_call):
    rets = np.log(df_hist['close']).diff().dropna()
    sims = simulate_prices(rets)
    return {
        s: pop_above(sims, s, is_call)
        for s in strikes
    }
