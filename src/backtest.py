import datetime
import yaml
from src.core.data import MarketData
from src.core.strategy import StrategyManager
from src.core.scanner import TickerScanner
from tests.test_backtest import run_backtest

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

def main():
    # Load config from YAML
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    tickers = config.get('tickers', ['TQQQ', 'SQQQ'])
    end_date = datetime.date.today()
    start_date = end_date - datetime.timedelta(days=365)
    initial_amount = 10000
    market_data = MarketData('config.yaml')
    strategy_manager = StrategyManager(config)

    all_trades = []
    for ticker in tickers:
        print(f"--- Backtesting for {ticker} ---")
        data = market_data.fetch(ticker, start_date, end_date)
        if data is None or data.empty:
            print(f"No data for {ticker}")
            continue
        signals = strategy_manager.run(data, 'short_term', ticker)
        # Attach index to each trade for price lookup
        for s in signals:
            s['index'] = data['c'].index[-1] if hasattr(data['c'], 'index') else -1
        final_balance, trade_log = simulate_account(signals, initial_amount, data)
        all_trades.extend([{'ticker': ticker, **t} for t in trade_log])
        print(f"  Final Account Balance: ${final_balance:.2f}")
        print(f"  Trades: {len(trade_log)}")
        wins = [t for t in trade_log if t['success']]
        fails = [t for t in trade_log if not t['success']]
        print(f"  Successful Trades: {len(wins)}")
        print(f"  Failed Trades: {len(fails)}")
        for fail in fails:
            print(f"    FAIL: {fail}")

    # Performance summary
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
