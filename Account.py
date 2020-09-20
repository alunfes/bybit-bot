import datetime
import time
import asyncio
import threading
from functools import partial
from SystemFlg import SystemFlg
from Trade import Trade


'''
order idを記録
topic:orderを取得してprivate wsのtopic=orderで約定を確認
約定をaccountで処理して、holding, order, plなどを更新

'''



class testA:
    @classmethod
    def r(cls, data):
        print(data)

    @classmethod
    async def process_execution(cls, data):
        loop = asyncio.get_event_loop()
        loop.run_in_executor(None, partial(cls.r, data))

class ws:
    def get_data(cls):
        loop = asyncio.get_event_loop()
        for i in range(10):
            loop.run_until_complete(testA.process_execution(i))
            print('c')

'''
botがorder出してorder idをaccountに渡す。
order idを基に逐次（10sec)確認して約定をholding, plnなどに反映させる。
botがprice update/cancelしたらaccountにその情報を渡す。
'''
class Account:
    @classmethod
    def initialize(cls):
        cls.lock_order_data = threading.Lock()
        cls.__initialize_order()
        cls.__initialize_holding()

        cls.taker_fee = 0.00075
        cls.maker_fee = -0.00025

        cls.start_ts = 0
        cls.total_pl = 0
        cls.realized_pl = 0
        cls.current_pl = 0
        cls.total_fee = 0
        cls.num_trade = 0
        cls.num_sell = 0
        cls.num_buy = 0
        cls.num_win = 0
        cls.win_rate = 0
        cls.pre_total_pl = 0 # for calc of win rate
        cls.num_market_order = 0
        cls.pl_per_min = 0

        th = threading.Thread(target=cls.__ohlc_thread)
        th.start()
        th1 = threading.Thread(target=cls.__display_thread)
        th1.start()

        print('Account thread started')



    @classmethod
    def __ohlc_thread(cls):
        print('started Account.ohlc_thread')
        cls.start_ts = time.time()
        while SystemFlg.get_system_flg():
            cls.__check_order_status_API()
            cls.__calc_total_pl()
            cls.pl_per_min = round((cls.total_pl / ((time.time() - cls.start_ts) / 60.0)), 4)
            time.sleep(10)

    @classmethod
    def __display_thread(cls):
        while SystemFlg.get_system_flg():
            print('pl=', cls.total_pl, 'num_trade=', cls.num_trade, 'win_rate=', cls.win_rate, 'pl_per_min=', cls.pl_per_min)
            print(cls.get_order_data())
            print('holding_side=', cls.holding_side, 'holding_price', cls.holding_price, 'holding_qty=', cls.holding_qty)
            time.sleep(60)

    @classmethod
    def __check_order_status_API(cls):
        if len(cls.order_id_list) > 0:
            orders = Trade.get_orders()#.reverse()
            for order in orders:
                if order['info']['order_id'] in cls.order_id_list:
                    if order['info']['leaves_qty'] < cls.order_leaves_qty[order['info']['order_id']]:
                        exec_qty = order['info']['qty'] - order['info']['leaves_qty']
                        cls.__process_execution(order['info']['order_id'], order['info']['leaves_qty'], exec_qty, order['info']['last_exec_price'], order['info']['order_type'], order['info']['order_status'])


    @classmethod
    def __initialize_order(cls):
        with cls.lock_order_data:
            cls.order_id_list = []
            cls.order_side = {}
            cls.order_price = {}
            cls.order_leaves_qty = {}
            cls.order_dt = {}
            cls.order_type = {}  # market / limit / limit-market (limit orderとしてentryして最初の1分で約定しなかったらmarket orderにする）
            cls.order_status = {}

    @classmethod
    def get_order_data(cls):
        with cls.lock_order_data:
            if len(cls.order_id_list) > 0:
                oid = cls.order_id_list[-1]
                return {'order_id':oid, 'side':cls.order_side[oid], 'type':cls.order_type[oid], 'price':cls.order_price[oid], 'leaves_qty':cls.order_leaves_qty[oid],'status':cls.order_status[oid]}
            else:
                return None

    @classmethod
    def __del_order(cls, target_order_id):
        with cls.lock_order_data:
            if target_order_id in cls.order_id_list:
                cls.order_id_list.remove(target_order_id)
                del cls.order_side[target_order_id]
                del cls.order_price[target_order_id]
                del cls.order_leaves_qty[target_order_id]
                del cls.order_dt[target_order_id]
                del cls.order_type[target_order_id]  # market / limit
                del cls.order_status[target_order_id]

    @classmethod
    def get_latest_order_num(cls):
        with cls.lock_order_data:
            if len(cls.order_serial) > 0:
                return sorted(list(cls.order_serial.keys()))[-1]
            else:
                return -1

    @classmethod
    def __initialize_holding(cls):
        cls.holding_side = ''
        cls.holding_price = 0
        cls.holding_qty = 0
        cls.holding_dt = ''


    @classmethod
    def entry_order(cls, order_id, side, price, qty, type):
        with cls.lock_order_data:
            if side == 'Buy':
                cls.num_buy += 1
            elif side == 'Sell':
                cls.num_sell += 1
            else:
                print('Account.entry_order: invalid order type!', type)
            if order_id not in cls.order_id_list:
                cls.order_id_list.append(order_id)
                cls.order_side[order_id] = side
                cls.order_price[order_id] = price
                cls.order_leaves_qty[order_id] = qty
                cls.order_dt[order_id] = datetime.datetime.now()
                cls.order_type[order_id] = type  # Limit, Market
                cls.order_status[order_id] = 'new entry'

    @classmethod
    def cancel_order(cls, order_id):
        cls.__del_order(order_id)

    @classmethod
    def update_order_price(cls, order_id, price):
        with cls.lock_order_data:
            cls.order_price[order_id] = price


    @classmethod
    def exit_all(cls, i, dt):
        if cls.holding_side != '':
            cls.entry_order('buy' if cls.holding_side == 'sell' else 'sell', 0, cls.holding_qty, 'market', i, dt)

    @classmethod
    def __update_holding(cls, side, price, qty, dt):
        if cls.holding_side != '' and cls.holding_side != side:
            cls.num_trade += 1
            cls.__calc_total_pl()
            if cls.total_pl > cls.pre_total_pl:
                cls.num_win +=1
            cls.pre_total_pl = cls.total_pl
            cls.win_rate = round(cls.num_win / cls.num_trade, 4)
        cls.holding_side = side
        cls.holding_price = price
        cls.holding_qty = qty
        cls.holding_dt = dt

    @classmethod
    def __process_execution(cls, order_id, leaves_qty, exec_qty, last_exec_price, order_type, status):
        if order_id in cls.order_id_list:
            if status == 'Cancelled':
                if order_id in cls.order_id_list:
                    cls.__del_order(order_id)
            elif status == 'New':
                if order_id in cls.order_id_list:
                    if exec_qty > 0:
                        print('New status order exec_qty is bigger than 1', exec_qty)
                else:
                    print('New order is detected which is not in the bot order list!', order_id)
            else:
                if cls.holding_side == '': #new entry
                    cls.__calc_executed_fee(last_exec_price, exec_qty, order_type)
                    cls.__update_holding(cls.order_side[order_id], last_exec_price, exec_qty, datetime.datetime.now())
                elif cls.holding_side == cls.order_side[order_id]: #additional entry
                    ave_price = (cls.holding_qty * cls.holding_price + exec_qty * last_exec_price) / (cls.holding_qty + exec_qty)
                    cls.__calc_executed_fee(last_exec_price, exec_qty, order_type)
                    cls.__calc_executed_pl(last_exec_price, exec_qty)
                    cls.__update_holding(cls.order_side[order_id], ave_price, exec_qty, datetime.datetime.now())
                elif cls.holding_side != cls.order_side[order_id]: #exit execution
                    cls.__calc_executed_fee(last_exec_price, exec_qty, order_type)
                    cls.__calc_executed_pl(last_exec_price, exec_qty)
                    cls.__update_holding(cls.order_side[order_id], last_exec_price, exec_qty, datetime.datetime.now())
                with cls.lock_order_data:
                    cls.order_status[order_id] = status
                if status == 'PartiallyFilled':
                    with cls.lock_order_data:
                        print('Account: Order Partially Filled', cls.order_leaves_qty[order_id] - leaves_qty)
                        cls.order_leaves_qty[order_id] = leaves_qty
                elif status == 'Filled':
                    if cls.order_leaves_qty[order_id] - exec_qty < 10:
                        print('Account: Order Filled', cls.get_order_data())
                        cls.__del_order(order_id)
                    else:
                        print('Account.process_execution: order filled but leave qty and exec qty is not consistent', cls.order_leaves_qty, exec_qty)
                        cls.__del_order(order_id)
                else:
                    print('Account.process_execution: Invalid status!', status)
        else:
            print('Account.process_execution: Unknown order id!', order_id)


    @classmethod
    async def process_execution(cls, order_id, leaves_qty, exec_qty, cum_exec_qty, cum_exec_fee, last_exec_price, order_type, status):
        loop = asyncio.get_event_loop()
        loop.run_in_executor(None, partial(cls.__process_execution, order_id, leaves_qty, exec_qty, cum_exec_qty, cum_exec_fee, last_exec_price, order_type, status))


    @classmethod
    def __calc_executed_pl(cls, exec_price, exec_qty):
        pl = (exec_price - cls.holding_price if cls.holding_side == 'Buy' else cls.holding_price - exec_price) / cls.holding_price * exec_qty
        cls.realized_pl += round(pl, 8)

    @classmethod
    def __calc_executed_fee(cls,  exec_price, exec_qty, order_type):
        fee = cls.maker_fee if order_type == 'Limit' else cls.taker_fee * exec_qty
        cls.total_fee -= round(fee, 8)

    @classmethod
    def __calc_total_pl(cls):
        if cls.holding_side == '':
            cls.current_pl = 0
        else:
            bid, ask = Trade.get_bid_ask()
            cls.current_pl = (bid - cls.holding_price) / cls.holding_price * cls.holding_qty if cls.holding_side == 'Buy' else (cls.holding_price - ask) / cls.holding_price * cls.holding_qty
        cls.total_pl = cls.realized_pl + cls.current_pl - cls.total_fee


if __name__ == '__main__':
    w = ws()
    w.get_data()