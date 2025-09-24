import datetime
import yaml
from src.core.data import MarketData
from src.core.strategy import StrategyManager
from src.core.scanner import TickerScanner
from tests.test_backtest import run_backtest
from src.core.config import Config

def simulate_account(trades, initial_amount, data):
    balance = initial_amount
    trade_log = []
    for trade in trades:
        idx = trade.get('index', -1)
        action = trade['action']
        price = data['c'].iloc[idx] if idx >= 0 else data['c'].iloc[-1]
        qty = trade.get('qty', 1)
        if action == 'buy':
            cost = price * qty
            if balance >= cost:
                balance -= cost
                trade_log.append({'type': 'buy', 'price': price, 'qty': qty, 'balance': balance, 'strategy': trade.get('strategy'), 'success': True, 'reason': trade.get('reason')})
            else:
                trade_log.append({'type': 'buy', 'price': price, 'qty': qty, 'balance': balance, 'strategy': trade.get('strategy'), 'success': False, 'reason': 'Insufficient funds'})
        elif action == 'sell':
            proceeds = price * qty
            balance += proceeds
            trade_log.append({'type': 'sell', 'price': price, 'qty': qty, 'balance': balance, 'strategy': trade.get('strategy'), 'success': True, 'reason': trade.get('reason')})
    return balance, trade_log

def rolling_backtest(strategy_manager, data, initial_amount, lookback_days=365):
    # data: DataFrame with at least 2 years of daily data
    # Simulate starting 1 year ago, rolling forward day by day
    from collections import defaultdict
    account = initial_amount
    trade_log = []
    strategy_stats = defaultdict(lambda: {'success': 0, 'fail': 0})
    # Only start after lookback_days (so indicators have enough data)
    for i in range(lookback_days, len(data)):
        window = data.iloc[:i+1]  # up to and including day i
        signals = strategy_manager.run(window, 'short_term')
        for s in signals:
            # Only act if the signal is for the current day
            if s.get('index', window.index[-1]) == window.index[-1]:
                price = window['c'].iloc[-1]
                qty = s.get('qty', 1)
                if s['action'] == 'buy' and account >= price * qty:
                    account -= price * qty
                    trade_log.append({'type': 'buy', 'price': price, 'qty': qty, 'balance': account, 'strategy': s.get('strategy'), 'success': True, 'reason': s.get('reason'), 'date': window.index[-1]})
                    strategy_stats[s.get('strategy')]['success'] += 1
                elif s['action'] == 'sell':
                    account += price * qty
                    trade_log.append({'type': 'sell', 'price': price, 'qty': qty, 'balance': account, 'strategy': s.get('strategy'), 'success': True, 'reason': s.get('reason'), 'date': window.index[-1]})
                    strategy_stats[s.get('strategy')]['success'] += 1
                else:
                    trade_log.append({'type': s['action'], 'price': price, 'qty': qty, 'balance': account, 'strategy': s.get('strategy'), 'success': False, 'reason': 'Insufficient funds', 'date': window.index[-1]})
                    strategy_stats[s.get('strategy')]['fail'] += 1
    return account, trade_log, strategy_stats

def main():
    # Load config from YAML
    config = Config.load('config.yaml')

    # Read backtest config
    backtest_cfg = config.backtest or {}
    years_of_data = float(backtest_cfg.get('years_of_data', 1))
    years_to_backtest = float(backtest_cfg.get('years_to_backtest', 0.5))
    days_of_data = int(years_of_data * 365)
    days_to_backtest = int(years_to_backtest * 365)
    end_date = datetime.date.today()
    start_date = end_date - datetime.timedelta(days=days_of_data)
    lookback_days = days_of_data - days_to_backtest

    tickers = config.tickers or ['TQQQ', 'SQQQ']
    initial_amount = 10000
    market_data = MarketData(config)
    strategy_manager = StrategyManager(config)

    for ticker in tickers:
        print(f"--- Rolling Backtest for {ticker} ---")
        # Force fresh download: ignore cache by deleting cache file if exists
        import os
        cache_path = f"market_cache/{ticker}_day_365.pkl"
        if os.path.exists(cache_path):
            os.remove(cache_path)
        data = market_data.fetch(ticker, start_date, end_date)
        if data is None or data.empty or len(data) < 190:
            print(f"Not enough data for {ticker}")
            continue
        # Ensure index is datetime for reporting
        if not hasattr(data.index, 'tz'):
            data.index = pd.to_datetime(data['t'], unit='ms')
        final_balance, trade_log, strategy_stats = rolling_backtest(strategy_manager, data, initial_amount, lookback_days=lookback_days)
        # Collect all trades for summary
        if 'all_trades' not in locals():
            all_trades = []
        all_trades.extend(trade_log)
        print(f"  Final Account Balance: ${final_balance:.2f}")
        print(f"  Trades: {len(trade_log)}")
        print(f"  Strategy Stats: {dict(strategy_stats)}")
        print(f"  Trade Log (last 5): {trade_log[-5:]}")
        wins = [t for t in trade_log if t['success']]
        fails = [t for t in trade_log if not t['success']]
        print(f"  Successful Trades: {len(wins)}")
        print(f"  Failed Trades: {len(fails)}")
        for fail in fails:
            print(f"    FAIL: {fail}")

    # Performance summary
    if 'all_trades' in locals() and all_trades:
        print("\n--- Performance Report ---")
        total_wins = [t for t in all_trades if t['success']]
        total_fails = [t for t in all_trades if not t['success']]
        print(f"Total Trades: {len(all_trades)}")
        print(f"Total Successful Trades: {len(total_wins)}")
        print(f"Total Failed Trades: {len(total_fails)}")
        print(f"Strategies Used: {set(t['strategy'] for t in all_trades)}")
        print("Failed Trades Details:")
        for fail in total_fails:
            print(fail)
        print("\nStrategy Success/Fail Counts:")
        from collections import Counter
        strat_counter = Counter([t['strategy'] for t in total_wins])
        strat_fail_counter = Counter([t['strategy'] for t in total_fails])
        for strat in set(strat_counter.keys()).union(strat_fail_counter.keys()):
            print(f"{strat}: Success={strat_counter.get(strat,0)}, Fail={strat_fail_counter.get(strat,0)}")

if __name__ == "__main__":
    main()
