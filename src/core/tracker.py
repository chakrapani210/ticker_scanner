import datetime

import pandas as pd

class PerformanceTracker:
    def __init__(self):
        self.orders = []
        self.performance = []

    def log_order(self, order, explanation):
        self.orders.append({'order': order, 'explanation': explanation, 'timestamp': datetime.datetime.now()})

    def update(self, brokerage):
        # Placeholder: fetch account performance from brokerage
        # Simulate with random value for now
        import random
        self.performance.append({'timestamp': datetime.datetime.now(), 'value': random.uniform(-1, 1)})

    def report(self):
        print('Order Log:')
        for o in self.orders:
            print(o['timestamp'], o['explanation'])
        print('\nPerformance:')
        for p in self.performance:
            print(p['timestamp'], p['value'])
        # Advanced reporting
        print('\n--- Advanced Report ---')
        if self.orders:
            df = pd.DataFrame(self.orders)
            print(f"Total Orders: {len(df)}")
            buy_orders = df[df['explanation'].str.contains('buy', case=False)]
            sell_orders = df[df['explanation'].str.contains('sell', case=False)]
            print(f"Buy Orders: {len(buy_orders)} | Sell Orders: {len(sell_orders)}")
        if self.performance:
            perf_df = pd.DataFrame(self.performance)
            avg_return = perf_df['value'].mean()
            print(f"Average Return: {avg_return:.2%}")
