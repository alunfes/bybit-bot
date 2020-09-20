import threading
import time
from Account import Account
from MarketData import MarketData, OneMinData
from Strategy import Strategy
from Trade import Trade
from PrivateWS import PrivateWS
from Account import Account
from SystemFlg import SystemFlg
from Bot import Bot

class Test:
    def main_thread(self):
        ACTest.main_thread()
        th = threading.Thread(target=self.main_loop())
        th.start()

    def main_loop(self):
        while True:
            start = time.time()
            time.sleep(1)
            print("Test", time.time() - start)


class ACTest:
    @classmethod
    def main_thread(cls):
        th = threading.Thread(target=cls.main_loop)
        th.start()

    @classmethod
    def main_loop(cls):
        while True:
            start = time.time()
            time.sleep(3)
            print('ACTest', time.time() -start)


class Master:
    def master_thread(self):
        # initalize
        print('Bot Started')
        SystemFlg.initialize()
        # pws = PrivateWS()
        Trade.initialize()
        MarketData.initialize_for_bot(5, 1, 1500, 10)
        Account.initialize()
        print('Bot: Waiting for initial prediction...')
        bot = Bot()
        bot.test_bot(10000)
        while SystemFlg.get_system_flg():
            time.sleep(10)





if __name__ == '__main__':
    master = Master()
    master.master_thread()
    while True:
        time.sleep(1)
