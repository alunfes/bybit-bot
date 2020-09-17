from SystemFlg import SystemFlg

import websocket
import json
import time
import threading
from datetime import datetime
import dateutil
import pytz
import pandas as pd
import copy
import pprint

'''
trade
{'topic': 'trade.BTCUSD', 'data': [{'trade_time_ms': 1590755573063, 'timestamp': '2020-05-29T12:32:53.000Z', 'symbol': 'BTCUSD', 'side': 'Buy', 'size': 100, 'price': 9423.5, 'tick_direction': 'PlusTick', 'trade_id': '47bab841-00c9-573b-bc1d-d8beabea4e4b', 'cross_seq': 1631609967}]}
{'topic': 'trade.BTCUSD', 'data': [{'trade_time_ms': 1590755573720, 'timestamp': '2020-05-29T12:32:53.000Z', 'symbol': 'BTCUSD', 'side': 'Sell', 'size': 1, 'price': 9423, 'tick_direction': 'MinusTick', 'trade_id': 'fa0380af-9f28-5b79-8304-6c8ebfd06d29', 'cross_seq': 1631609974}]}
{'topic': 'trade.BTCUSD', 'data': [{'trade_time_ms': 1590755575117, 'timestamp': '2020-05-29T12:32:55.000Z', 'symbol': 'BTCUSD', 'side': 'Buy', 'size': 164, 'price': 9423.5, 'tick_direction': 'PlusTick', 'trade_id': '10c48e73-9bb0-52f1-bd2d-655eca5b78d1', 'cross_seq': 1631610032}, {'trade_time_ms': 1590755575117, 'timestamp': '2020-05-29T12:32:55.000Z', 'symbol': 'BTCUSD', 'side': 'Buy', 'size': 10, 'price': 9423.5, 'tick_direction': 'ZeroPlusTick', 'trade_id': '7e5b986c-4412-53a7-81d6-0b6661779e6c', 'cross_seq': 1631610032}, {'trade_time_ms': 1590755575117, 'timestamp': '2020-05-29T12:32:55.000Z', 'symbol': 'BTCUSD', 'side': 'Buy', 'size': 32, 'price': 9423.5, 'tick_direction': 'ZeroPlusTick', 'trade_id': '95723b56-8534-50cd-93ff-7e92409e2192', 'cross_seq': 1631610032}, {'trade_time_ms': 1590755575117, 'timestamp': '2020-05-29T12:32:55.000Z', 'symbol': 'BTCUSD', 'side': 'Buy', 'size': 2, 'price': 9423.5, 'tick_direction': 'ZeroPlusTick', 'trade_id': '72b0151f-477d-56a0-afff-ecd2ba7eaab4', 'cross_seq': 1631610032}, {'trade_time_ms': 1590755575117, 'timestamp': '2020-05-29T12:32:55.000Z', 'symbol': 'BTCUSD', 'side': 'Buy', 'size': 2, 'price': 9423.5, 'tick_direction': 'ZeroPlusTick', 'trade_id': '5694b5f2-a052-5dc7-a3c4-153f4fc43d92', 'cross_seq': 1631610032}, {'trade_time_ms': 1590755575117, 'timestamp': '2020-05-29T12:32:55.000Z', 'symbol': 'BTCUSD', 'side': 'Buy', 'size': 52, 'price': 9423.5, 'tick_direction': 'ZeroPlusTick', 'trade_id': '840dfee8-9e94-5ae6-9ecf-b85477b64eef', 'cross_seq': 1631610032}, {'trade_time_ms': 1590755575117, 'timestamp': '2020-05-29T12:32:55.000Z', 'symbol': 'BTCUSD', 'side': 'Buy', 'size': 2, 'price': 9423.5, 'tick_direction': 'ZeroPlusTick', 'trade_id': '1ce21432-f5af-5a02-ad4e-dd95eb689beb', 'cross_seq': 1631610032}, {'trade_time_ms': 1590755575117, 'timestamp': '2020-05-29T12:32:55.000Z', 'symbol': 'BTCUSD', 'side': 'Buy', 'size': 127, 'price': 9423.5, 'tick_direction': 'ZeroPlusTick', 'trade_id': '673b0948-21b0-5ff5-896b-922c9c62209d', 'cross_seq': 1631610032}, {'trade_time_ms': 1590755575117, 'timestamp': '2020-05-29T12:32:55.000Z', 'symbol': 'BTCUSD', 'side': 'Buy', 'size': 5, 'price': 9424, 'tick_direction': 'PlusTick', 'trade_id': '4ea2e451-76c7-5065-9576-3fa45eca9dda', 'cross_seq': 1631610032}, {'trade_time_ms': 1590755575117, 'timestamp': '2020-05-29T12:32:55.000Z', 'symbol': 'BTCUSD', 'side': 'Buy', 'size': 2, 'price': 9424, 'tick_direction': 'ZeroPlusTick', 'trade_id': 'fadcb18b-5dc0-5308-ab4b-d25b0e6ba732', 'cross_seq': 1631610032}, {'trade_time_ms': 1590755575117, 'timestamp': '2020-05-29T12:32:55.000Z', 'symbol': 'BTCUSD', 'side': 'Buy', 'size': 2, 'price': 9424, 'tick_direction': 'ZeroPlusTick', 'trade_id': 'ebc1e0dc-516d-5e5e-a0d3-79541b2e9d10', 'cross_seq': 1631610032}, {'trade_time_ms': 1590755575117, 'timestamp': '2020-05-29T12:32:55.000Z', 'symbol': 'BTCUSD', 'side': 'Buy', 'size': 2, 'price': 9424.5, 'tick_direction': 'PlusTick', 'trade_id': '9c1544e0-0a8e-522e-80c2-cd35d7a89ddd', 'cross_seq': 1631610032}, {'trade_time_ms': 1590755575117, 'timestamp': '2020-05-29T12:32:55.000Z', 'symbol': 'BTCUSD', 'side': 'Buy', 'size': 2, 'price': 9424.5, 'tick_direction': 'ZeroPlusTick', 'trade_id': '259c5f76-f74b-55d2-b739-cadf18a70405', 'cross_seq': 1631610032}, {'trade_time_ms': 1590755575117, 'timestamp': '2020-05-29T12:32:55.000Z', 'symbol': 'BTCUSD', 'side': 'Buy', 'size': 5, 'price': 9425, 'tick_direction': 'PlusTick', 'trade_id': 'f0ea2764-20c0-57dc-b510-21fe4a4c1fe4', 'cross_seq': 1631610032}, {'trade_time_ms': 1590755575117, 'timestamp': '2020-05-29T12:32:55.000Z', 'symbol': 'BTCUSD', 'side': 'Buy', 'size': 3465, 'price': 9425, 'tick_direction': 'ZeroPlusTick', 'trade_id': 'b82c0b76-e674-52b0-837f-63a191d00521', 'cross_seq': 1631610032}]}
{'topic': 'trade.BTCUSD', 'data': [{'trade_time_ms': 1590755576754, 'timestamp': '2020-05-29T12:32:56.000Z', 'symbol': 'BTCUSD', 'side': 'Buy', 'size': 100, 'price': 9425, 'tick_direction': 'ZeroPlusTick', 'trade_id': 'a988bb38-0ba7-56de-af8e-80addae09539', 'cross_seq': 1631610183}]}
{'topic': 'trade.BTCUSD', 'data': [{'trade_time_ms': 1590755578852, 'timestamp': '2020-05-29T12:32:58.000Z', 'symbol': 'BTCUSD', 'side': 'Buy', 'size': 890, 'price': 9425, 'tick_direction': 'ZeroPlusTick', 'trade_id': 'da9d34cb-4d7b-55c9-afd6-d876d64f9454', 'cross_seq': 1631610202}]}
{'topic': 'trade.BTCUSD', 'data': [{'trade_time_ms': 1590755579029, 'timestamp': '2020-05-29T12:32:59.000Z', 'symbol': 'BTCUSD', 'side': 'Buy', 'size': 545, 'price': 9425, 'tick_direction': 'ZeroPlusTick', 'trade_id': '7b12640e-8c3c-50e2-a6f9-24fadad03074', 'cross_seq': 1631610244}, {'trade_time_ms': 1590755579029, 'timestamp': '2020-05-29T12:32:59.000Z', 'symbol': 'BTCUSD', 'side': 'Buy', 'size': 164, 'price': 9425, 'tick_direction': 'ZeroPlusTick', 'trade_id': '2f23ad24-065d-54d9-b4bf-f30f8cddcd85', 'cross_seq': 1631610244}, {'trade_time_ms': 1590755579029, 'timestamp': '2020-05-29T12:32:59.000Z', 'symbol': 'BTCUSD', 'side': 'Buy', 'size': 2026, 'price': 9425, 'tick_direction': 'ZeroPlusTick', 'trade_id': '412b29e1-04c5-5a2d-8f6e-76138c35c2b3', 'cross_seq': 1631610244}, {'trade_time_ms': 1590755579029, 'timestamp': '2020-05-29T12:32:59.000Z', 'symbol': 'BTCUSD', 'side': 'Buy', 'size': 2265, 'price': 9425, 'tick_direction': 'ZeroPlusTick', 'trade_id': '5b938347-643d-5554-99ba-959c8a01aef1', 'cross_seq': 1631610244}]}
{'topic': 'trade.BTCUSD', 'data': [{'trade_time_ms': 1590755581016, 'timestamp': '2020-05-29T12:33:01.000Z', 'symbol': 'BTCUSD', 'side': 'Buy', 'size': 1, 'price': 9425, 'tick_direction': 'ZeroPlusTick', 'trade_id': '7cdda5af-f1fb-5356-9389-13028dc2c04f', 'cross_seq': 1631610280}]}
{'topic': 'trade.BTCUSD', 'data': [{'trade_time_ms': 1590755585210, 'timestamp': '2020-05-29T12:33:05.000Z', 'symbol': 'BTCUSD', 'side': 'Sell', 'size': 100, 'price': 9424.5, 'tick_direction': 'MinusTick', 'trade_id': 'b1a6c983-aef9-5d4e-b944-7d61e707d446', 'cross_seq': 1631610508}]}
{'topic': 'trade.BTCUSD', 'data': [{'trade_time_ms': 1590755585448, 'timestamp': '2020-05-29T12:33:05.000Z', 'symbol': 'BTCUSD', 'side': 'Buy', 'size': 4289, 'price': 9425, 'tick_direction': 'PlusTick', 'trade_id': '5d16eaf9-ce7d-562a-ad52-4ca8964d7692', 'cross_seq': 1631610515}]}
{'topic': 'trade.BTCUSD', 'data': [{'trade_time_ms': 1590755586042, 'timestamp': '2020-05-29T12:33:06.000Z', 'symbol': 'BTCUSD', 'side': 'Sell', 'size': 1, 'price': 9424.5, 'tick_direction': 'MinusTick', 'trade_id': '364f7ae4-8401-5e71-8579-2dbd200ea6e3', 'cross_seq': 1631610529}]}
{'topic': 'trade.BTCUSD', 'data': [{'trade_time_ms': 1590755586384, 'timestamp': '2020-05-29T12:33:06.000Z', 'symbol': 'BTCUSD', 'side': 'Sell', 'size': 1000, 'price': 9424.5, 'tick_direction': 'ZeroMinusTick', 'trade_id': 'a5d49afa-2f05-5305-a68b-656eb3ba45ce', 'cross_seq': 1631610536}]}
{'topic': 'trade.BTCUSD', 'data': [{'trade_time_ms': 1590755586444, 'timestamp': '2020-05-29T12:33:06.000Z', 'symbol': 'BTCUSD', 'side': 'Sell', 'size': 143, 'price': 9424.5, 'tick_direction': 'ZeroMinusTick', 'trade_id': '9aea47b7-053d-5862-a658-7902db8ea2e8', 'cross_seq': 1631610538}]}
{'topic': 'trade.BTCUSD', 'data': [{'trade_time_ms': 1590755586796, 'timestamp': '2020-05-29T12:33:06.000Z', 'symbol': 'BTCUSD', 'side': 'Buy', 'size': 143, 'price': 9425, 'tick_direction': 'PlusTick', 'trade_id': 'f7b41531-8808-5e88-b288-a10f6aa168a3', 'cross_seq': 1631610544}]}
{'topic': 'trade.BTCUSD', 'data': [{'trade_time_ms': 1590755588436, 'timestamp': '2020-05-29T12:33:08.000Z', 'symbol': 'BTCUSD', 'side': 'Sell', 'size': 10539, 'price': 9424.5, 'tick_direction': 'MinusTick', 'trade_id': 'd09d8494-aa0d-5393-9d30-f620b197394b', 'cross_seq': 1631610617}]}


'''

