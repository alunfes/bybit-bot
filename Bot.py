from DRF import DRF
from Account import Account
from MarketData import MarketData, OneMinData

from Trade import Trade
from PrivateWS import PrivateWS
from Account import Account
from SystemFlg import SystemFlg
import threading
import pytz
import pandas as pd
import time
import os
from datetime import datetime

class Bot:
    def __init__(self):
        th = threading.Thread(target=self.__bot_thread)
        th.start()


    def __bot_thread(self):
        while SystemFlg.get_system_flg():
            pass
            #get ohlc data
            #calc model
            #trade
            #calc ac
            #



    def test_bot(self):
        #initalize
        SystemFlg.initialize()
        MarketData.initialize_for_bot(5, 1, 1500, 10)
        Trade.initialize()
        #start trade data thread

        #start account thread
        #start bot loop
        while SystemFlg.get_system_flg():
            #get pred check if opt_position matched with current position
            MarketData.get_prediction()
            #trade to have same position as pred
            time.sleepp(1)


if __name__ == '__main__':
    bot = Bot()
    bot.test_bot()
    while True:
        time.sleep(1)