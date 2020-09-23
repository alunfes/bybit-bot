from functools import partial
import requests
import asyncio
import numpy as np
import matplotlib.pyplot as plt
import json
import os


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
        loop = asyncio.new_event_loop()
        loop.run_until_complete(cls.__send_message(message))

    @classmethod
    async def __send_message(cls, message):
        payload = {"message": str(message)}
        try:
            res = requests.post(cls.api_url, headers=cls.headers, data=payload, timeout=(6.0))
        except Exception as e:
            print('Line notify error!={}'.format(e))

    @classmethod
    def send_image(cls, image):
        loop = asyncio.new_event_loop()
        loop.run_until_complete(cls.__send_image(image))

    @classmethod
    async def __send_image(cls, image):
        payload = {"imageFile": image}
        try:
            res = requests.post(cls.api_url, headers=cls.headers, params={"message" :  'PL Chart'}, files=payload, timeout=(6.0))
        except Exception as e:
            print('Line notify error!={}'.format(e))


if __name__ == '__main__':
    LineNotification.initialize()
    li = [1,2,3,4,3,4,5,6,5,4,3,4,5,6,7]
    plt.plot(li)
    plt.savefig('./ignore/test.jpeg')
    print('kita1')
    LineNotification.send_image(open('./ignore/test.jpeg', 'rb'))
    print('kita')