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
from LineNotification import LineNotification
import matplotlib.pyplot as plt


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


class Image:
    def display(self):
        LineNotification.initialize()
        l = [1, 2, 3, 4, 5, 4,6,7,8,9,3,4,5,6,3,4]
        plt.plot(l)
        plt.savefig('./ignore/figure.jpeg')
        LineNotification.send_image(open('./ignore/figure.jpeg','rb'))








if __name__ == '__main__':

    img = Image()
    img.display()
    for i in range(10):
        time.sleep(1)

