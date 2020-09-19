from Trade import Trade
from Account import Account


class Strategy:
    @classmethod
    def model_prediction_opt_posi_limit(cls, pred, amount):
        ad = ActionData()
        if pred=='Buy' or pred=='Sell':
            bid, ask = Trade.get_bid_ask()
            order_data = Account.get_order_data()
            if Account.holding_side == pred and order_data == None:
                pass
            elif Account.holding_side == pred and order_data['side'] == pred: #entry order is partially filled -> update price if necessary
                if (order_data['side'] == 'Buy' and bid > order_data['price']) or (order_data['side'] == 'Sell' and ask < order_data['price']): #order price is far from bid or ask
                    ad.add_action('update', '', bid if order_data['side'] == 'Buy' else ask, 0, '', order_data['order_id'], 'update order price')
            elif Account.holding_side == pred and order_data['side'] != pred: #unexpexted situation, opposite order exist -> cancel unexpected order
                ad.add_action('cancel', '', 0,0,'',order_data['order_id'], 'cancel unexpected order')
                print('Strategy: Holding == pred but opposite side order exist!')
            elif Account.holding_side != pred and order_data == None: #opposite pred but no order -> entry exit and entry order
                ad.add_action('entry', pred, bid if pred=='Buy' else ask, Account.holding_size + amount, 'Limit', '', 'exit and entry order')
            elif Account.holding_side != pred and order_data['side'] == pred:  # opposite pred and exit entry order already exist -> update order price if necessary
                if (order_data['side'] == 'Buy' and bid > order_data['price']) or (order_data['side'] == 'Sell' and ask < order_data['price']):  # order price is far from bid or ask
                    ad.add_action('update', '', bid if order_data['side'] == 'Buy' else ask, 0, '', order_data['order_id'], 'update order price')
            elif Account.holding_side != pred and order_data['side'] != pred:  # opposite pred and opposite order exist (maybe old pred order is still exist without fully filled)
                ad.add_action('cancel', '', 0,0,'',order_data['order_id'], 'cancel unexpected order')
                ad.add_action('entry', pred, bid if pred == 'Buy' else ask, Account.holding_size + amount, 'Limit', '', 'exit and entry order')
            else:
                print('Strategy: Unexpected situation!', order_data)
                print('holding side:', Account.holding_side)
                print('holding price:', Account.holding_price)
                print('holding size:', Account.holding_size)
        else:
            print('Strategy: Unknown pred!', pred)
        return ad




class ActionData:
    def __init__(self):
        self.action = [] #entry, cancel, update
        self.order_side = []
        self.order_size = []
        self.order_price = []
        self.order_type = []
        self.order_id = []
        self.message = []

    def add_action(self, action, order_side, order_price, order_size, order_type, order_id, message):
        self.action.append(action)
        self.order_side.append(order_side)
        self.order_price.append(order_price)
        self.order_size.append(order_size)
        self.order_type.append(order_type)
        self.order_id.append(order_id)
        self.message.append(message)