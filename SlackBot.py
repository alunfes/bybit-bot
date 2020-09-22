from slackbot.bot import Bot
from functools import partial
import asyncio
import requests
import json



class SlackBot:
    @classmethod
    def initialize(cls):
        print('SlackBot Started')
        json_dict = json.load(open('./ignore/slack.json', 'r'))
        cls.bot = Bot()
        cls.bot.run()
        cls.webhook = json_dict['webhook_url']
        cls.send_message_webhook('SlackBot Started')


    @classmethod
    def __send_message_webhook(cls, message):
        requests.post(cls.webhook, data=json.dumps({"text": message}))

    @classmethod
    def send_message_webhook(cls, message):
        loop = asyncio.get_event_loop()
        loop.run_in_executor(None, partial(cls.__send_message_webhook, message))


if __name__ == '__main__':
    SlackBot.initialize()