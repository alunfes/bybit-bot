import threading
import pandas as pd

class LogMaster:
    @classmethod
    def initialize(cls):
        cls.lock_data = threading.Lock()
        cls.dt_log = []
        cls.close_log = []
        cls.error_log = []
        cls.total_pl_log = []
        cls.total_fee_log = []
        cls.num_trade_log = []
        cls.win_rate_log = []

    @classmethod
    def add_account_log(cls, dt, close, total_pl, total_fee, num_trade, win_rate):
        with cls.lock_data:
            cls.dt_log.append(dt)
            cls.close_log.append(close)
            cls.total_pl_log.append(total_pl)
            cls.total_fee_log.append(total_fee)
            cls.num_trade_log.append(num_trade)
            cls.win_rate_log.append(win_rate)


    @classmethod
    def get_account_log(cls):
        with cls.lock_data:
            df = pd.DataFrame({'dt':cls.dt_log, 'close':cls.close_log, 'total_pl':cls.total_pl_log, 'total_fee':cls.total_fee_log, 'num_trade':cls.num_trade_log, 'win_rate':cls.win_rate_log})
            return df

