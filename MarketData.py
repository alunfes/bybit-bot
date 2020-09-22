import glob
import datetime
import gzip
import pandas as pd
import time
import scipy
from sklearn.preprocessing import MinMaxScaler
from sklearn.preprocessing import StandardScaler
from sklearn.preprocessing import OneHotEncoder
from tensorflow import keras
import tensorflow_hub as hub
import matplotlib.pyplot as plt
import numpy as np
import threading
from RestAPI import RestAPI
from SystemFlg import SystemFlg


class OneMinData:
    def initialize(self):
        self.unix_time = []
        self.dt = []
        self.open = []
        self.high = []
        self.low = []
        self.close = []
        self.size = []
        self.opt_position = []

class LogData:
    def __init__(self):
        self.log_prediction = {} #datetime, prediction
        self.log_opt_position = {} #datetime, opt_position
        self.correct_pred_ratio = 0
        self.log_close = {} #datetime. close

    def calc_correct_pred_ratio(self):#predが正しいかはopt window size分後にわかる。
        check_df = MarketData.get_df()
        check_dict = dict(zip(check_df['dt'], check_df['opt_position']))
        num_correct = 0
        for k in list(self.log_prediction.keys()):
            if self.log_prediction[k] == check_dict[k]:
                num_correct += 1
        self.correct_pred_ratio = round(num_correct / len(self.log_prediction), 4)
        print('pred_ratio:', self.correct_pred_ratio)


