import requests
import pandas as pd
import shutil
import os
import gzip
import glob
import asyncio
import time
import datetime
from bs4 import BeautifulSoup


class DownloadMarketData:
      def __init__(self):
            self.file_urls = []
            self.num_files = 0
            self.downloaded_file = []
            self.target_file = []


      def __check_downloaded_file(self):
            self.downloaded_file = []
            files = glob.glob('./Data/*')
            for file in files:
                  #./Data/BTCUSD2020-05-11.csv.gz
                  if 'BTCUSD' in file:
                        self.downloaded_file.append(file.split('/')[2])
                        #print(file)
            print('checked ', len(files), ' files are in the Data directory.')

      def __check_download_target_file(self):
            self.target_file = list(set(self.file_urls) - set(self.downloaded_file))
            print('target files')
            [print(f) for f in self.target_file]


      def get_file_list(self):
            target_url = 'https://public.bybit.com/trading/BTCUSD/'
            r = requests.get(target_url)         #requestsを使って、webから取得
            soup = BeautifulSoup(r.text, 'lxml') #要素を抽出
            for a in soup.find_all('a'):
                  #print(a.get('href'))
                  self.file_urls.append(a.get('href'))
                  self.num_files += 1
            return self.file_urls

      def download_file(self, file_url):
            file_name = os.path.basename(file_url)
            res = requests.get(file_url, stream=True)
            if res.status_code == 200:
                  print('url=', file_url)
                  print('file name=', file_name)
                  with open(os.path.basename(file_url), 'wb') as file:
                        res.raw.decode_content = True
                        shutil.copyfileobj(res.raw, file)
                        shutil.move(file.name, './Data')
                        print('downloaded ' + file_name)

      def download_all_targets(self):
            for f in self.target_file:
                  self.download_file('https://public.bybit.com/trading/BTCUSD/' + str(f))
                  time.sleep(1)

      def download_all_targets_async(self):
            self.get_file_list()
            self.__check_downloaded_file()
            self.__check_download_target_file()
            loop = asyncio.get_event_loop()
            data = loop.run_until_complete(self.handler(loop))
            print('completed download files !')

      def convert_all_tick_to_ohlcv(self):
            print('Converting tick files to ohlcv data...')
            self.__check_downloaded_file()
            ts, dt, size, price = [], [], [], []
            ohlcv_df = pd.DataFrame()
            for d in self.downloaded_file:
                  df = pd.read_csv('./Data/'+d)
                  ts.extend(df['timestamp'])
                  for timestamp_data in df['timestamp']:
                        dt.append(datetime.datetime.fromtimestamp(timestamp_data))
                  size.extend(df['size'])
                  price.extend(df['price'])
            ohlcv_df = pd.DataFrame({'price':price, 'size':size}, index=dt)
            con_df = ohlcv_df['price'].resample('1T').ohlc()
            con_df = con_df.assign(size=ohlcv_df['size'].resample('1T').sum())
            con_df = con_df.reset_index().rename(columns={'index':'datetime'})
            con_df = self.__check_ohlc_data(con_df)
            con_df.to_csv('./Data/onemin_bybit.csv', index=False)
            print('Generated ohlcv data, ./Data/onemin_bybit.csv')
            print(con_df)


      def __check_ohlc_data(self, df):
            num_correction = 0
            for i in range(len(df)):
                  if df['size'].iloc[i] == 0:
                        df['open'].iloc[i], df['high'].iloc[i], df['low'].iloc[i], df['close'].iloc[i], df['size'].iloc[i]  = df['open'].iloc[i-1], df['high'].iloc[i-1], df['low'].iloc[i-1], df['close'].iloc[i-1], 0
                        num_correction += 1
            print('corrected ', num_correction, ' data.')
            return df


      async def handler(self, loop):
            async def async_download_file(f):
                  async with asyncio.Semaphore(1000):
                        return await loop.run_in_executor(None, self.download_file, 'https://public.bybit.com/trading/BTCUSD/' + str(f))
            tasks = [async_download_file(f) for f in self.target_file]
            return await asyncio.gather(*tasks)


if __name__ == '__main__':
      dmd = DownloadMarketData()
      dmd.download_all_targets_async()
      dmd.convert_all_tick_to_ohlcv()

      '''
    dmd = DownloadMarketData()
    #dmd.download_all_targets()
    loop = asyncio.get_event_loop()
    data = loop.run_until_complete(dmd.handler(loop))
    print('completed download files !')
      '''