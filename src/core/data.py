import requests
import pandas as pd
import yaml

import os
import pickle
import time

import json
from .rate_limiter import RateLimiter
from .config import Config

class MarketData:
    def __init__(self, config: Config):
        self.config = config
        self.api_key = self.config.polygon.get('api_key')
        if not self.api_key or self.api_key == "YOUR_POLYGON_API_KEY":
            raise ValueError("Polygon API key is not configured or is a placeholder. Please set it in your config.yaml.")
        print(f"Loaded Polygon API key: '{self.api_key}'")
        self.base_url = 'https://api.polygon.io/v2/aggs/ticker/'
        self.cache_dir = self.config.data.get('data_cache_dir', 'market_cache')
        self.cache_expiry_days = self.config.data.get('cache_expiry_days', 3)
        data_cfg = self.config.data
        self.keep_days = data_cfg.get('keep_days', 260)
        self.discard_old_data = data_cfg.get('discard_old_data', True)
        self.meta_path = os.path.join(self.cache_dir, 'meta.json')
        os.makedirs(self.cache_dir, exist_ok=True)

        self.force_full_fetch = self.config.data.get('force_full_fetch', False)
        self.discard_years = self.config.data.get('discard_years', 3)

        self._cache = {}
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

    def fetch(self, ticker, start_date, end_date):
        timespan = 'day'
        # Use a cache key that is independent of the exact date range for broader reusability
        cache_key = (ticker, timespan, self.keep_days)
        cache_path = self._cache_path(ticker, timespan, self.keep_days)
        
        df = None
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
        
        # Check meta for cached date range
        meta_key = f'{ticker}_{timespan}_{self.keep_days}'
        cached_range = self.meta.get(meta_key, {})
        cached_start = pd.to_datetime(cached_range.get('start')) if 'start' in cached_range else None
        cached_end = pd.to_datetime(cached_range.get('end')) if 'end' in cached_range else None
        print(f"[MarketData] fetch() ticker={ticker}")
        print(f"[MarketData]   start_date={start_date}, end_date={end_date}")
        print(f"[MarketData]   cached_start={cached_start}, cached_end={cached_end}")

        # If force_full_fetch is set, always fetch the full range
        if self.force_full_fetch:
            start_date_str = start_date.strftime('%Y-%m-%d')
            end_date_str = end_date.strftime('%Y-%m-%d')
            print(f"[MarketData] [FORCE] start_date_str={start_date_str}, end_date_str={end_date_str}")
            url = f"{self.base_url}{ticker}/range/1/{timespan}/{start_date_str}/{end_date_str}?adjusted=true&sort=desc&limit=50000&apiKey={self.api_key}"
            print(f"[MarketData] [FORCE] Fetching (full) URL: {url}")
            resp = requests.get(url)
            resp.raise_for_status()
            raw_json = resp.json()
            print(f"[MarketData] [FORCE] Raw API response keys: {list(raw_json.keys())}")
            print(f"[MarketData] [FORCE] Raw API response: {str(raw_json)[:500]}")
            data = raw_json.get('results', [])
            print(f"[MarketData] [FORCE] Results length: {len(data)}")
            if data:
                df = pd.DataFrame(data)
                print(f"[MarketData] [FORCE] DataFrame shape after load: {df.shape}")
                print(f"[MarketData] [FORCE] DataFrame head:\n{df.head()}")
        # If cache exists and we need more recent data, fetch only the diff
        elif cached_end is not None and end_date > cached_end.date():
            fetch_start_date = cached_end.date() + pd.Timedelta(days=1)
            fetch_end_date = fetch_start_date  # Only fetch one day
            print(f"[MarketData]   fetch_start_date={fetch_start_date}, fetch_end_date={fetch_end_date}")
            url = f"{self.base_url}{ticker}/range/1/{timespan}/{fetch_start_date}/{fetch_end_date}?adjusted=true&sort=desc&limit=50000&apiKey={self.api_key}"
            print(f"[MarketData] Fetching (diff) URL: {url}")
            resp = requests.get(url)
            resp.raise_for_status()
            new_data = resp.json().get('results', [])
            if new_data:
                new_df = pd.DataFrame(new_data)
                if df is not None and not df.empty:
                    new_df = new_df[~new_df['t'].isin(df['t'])]
                    if not new_df.empty:
                        df = pd.concat([new_df, df], ignore_index=True).sort_values('t', ascending=False).reset_index(drop=True)
                else:
                    df = new_df
                # Update meta with new end date
                if not df.empty:
                    start_dt = pd.to_datetime(df['t'].iloc[-1], unit='ms').strftime('%Y-%m-%d')
                    end_dt = pd.to_datetime(df['t'].iloc[0], unit='ms').strftime('%Y-%m-%d')
                    self.meta[meta_key] = {
                        'start': start_dt,
                        'end': end_dt,
                        'last_updated': int(time.time())
                    }
                    self._save_meta()
        else:
            # If we have cached data, try to fetch only new (diff) data
            if df is not None and not df.empty:
                last_timestamp = int(df.iloc[0]['t'])
                from datetime import datetime, timedelta
                # Fetch from the day after the last recorded date
                last_date = datetime.utcfromtimestamp(last_timestamp / 1000) + timedelta(days=1)
                fetch_start_date_str = last_date.strftime('%Y-%m-%d')
                fetch_end_date_str = end_date.strftime('%Y-%m-%d')
                print(f"[MarketData]   last_date={last_date}, fetch_start_date_str={fetch_start_date_str}, fetch_end_date_str={fetch_end_date_str}")

                # Only fetch if the start date is not after the end date
                if last_date.date() < end_date:
                    url = f"{self.base_url}{ticker}/range/1/{timespan}/{fetch_start_date_str}/{fetch_end_date_str}?adjusted=true&sort=desc&limit=50000&apiKey={self.api_key}"
                    print(f"[MarketData] Fetching (diff2) URL: {url}")
                    resp = requests.get(url)
                    resp.raise_for_status()
                    new_data = resp.json().get('results', [])
                    if new_data:
                        new_df = pd.DataFrame(new_data)
                        new_df = new_df[~new_df['t'].isin(df['t'])]
                        if not new_df.empty:
                            df = pd.concat([new_df, df], ignore_index=True).sort_values('t', ascending=False).reset_index(drop=True)
            else:
                # No cache, fetch all for the requested range
                start_date_str = start_date.strftime('%Y-%m-%d')
                end_date_str = end_date.strftime('%Y-%m-%d')
                print(f"[MarketData]   start_date_str={start_date_str}, end_date_str={end_date_str}")
                url = f"{self.base_url}{ticker}/range/1/{timespan}/{start_date_str}/{end_date_str}?adjusted=true&sort=desc&limit=50000&apiKey={self.api_key}"
                print(f"[MarketData] Fetching (full) URL: {url}")
                resp = requests.get(url)
                resp.raise_for_status()
                data = resp.json().get('results', [])
                if data:
                    df = pd.DataFrame(data)

        # Purge old data and filter date range
        if df is not None and not df.empty:
            df['date'] = pd.to_datetime(df['t'], unit='ms').dt.date
            
            # Filter for the requested backtest date range
            df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]

            # Discard data older than discard_years from today, to manage cache size
            if self.discard_old_data:
                cutoff_days = int(self.discard_years * 365)
                cutoff_date = (pd.Timestamp.now() - pd.Timedelta(days=cutoff_days)).date()
                df = df[df['date'] >= cutoff_date].reset_index(drop=True)

            df = df.drop(columns=['date'])

            # Update cache and meta
            self._cache[cache_key] = df
            with open(cache_path, 'wb') as f:
                pickle.dump(df, f)
            # Save meta with date range
            if not df.empty:
                start_dt = pd.to_datetime(df['t'].iloc[-1], unit='ms').strftime('%Y-%m-%d')
                end_dt = pd.to_datetime(df['t'].iloc[0], unit='ms').strftime('%Y-%m-%d')
                self.meta[f'{ticker}_{timespan}_{self.keep_days}'] = {
                    'start': start_dt,
                    'end': end_dt,
                    'last_updated': int(time.time())
                }
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
