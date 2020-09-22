from functools import partial
import requests
import asyncio
import numpy as np
import matplotlib as plt
import json
import time


class LineNotification:
    @classmethod
    def initialize(cls):
        json_dict = json.load(open('./ignore/line.json', 'r'))
        cls.token = json_dict['api_token']
        cls.api_url = json_dict['api_url']
        cls.headers = {"Authorization": "Bearer " + cls.token}
        print('initialized LineNotification')

    @classmethod
    def send_message(cls, message):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(cls.send_message(message))


    @classmethod
    async def __send_message__wrapper(cls, message):
        loop = asyncio.get_event_loop()
        loop.run_in_executor(None, partial(cls.__send_message, message))

    @classmethod
    def __send_message(cls, message):
        payload = {"message": message}
        try:
            res = requests.post(cls.api_url, headers=cls.headers, data=payload, timeout=(6.0))
        except Exception as e:
            print('Line notify error!={}'.format(e))


if __name__ == '__main__':
    LineNotification.initialize()
    LineNotification.do_send_message('test')