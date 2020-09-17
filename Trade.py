import ccxt
import time
import json
import asyncio
from datetime import datetime
from SystemFlg import SystemFlg
import pandas as pd


class Trade:
    @classmethod
    def initialize(cls):
        api_info = open('./ignore/api.json', "r")
        json_data = json.load(api_info)  # JSON形式で読み込む
        id = json_data['id']
        secret = json_data['secret']
        api_info.close()
        cls.bb = ccxt.bybit({
            'apiKey': id,
            'secret': secret,
        })
        cls.num_private_access = 0
        cls.num_public_access = 0
        cls.error_trial = 5
        cls.rest_interval = 1

    @classmethod
    def get_balance(cls):
        balance = ''
        cls.num_private_access += 1
        try:
            balance = cls.bb.fetch_balance()
        except Exception as e:
            print(e)
        return balance


    @classmethod
    def get_bid_ask(cls):
        cls.num_public_access += 1
        book = cls.bb.fetch_order_book("BTC/USD")
        return book['bids'][0][0], book['asks'][0][0]

    @classmethod
    def get_positions(cls):  # None
        cls.num_private_access += 1
        try:
            positions = cls.bb.private_get_position()
        except Exception as e:
            print('error in get_positions ' + e)
        return positions

    '''
    #https://bybit-exchange.github.io/bybit-official-api-docs/en/index.html#tag/order/paths/open-api~1order~1create/post
    {'info': {'user_id': 733028, 'order_id': 'ca55bcff-559a-47d8-bc13-edd8942dbac4', 'symbol': 'BTCUSD', 'side': 'Buy', 'order_type': 'Limit', 'price': 9000, 'qty': 10000, 'time_in_force': 'GoodTillCancel', 'order_status': 'Created', 'last_exec_time': 0, 'last_exec_price': 0, 'leaves_qty': 10000, 'cum_exec_qty': 0, 'cum_exec_value': 0, 'cum_exec_fee': 0, 'reject_reason': '', 'order_link_id': '', 'created_at': '2020-06-01T07:00:38.441Z', 'updated_at': '2020-06-01T07:00:38.442Z'}, 'id': 'ca55bcff-559a-47d8-bc13-edd8942dbac4', 'clientOrderId': None, 'timestamp': 1590994838441, 'datetime': '2020-06-01T07:00:38.441Z', 'lastTradeTimestamp': None, 'symbol': 'BTC/USD', 'type': 'limit', 'side': 'buy', 'price': 9000.0, 'amount': 0.0, 'cost': 0.0, 'average': None, 'filled': 0.0, 'remaining': 0.0, 'status': 'open', 'fee': {'cost': 0.0, 'currency': 'BTC'}, 'trades': None}
    '''
    @classmethod
    def order(cls, side, price, type, amount):
        for i in range(cls.error_trial):
            cls.num_private_access += 1
            order_info = ''
            error_message = ''
            try:
                if type == 'limit':
                    order_info = cls.bb.createOrder('BTC/USD', 'limit', side, amount, price, {'time_in_force': 'GoodTillCancel'})
                elif type == 'market':
                    order_info = cls.bb.createOrder('BTC/USD', 'market', side, amount, price, {'time_in_force': 'GoodTillCancel'})
            except Exception as e:
                error_message = str(e)
                print('Trade-order error!, ' + str(e))
                print('side=', side, ', price=', price, ', type', type, ', amount', amount)
                print('error in order! ' + '\r\n' + order_info + '\r\n' + str(e))
            finally:
                if 'error' not in error_message:
                    return order_info
                else:
                    time.sleep(cls.rest_interval)
        return None

    @classmethod
    def cancel_order(cls, order_id):
        for i in range(cls.error_trial):
            cls.num_private_access += 1
            cancel = ''
            error_message = ''
            try:
                cancel = cls.bb.cancel_order(id=order_id, symbol='BTC/USD')
            except Exception as e:
                error_message = str(e)
                print('error in cancel_order ' + str(e), cancel)
            finally:
                if 'error' not in error_message:
                    return cancel
                else:
                    time.sleep(cls.rest_interval)
        return None

    '''
    [{'user_id': 733028, 'symbol': 'BTCUSD', 'side': 'Buy', 'order_type': 'Limit', 'price': 9000, 'qty': 1000, 'time_in_force': 'GoodTillCancel', 'order_status': 'New', 
    'ext_fields': {'op_from': 'api', 'remark': '126.245.76.229', 'o_req_num': -3832568803136, 'xreq_type': 'x_create'}, 'last_exec_time': '0.000000', 'last_exec_price': 0, ¥
    'leaves_qty': 1000, 'leaves_value': 0.11111111, 'cum_exec_qty': 0, 'cum_exec_value': 0, 'cum_exec_fee': 0, 'reject_reason': 'NoError', 'order_link_id': '', 
    'created_at': '2020-06-13T05:19:44.000Z', 'updated_at': '2020-06-13T05:19:44.000Z', 'order_id': '1d8eb7f1-76d4-4e92-ad7f-ae3debe83df8'}]
    
    order_status:Cancelled, Created, New, PartiallyFilled, Filled, Rejected
    '''
    @classmethod
    def get_order_byid(cls, order_id):
        cls.num_private_access += 1
        orders = None
        try:
            orders = cls.bb.fetch_orders(symbol='BTC/USD', since=None, limit=None, params={'count': 100, 'reverse': True})
            if len(order_id) > 0:
                orders = map(lambda x: x['info'] if x['info']['order_id'] == order_id else {}, orders)
                orders = [x for x in orders if x != {}]
                if len(orders) == 0:
                    order_id = None
        except Exception as e:
            print('error in get_order_byid' + str(e))
        return orders


if __name__ == '__main__':
    Trade.initialize()
    print(Trade.get_bid_ask())
    #res = Trade.order('buy', 9000, 'limit', 1000)
    #time.sleep(1)
    #Trade.cancel_order(res['info']['order_id'])
    #time.sleep(1)
    #ress = Trade.get_order_byid(res['info']['order_id'])
    #print(ress)