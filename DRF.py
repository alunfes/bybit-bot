from Account import Account
from TradingEnv import TradingEnv
from stable_baselines import PPO2
from stable_baselines.common.policies import MlpPolicy, MlpLnLstmPolicy, CnnLnLstmPolicy
from stable_baselines.common.vec_env import DummyVecEnv, SubprocVecEnv
import matplotlib.pyplot as plt
import numpy as np


class DRF:
    def train_drf(self, df, ohlc_df, train_len):
        train_df = df.iloc[:train_len].copy()
        test_df = df.iloc[train_len:].copy()
        train_ohlc = ohlc_df.iloc[:train_len].copy()
        test_ohlc = ohlc_df.iloc[train_len:].copy()

        env = DummyVecEnv([lambda: TradingEnv(train_df.drop('close', axis=1), train_ohlc, -1)])
        # env = SubprocVecEnv([make_env(train_provider, i) for i in range(4)])
        # model = PPO2(MlpLnLstmPolicy, env,  verbose=1, nminibatches=1, tensorboard_log=log_dir) # MlpLnLstmPolicy, CnnLnLstmPolicy
        model = PPO2(MlpLnLstmPolicy, env, verbose=1, nminibatches=1, tensorboard_log='./Model')  # MlpLnLstmPolicy, CnnLnLstmPolicy
        # %tensorboard --logdir log_dir
        # tb=TensorBoardColab(startup_waiting_time=1)
        # tb=SummaryWriter('./Graph')

        model.learn(total_timesteps=10000)
        env.close()
        model.save('./Model/rf_ppo2')
        return model

    def test_df(self, model, df, ohlc_df, train_len):
        train_df = df.iloc[:train_len].copy()
        test_df = df.iloc[train_len:].copy()
        train_ohlc = ohlc_df.iloc[:train_len].copy()
        test_ohlc = ohlc_df.iloc[train_len:].copy()

        # check test for train data
        test_env = DummyVecEnv([lambda: TradingEnv(train_df.drop('close', axis=1), train_ohlc, 1440)])
        obs = test_env.reset()
        done = False
        ac_data = None
        while done == False:
            action, _states = model.predict(obs)
            obs, rewards, done, ac_data = test_env.step(action)
            # test_env.render()
        test_env.close()

        print('pl=', ac_data[0]['ac'].total_pl, 'num trade=', ac_data[0]['ac'].num_trade, 'win_rate=', ac_data[0]['ac'].win_rate, 'fee ratio=', round(ac_data[0]['ac'].total_fee / ac_data[0]['ac'].total_pl, 4) if ac_data[0]['ac'].num_trade > 0 else 0)
        print('num market order=', ac_data[0]['ac'].num_market_order)
        fig, ax1 = plt.subplots()
        plt.figure(figsize=(30, 30), dpi=200)
        ax1.plot(np.array(ac_data[0]['ac'].performance_total_pl_log).reshape(-1, 1), color='red', linewidth=3.0, label='pl')
        ax1.legend(loc="best", edgecolor="red")
        ax2 = ax1.twinx()
        ax2.plot(np.array(train_ohlc['close'].iloc[1440: len(ac_data[0]['ac'].performance_total_pl_log) + 1440]).reshape(-1, 1), label='close')
        h1, l1 = ax1.get_legend_handles_labels()
        h2, l2 = ax2.get_legend_handles_labels()
        ax2.legend(h1 + h2, l1 + l2, loc="best", frameon=True, edgecolor="blue")
        plt.show()
        return ac_data



if __name__ == '__main__':
    print('start df')