class MarketData:
    @classmethod
    def initialize_for_bot(cls, opt_window_size, opt_kijun, time_steps, timestep_skip):
        print('initializing MarketData....')
        cls.model_data_lock = threading.Lock()
        cls.df_lock = threading.Lock()
        cls.pred_lock = threading.Lock()
        cls.time_sleep_lock = threading.Lock() #adjust time sleep for Bot and Account to prioritize MarketData calc
        cls.time_sleep = 1
        cls.prediction = ''
        cls.opt_window_size = opt_window_size
        cls.opt_kijun = opt_kijun
        cls.time_steps = time_steps
        cls.timestep_skip = timestep_skip
        cls.df = cls.download_ohlc()
        cls.log_data = LogData()
        cls.df['opt_position'] = cls.calc_opt_position()
        cls.set_model_data(cls.generate_data_for_model(cls.df))
        cls.model = keras.models.load_model('./Model/model3.h5', compile=False, custom_objects={'KerasLayer':hub.KerasLayer})
        cls.model.summary()
        print('initialized MarketData')
        #print(cls.x_train[-1])
        #print(cls.y_train[-1])
        #print(cls.abs_train[-1])
        th = threading.Thread(target=cls.__ohlc_thread)
        th.start()
        print('MarketData thread started')
        #cls.ohlc = cls.con_df_to_ohlc(df)


    @classmethod
    def initialize_for_sim(cls, opt_window_size, opt_kijun, time_steps, timestep_skip):
        print('initializing MarketData....')
        cls.model_data_lock = threading.Lock()
        cls.opt_window_size = opt_window_size
        cls.prediction = ''
        cls.opt_kijun = opt_kijun
        cls.time_steps = time_steps
        cls.timestep_skip = timestep_skip
        cls.df = pd.read_csv('./Data/onemin_bybit_opt.csv')
        cls.df['timestamp'] = 1
        cls.set_model_data(cls.generate_data_for_model(cls.df.iloc[-5000:]))
        cls.model = keras.models.load_model('./Model/model2.h5', compile=False, custom_objects={'KerasLayer': hub.KerasLayer})



    @classmethod
    def get_model_data(cls):
        with cls.model_data_lock:
            return cls.x_train, cls.y_train, cls.abs_train

    @classmethod
    def set_model_data(cls, model_data):
        with cls.model_data_lock:
            cls.x_train, cls.y_train, cls.abs_train = model_data[0], model_data[1], model_data[2].reshape(model_data[2].shape[0], model_data[2].shape[1], 1)

    @classmethod
    def __set_time_sleep(cls, t):
        with cls.time_sleep_lock:
            cls.time_sleep = t

    @classmethod
    def get_time_sleep(cls):
        with cls.time_sleep_lock:
            return cls.time_sleep

    @classmethod
    def get_df(cls):
        with cls.df_lock:
            return cls.df

    @classmethod
    def add_df(cls, new_df):
        with cls.df_lock:
            copy_start_index = -1 #dfの最後のtimestampより大きいtimestampからconcatする
            for i in range(len(new_df['timestamp'])):
                if float(new_df['timestamp'].iloc[i]) > float(cls.df['timestamp'].iloc[-1]):
                    copy_start_index = i
                    break
            if copy_start_index != -1:
                new_df = new_df.iloc[copy_start_index:]
                cls.df = pd.concat([cls.df, new_df])
                cls.df = cls.df.iloc[len(new_df):]
                cls.df = cls.df.reset_index(drop=True)
                for i in range(len(new_df)):
                    cls.df.loc[cls.df.index[-i-1], 'opt_position'] = -1
                for i in range(len(new_df)):
                    if cls.df['opt_position'].iloc[-i-1-cls.opt_window_size] == -1:
                        if cls.df['close'].iloc[-i-1] - cls.df['close'].iloc[-i-1-cls.opt_window_size] >= cls.opt_kijun:
                            cls.df.loc[cls.df.index[-i-1-cls.opt_window_size], 'opt_position'] = 1
                        elif cls.df['close'].iloc[-i-1] - cls.df['close'].iloc[-i-1-cls.opt_window_size] <= -cls.opt_kijun:
                            cls.df.loc[cls.df.index[-i - 1 - cls.opt_window_size], 'opt_position'] = 2
                        else:
                            cls.df.loc[cls.df.index[-i - 1 - cls.opt_window_size], 'opt_position'] = cls.df['opt_position'].iloc[-i - 1 - cls.opt_window_size-1]
                            #cls.df.iloc[-i - 1 - cls.opt_window_size]['opt_position'] = cls.df['opt_position'].iloc[-i - 1 - cls.opt_window_size - 1]
                cls.log_data.log_close[cls.df['dt'].iloc[-1]] = cls.df['close'].iloc[-1]
                print('added df. current len df=', len(cls.df.iloc[-1]))

    @classmethod
    def set_prediction(cls, pred):
        with cls.pred_lock:
            cls.prediction = pred

    @classmethod
    def get_prediction(cls):
        with cls.pred_lock:
            return cls.prediction


    @classmethod
    def download_ohlc(cls):
        dt = datetime.datetime.now()
        target_from = int(dt.timestamp() - cls.time_steps * 60 * 2 - cls.opt_window_size - 120) #cov, skew, kurtなどのデータは、1データを計算するのにtime_steps分のデータが必要になる。
        df = RestAPI.get_ohlc(1, target_from)
        print('downloaded ohlc: ', len(df), ' minutes data.')
        return df

    @classmethod
    def calc_opt_position(cls):
        opt_posi = []
        closed = np.array(cls.df['close'])
        if closed[cls.opt_window_size] - closed[0] > 0: #最初のopt posiを計算
            opt_posi.append(1)
        else:
            opt_posi.append(2)
        for i in range(len(closed) - cls.opt_window_size -1): #残り全てのopt posiを計算
            if closed[i+1+cls.opt_window_size] - closed[i+1] >= cls.opt_kijun:
                opt_posi.append(1)
            elif closed[i+1+cls.opt_window_size] - closed[i+1] <= -cls.opt_kijun:
                opt_posi.append(2)
            else:
                opt_posi.append(opt_posi[-1])
        for i in range(cls.opt_window_size):
            opt_posi.append(-1) #shift分だけ−１を追加。model input dataを作成する際にはcutされる。
        return opt_posi


    @classmethod
    def con_df_to_ohlc(cls, df):
        omd = OneMinData()
        omd.unix_time = list(df['timestamp'])
        omd.dt = list(map(lambda x: datetime.strptime(str(x), '%Y-%m-%d %H:%M:%S'), list(df['timestamp'])))
        omd.open = list(df['open'])
        omd.high = list(df['high'])
        omd.low = list(df['low'])
        omd.close = list(df['close'])
        omd.size = list(df['size'])
        return omd


    @classmethod
    def generate_data_for_model(cls, df_master):
        cls.__set_time_sleep(7)
        start = time.time()
        scaler = MinMaxScaler()
        df = df_master.copy()
        sk = [0] * cls.time_steps
        ku = [0] * cls.time_steps
        close = np.array(df['close'])
        for i in range(len(df) - cls.time_steps):
            sk.append(scipy.stats.skew(np.diff(close[i:i + cls.time_steps])))
            ku.append(scipy.stats.kurtosis(np.diff(close[i:i + cls.time_steps])))
        df['skew'] = sk
        df['kurt'] = ku
        # cov, ave_div
        cov = [0] * cls.time_steps
        ave_div = [0] * cls.time_steps
        for i in range(len(df) - cls.time_steps):
            #cov.append(np.cov(scaler.fit_transform(np.array(df['close'].iloc[i:i + cls.time_steps]).reshape(-1, 1)).reshape(-1)))
            #ave_div.append(np.array(df['close'])[i + cls.time_steps - 1] / np.average(df['close'].iloc[i:i + cls.time_steps]))
            cov.append(np.cov(scaler.fit_transform(close[i:i + cls.time_steps].reshape(-1, 1)).reshape(-1)))
            ave_div.append(close[i + cls.time_steps - 1] / np.average(close[i:i + cls.time_steps]))
        df['cov'] = cov
        df['ave_div'] = ave_div
        df['pre_opt'] = df['opt_position'].shift(6) - 1

        con_df_train_x = []
        con_df_train_y = []
        abs_df_train_x = []  # max price / 10000, min price /10000, median price / 10000 for dence input as functional api
        dftrain_x = df.drop(['timestamp', 'dt', 'opt_position', 'open', 'high', 'low'], axis='columns')
        dftrain_y = df['opt_position']
        dftrain_y = dftrain_y.replace(-1, 1)
        dftrain_y = OneHotEncoder(categories="auto", sparse=False).fit_transform(np.array(dftrain_y).reshape(-1, 1))

        i = len(dftrain_x)
        li = list(scaler.fit_transform(dftrain_x.iloc[i - cls.time_steps: i]))  # timeskipしても最新のデータが含まれるようにreverseする
        li.reverse()
        li = li[::cls.timestep_skip]
        li.reverse()
        con_df_train_x.append(np.array(li))
        con_df_train_y.append(dftrain_y[i-1])
        di = dftrain_x.iloc[i - cls.time_steps: i]['close']
        abs_df_train_x.append(np.array([max(di) / 10000, min(di) / 10000, np.median(np.array(di)) / 10000, (max(di) - di.iloc[-1]) / 1000, (di.iloc[-1] - min(di)) / 1000]))
        x_train = np.array(con_df_train_x)
        y_train = np.array(con_df_train_y)
        abs_train = np.array(abs_df_train_x)
        print('Generated model data, time:', time.time() - start)
        cls.__set_time_sleep(1)
        return x_train, y_train, abs_train


    @classmethod
    def __calc_prediction(cls):
        x_train, y_train, abs_train = cls.get_model_data()
        prediction = []
        preds = cls.model.predict([x_train, abs_train])
        #np.save('./'+str(time.time())+'-x_train', x_train[-1])
        #np.save('./'+str(time.time())+'-abs_train', abs_train[-1])
        #np.save('./' + str(time.time()) + '-pred', np.array(preds)[-1])
        for i, p in enumerate(preds):
            #print(p)
            res = np.argmax(p)
            if res == 0:
                prediction.append('Buy')
            elif res == 1:
                prediction.append('Sell')
            else:
                print('prediction error', res)
        print('prediction=', prediction[-1])
        cls.log_data.log_prediction[cls.get_df()['dt'].iloc[-1]] = prediction[-1]
        cls.log_data.calc_correct_pred_ratio()
        cls.set_prediction(prediction[-1])

    @classmethod
    def __check_df_datetime(cls):
        first_ts = cls.get_df().iloc[0]['timestamp']
        check_df = cls.get_df()
        pass

    '''
    毎分dfの最新のdt以降のohlcを取得して、model_dataを計算。
    '''
    @classmethod
    def __ohlc_thread(cls):
        print('started MarketData.ohlc_thread')
        t = datetime.datetime.now().timestamp()
        kijun_timestamp = int(t - (t - (t // 60.0) * 60.0)) + 60  # timestampの秒を次の分の0に修正
        while SystemFlg.get_system_flg():
            if kijun_timestamp + 1 <= datetime.datetime.now().timestamp():
                downloaded_df = RestAPI.get_ohlc(1, cls.df['timestamp'].iloc[-1] - 60)
                cls.add_df(downloaded_df)
                print(cls.get_df().iloc[-10:])
                cls.set_model_data(cls.generate_data_for_model(cls.get_df()))
                cls.__calc_prediction()
                kijun_timestamp += 60
            else:
                time.sleep(1)
        print('stopped MarketData.ohlc_thread!')




if __name__ == '__main__':
    SystemFlg.initialize()
    MarketData.initialize_for_bot(5, 1, 1500, 10)
    while True:
        time.sleep(0.1)

    '''
    MarketData.initialize_for_sim(5, 1, 1500, 10)
    x_train, y_train, abs_train = MarketData.get_model_data()
    preds = MarketData.model.predict([x_train, abs_train])
    for p in preds:
        res = np.argmax(p)
        if res == 0:
            print(1)
        elif res == 1:
            print(2)
    '''






