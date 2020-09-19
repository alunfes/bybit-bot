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
        cls.error_trial = 3
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
                if type == 'Limit' or type == 'limit':
                    order_info = cls.bb.createOrder('BTC/USD', 'limit', side, amount, price, {'time_in_force': 'GoodTillCancel'})
                elif type == 'Market' or type == 'market':
                    order_info = cls.bb.createOrder('BTC/USD', 'market', side, amount, price, {'time_in_force': 'GoodTillCancel'})
            except Exception as e:
                error_message = str(e)
                print('Trade-order error!, ' + str(e))
                print('side=', side, ', price=', price, ', type', type, ', amount', amount)
                print('error in order! ' + '\r\n' + order_info + '\r\n' + str(e))
                time.sleep(1)
            finally:
                if 'error' not in error_message:
                    return order_info
                elif 'expire' in error_message:
                    print('API key expired!')
                    print('Force finish all processes!')
                    SystemFlg.set_system_flg(False)
                    return None
                else:
                    time.sleep(cls.rest_interval)
        return None

    '''
    {'info': {'ret_code': 0, 'ret_msg': 'ok', 'ext_code': '', 'result': {'order_id': 'fbe8c420-b49e-4bf1-88cb-4b1e9d29442a'}, 'ext_info': None, 'time_now': '1600402624.772217', 'rate_limit_status': 98, 'rate_limit_reset_ms': 1600402624781, 'rate_limit': 100}, 'id': 'fbe8c420-b49e-4bf1-88cb-4b1e9d29442a', 'order_id': 'fbe8c420-b49e-4bf1-88cb-4b1e9d29442a', 'stop_order_id': None}
    '''
    @classmethod
    def update_order_price(cls, order_id, new_price):
        for i in range(cls.error_trial):
            cls.num_private_access += 1
            order_info = ''
            error_message = ''
            order_data = cls.get_order_byid(order_id)
            if 'user_id' in order_data:
                try:
                    order_info = cls.bb.edit_order(order_id,'BTC/USD', order_data['order_type'], order_data['side'], None, new_price, {'time_in_force': 'GoodTillCancel'})
                except Exception as e:
                    error_message = str(e)
                    print('Trade.update_order_price: Error', e)
                    print('order_data', order_data)
                    print('order_info', order_info)
                    time.sleep(1)
                finally:
                    if 'info' in order_info:
                        if order_info['info']['ret_msg'] == 'ok':
                            print('Trade.update_order_price:Order price successfully updated.')
                    else:
                        print('Trade.update_order_price:Order price failed.', order_info)
                    return order_info
            else:
                print('Trade.update_order_price: Order id is not found!', order_id)


    '''
    {'info': {'user_id': 733028, 'order_id': '8e469305-a916-44ea-aefc-676f2b9190c7', 'symbol': 'BTCUSD', 'side': 'Buy', 'order_type': 'Limit', 'price': 9000, 'qty': 1000, 'time_in_force': 'GoodTillCancel', 'order_status': 'New', 'last_exec_time': 0, 'last_exec_price': 0, 'leaves_qty': 1000, 'cum_exec_qty': 0, 'cum_exec_value': 0, 'cum_exec_fee': 0, 'reject_reason': '', 'order_link_id': '', 'created_at': '2020-09-18T07:41:02.147Z', 'updated_at': '2020-09-18T07:41:05.263Z'}, 'id': '8e469305-a916-44ea-aefc-676f2b9190c7', 'clientOrderId': None, 'timestamp': 1600414862147, 'datetime': '2020-09-18T07:41:02.147Z', 'lastTradeTimestamp': None, 'symbol': 'BTC/USD', 'type': 'limit', 'side': 'buy', 'price': 9000.0, 'amount': 0.0, 'cost': 0.0, 'average': None, 'filled': 0.0, 'remaining': 0.0, 'status': 'open', 'fee': {'cost': 0.0, 'currency': 'BTC'}, 'trades': None}
    '''
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
                time.sleep(1)
            finally:
                if 'error' not in error_message:
                    return cancel
                else:
                    print('error in cancel_order', cancel)
                    time.sleep(cls.rest_interval)
        return None

    '''
    {'info': {'user_id': 733028, 'symbol': 'BTCUSD', 'side': 'Buy', 'order_type': 'Limit', 'price': '9000', 'qty': 1000, 'time_in_force': 'GoodTillCancel', 'order_status': 'New', 'ext_fields': {'o_req_num': -1274537421712, 'xreq_type': 'x_create'}, 'leaves_qty': 1000, 'leaves_value': '0.11111111', 'cum_exec_qty': 0, 'cum_exec_value': None, 'cum_exec_fee': None, 'reject_reason': '', 'cancel_type': '', 'order_link_id': '', 'created_at': '2020-09-18T04:15:52.984996Z', 'updated_at': '2020-09-18T04:15:52.985133Z', 'order_id': 'ecd48762-f842-4cde-901e-fbc3be1cff99'}, 'id': 'ecd48762-f842-4cde-901e-fbc3be1cff99', 'clientOrderId': None, 'timestamp': 1600402552984, 'datetime': '2020-09-18T04:15:52.984Z', 'lastTradeTimestamp': None, 'symbol': 'BTC/USD', 'type': 'limit', 'side': 'buy', 'price': 9000.0, 'amount': 0.11111111, 'cost': 0.0, 'average': None, 'filled': 0.0, 'remaining': 0.11111111, 'status': 'open', 'fee': None, 'trades': None}
    '''
    @classmethod
    def get_order_byid(cls, order_id):
        cls.num_private_access += 1
        order_data = None
        try:
            order_data = cls.bb.fetch_order(order_id, symbol='BTC/USD', params={})
            if 'info' not in order_data:
                print('Trade.get_order_byid: No order found!', order_id)
        except Exception as e:
            print('Error in Trade.get_order_byid:', str(e))
        finally:
            return order_data['info']


    @classmethod
    def get_orders(cls):
        cls.num_private_access += 1
        order_data = None
        try:
            order_data = cls.bb.fetch_orders(symbol="BTC/USD", params={"count": 10})
        except Exception as e:
            print('Error in Trade.get_orders:', str(e))
        finally:
            return order_data



    '''
    [{'info': {'user_id': 733028, 'symbol': 'BTCUSD', 'side': 'Buy', 'order_type': 'Limit', 'price': 10944, 'qty': 10000, 'time_in_force': 'GoodTillCancel', 'order_status': 'New', 'ext_fields': {'op_from': 'ios', 'remark': '221.243.49.177', 'o_req_num': -1543203021712, 'xreq_type': 'x_create'}, 'last_exec_time': '0.000000', 'last_exec_price': 0, 'leaves_qty': 10000, 'leaves_value': 0.91374269, 'cum_exec_qty': 0, 'cum_exec_value': 0, 'cum_exec_fee': 0, 'reject_reason': 'NoError', 'order_link_id': '', 'created_at': '2020-09-19T03:03:56.000Z', 'updated_at': '2020-09-19T03:03:56.000Z', 'order_id': '0971638d-7ae2-44fa-8e3e-fccd06fa1970'}, 'id': '0971638d-7ae2-44fa-8e3e-fccd06fa1970', 'clientOrderId': None, 'timestamp': 1600484636000, 'datetime': '2020-09-19T03:03:56.000Z', 'lastTradeTimestamp': None, 'symbol': 'BTC/USD', 'type': 'limit', 'side': 'buy', 'price': 10944.0, 'amount': 0.91374269, 'cost': 0.0, 'average': None, 'filled': 0.0, 'remaining': 0.91374269, 'status': 'open', 'fee': {'cost': 0.0, 'currency': 'BTC'}, 'trades': None}, 
    {'info': {'user_id': 733028, 'symbol': 'BTCUSD', 'side': 'Buy', 'order_type': 'Limit', 'price': 9000, 'qty': 1000, 'time_in_force': 'GoodTillCancel', 'order_status': 'New', 'ext_fields': {'op_from': 'api', 'remark': '221.243.49.177', 'o_req_num': -1547736221712, 'xreq_type': 'x_create'}, 'last_exec_time': '0.000000', 'last_exec_price': 0, 'leaves_qty': 1000, 'leaves_value': 0.11111111, 'cum_exec_qty': 0, 'cum_exec_value': 0, 'cum_exec_fee': 0, 'reject_reason': 'NoError', 'order_link_id': '', 'created_at': '2020-09-19T03:27:29.000Z', 'updated_at': '2020-09-19T03:27:29.000Z', 'order_id': '4b5477a7-c882-4508-85c3-0a7eb5432ce8'}, 'id': '4b5477a7-c882-4508-85c3-0a7eb5432ce8', 'clientOrderId': None, 'timestamp': 1600486049000, 'datetime': '2020-09-19T03:27:29.000Z', 'lastTradeTimestamp': None, 'symbol': 'BTC/USD', 'type': 'limit', 'side': 'buy', 'price': 9000.0, 'amount': 0.11111111, 'cost': 0.0, 'average': None, 'filled': 0.0, 'remaining': 0.11111111, 'status': 'open', 'fee': {'cost': 0.0, 'currency': 'BTC'}, 'trades': None}]
    '''
    @classmethod
    def get_open_orders(cls):
        cls.num_private_access += 1
        order_data = None
        try:
            order_data = cls.bb.fetch_open_orders(symbol='BTC/USD', params={})
        except Exception as e:
            print('Error in Trade.get_open_orders:', str(e))
        finally:
            return order_data



if __name__ == '__main__':
    Trade.initialize()
    print(Trade.get_orders())
    #print(Trade.get_bid_ask())
    #res = Trade.order('Buy', 9000, 'Limit', 1000)
    #time.sleep(3)
    #open_orders = Trade.get_open_orders()
    #print(open_orders)
    #update_res = Trade.update_order_price(res['info']['order_id'], 10000)
    #print(update_res)
    #time.sleep(3)
    #print(Trade.get_order_byid(res['info']['order_id']))
    #time.sleep(1)
    #Trade.cancel_order(res['info']['order_id'])
    #time.sleep(1)
    #ress = Trade.get_order_byid(res['info']['order_id'])
    #print(ress)
