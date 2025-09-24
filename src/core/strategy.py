import pandas as pd
import numpy as np

class StrategyManager:
    def __init__(self, config):
        self.config = config
        # Always-on basic strategies
        always_on = {
            'sma_rsi_combo': True,
            'rsi_reversal': True,
            'trend_following': True,
            'trend_reversal': True
        }
        # Others configurable
        config_enabled = getattr(config, 'strategies', {})
        self.enabled_strategies = {**always_on, **config_enabled}
        # For efficiency tracking
        self.stats = {k: {'success': 0, 'fail': 0} for k in self.enabled_strategies}

    def run(self, daily_data, bucket_name, ticker=None):
        signals = []
        close = daily_data['c']
        if bucket_name == 'short_term':
            # Advanced: SMA crossover + RSI
            sma10 = close.rolling(window=10).mean()
            sma30 = close.rolling(window=30).mean()
            rsi = self.compute_rsi(close, 14)
            volume = daily_data['v'] if 'v' in daily_data else None
            open_ = daily_data['o'] if 'o' in daily_data else None
            high = daily_data['h'] if 'h' in daily_data else None
            low = daily_data['l'] if 'l' in daily_data else None

            # Debug print for test failures
            print(f"[DEBUG] close[-1]={close.iloc[-1]}, sma10[-1]={sma10.iloc[-1]}, sma30[-1]={sma30.iloc[-1]}, rsi[-1]={rsi.iloc[-1]}")

            # 1. SMA/RSI combo
            if self.enabled_strategies.get('sma_rsi_combo', True):
                if close.iloc[-1] > sma10.iloc[-1] and sma10.iloc[-1] > sma30.iloc[-1] and rsi.iloc[-1] < 70:
                    signals.append({
                        'action': 'buy',
                        'qty': 1,
                        'reason': 'Bullish SMA crossover and RSI below 70',
                        'risk': 'medium',
                        'strategy': 'sma_rsi_combo',
                        'ticker': ticker
                    })
            if self.enabled_strategies.get('rsi_reversal', True):
                if rsi.iloc[-1] > 80:
                    signals.append({
                        'action': 'sell',
                        'qty': 1,
                        'reason': 'RSI above 80 (overbought)',
                        'risk': 'high',
                        'strategy': 'rsi_reversal',
                        'ticker': ticker
                    })

            # 2. Volume Surge
            if self.enabled_strategies.get('volume_surge', True):
                if volume is not None and len(volume) > 10:
                    avg_vol = volume.iloc[1:11].mean()
                    if volume.iloc[0] > 2 * avg_vol:
                        signals.append({
                            'action': 'buy',
                            'qty': 1,
                            'reason': 'Volume surge detected',
                            'risk': 'medium',
                            'strategy': 'volume_surge',
                            'ticker': ticker
                        })

            # 3. Gap Up/Down
            if self.enabled_strategies.get('gap_up', True) or self.enabled_strategies.get('gap_down', True):
                if open_ is not None and close is not None and len(close) > 1:
                    prev_close = close.iloc[1]
                    gap = (open_.iloc[0] - prev_close) / prev_close
                    if gap > 0.05 and self.enabled_strategies.get('gap_up', True):
                        signals.append({
                            'action': 'buy',
                            'qty': 1,
                            'reason': 'Gap up > 5%',
                            'risk': 'high',
                            'strategy': 'gap_up',
                            'ticker': ticker
                        })
                    elif gap < -0.05 and self.enabled_strategies.get('gap_down', True):
                        signals.append({
                            'action': 'sell',
                            'qty': 1,
                            'reason': 'Gap down > 5%',
                            'risk': 'high',
                            'strategy': 'gap_down',
                            'ticker': ticker
                        })

            # 4. MACD Crossover
            if self.enabled_strategies.get('macd_bullish', True) or self.enabled_strategies.get('macd_bearish', True):
                macd, signal_line = self.compute_macd(close)
                if macd is not None and signal_line is not None and len(macd) > 1:
                    if macd.iloc[0] > signal_line.iloc[0] and macd.iloc[1] < signal_line.iloc[1] and self.enabled_strategies.get('macd_bullish', True):
                        signals.append({
                            'action': 'buy',
                            'qty': 1,
                            'reason': 'MACD bullish crossover',
                            'risk': 'medium',
                            'strategy': 'macd_bullish',
                            'ticker': ticker
                        })
                    elif macd.iloc[0] < signal_line.iloc[0] and macd.iloc[1] > signal_line.iloc[1] and self.enabled_strategies.get('macd_bearish', True):
                        signals.append({
                            'action': 'sell',
                            'qty': 1,
                            'reason': 'MACD bearish crossover',
                            'risk': 'medium',
                            'strategy': 'macd_bearish',
                            'ticker': ticker
                        })

            # 5. 52-Week High/Low Breakout
            if self.enabled_strategies.get('breakout_high', True) or self.enabled_strategies.get('breakout_low', True):
                if len(close) >= 252:
                    high_52w = close.iloc[0:252].max()
                    low_52w = close.iloc[0:252].min()
                    if close.iloc[0] >= high_52w and self.enabled_strategies.get('breakout_high', True):
                        signals.append({
                            'action': 'buy',
                            'qty': 1,
                            'reason': '52-week high breakout',
                            'risk': 'high',
                            'strategy': 'breakout_high',
                            'ticker': ticker
                        })
                    elif close.iloc[0] <= low_52w and self.enabled_strategies.get('breakout_low', True):
                        signals.append({
                            'action': 'sell',
                            'qty': 1,
                            'reason': '52-week low breakdown',
                            'risk': 'high',
                            'strategy': 'breakout_low',
                            'ticker': ticker
                        })

            # 6. Bullish Engulfing Pattern (simple version)
            if self.enabled_strategies.get('bullish_engulfing', True):
                if open_ is not None and close is not None and len(close) > 1:
                    if close.iloc[0] > open_.iloc[0] and close.iloc[1] < open_.iloc[1] and close.iloc[0] > open_.iloc[1] and open_.iloc[0] < close.iloc[1]:
                        signals.append({
                            'action': 'buy',
                            'qty': 1,
                            'reason': 'Bullish engulfing pattern',
                            'risk': 'medium',
                            'strategy': 'bullish_engulfing',
                            'ticker': ticker
                        })

        elif bucket_name == 'long_term':
            # Advanced: Buy if price above 200-day SMA, sell if below
            sma200 = close.rolling(window=200).mean()
            if self.enabled_strategies.get('trend_following', True):
                if close.iloc[0] > sma200.iloc[0]:
                    signals.append({
                        'action': 'buy',
                        'qty': 1,
                        'reason': 'Price above 200-day SMA (long-term uptrend)',
                        'risk': 'low',
                        'strategy': 'trend_following',
                        'ticker': ticker
                    })
            if self.enabled_strategies.get('trend_reversal', True):
                if close.iloc[0] < sma200.iloc[0]:
                    signals.append({
                        'action': 'sell',
                        'qty': 1,
                        'reason': 'Price below 200-day SMA (trend reversal)',
                        'risk': 'medium',
                        'strategy': 'trend_reversal',
                        'ticker': ticker
                    })

        elif bucket_name == 'options':
            # Example: Buy call if price above 10-day SMA and volatility is high
            sma10 = close.rolling(window=10).mean()
            volatility = close.pct_change().rolling(window=10).std()
            if self.enabled_strategies.get('momentum_options', True):
                if close.iloc[0] > sma10.iloc[0] and volatility.iloc[0] > 0.02:
                    signals.append({
                        'action': 'buy_call',
                        'qty': 1,
                        'reason': 'Price above 10-day SMA and high volatility',
                        'risk': 'high',
                        'strategy': 'momentum_options',
                        'ticker': ticker
                    })

        return signals

    def compute_macd(self, series, fast=12, slow=26, signal=9):
        exp1 = series.ewm(span=fast, adjust=False).mean()
        exp2 = series.ewm(span=slow, adjust=False).mean()
        macd = exp1 - exp2
        signal_line = macd.ewm(span=signal, adjust=False).mean()
        return macd, signal_line
        if strategy in self.stats:
            if success:
                self.stats[strategy]['success'] += 1
            else:
                self.stats[strategy]['fail'] += 1

    def report_stats(self):
        print("\n--- Strategy Efficiency Report ---")
        for strat, res in self.stats.items():
            total = res['success'] + res['fail']
            if total > 0:
                pct = 100 * res['success'] / total
                print(f"{strat}: {res['success']} wins / {total} signals ({pct:.1f}% win rate)")
            else:
                print(f"{strat}: No signals yet.")
        return None

    def explain(self, signal):
        base = f"Order: {signal['action']} {signal['qty']} {signal['ticker']} because {signal['reason']}"
        details = f" | Risk: {signal.get('risk', 'N/A')}, Strategy: {signal.get('strategy', 'N/A')}"
        return base + details

    def compute_rsi(self, series, period=14):
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
