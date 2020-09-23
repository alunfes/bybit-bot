import ccxt
import time
import json
import asyncio
from datetime import datetime
from SystemFlg import SystemFlg
from LineNotification import LineNotification
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
            LineNotification.send_message('error in get_positions ' + e)
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
                LineNotification.send_message('Trade-order error!, ' + str(e))
                cls.initialize()
                time.sleep(1)
            finally:
                if 'error' not in error_message:
                    return order_info
                elif 'expire' in error_message:
                    print('API key expired!')
                    print('Force finish all processes!')
                    LineNotification.send_message('API key expired!')
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
                    LineNotification.send_message('Trade.update_order_price: Error\n'+ str(e))
                    cls.initialize()
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
                LineNotification.send_message('error in cancel_order ' + str(e)+'\n'+cancel)
                cls.initialize()
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
            LineNotification.send_message('Error in Trade.get_order_byid:\n'+ str(e))
            cls.initialize()
        finally:
            return order_data['info']



    '''
    [{'info': {'user_id': 733028, 'symbol': 'BTCUSD', 'side': 'Buy', 'order_type': 'Limit', 'price': 9000, 'qty': 1000, 'time_in_force': 'GoodTillCancel', 'order_status': 'Cancelled', 'ext_fields': {'op_from': 'api', 'remark': '221.243.49.177', 'o_req_num': -1547736221712, 'xreq_type': 'x_create', 'cross_status': 'Canceled'}, 'last_exec_time': '0.000000', 'last_exec_price': 0, 'leaves_qty': 0, 'leaves_value': 0, 'cum_exec_qty': 0, 'cum_exec_value': 0, 'cum_exec_fee': 0, 'reject_reason': 'EC_PerCancelRequest', 'order_link_id': '', 'created_at': '2020-09-19T03:27:29.000Z', 'updated_at': '2020-09-19T03:27:32.000Z', 'order_id': '4b5477a7-c882-4508-85c3-0a7eb5432ce8'}, 'id': '4b5477a7-c882-4508-85c3-0a7eb5432ce8', 'clientOrderId': None, 'timestamp': 1600486049000, 'datetime': '2020-09-19T03:27:29.000Z', 'lastTradeTimestamp': None, 'symbol': 'BTC/USD', 'type': 'limit', 'side': 'buy', 'price': 9000.0, 'amount': 0.0, 'cost': 0.0, 'average': None, 'filled': 0.0, 'remaining': 0.0, 'status': 'canceled', 'fee': {'cost': 0.0, 'currency': 'BTC'}, 'trades': None}, {'info': {'user_id': 733028, 'symbol': 'BTCUSD', 'side': 'Sell', 'order_type': 'Limit', 'price': 11098, 'qty': 10000, 'time_in_force': 'GoodTillCancel', 'order_status': 'Cancelled', 'ext_fields': {'op_from': 'api', 'remark': '221.243.49.177', 'o_req_num': -1673867721712, 'xreq_type': 'x_create', 'cross_status': 'Canceled'}, 'last_exec_time': '0.000000', 'last_exec_price': 0, 'leaves_qty': 0, 'leaves_value': 0, 'cum_exec_qty': 0, 'cum_exec_value': 0, 'cum_exec_fee': 0, 'reject_reason': 'EC_PerCancelRequest', 'order_link_id': '', 'created_at': '2020-09-19T14:08:22.000Z', 'updated_at': '2020-09-19T14:08:28.000Z', 'order_id': '7fd5eaec-3553-4e10-b42a-667e3b5d5ffe'}, 'id': '7fd5eaec-3553-4e10-b42a-667e3b5d5ffe', 'clientOrderId': None, 'timestamp': 1600524502000, 'datetime': '2020-09-19T14:08:22.000Z', 'lastTradeTimestamp': None, 'symbol': 'BTC/USD', 'type': 'limit', 'side': 'sell', 'price': 11098.0, 'amount': 0.0, 'cost': 0.0, 'average': None, 'filled': 0.0, 'remaining': 0.0, 'status': 'canceled', 'fee': {'cost': 0.0, 'currency': 'BTC'}, 'trades': None}, {'info': {'user_id': 733028, 'symbol': 'BTCUSD', 'side': 'Sell', 'order_type': 'Limit', 'price': 11080.5, 'qty': 10000, 'time_in_force': 'GoodTillCancel', 'order_status': 'Cancelled', 'ext_fields': {'op_from': 'api', 'remark': '221.243.49.177|~unknown:221.243.49.177', 'o_req_num': -1676904821712, 'xreq_type': 'x_replace', 'cross_status': 'Canceled'}, 'last_exec_time': '0.000000', 'last_exec_price': 0, 'leaves_qty': 0, 'leaves_value': 0, 'cum_exec_qty': 0, 'cum_exec_value': 0, 'cum_exec_fee': 0, 'reject_reason': 'EC_PerCancelRequest', 'order_link_id': '', 'created_at': '2020-09-19T14:14:27.000Z', 'updated_at': '2020-09-19T14:24:21.000Z', 'order_id': '259a8394-0878-4ee0-9f5e-ed6dba5d54e5'}, 'id': '259a8394-0878-4ee0-9f5e-ed6dba5d54e5', 'clientOrderId': None, 'timestamp': 1600524867000, 'datetime': '2020-09-19T14:14:27.000Z', 'lastTradeTimestamp': None, 'symbol': 'BTC/USD', 'type': 'limit', 'side': 'sell', 'price': 11080.5, 'amount': 0.0, 'cost': 0.0, 'average': None, 'filled': 0.0, 'remaining': 0.0, 'status': 'canceled', 'fee': {'cost': 0.0, 'currency': 'BTC'}, 'trades': None}, {'info': {'user_id': 733028, 'symbol': 'BTCUSD', 'side': 'Sell', 'order_type': 'Limit', 'price': 11074.5, 'qty': 10000, 'time_in_force': 'GoodTillCancel', 'order_status': 'Filled', 'ext_fields': {'op_from': 'api', 'remark': '221.243.49.177', 'o_req_num': -1684053221712, 'xreq_type': 'x_create'}, 'last_exec_time': '1600527602.564752', 'last_exec_price': 11074.5, 'leaves_qty': 0, 'leaves_value': 0, 'cum_exec_qty': 10000, 'cum_exec_value': 0.9029753, 'cum_exec_fee': -0.00022574, 'reject_reason': '', 'order_link_id': '', 'created_at': '2020-09-19T14:58:24.000Z', 'updated_at': '2020-09-19T15:00:02.000Z', 'order_id': 'a20454db-b6c4-4176-a5d7-8f16be43d5da'}, 'id': 'a20454db-b6c4-4176-a5d7-8f16be43d5da', 'clientOrderId': None, 'timestamp': 1600527504000, 'datetime': '2020-09-19T14:58:24.000Z', 'lastTradeTimestamp': 1600527602564, 'symbol': 'BTC/USD', 'type': 'limit', 'side': 'sell', 'price': 11074.5, 'amount': 0.9029753, 'cost': 10000.0, 'average': None, 'filled': 0.9029753, 'remaining': 0.0, 'status': 'filled', 'fee': {'cost': 0.00022574, 'currency': 'BTC'}, 'trades': None}, {'info': {'user_id': 733028, 'symbol': 'BTCUSD', 'side': 'Buy', 'order_type': 'Limit', 'price': 11065, 'qty': 10000, 'time_in_force': 'GoodTillCancel', 'order_status': 'Filled', 'ext_fields': {'op_from': 'ios', 'remark': '221.243.49.177', 'o_req_num': -1684589821712, 'xreq_type': 'x_create'}, 'last_exec_time': '1600528613.367782', 'last_exec_price': 11065, 'leaves_qty': 0, 'leaves_value': 0, 'cum_exec_qty': 10000, 'cum_exec_value': 0.90375056, 'cum_exec_fee': -0.00022593, 'reject_reason': '', 'order_link_id': '', 'created_at': '2020-09-19T15:00:54.000Z', 'updated_at': '2020-09-19T15:16:53.000Z', 'order_id': '3f7a3cc6-1858-45b1-8d24-16a86c1d61ac'}, 'id': '3f7a3cc6-1858-45b1-8d24-16a86c1d61ac', 'clientOrderId': None, 'timestamp': 1600527654000, 'datetime': '2020-09-19T15:00:54.000Z', 'lastTradeTimestamp': 1600528613367, 'symbol': 'BTC/USD', 'type': 'limit', 'side': 'buy', 'price': 11065.0, 'amount': 0.90375056, 'cost': 10000.0, 'average': None, 'filled': 0.90375056, 'remaining': 0.0, 'status': 'filled', 'fee': {'cost': 0.00022593, 'currency': 'BTC'}, 'trades': None}, {'info': {'user_id': 733028, 'symbol': 'BTCUSD', 'side': 'Sell', 'order_type': 'Limit', 'price': 11053, 'qty': 10000, 'time_in_force': 'GoodTillCancel', 'order_status': 'Filled', 'ext_fields': {'op_from': 'api', 'remark': '221.243.49.177|~unknown:221.243.49.177', 'o_req_num': -1688043221712, 'xreq_type': 'x_replace', 'cross_status': 'ReAdded'}, 'last_exec_time': '1600528754.108708', 'last_exec_price': 11053, 'leaves_qty': 0, 'leaves_value': 0, 'cum_exec_qty': 10000, 'cum_exec_value': 0.90473174, 'cum_exec_fee': -0.00022618, 'reject_reason': '', 'order_link_id': '', 'created_at': '2020-09-19T15:07:25.000Z', 'updated_at': '2020-09-19T15:19:14.000Z', 'order_id': '07796e4a-0c30-4c88-be5e-59adb094fa09'}, 'id': '07796e4a-0c30-4c88-be5e-59adb094fa09', 'clientOrderId': None, 'timestamp': 1600528045000, 'datetime': '2020-09-19T15:07:25.000Z', 'lastTradeTimestamp': 1600528754108, 'symbol': 'BTC/USD', 'type': 'limit', 'side': 'sell', 'price': 11053.0, 'amount': 0.90473174, 'cost': 10000.0, 'average': None, 'filled': 0.90473174, 'remaining': 0.0, 'status': 'filled', 'fee': {'cost': 0.00022618, 'currency': 'BTC'}, 'trades': None}, {'info': {'user_id': 733028, 'symbol': 'BTCUSD', 'side': 'Buy', 'order_type': 'Limit', 'price': 11053, 'qty': 10000, 'time_in_force': 'GoodTillCancel', 'order_status': 'Filled', 'ext_fields': {'op_from': 'ios', 'remark': '221.243.49.177', 'o_req_num': -1692472421712, 'xreq_type': 'x_create'}, 'last_exec_time': '1600538846.720235', 'last_exec_price': 11053, 'leaves_qty': 0, 'leaves_value': 0, 'cum_exec_qty': 10000, 'cum_exec_value': 0.90473174, 'cum_exec_fee': -0.00022618, 'reject_reason': '', 'order_link_id': '', 'created_at': '2020-09-19T15:40:27.000Z', 'updated_at': '2020-09-19T18:07:26.000Z', 'order_id': '85c87fb8-d6fc-40be-b489-4ec68b2ae136'}, 'id': '85c87fb8-d6fc-40be-b489-4ec68b2ae136', 'clientOrderId': None, 'timestamp': 1600530027000, 'datetime': '2020-09-19T15:40:27.000Z', 'lastTradeTimestamp': 1600538846720, 'symbol': 'BTC/USD', 'type': 'limit', 'side': 'buy', 'price': 11053.0, 'amount': 0.90473174, 'cost': 10000.0, 'average': None, 'filled': 0.90473174, 'remaining': 0.0, 'status': 'filled', 'fee': {'cost': 0.00022618, 'currency': 'BTC'}, 'trades': None}, {'info': {'user_id': 733028, 'symbol': 'BTCUSD', 'side': 'Sell', 'order_type': 'Limit', 'price': 10980.5, 'qty': 10000, 'time_in_force': 'GoodTillCancel', 'order_status': 'Filled', 'ext_fields': {'op_from': 'api', 'remark': '221.243.49.177|~unknown:221.243.49.177', 'o_req_num': -1796591221712, 'xreq_type': 'x_replace', 'cross_status': 'ReAdded'}, 'last_exec_time': '1600564464.754425', 'last_exec_price': 10980.5, 'leaves_qty': 0, 'leaves_value': 0, 'cum_exec_qty': 10000, 'cum_exec_value': 0.91070532, 'cum_exec_fee': -0.00022766, 'reject_reason': '', 'order_link_id': '', 'created_at': '2020-09-20T01:12:25.000Z', 'updated_at': '2020-09-20T01:14:24.000Z', 'order_id': 'a9e48343-e7c9-43e5-9f7e-33d917d2c25c'}, 'id': 'a9e48343-e7c9-43e5-9f7e-33d917d2c25c', 'clientOrderId': None, 'timestamp': 1600564345000, 'datetime': '2020-09-20T01:12:25.000Z', 'lastTradeTimestamp': 1600564464754, 'symbol': 'BTC/USD', 'type': 'limit', 'side': 'sell', 'price': 10980.5, 'amount': 0.91070532, 'cost': 10000.0, 'average': None, 'filled': 0.91070532, 'remaining': 0.0, 'status': 'filled', 'fee': {'cost': 0.00022766, 'currency': 'BTC'}, 'trades': None}, {'info': {'user_id': 733028, 'symbol': 'BTCUSD', 'side': 'Buy', 'order_type': 'Limit', 'price': 10980.5, 'qty': 10000, 'time_in_force': 'GoodTillCancel', 'order_status': 'Filled', 'ext_fields': {'op_from': 'ios', 'remark': '221.243.49.177', 'o_req_num': -1796734221712, 'xreq_type': 'x_create'}, 'last_exec_time': '1600564518.676396', 'last_exec_price': 10980.5, 'leaves_qty': 0, 'leaves_value': 0, 'cum_exec_qty': 10000, 'cum_exec_value': 0.91070533, 'cum_exec_fee': -0.00022765, 'reject_reason': '', 'order_link_id': '', 'created_at': '2020-09-20T01:14:55.000Z', 'updated_at': '2020-09-20T01:15:18.000Z', 'order_id': 'f87a83a7-437d-4b36-98e1-3e46032f2212'}, 'id': 'f87a83a7-437d-4b36-98e1-3e46032f2212', 'clientOrderId': None, 'timestamp': 1600564495000, 'datetime': '2020-09-20T01:14:55.000Z', 'lastTradeTimestamp': 1600564518676, 'symbol': 'BTC/USD', 'type': 'limit', 'side': 'buy', 'price': 10980.5, 'amount': 0.91070533, 'cost': 10000.0, 'average': None, 'filled': 0.91070533, 'remaining': 0.0, 'status': 'filled', 'fee': {'cost': 0.00022765, 'currency': 'BTC'}, 'trades': None}, {'info': {'user_id': 733028, 'symbol': 'BTCUSD', 'side': 'Sell', 'order_type': 'Limit', 'price': 10972, 'qty': 10000, 'time_in_force': 'GoodTillCancel', 'order_status': 'Filled', 'ext_fields': {'op_from': 'api', 'remark': '221.243.49.177', 'o_req_num': -1798261321712, 'xreq_type': 'x_create'}, 'last_exec_time': '1600564952.308042', 'last_exec_price': 10972, 'leaves_qty': 0, 'leaves_value': 0, 'cum_exec_qty': 10000, 'cum_exec_value': 0.91141085, 'cum_exec_fee': -0.00022784, 'reject_reason': '', 'order_link_id': '', 'created_at': '2020-09-20T01:22:27.000Z', 'updated_at': '2020-09-20T01:22:32.000Z', 'order_id': '13e0883e-1d46-4ba4-8e3f-2f19ee44f6b6'}, 'id': '13e0883e-1d46-4ba4-8e3f-2f19ee44f6b6', 'clientOrderId': None, 'timestamp': 1600564947000, 'datetime': '2020-09-20T01:22:27.000Z', 'lastTradeTimestamp': 1600564952308, 'symbol': 'BTC/USD', 'type': 'limit', 'side': 'sell', 'price': 10972.0, 'amount': 0.91141085, 'cost': 10000.0, 'average': None, 'filled': 0.91141085, 'remaining': 0.0, 'status': 'filled', 'fee': {'cost': 0.00022784, 'currency': 'BTC'}, 'trades': None}, {'info': {'user_id': 733028, 'symbol': 'BTCUSD', 'side': 'Buy', 'order_type': 'Limit', 'price': 10972.5, 'qty': 10000, 'time_in_force': 'GoodTillCancel', 'order_status': 'Filled', 'ext_fields': {'op_from': 'ios', 'remark': '221.243.49.177', 'o_req_num': -1798450621712, 'xreq_type': 'x_create'}, 'last_exec_time': '1600565043.381575', 'last_exec_price': 10972.5, 'leaves_qty': 0, 'leaves_value': 0, 'cum_exec_qty': 10000, 'cum_exec_value': 0.91136933, 'cum_exec_fee': -0.00022784, 'reject_reason': '', 'order_link_id': '', 'created_at': '2020-09-20T01:23:25.000Z', 'updated_at': '2020-09-20T01:24:03.000Z', 'order_id': '272b3b8d-3c93-44ce-9cd9-0fe400d99e9f'}, 'id': '272b3b8d-3c93-44ce-9cd9-0fe400d99e9f', 'clientOrderId': None, 'timestamp': 1600565005000, 'datetime': '2020-09-20T01:23:25.000Z', 'lastTradeTimestamp': 1600565043381, 'symbol': 'BTC/USD', 'type': 'limit', 'side': 'buy', 'price': 10972.5, 'amount': 0.91136933, 'cost': 10000.0, 'average': None, 'filled': 0.91136933, 'remaining': 0.0, 'status': 'filled', 'fee': {'cost': 0.00022784, 'currency': 'BTC'}, 'trades': None}, {'info': {'user_id': 733028, 'symbol': 'BTCUSD', 'side': 'Sell', 'order_type': 'Limit', 'price': 10972, 'qty': 10000, 'time_in_force': 'GoodTillCancel', 'order_status': 'Filled', 'ext_fields': {'op_from': 'api', 'remark': '221.243.49.177', 'o_req_num': -1798844821712, 'xreq_type': 'x_create'}, 'last_exec_time': '1600565142.429804', 'last_exec_price': 10972, 'leaves_qty': 0, 'leaves_value': 0, 'cum_exec_qty': 10000, 'cum_exec_value': 0.91141086, 'cum_exec_fee': -0.00022785, 'reject_reason': '', 'order_link_id': '', 'created_at': '2020-09-20T01:25:23.000Z', 'updated_at': '2020-09-20T01:25:42.000Z', 'order_id': 'a1837f04-0ce8-4f6f-a08e-7c0a500985a5'}, 'id': 'a1837f04-0ce8-4f6f-a08e-7c0a500985a5', 'clientOrderId': None, 'timestamp': 1600565123000, 'datetime': '2020-09-20T01:25:23.000Z', 'lastTradeTimestamp': 1600565142429, 'symbol': 'BTC/USD', 'type': 'limit', 'side': 'sell', 'price': 10972.0, 'amount': 0.91141086, 'cost': 10000.0, 'average': None, 'filled': 0.91141086, 'remaining': 0.0, 'status': 'filled', 'fee': {'cost': 0.00022785, 'currency': 'BTC'}, 'trades': None}, {'info': {'user_id': 733028, 'symbol': 'BTCUSD', 'side': 'Buy', 'order_type': 'Limit', 'price': 10971, 'qty': 10000, 'time_in_force': 'GoodTillCancel', 'order_status': 'Filled', 'ext_fields': {'op_from': 'ios', 'remark': '221.243.49.177', 'o_req_num': -1799456921712, 'xreq_type': 'x_create'}, 'last_exec_time': '1600565429.845867', 'last_exec_price': 10971, 'leaves_qty': 0, 'leaves_value': 0, 'cum_exec_qty': 10000, 'cum_exec_value': 0.91149393, 'cum_exec_fee': -0.00022787, 'reject_reason': '', 'order_link_id': '', 'created_at': '2020-09-20T01:28:32.000Z', 'updated_at': '2020-09-20T01:30:29.000Z', 'order_id': '98e24f1e-8f5a-470c-9b52-5611144fa51d'}, 'id': '98e24f1e-8f5a-470c-9b52-5611144fa51d', 'clientOrderId': None, 'timestamp': 1600565312000, 'datetime': '2020-09-20T01:28:32.000Z', 'lastTradeTimestamp': 1600565429845, 'symbol': 'BTC/USD', 'type': 'limit', 'side': 'buy', 'price': 10971.0, 'amount': 0.91149393, 'cost': 10000.0, 'average': None, 'filled': 0.91149393, 'remaining': 0.0, 'status': 'filled', 'fee': {'cost': 0.00022787, 'currency': 'BTC'}, 'trades': None}, {'info': {'user_id': 733028, 'symbol': 'BTCUSD', 'side': 'Buy', 'order_type': 'Limit', 'price': 10452.5, 'qty': 10000, 'time_in_force': 'GoodTillCancel', 'order_status': 'Filled', 'ext_fields': {'op_from': 'api', 'remark': '221.243.49.177|~unknown:221.243.49.177', 'o_req_num': -2395909821712, 'xreq_type': 'x_replace', 'cross_status': 'ReAdded'}, 'last_exec_time': '1600753778.483345', 'last_exec_price': 10452.5, 'leaves_qty': 0, 'leaves_value': 0, 'cum_exec_qty': 10000, 'cum_exec_value': 0.95670892, 'cum_exec_fee': -0.00023917, 'reject_reason': '', 'order_link_id': '', 'created_at': '2020-09-22T05:46:09.000Z', 'updated_at': '2020-09-22T05:49:38.000Z', 'order_id': '5a26adf3-4770-4d31-8757-f2d17ef4cdb3'}, 'id': '5a26adf3-4770-4d31-8757-f2d17ef4cdb3', 'clientOrderId': None, 'timestamp': 1600753569000, 'datetime': '2020-09-22T05:46:09.000Z', 'lastTradeTimestamp': 1600753778483, 'symbol': 'BTC/USD', 'type': 'limit', 'side': 'buy', 'price': 10452.5, 'amount': 0.95670892, 'cost': 10000.0, 'average': None, 'filled': 0.95670892, 'remaining': 0.0, 'status': 'filled', 'fee': {'cost': 0.00023917, 'currency': 'BTC'}, 'trades': None}, {'info': {'user_id': 733028, 'symbol': 'BTCUSD', 'side': 'Sell', 'order_type': 'Limit', 'price': 10458, 'qty': 20000, 'time_in_force': 'GoodTillCancel', 'order_status': 'Filled', 'ext_fields': {'op_from': 'api', 'remark': '221.243.49.177', 'o_req_num': -2396676721712, 'xreq_type': 'x_create'}, 'last_exec_time': '1600754042.123884', 'last_exec_price': 10458, 'leaves_qty': 0, 'leaves_value': 0, 'cum_exec_qty': 20000, 'cum_exec_value': 1.91241155, 'cum_exec_fee': -0.0004781, 'reject_reason': '', 'order_link_id': '', 'created_at': '2020-09-22T05:53:10.000Z', 'updated_at': '2020-09-22T05:54:02.000Z', 'order_id': '7a75d918-3893-4449-97af-b45b240a07e7'}, 'id': '7a75d918-3893-4449-97af-b45b240a07e7', 'clientOrderId': None, 'timestamp': 1600753990000, 'datetime': '2020-09-22T05:53:10.000Z', 'lastTradeTimestamp': 1600754042123, 'symbol': 'BTC/USD', 'type': 'limit', 'side': 'sell', 'price': 10458.0, 'amount': 1.91241155, 'cost': 20000.0, 'average': None, 'filled': 1.91241155, 'remaining': 0.0, 'status': 'filled', 'fee': {'cost': 0.0004781, 'currency': 'BTC'}, 'trades': None}, {'info': {'user_id': 733028, 'symbol': 'BTCUSD', 'side': 'Buy', 'order_type': 'Limit', 'price': 10460, 'qty': 30000, 'time_in_force': 'GoodTillCancel', 'order_status': 'Cancelled', 'ext_fields': {'op_from': 'api', 'remark': '221.243.49.177', 'o_req_num': -2397149521712, 'xreq_type': 'x_create', 'cross_status': 'Canceled'}, 'last_exec_time': '0.000000', 'last_exec_price': 0, 'leaves_qty': 0, 'leaves_value': 0, 'cum_exec_qty': 0, 'cum_exec_value': 0, 'cum_exec_fee': 0, 'reject_reason': 'EC_PerCancelRequest', 'order_link_id': '', 'created_at': '2020-09-22T05:56:11.000Z', 'updated_at': '2020-09-22T05:58:56.000Z', 'order_id': '83c309f7-be9b-47cc-bcd4-952d0dcc1c6e'}, 'id': '83c309f7-be9b-47cc-bcd4-952d0dcc1c6e', 'clientOrderId': None, 'timestamp': 1600754171000, 'datetime': '2020-09-22T05:56:11.000Z', 'lastTradeTimestamp': None, 'symbol': 'BTC/USD', 'type': 'limit', 'side': 'buy', 'price': 10460.0, 'amount': 0.0, 'cost': 0.0, 'average': None, 'filled': 0.0, 'remaining': 0.0, 'status': 'canceled', 'fee': {'cost': 0.0, 'currency': 'BTC'}, 'trades': None}, {'info': {'user_id': 733028, 'symbol': 'BTCUSD', 'side': 'Buy', 'order_type': 'Limit', 'price': 10458, 'qty': 10000, 'time_in_force': 'GoodTillCancel', 'order_status': 'Filled', 'ext_fields': {'op_from': 'ios', 'remark': '221.243.49.177', 'o_req_num': -2397621121712, 'xreq_type': 'x_create'}, 'last_exec_time': '1600754361.908185', 'last_exec_price': 10458, 'leaves_qty': 0, 'leaves_value': 0, 'cum_exec_qty': 10000, 'cum_exec_value': 0.95620577, 'cum_exec_fee': -0.00023905, 'reject_reason': '', 'order_link_id': '', 'created_at': '2020-09-22T05:59:19.000Z', 'updated_at': '2020-09-22T05:59:21.000Z', 'order_id': 'ba7164d6-ff9e-42a6-a1e9-a5c63cf0bf9c'}, 'id': 'ba7164d6-ff9e-42a6-a1e9-a5c63cf0bf9c', 'clientOrderId': None, 'timestamp': 1600754359000, 'datetime': '2020-09-22T05:59:19.000Z', 'lastTradeTimestamp': 1600754361908, 'symbol': 'BTC/USD', 'type': 'limit', 'side': 'buy', 'price': 10458.0, 'amount': 0.95620577, 'cost': 10000.0, 'average': None, 'filled': 0.95620577, 'remaining': 0.0, 'status': 'filled', 'fee': {'cost': 0.00023905, 'currency': 'BTC'}, 'trades': None}, {'info': {'user_id': 733028, 'symbol': 'BTCUSD', 'side': 'Buy', 'order_type': 'Limit', 'price': 10453.5, 'qty': 10000, 'time_in_force': 'GoodTillCancel', 'order_status': 'Filled', 'ext_fields': {'op_from': 'api', 'remark': '221.243.49.177', 'o_req_num': -2432201921712, 'xreq_type': 'x_create'}, 'last_exec_time': '1600765701.718926', 'last_exec_price': 10453.5, 'leaves_qty': 0, 'leaves_value': 0, 'cum_exec_qty': 10000, 'cum_exec_value': 0.95661739, 'cum_exec_fee': -0.00023915, 'reject_reason': '', 'order_link_id': '', 'created_at': '2020-09-22T09:08:07.000Z', 'updated_at': '2020-09-22T09:08:21.000Z', 'order_id': '7592d5ea-9338-4d25-97a6-cdb37eafce87'}, 'id': '7592d5ea-9338-4d25-97a6-cdb37eafce87', 'clientOrderId': None, 'timestamp': 1600765687000, 'datetime': '2020-09-22T09:08:07.000Z', 'lastTradeTimestamp': 1600765701718, 'symbol': 'BTC/USD', 'type': 'limit', 'side': 'buy', 'price': 10453.5, 'amount': 0.95661739, 'cost': 10000.0, 'average': None, 'filled': 0.95661739, 'remaining': 0.0, 'status': 'filled', 'fee': {'cost': 0.00023915, 'currency': 'BTC'}, 'trades': None}, {'info': {'user_id': 733028, 'symbol': 'BTCUSD', 'side': 'Sell', 'order_type': 'Limit', 'price': 10446, 'qty': 24988, 'time_in_force': 'GoodTillCancel', 'order_status': 'Cancelled', 'ext_fields': {'op_from': 'api', 'remark': '221.243.49.177|~unknown:221.243.49.177', 'o_req_num': -2432845621712, 'xreq_type': 'x_replace', 'cross_status': 'Canceled'}, 'last_exec_time': '1600765968.207688', 'last_exec_price': 10446, 'leaves_qty': 0, 'leaves_value': 0, 'cum_exec_qty': 22208, 'cum_exec_value': 2.12598121, 'cum_exec_fee': -0.00053147, 'reject_reason': 'EC_PerCancelRequest', 'order_link_id': '', 'created_at': '2020-09-22T09:11:07.000Z', 'updated_at': '2020-09-22T09:12:49.000Z', 'order_id': '171fc072-082b-48b3-b811-0961369c9c43'}, 'id': '171fc072-082b-48b3-b811-0961369c9c43', 'clientOrderId': None, 'timestamp': 1600765867000, 'datetime': '2020-09-22T09:11:07.000Z', 'lastTradeTimestamp': 1600765968207, 'symbol': 'BTC/USD', 'type': 'limit', 'side': 'sell', 'price': 10446.0, 'amount': 2.12598121, 'cost': 22208.0, 'average': None, 'filled': 2.12598121, 'remaining': 0.0, 'status': 'canceled', 'fee': {'cost': 0.00053147, 'currency': 'BTC'}, 'trades': None}, {'info': {'user_id': 733028, 'symbol': 'BTCUSD', 'side': 'Buy', 'order_type': 'Limit', 'price': 10445.5, 'qty': 12208, 'time_in_force': 'GoodTillCancel', 'order_status': 'Filled', 'ext_fields': {'op_from': 'ios', 'remark': '221.243.49.177', 'o_req_num': -2433111221712, 'xreq_type': 'x_create'}, 'last_exec_time': '1600766335.594982', 'last_exec_price': 10445.5, 'leaves_qty': 0, 'leaves_value': 0, 'cum_exec_qty': 12208, 'cum_exec_value': 1.16873294, 'cum_exec_fee': -0.00029218, 'reject_reason': '', 'order_link_id': '', 'created_at': '2020-09-22T09:13:29.000Z', 'updated_at': '2020-09-22T09:18:55.000Z', 'order_id': 'bdce8d56-f392-4224-bdb1-90e5cafb011f'}, 'id': 'bdce8d56-f392-4224-bdb1-90e5cafb011f', 'clientOrderId': None, 'timestamp': 1600766009000, 'datetime': '2020-09-22T09:13:29.000Z', 'lastTradeTimestamp': 1600766335594, 'symbol': 'BTC/USD', 'type': 'limit', 'side': 'buy', 'price': 10445.5, 'amount': 1.16873294, 'cost': 12208.0, 'average': None, 'filled': 1.16873294, 'remaining': 0.0, 'status': 'filled', 'fee': {'cost': 0.00029218, 'currency': 'BTC'}, 'trades': None}]
    '''
    @classmethod
    def get_orders(cls):
        cls.num_private_access += 1
        order_data = None
        try:
            order_data = cls.bb.fetch_orders(symbol="BTC/USD", params={"count": 10})
        except Exception as e:
            print('Error in Trade.get_orders:', str(e))
            LineNotification.send_message('Error in Trade.get_orders:\n'+ str(e))
            cls.initialize()
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
            cls.initialize()
        finally:
            return order_data



if __name__ == '__main__':
    Trade.initialize()
    #print(Trade.get_orders())
    print(Trade.get_bid_ask())
    #res = Trade.order('Sell', 19000, 'Limit', -1000)
    #print(res)
    #time.sleep(3)
    #open_orders = Trade.get_orders()
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
