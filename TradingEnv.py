import gym
from gym import spaces
import random
from sklearn.preprocessing import MinMaxScaler
import numpy as np
from Account import Account

class TradingEnv(gym.Env):
    """A stock trading environment for OpenAI gym"""
    metadata = {'render.modes': ['human']}



    '''
    index of train_df and ohlc_df should be matched
    '''
    def __init__(self, train_df, ohlc_df, test_start_ind):
        super(TradingEnv, self).__init__()
        self.train_df = train_df
        self.ohlc_df = ohlc_df
        self.test_start_ind = test_start_ind

        self.MAX_ACCOUNT_BALANCE = 1
        self.price_data_scaling_length = 1440
        self.observation_length = 1000
        self.skip = 100

        self.reward_range = (-self.MAX_ACCOUNT_BALANCE, self.MAX_ACCOUNT_BALANCE)
        self.pre_reward = 0
        self.pre_num_trade = 0
        self.num_market_order = 0
        # Actions of the format market Buy, market Sell, Hold.
        self.action_space = spaces.Discrete(6)
    # dataframe,
        #self.observation_space = spaces.Box(low=0, high=1, shape=(len(train_df.columns)+1, observation_length, 1), dtype=np.float64)
        #self.observation_space = spaces.Box(low=0, high=1, shape=(7 + observation_length * 5 , ), dtype=np.float64)
        #self.observation_space = spaces.Box(low=0, high=1, shape=((observation_length  / skip) * 2 + 7,), dtype=np.float64)
        self.observation_space = spaces.Box(low=0, high=1, shape=(70 + 3,), dtype=np.float64)

    def _on_training_end(self) -> None:
        """
        This event is triggered before exiting the `learn()` method.
        """
        pass

    def _on_rollout_end(self) -> None:
        """
        This event is triggered before updating the policy.
        """
        pass

    def _next_observation(self):
        # Get the last observation period of index data and scale to between 0-1
        ob_data = []
        ac_data = [
                1 if self.ac.current_pl > 0 else 0,
                #1 if float(self.i - self.ac.order_i[self.ac.get_latest_order_num()]) / 300 > 1 else round(float(self.i - self.ac.order_i[self.ac.get_latest_order_num()]) / 300, 4),
                1 if self.ac.holding_side == 'buy' else 0,
                1 if self.ac.holding_side == 'sell' else 0
               ]
        #if observation_length > len(ac_data):
        #    ac_data.extend([0] * (observation_length - len(ac_data)))

        scaler = MinMaxScaler()
        d = np.array([
        scaler.fit_transform(self.ohlc_df['close'].iloc[self.i - self.price_data_scaling_length + 1: self.i+1].values.reshape(-1,1))[-self.observation_length:][::self.skip],
        scaler.fit_transform(self.ohlc_df['size'].iloc[self.i - self.price_data_scaling_length + 1: self.i+1].values.reshape(-1,1))[-self.observation_length:][::self.skip],
        scaler.fit_transform(self.train_df['ema_kairi:670'].iloc[self.i - self.price_data_scaling_length + 1: self.i+1].values.reshape(-1,1))[-self.observation_length:][::self.skip],
        scaler.fit_transform(self.train_df['cci:780'].iloc[self.i - self.price_data_scaling_length + 1: self.i+1].values.reshape(-1,1))[-self.observation_length:][::self.skip],
        scaler.fit_transform(self.train_df['dx:780'].iloc[self.i - self.price_data_scaling_length + 1: self.i+1].values.reshape(-1,1))[-self.observation_length:][::self.skip],
        scaler.fit_transform(self.train_df['rsi:780'].iloc[self.i - self.price_data_scaling_length + 1: self.i+1].values.reshape(-1,1))[-self.observation_length:][::self.skip],
        scaler.fit_transform(self.train_df['aroon_os:780'].iloc[self.i - self.price_data_scaling_length + 1: self.i+1].values.reshape(-1,1))[-self.observation_length:][::self.skip]
        ])
        d = np.append(np.array(ac_data).reshape(-1,1).reshape(-1), d)
        return d


    def _next_observation3(self):
        # Get the last observation period of index data and scale to between 0-1
        ob_data = []
        ac_data = [
                (self.ac.current_pl / self.ac.holding_size) / self.ac.holding_price if self.ac.holding_price > 0 else 0,
                float(self.i - self.ac.order_i[self.ac.get_latest_order_num()]) / float(len(self.train_df)) if len(self.ac.order_side) > 0 else 0,
                1 if self.ac.holding_side == 'buy' else 0,
                1 if self.ac.holding_side == 'sell' else 0,
                0 if len(self.ac.order_side) ==0 else 1,
                0 if len(self.ac.order_side) ==1 else 1,
                0 if len(self.ac.order_side) > 1 else 1
               ]
        scaler = MinMaxScaler()
        d = np.array([scaler.fit_transform(self.ohlc_df['open'].iloc[self.i - self.price_data_scaling_length + 1: self.i+1].values.reshape(-1,1))[-self.observation_length:],
        scaler.fit_transform(self.ohlc_df['high'].iloc[self.i - self.price_data_scaling_length + 1: self.i+1].values.reshape(-1,1))[-self.observation_length:],
        scaler.fit_transform(self.ohlc_df['low'].iloc[self.i - self.price_data_scaling_length + 1: self.i+1].values.reshape(-1,1))[-self.observation_length:],
        scaler.fit_transform(self.ohlc_df['close'].iloc[self.i - self.price_data_scaling_length + 1: self.i+1].values.reshape(-1,1))[-self.observation_length:],
        scaler.fit_transform(self.ohlc_df['size'].iloc[self.i - self.price_data_scaling_length + 1: self.i+1].values.reshape(-1,1)[-self.observation_length:])
        ])
        d = np.append(d.reshape(-1), np.array(ac_data).reshape(-1,1).reshape(-1))
        return d


    def _next_observation2(self):
        # Get the last observation period of index data and scale to between 0-1
        ob_data = []
        ac_data = [
                (self.ac.current_pl / self.ac.holding_size) / self.ac.holding_price if self.ac.holding_price > 0 else 0,
                float(self.i - self.ac.order_i[self.ac.get_latest_order_num()]) / float(len(self.train_df)) if len(self.ac.order_side) > 0 else 0,
                1 if self.ac.holding_side == 'buy' else 0,
                1 if self.ac.holding_side == 'sell' else 0,
                0 if len(self.ac.order_side) ==0 else 1,
                0 if len(self.ac.order_side) ==1 else 1,
                0 if len(self.ac.order_side) > 1 else 1
               ]

        cols = list(self.train_df.columns)
        scaler = MinMaxScaler()
        for col in cols:
            d = scaler.fit_transform(self.train_df[col].iloc[self.i - self.observation_length +1: self.i+1].values.reshape(-1,1))
            ob_data.append(list(d.reshape(1,-1).reshape(-1))[-1])
        ob_data.extend(ac_data)
        #return np.array(ob_data).reshape(len(ob_data),1)
        print(ac_data)
        return ac_data

    def _take_action(self, action):
        self.ac.check_executions(self.i, self.ohlc_df['dt'].iloc[self.i], self.ohlc_df['open'].iloc[self.i], self.ohlc_df['high'].iloc[self.i], self.ohlc_df['low'].iloc[self.i])
        if action == 0: #market buy
            self.ac.entry_order('buy', 0, self.order_size, 'market', self.i, self.ohlc_df['dt'].iloc[self.i])
            self.num_market_order += 1
        elif action == 1: #market sell
            self.ac.entry_order('sell', 0, self.order_size, 'market', self.i, self.ohlc_df['dt'].iloc[self.i])
            self.num_market_order += 1
        elif action == 2: #limit buy
            self.ac.entry_order('buy', self.ohlc_df['close'].iloc[self.i], self.order_size, 'limit', self.i, self.ohlc_df['dt'].iloc[self.i])
        elif action == 3: #limit sell
            self.ac.entry_order('sell', self.ohlc_df['close'].iloc[self.i], self.order_size, 'limit', self.i, self.ohlc_df['dt'].iloc[self.i])
        elif action == 4: #cancel order
            self.ac.cancel_all_order(self.i, self.ohlc_df['dt'].iloc[self.i])
        elif action == 6: #hold / do nothing
            pass
        self.ac.move_to_next(self.i, self.ohlc_df['dt'].iloc[self.i], self.ohlc_df['open'].iloc[self.i], self.ohlc_df['high'].iloc[self.i], self.ohlc_df['low'].iloc[self.i], self.ohlc_df['close'].iloc[self.i])
        #print('total_pl=',self.ac.total_pl, 'num trade=', self.ac.num_trade)


    def step(self, action):
        # Execute one time step within the environment
        self._take_action(action)
        self.current_step += 1
        self.i += 1
        done = False
        if self.ac.total_pl < -100 and self.test_start_ind < 0.:
            done  =True
        elif self.test_start_ind >= 0 and self.i >= len(self.ohlc_df)-1:
            done  =True
        if self.i >= len(self.ohlc_df) - 1:
            self.i = self.price_data_scaling_length +1
        reward = 0
        reward = self.ac.total_pl - self.pre_reward
        #reward = 1 if self.ac.total_pl - self.pre_reward > 0 else -1
        #if self.ac.total_pl - self.pre_reward == 0:
        #    reward = 0
        '''
        if self.ac.num_trade > self.pre_num_trade:
            self.pre_num_trade = self.ac.num_trade
            reward = self.ac.total_pl - self.pre_reward
            self.pre_reward = self.ac.total_pl
        else:
            reward  =0
        '''
        self.pre_reward = self.ac.total_pl
        obs = self._next_observation()
        #obs = self._next_observation2()
        return obs, reward, done, {'ac':self.ac}

    def reset(self):
        # Reset the state of the environment to an initial state
        self.ac = Account()
        self.order_size = 0.1
        # Set the i to a random point within the data frame
        self.i = self.test_start_ind
        if self.test_start_ind < 0:
            self.i = random.randint(self.price_data_scaling_length+1, len(self.ohlc_df) - 1)
        self.current_step = 0
        return self._next_observation()
        #return self._next_observation2()

    def render(self, mode='human', close=False):
        # Render the environment to the screen
        print('No.', self.current_step, 'i',self.i , 'total_pl:', self.ac.total_pl, 'num_trade:', self.ac.num_trade)