import threading
import time

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


if __name__ == '__main__':
    test = Test()
    test.main_thread()
    while True:
        time.sleep(100)