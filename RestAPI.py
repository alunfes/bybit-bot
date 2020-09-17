import requests
import json
import time
import datetime
import pandas as pd
import threading
from SystemFlg import SystemFlg

class RestAPI:

    '''
    多くても数日分のohlc取得に使う。
    分の途中でもohlc返すので、最後のデータは使わない。
    interval:ohlcのminutes
    '''
    @classmethod
    def get_ohlc(cls, interval, from_ut):
        #https://api.bybit.com/v2/public/kline/list?symbol=BTCUSD&interval=1&limit=10&from=1590956090
        '''
        [{'symbol': 'BTCUSD', 'interval': '1', 'open_time': 1590956100, 'open': '9497.5', 'high': '9497.5', 'low': '9497', 'close': '9497', 'volume': '119952', 'turnover': '12.630514759999999'}, {'symbol': 'BTCUSD', 'interval': '1', 'open_time': 1590956160, 'open': '9497', 'high': '9497.5', 'low': '9497', 'close': '9497', 'volume': '71382', 'turnover': '7.516256749999998'}, {'symbol': 'BTCUSD', 'interval': '1', 'open_time': 1590956220, 'open': '9497', 'high': '9497.5', 'low': '9497', 'close': '9497', 'volume': '15624', 'turnover': '1.6451110899999999'}, {'symbol': 'BTCUSD', 'interval': '1', 'open_time': 1590956280, 'open': '9497', 'high': '9501', 'low': '9497', 'close': '9501', 'volume': '204107', 'turnover': '21.486218679999986'}, {'symbol': 'BTCUSD', 'interval': '1', 'open_time': 1590956340, 'open': '9501', 'high': '9505', 'low': '9501', 'close': '9505', 'volume': '92542', 'turnover': '9.736941810000001'}, {'symbol': 'BTCUSD', 'interval': '1', 'open_time': 1590956400, 'open': '9505', 'high': '9505', 'low': '9504.5', 'close': '9505', 'volume': '47031', 'turnover': '4.94804154'}, {'symbol': 'BTCUSD', 'interval': '1', 'open_time': 1590956460, 'open': '9505', 'high': '9505', 'low': '9501.5', 'close': '9501.5', 'volume': '67640', 'turnover': '7.116735020000003'}, {'symbol': 'BTCUSD', 'interval': '1', 'open_time': 1590956520, 'open': '9501.5', 'high': '9502', 'low': '9501.5', 'close': '9502', 'volume': '31054', 'turnover': '3.26817925'}, {'symbol': 'BTCUSD', 'interval': '1', 'open_time': 1590956580, 'open': '9502', 'high': '9502', 'low': '9501.5', 'close': '9501.5', 'volume': '15395', 'turnover': '1.6202682699999995'}, {'symbol': 'BTCUSD', 'interval': '1', 'open_time': 1590956640, 'open': '9501.5', 'high': '9502', 'low': '9497', 'close': '9497', 'volume': '213264', 'turnover': '22.44883971999999'}]
        '''
        url = 'https://api.bybit.com/v2/public/kline/list'
        current_ts = from_ut
        reminaing_limit = 200 #一度に取得できるデータ数で200以下
        timestamp = []
        dt = []
        open = []
        high = []
        low = []
        close = []
        volume = []
        flg = True
        while flg:
            params = {
                'symbol':'BTCUSD',
                'interval':interval,
                'limit':reminaing_limit,
                'from':current_ts
            }
            res = requests.get(url, params=params)
            jdata = res.json()
            if jdata['result'] != None:
                if len(jdata['result']) > 0:
                    timestamp.extend([d.get('open_time') for d in jdata['result']])
                    li = list(map(lambda x: datetime.datetime.strptime(str(datetime.datetime.fromtimestamp(int(x))), '%Y-%m-%d %H:%M:%S'), [d.get('open_time') for d in jdata['result']]))
                    dt.extend(li)
                    open.extend([d.get('open') for d in jdata['result']])
                    high.extend([d.get('high') for d in jdata['result']])
                    low.extend([d.get('low') for d in jdata['result']])
                    close.extend([d.get('close') for d in jdata['result']])
                    volume.extend([d.get('volume') for d in jdata['result']])
                    current_ts = timestamp[-1] + 60
                else:
                    flg = False
                    break
            else:
                flg=False
                break
            time.sleep(0.5)
        df = pd.DataFrame({'timestamp':timestamp, 'dt':dt, 'open':open, 'high':high, 'low':low, 'close':close, 'size':volume})
        df = df.astype({'timestamp': 'int64', 'dt':'object', 'open': 'float64', 'high': 'float64', 'low': 'float64', 'close': 'float64', 'size': 'int64'})
        if time.time() - df.iloc[-1]['timestamp'] <= 59: #分の途中でもohlcを返すので、60秒経過しているかチェックして、経過していなければ削除
            df = df.iloc[0:-2]
        return df

    @classmethod
    def get_order_status(cls, order_id):
        #url = 'https://api.bybit.com/v2/private/order'
        url = 'https://api.bybit.com/v2/private/execution/list'
        #url = 'https://api.bybit.com/v2/open-api/order/list'
        params = {
            'order_id': order_id,
            'symbol': 'BTCUSD',
        }
        res = requests.get(url, params=params)
        jdata = res.json()
        #if jdata['result'] != None:





    @classmethod
    def __ohlc_thread(cls):
        t = datetime.datetime.now().timestamp()
        cls.kijun_timestamp = int(t - (t - (t // 60.0) * 60.0))+ 60 #timestampの秒を次の分の0に修正
        while SystemFlg.get_system_flg():
            if cls.kijun_timestamp <= datetime.datetime.now().timestamp():
                #download last 1m ohlc

                df = cls.get_ohlc(1, cls.kijun_timestamp - 60)
                print(datetime.datetime.now())
                print(df)
                cls.kijun_timestamp += 60
            else:
                time.sleep(1)





if __name__ == '__main__':
    #RestAPI.initialize()
    print(RestAPI.get_ohlc(1, 1595745510))
    #RestAPI.get_order_status('e99d3624-0a5b-43c7-a518-55d139fee8f1')