class PublicWS:
    def __init__(self):
        PublicWSData.initialize()
        websocket.enableTrace(True)
        # 接続先URLと各コールバック関数を引数に指定して、WebSocketAppのインスタンスを作成
        self.ws_pub = websocket.WebSocketApp(url='wss://stream.bybit.com/realtime',
                                             on_open=self.on_open,
                                             on_message=self.on_message,
                                             on_close=self.on_close,
                                             on_error=self.on_error)
        self.thread = threading.Thread(target=lambda: self.ws_pub.run_forever())
        self.thread.daemon = True
        self.thread.start()

    def on_open(self):
        print('opened bybit public ws.')
        channels = {
            'op': 'subscribe',
            'args': [
                'trade.BTCUSD',
                #'klineV2.360.BTCUSD',
         #       'orderBookL2_25.BTCUSD'
            ]
        }
        self.ws_pub.send(json.dumps(channels))

    def on_message(self, message):
        # message = dict(message)
        s = time.time()
        message = json.loads(message)
        if 'topic' in message.keys():
            if message['topic'] == 'trade.BTCUSD':
                prices = list(map(lambda x: (x['timestamp'], x['price']), message['data']))
                [print(i) for i in prices]
                PublicWSData.add_trade_data(message['data'])
                PublicWSData.add_price_data(message['data'])
            elif message['topic'] == 'orderBookL2_25.BTCUSD':
                print(message)
            elif message['topic'] == 'klineV2.360.BTCUSD':
                pass
                #[print(i) for i in message['data']]
            else:
                print(message)
                print('unknown message in RealtimeWSAPI!')
        else:
            print(message)

    def on_close(self, ws):
        print('closed public ws')

    def on_error(self, ws, error):
        print('Error occurred in public webscoket! restart the ws thread.', error)
        self.__init__()


