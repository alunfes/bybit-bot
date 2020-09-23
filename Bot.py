from Account import Account
from MarketData import MarketData, OneMinData
from Strategy import Strategy
from Trade import Trade
from PrivateWS import PrivateWS
from Account import Account
from SystemFlg import SystemFlg
from LineNotification import LineNotification
from LogMaster import LogMaster
import threading
import pytz
import pandas as pd
import time
import os
from datetime import datetime

class Bot:
    def __init__(self):
        pass
        #th = threading.Thread(target=self.__bot_thread)
        #th.start()


    def __bot_thread(self):
        while SystemFlg.get_system_flg():
            pass
            #get ohlc data
            #calc model
            #trade
            #calc ac

    '''
    Assume maximum num order is 1
    limit orderでentry / update priceしたはずが、market orderとして約定してしまった場合の処理が必要 ->まずはwsでどのようなデータになるのかを確認する。Filledになったorderはfetch_orderで取得して
    plとか定期的に表示させる
    updateが毎分ではなく即時にやってしまう（そっちの方がパフォーマンス良いかは不明だが）
    privatews数分に一回切れるのでaccountで定期的にorder / holdingの状況をチェックする必要がある。 -> ws単独だと切れないので原因はorder data処理に時間かかりすぎていることかも。（accountでの処理が終わる前に新しいorder dataがくるから？）
    とりあえずは、ws dataを使わずにrest apiでorder / position data取得する方がいい？
    marketdataの計算がbot / account threadの計算に邪魔されて通常の3倍くらいの12秒くらいかかる -> MarketData calcが始まる時はbot /accountのtime.sleepを長めにする?
    '''
    def test_bot(self, order_size):
        #th = threading.Thread(target=self.bot_loop(order_size))
        #th.start()
        #initalize
        print('Bot Started')
        SystemFlg.initialize()
        LogMaster.initialize()
        LineNotification.initialize()
        #pws = PrivateWS()
        Trade.initialize()
        MarketData.initialize_for_bot(5, 1, 1500, 10)
        Account.initialize()
        print('Bot: Waiting for initial prediction...')
        while MarketData.get_prediction() != 'Buy' and MarketData.get_prediction() != 'Sell':
            time.sleep(1)
        while SystemFlg.get_system_flg():
            pred = MarketData.get_prediction()
            actions = Strategy.model_prediction_opt_posi_limit(pred, order_size)
            for i, act in enumerate(actions.action):
                if act == 'entry':
                    res = Trade.order(actions.order_side[i], actions.order_price[i], actions.order_type[i], actions.order_size[i])
                    if res != None:
                        Account.entry_order(res['info']['order_id'], res['info']['side'], res['info']['price'], res['info']['qty'], res['info']['order_type'])
                        print('Bot: Entry order - ', 'side:'+res['info']['side'], 'price:'+str(res['info']['price']), 'qty:'+str(res['info']['qty']), 'type:'+res['info']['order_type'])
                elif act == 'cancel':
                    res = Trade.cancel_order(actions.order_id[i])
                    if res != None:
                        print('Bot: Cancelled order - ', Account.get_order_data())
                        Account.cancel_order(actions.order_id[i])
                elif act == 'update':
                    res = Trade.update_order_price(actions.order_id[i], actions.order_price[i])
                    if 'info' in res:
                        if res['info']['ret_msg'] == 'ok':
                            print('Bot: Updated order price - ', str(Account.get_order_data()['price']), ' -> ', str(actions.order_price[i]))
                            Account.update_order_price(actions.order_id[i], actions.order_price[i])
            time.sleep(1)



if __name__ == '__main__':
    bot = Bot()
    bot.test_bot(1000)
    while True:
        time.sleep(1)