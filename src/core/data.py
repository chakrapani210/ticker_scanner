import requests
import pandas as pd

import os
import pickle
import time

import json

class MarketData:
    def __init__(self, config):
        self.api_key = config['api_key']
        self.base_url = 'https://api.polygon.io/v2/aggs/ticker/'
        self._cache = {}
        self.cache_dir = config.get('cache_dir', 'market_cache')
        self.cache_expiry_days = config.get('cache_expiry_days', 3)  # default: 3 days
        # Data retention configs
        data_cfg = config.get('data', {})
        self.keep_days = data_cfg.get('keep_days', 260)
        self.discard_old_data = data_cfg.get('discard_old_data', True)
        self.meta_path = os.path.join(self.cache_dir, 'meta.json')
        os.makedirs(self.cache_dir, exist_ok=True)
        self.cleanup_cache()
        self._load_meta()

    def _load_meta(self):
        if os.path.exists(self.meta_path):
            with open(self.meta_path, 'r') as f:
                self.meta = json.load(f)
        else:
            self.meta = {}

    def _save_meta(self):
        with open(self.meta_path, 'w') as f:
            json.dump(self.meta, f)

    def _cache_path(self, ticker, timespan, limit):
        return os.path.join(self.cache_dir, f"{ticker}_{timespan}_{limit}.pkl")

    def fetch_daily(self, ticker='AAPL', timespan='day', limit=30):
        cache_key = (ticker, timespan, limit)
        cache_path = self._cache_path(ticker, timespan, limit)
        last_fetched = self.meta.get(f'{ticker}_{timespan}_{limit}', None)
        # Try in-memory cache first
        if cache_key in self._cache:
            df = self._cache[cache_key]
        elif os.path.exists(cache_path):
            mtime = os.path.getmtime(cache_path)
            age_days = (time.time() - mtime) / 86400
            if age_days < self.cache_expiry_days:
                with open(cache_path, 'rb') as f:
                    df = pickle.load(f)
                self._cache[cache_key] = df
            else:
                os.remove(cache_path)
                df = None
        else:
            df = None

        # If we have cached data, try to fetch only new (diff) data
        if df is not None and not df.empty:
            # Polygon returns data sorted desc, so first row is latest
            last_timestamp = int(df.iloc[0]['t'])
            # Convert ms to date string for API
            from datetime import datetime, timedelta
            last_date = datetime.utcfromtimestamp(last_timestamp / 1000).strftime('%Y-%m-%d')
            url = f"{self.base_url}{ticker}/range/1/{timespan}/{last_date}/{datetime.utcnow().strftime('%Y-%m-%d')}?adjusted=true&sort=desc&limit={limit}&apiKey={self.api_key}"
            resp = requests.get(url)
            resp.raise_for_status()
            new_data = resp.json().get('results', [])
            if new_data:
                new_df = pd.DataFrame(new_data)
                # Remove any overlap (same timestamp)
                new_df = new_df[~new_df['t'].isin(df['t'])]
                if not new_df.empty:
                    df = pd.concat([new_df, df], ignore_index=True).sort_values('t', ascending=False).reset_index(drop=True)
        else:
            # No cache, fetch all
            url = f"{self.base_url}{ticker}/range/1/{timespan}/2023-01-01/2025-12-31?adjusted=true&sort=desc&limit={limit}&apiKey={self.api_key}"
            resp = requests.get(url)
            resp.raise_for_status()
            data = resp.json().get('results', [])
            df = pd.DataFrame(data)

        # Purge old data if enabled: keep only the most recent N days
        if not df.empty and self.discard_old_data:
            df = df.sort_values('t', ascending=False)
            # Convert ms timestamp to date (naive)
            df['date'] = pd.to_datetime(df['t'], unit='ms').dt.tz_localize(None)
            cutoff = pd.Timestamp.now() - pd.Timedelta(days=self.keep_days)
            df = df[df['date'] >= cutoff].reset_index(drop=True)
            df = df.drop(columns=['date'])

        # Update cache and meta
        self._cache[cache_key] = df
        with open(cache_path, 'wb') as f:
            pickle.dump(df, f)
        # Mark last fetch time
        if not df.empty:
            self.meta[f'{ticker}_{timespan}_{limit}'] = int(time.time())
            self._save_meta()
        return df

    def cleanup_cache(self):
        now = time.time()
        for fname in os.listdir(self.cache_dir):
            fpath = os.path.join(self.cache_dir, fname)
            if os.path.isfile(fpath):
                mtime = os.path.getmtime(fpath)
                age_days = (now - mtime) / 86400
                if age_days > self.cache_expiry_days:
                    os.remove(fpath)