'''
trade data: orderの約定/cancel確認に使う。
->BotAccoutがBotのオーダーがあった場合にorder_idで一致するものを探して適切に処理する。
よって、一旦BotAccountが取得したデータは削除していい。

price data: ohlc作成に使う。
->毎分00秒のデータが入ってきた時点で、00-59.99までのデータを使ってohlc計算する。
スレッドが始まって時刻の次の1分の00秒をkijun_timestampとして、最初の00秒を迎えるまでのデータは破棄する。
'''
class PublicWSData:
    @classmethod
    def initialize(cls):
        cls.lock_trade_data = threading.Lock()
        cls.trade_data = []
        cls.tmp_trade_data = []
        cls.price_data = [] #{timestamp, price, size}
        cls.lock_price_data = threading.Lock()
        cls.kijun_timestamp = 0
        cls.current_ohlcv = {} #{timestamp, open, high, low, close, volume}

    @classmethod
    def add_trade_data(cls, data):
        with cls.lock_trade_data:
            cls.trade_data.extend(data)

    @classmethod
    def get_trade_data(cls):
        with cls.lock_trade_data:
            tmp = copy.copy(cls.trade_data[:])
            cls.trade_data.clear()
            return tmp

    @classmethod
    def add_price_data(cls, data):
        with cls.lock_price_data:
            if cls.kijun_timestamp == 0:
                t = data[0].get('timestamp')
                cls.kijun_timestamp = int(datetime.strptime(data[0].get('timestamp').split('.')[0], '%Y-%m-%dT%H:%M:%S').timestamp())
                cls.kijun_timestamp = cls.kijun_timestamp - int(t[-7:-5]) + 120 #基準を次の1分00秒に設定
            else:
                '''
                入ってきたデータを一つずつkijun分かチェックする、次の分が入ってきたらその時点でohlc計算して次の分のデータのみ残してkijunを更新
                '''
                for d in data:
                    ts = int(datetime.strptime(d['timestamp'].split('.')[0], '%Y-%m-%dT%H:%M:%S').timestamp())
                    if ts >= cls.kijun_timestamp:
                        #calc ohlc
                        tmp_data = []
                        for dtmp in data:
                            ts = int(datetime.strptime(d['timestamp'].split('.')[0], '%Y-%m-%dT%H:%M:%S').timestamp())
                            if ts >= cls.kijun_timestamp:
                                cls.price_data.append({'timestamp':ts, 'price':d['price'], 'size':d['size']})
                            else:
                                tmp_data.append({'timestamp':ts, 'price':d['price'], 'size':d['size']})
                        prices = [d.get('price') for d in cls.price_data]
                        sizes = [d.get('size') for d in cls.price_data]
                        cls.current_ohlcv = {'timestamp':cls.kijun_timestamp, 'open':cls.price_data[0]['price'], 'high':max(prices), 'low':min(prices), 'close':cls.price_data[-1]['price'], 'volume':sum(sizes)}
                        print(cls.current_ohlcv)
                        cls.kijun_timestamp += 60
                        cls.price_data = tmp_data
                    else:
                        if cls.kijun_timestamp >= ts:
                            cls.price_data.append({'timestamp':ts, 'price':d['price'], 'size':d['size']})


import asyncio
import functools

class test:
    @classmethod
    def mainmethod(cls):
        loop = asyncio.get_event_loop()

        print('=== 一つだけ実行してみよう ===')
        #loop.run_until_complete(cls.sleeping(5))
        task1 = loop.create_task(cls.sleeping(5))
        if task1.result() != None:
            print(task1.result())

        print('\n=== 5つ並列的に動かしてみよう')
        gather = asyncio.gather(
            cls.sleeping(2),
            cls.sleeping(1),
            cls.sleeping(8),
            cls.sleeping(3),
            cls.sleeping(4)
        )
        loop.run_until_complete(gather)
        print(task1.result())

    @classmethod
    async def sleeping(cls, sec):
        loop = asyncio.get_event_loop()
        print(f'start:  {sec}秒待つよ')
        await loop.run_in_executor(None, time.sleep, sec)
        print(f'finish: {sec}秒待つよ')
        return 'ok'




if __name__ == '__main__':
    #test.mainmethod()
    SystemFlg.initialize()
    pw = PublicWS()
    # OneMinMarketData.initialize_for_bot()
    while True:
        time.sleep(1)

