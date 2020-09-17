import threading


class SystemFlg:
    @classmethod
    def initialize(cls):
        cls.system_flg = True
        cls.lock = threading.Lock()

    @classmethod
    def set_system_flg(cls, flg):
        with cls.lock:
            cls.system_flg = flg

    @classmethod
    def get_system_flg(cls):
        return cls.system_flg