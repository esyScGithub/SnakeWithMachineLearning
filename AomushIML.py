import chainer
import chainer.functions as F
import chainer.links as L
import chainerrl
import numpy as np
from matplotlib import pyplot
import AomushI as ai

# 環境名を指定して、環境インスタンスを作成
aomushiEnv = ai.SnakeGameApp()
# aomushiEnv.run()

# 環境を初期化（戻り値で、初期状態の観測データobservationが取得できる）
obs = aomushiEnv.reset()

class QFunction(chainer.Chain):

    def __init__(self, obs_size, n_actions, n_hidden_channels=50):
        super().__init__()
        with self.init_scope():
            # 各層の数を定義している。以下の場合は4レイヤー構造。
            self.l0 = L.Linear(obs_size, n_hidden_channels)
            self.l1 = L.Linear(n_hidden_channels, n_hidden_channels)
            self.l2 = L.Linear(n_hidden_channels, n_actions)

    def __call__(self, x, test=False):
        """
        Args:
            x (ndarray or chainer.Variable): An observation
            test (bool): a flag indicating whether it is in test mode
        """
        h = F.relu(self.l0(x))
        h = F.relu(self.l1(h))
        return chainerrl.action_value.DiscreteActionValue(self.l2(h))

# 環境サイズとアクションのサイズを取得して、InputとOutputのノード数を決める。
obs_size = obs.reshape(1,-1).shape[1]
n_actions = 4

print("CP1")

# Q関数の定義
q_func = QFunction(obs_size, n_actions)

# Uncomment to use CUDA
#q_func.to_gpu(0)

print("CP2")

_q_func = chainerrl.q_functions.FCStateQFunctionWithDiscreteAction(
    obs_size, n_actions,
    n_hidden_layers=2, n_hidden_channels=50)

# Use Adam to optimize q_func. eps=1e-2 is for stability.
optimizer = chainer.optimizers.Adam(eps=1e-4)
optimizer.setup(q_func)

# Set the discount factor that discounts future rewards.
gamma = 0.95

# Use epsilon-greedy for exploration
explorer = chainerrl.explorers.ConstantEpsilonGreedy(
    epsilon=0.3, random_action_func=aomushiEnv.actionSample)

# DQN uses Experience Replay.
# Specify a replay buffer and its capacity.
replay_buffer = chainerrl.replay_buffer.ReplayBuffer(capacity=10 ** 6)

# Since observations from CartPole-v0 is numpy.float64 while
# Chainer only accepts numpy.float32 by default, specify
# a converter as a feature extractor function phi.
phi = lambda x: x.astype(np.float32, copy=False)

# Now create an agent that will interact with the envEnvironment.
agent = chainerrl.agents.DoubleDQN(
    q_func, optimizer, replay_buffer, gamma, explorer,
    replay_start_size=500, update_interval=1,
    target_update_interval=100, phi=phi)

print("CP3")

n_episodes = 2000
max_episode_len = 20000

rewards = []

for i in range(1, n_episodes + 1):
    obs = aomushiEnv.reset()
    reward = 0
    done = False
    R = 0  # return (sum of rewards)
    t = 0  # time step
    while not done and t < max_episode_len:
        # Uncomment to watch the behaviour
        # aomushiEnv.render()
        action = agent.act_and_train(obs, reward)
        obs, reward, done = aomushiEnv.step(action)
        R += reward
        t += 1
        # aomushiEnv.render()  #追記；学習途中の様子も描画する
    if i % 10 == 0:
        print('episode:', i,
              'R:', R,
              'statistics:', agent.get_statistics())
    agent.stop_episode_and_train(obs, reward, done)
    rewards.append(R)
# aomushiEnv.render()

pyplot.plot(range(len(rewards)),rewards)
pyplot.show()

print('Finished.')