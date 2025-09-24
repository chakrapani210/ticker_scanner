from webull import paper_webull

class BrokerageManager:
    def __init__(self, config):
        self.webull = paper_webull()
        webull_cfg = getattr(config, 'webull', {})
        self.webull.login(webull_cfg.get('username', ''), webull_cfg.get('password', ''))

    def place_order(self, signal, bucket):
        # Market buy
        if signal['action'] == 'buy':
            order = self.webull.place_order(stock=signal['ticker'],
                                            price=0,  # market order
                                            qty=signal['qty'],
                                            action='BUY',
                                            orderType='MKT',
                                            enforce='GTC')
            return order
        # Market sell
        elif signal['action'] == 'sell':
            order = self.webull.place_order(stock=signal['ticker'],
                                            price=0,
                                            qty=signal['qty'],
                                            action='SELL',
                                            orderType='MKT',
                                            enforce='GTC')
            return order
        # Options: buy call/put (placeholder, requires real contract details)
        elif signal['action'] in ['buy_call', 'buy_put']:
            # You must provide contract_id, price, and other details in signal for real trading
            contract_id = signal.get('contract_id')
            if not contract_id:
                return {'error': 'Missing contract_id for options order'}
            order = self.webull.place_option_order(
                contract_id=contract_id,
                action='BUY',
                price=signal.get('price', 0),
                qty=signal['qty'],
                orderType='MKT',
                enforce='GTC')
            return order
        elif signal['action'] in ['sell_call', 'sell_put']:
            contract_id = signal.get('contract_id')
            if not contract_id:
                return {'error': 'Missing contract_id for options order'}
            order = self.webull.place_option_order(
                contract_id=contract_id,
                action='SELL',
                price=signal.get('price', 0),
                qty=signal['qty'],
                orderType='MKT',
                enforce='GTC')
            return order
        return None
