import pickle
import os
import pandas as pd

tickers = ['TQQQ', 'SQQQ']
for t in tickers:
    fn = f'market_cache/{t}_day_365.pkl'
    print(f'{t}:', os.path.exists(fn))
    if os.path.exists(fn):
        df = pickle.load(open(fn, 'rb'))
        print('  Rows:', len(df))
        if len(df) > 0:
            print('  First:', pd.to_datetime(df['t'].iloc[-1], unit='ms'), 'Last:', pd.to_datetime(df['t'].iloc[0], unit='ms'))
