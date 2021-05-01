#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Implement DQN model for training on kingsoopers dataset.

References:
  * https://pytorch.org/tutorials/intermediate/reinforcement_q_learning.html
  * https://pytorch.org/tutorials/beginner/basics/buildmodel_tutorial.html
  * https://pytorch.org/tutorials/recipes/recipes/defining_a_neural_network.html
  * https://www.mlq.ai/deep-reinforcement-learning-q-learning/
  * https://github.com/PyTorchLightning/Lightning-Bolts/blob/master/pl_bolts/models/rl/dqn_model.py#L33-L405
"""
import random
import math
from typing import Callable, List, Tuple, Dict
from collections import namedtuple, deque, OrderedDict
import numpy as np

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader

import pytorch_lightning as pl
from pl_bolts.losses.rl import dqn_loss
from pl_bolts.datamodules.experience_source import (
    ExperienceSourceDataset
)

from glo.data.kingsoopers import ScrapyKingSoopersDataModule


Transition = namedtuple(
    "Transition", ("state", "action", "next_state", "reward")
)


class Environment:
    """
    Environment for ScrapyKingSoopersDataModule.

    See description in DQModel for more information

    Parameters
    ----------
    dm: ScrapyKingSoopersDataModule
        DataModule to use.
    gc_size: int
        Size of the grocery cart.
    """

    def __init__(self, dm: ScrapyKingSoopersDataModule, gc_size: int):
        self.dm = dm
        self.items = self.dm.ks_norm_numpy
        self.gc_size = gc_size
        self.state = None
        self.reset()

    def reset(self):
        self.state = np.zeros((2, self.gc_size), dtype=np.float64)

    @staticmethod
    def is_done(prev_reward, next_reward, tol, max_steps, steps):
        if (next_reward - prev_reward) <= tol or steps > max_steps:
            return True
        else:
            return False

    def step(self, action: int):
        """Get next state"""

        # map action index to state index
        # 0 and 1 -> 0
        # 2 and 3 -> 1
        # 4 and 5 -> 2
        action_index = math.floor(action / 2)

        # odd is cw, even is ccw
        if action % 2 == 0:
            direction = -1
        else:
            direction = 1

        max_items = len(self.items) + 1
        prev_index = self.state[0][action_index]
        new_index = (prev_index + direction) % (max_items + 1)

        self.state[0][action_index] = new_index
        if new_index == max_items:
            self.state[1][action_index] = np.zeros(self.items[0].shape)
        else:
            self.state[1][action_index] = self.items[new_index]


class ReplayMemory:
    """
    Class to help replay memory during training.

    Parameters
    ----------
    capacity: int
        Max memory capacity.

    Attributes
    ----------
    memory
        ``collections.deque`` instance representing internal memory.

    Notes
    -----
    Here is a snippet from pytorch's DQN tutorial:

       We’ll be using experience replay memory for training our DQN.
       It stores the transitions that the agent observes, allowing us
       to reuse this data later. By sampling from it randomly, the t
       ransitions that build up a batch are decorrelated. It has been
       shown that this greatly stabilizes and improves the DQN training
       procedure.

       *Source: https://pytorch.org/tutorials/intermediate/reinforcement_q_learning.html*
    """

    def __init__(self, capacity: int):
        self.memory = deque([], maxlen=capacity)

    def __len__(self):
        return len(self.memory)

    def push(self, *args):
        """
        Save a ``Transition`` into memory.

        args given are passed directly to a new ``Transition`` instance.

        See Also
        --------
        Transition
        """

        self.memory.append(Transition(*args))

    def sample(self, bach_size: int):
        """
        Return a random sample of size ``batch_size``

        Arguments
        ---------
        batch_size: int
            Number of random samples to return.
        """

        return random.sample(self.memory, bach_size)


class DQN(nn.Module):
    """
    Deep Q-Learning Network.

    For our use case this is implemented as a simple FFNN with ReLU
    activations between layers. No softmax is used because we
    are predicting Q-Values for each action rather than predicting
    which action should be taken.

    Parameters
    ---------
    n_features: int
        Number of input features to expect
    n_hidden: int
        Number of hidden layers to use
    n_conn: int
        Number of connections between hidden layers.
    n_actions: int
        Number of output actions to predict Q values for

    Attributes
    ----------
    linear_relu_stack:
        ``nn.Sequential`` of our fully-connected layers with ReLU
        between.
    """

    def __init__(
        self, n_features: int, n_hidden: int, n_conn: int, n_actions: int
    ):
        super().__init__()

        layers = [nn.Linear(n_features, n_conn), nn.ReLU()]
        for h in range(n_hidden - 1):
            layers.append(nn.Linear(n_conn, n_conn))
            layers.append(nn.ReLU())
        layers.append(nn.Linear(n_conn, n_actions))
        layers.append(nn.ReLU())

        self.linear_relu_stack = nn.Sequential(*layers)

    def forward(self, x):
        """Perform forward prop. given input feature vector x"""
        return self.linear_relu_stack(x)


class DQModel(pl.LightningModule):
    """
    Deep Q-Learning Model implementation.

    State space is a grocery cart of a fixed max size, which can
    contain different foods from the KingSoopers dataset. The way
    that the problem is set up is similar to someone trying
    to find the combination to a combo lock using brute force. See,
    each 'slot' in the grocery cart has in index value which points
    into the dataset. Each slot has two associated actions: turn
    clockwise (increment the index by one) or turn counter-clockwise
    (decrement then index by one). This allows the agent to explore
    permutations of the dataset. Note that an 'empty' item is added
    to the dataset to simulate a slot in the grocery cart
    being empty.

    TODO: allow for the model to take in an abstract action class so we can
     separate actions from the model.

    We select an action based on an epsilon greedy policy, meaning,
    with probability epsilon we will sample an action uniformly rather
    than using our model. The starting value, ending value, and
    decay of epsilon can be changed using input parameters.

    Parameters
    ----------
    dm: ScrapyKingSoopersDataModule
        DataModule to use
    reward_func: callable
        Reward function that takes in an Environment and outputs
        a value.
    gc_size: int
        Size of the grocery cart passed to our model.
    n_features: int
        Size of the features passed to the model. Depends on how
        the dataset is setup.
    n_conn: int
        Number of connections between hidden layers in the model.
    n_hidden: int
        Number of hidden layers to use.
    batch_size: int
        Batch size to pull from memory when optimizing.
    memory_size: int
        Max memory size.
    gamma: float
        Discount factor.
    learning_rate: float
        learning rate
    eps_start: float
        Starting value for epsilon.
    eps_end: float
        Ending value for epsilon.
    eps_last_frame: float
        The final frame in for the decrease of epsilon. At this frame
        epsilon = eps_end
    sync_rate: int
        Number of iterations between syncing up the target network
        with the train network
    batches_per_epoch: int
        Number of batches per epoch
    n_steps: int
        Size of n step look ahead
    min_episode_reward: int
        The minimum score that can be achieved in an episode. Used
        for filling the avg buffer before training begins
    avg_reward_len: int
        How many episodes to take into account when calculating the
        avg reward
    warm_start_size: int
        How many random steps through the environment to be carried out
        at the start of training to fill the buffer with a starting point
    tol: float
        Tolerance of difference in reward we use to stop a training
        episode.
    max_steps: int
        Maximum number of steps during a training episode
    """

    def __init__(
        self,
        dm: ScrapyKingSoopersDataModule,
        reward_func: Callable,
        gc_size: int,
        n_features: int,
        n_conn: int,
        n_hidden: int,
        batch_size: int = 32,
        memory_size: int = 100000,
        gamma: float = 0.99,
        learning_rate: float = 1e-4,
        eps_start: float = 1.0,
        eps_end: float = 0.02,
        eps_last_frame: int = 150000,
        sync_rate: int = 1000,
        batches_per_epoch: int = 1000,
        n_steps: int = 1,
        min_episode_reward: int = 0,
        avg_reward_len: int = 100,
        warm_start_size: int = 1000,
        tol: float = 1e-2,
        max_steps: int = 200000
    ):
        super().__init__()

        # Model attributes
        self.memory = ReplayMemory(capacity=memory_size)
        self.dm = dm
        self.dataset = None
        self.policy_net = DQN(
            n_features=n_features,
            n_conn=n_conn,
            n_hidden=n_hidden,
            n_actions=self.n_actions
        )
        self.target_net = DQN(
            n_features=n_features,
            n_conn=n_conn,
            n_hidden=n_hidden,
            n_actions=self.n_actions
        )

        # Hyperparameters
        self.min_episode_reward = min_episode_reward
        self.eps_start = eps_start
        self.eps_end = eps_end
        self.eps_last_frame = eps_last_frame
        self.tol = tol
        self.sync_rate = sync_rate
        self.gamma = gamma
        self.lr = learning_rate
        self.batch_size = batch_size
        self.memory_size = memory_size
        self.warm_start_size = warm_start_size
        self.batches_per_epoch = batches_per_epoch
        self.n_steps = n_steps
        self.max_steps = max_steps
        self.save_hyperparameters()

        # Environment
        self.env = Environment(self.dm, self.gc_size)
        self.test_env = Environment(self.dm, self.gc_size)
        self.state = self.env.state[0]
        self.reward_func = reward_func
        self.n_actions = gc_size * 2
        self.epsilon = self.eps_start

        # Metrics
        self.total_episode_steps = [0]
        self.total_rewards = [0]
        self.done_episodes = 0
        self.total_steps = 0

        # Average Rewards
        self.avg_reward_len = avg_reward_len
        for _ in range(avg_reward_len):
            self.total_rewards.append(
                torch.tensor(self.min_episode_reward, device=self.device)
            )
        self.avg_rewards = float(
            np.mean(self.total_rewards[-self.avg_reward_len:])
        )

    @torch.no_grad()
    def update_epsilon(self, step):
        self.epsilon = max(
            self.eps_end, self.eps_start - (step + 1) / self.eps_last_frame
        )

    @torch.no_grad()
    def get_action(self, env: Environment, epsilon: float):
        """Get action given current state of environment."""

        sample = random.random()
        if sample > epsilon:
            return self.policy_net(env.state[0]).max(-1)[1].view(1, 1)
        else:
            return torch.tensor(
                [[random.randrange(self.n_actions)]],
                device=self.device, dtype=torch.long
            )

    def run_n_episodes(
        self, env, n_episodes: int = 1, epsilon: float = 1.0
    ) -> List[int]:
        """
        Carry out N episodes.

        Parameters
        ----------
        env: Environment
        n_episodes: int
            Number of episodes to run
        epsilon: float
            epsilon value for DQN Agent
        """

        total_rewards = []
        for _ in range(n_episodes):
            env.reset()
            done = False
            episode_reward = 0

            while not done:
                self.epsilon = epsilon
                action = self.get_action(env, epsilon).item()
                env.step(action)
                reward = self.reward_func(env)
                episode_reward += reward

            total_rewards += episode_reward

        return total_rewards

    def populate(self, warm_start: int) -> None:
        """Populates the buffer with initial experiences."""

        if warm_start > 0:
            self.env.reset()
            self.state = self.env.state[0]
            prev_reward = self.min_episode_reward
            local_steps = 0

            for _ in range(warm_start):
                local_steps += 1
                self.epsilon = 1.0
                action = self.get_action(self.env, self.epsilon)
                self.env.step(action)

                next_state = self.env.state[0]
                reward = self.reward_func(self.env)

                self.memory.push(
                    self.state, action, next_state, reward
                )

                if self.env.is_done(
                    prev_reward, reward, self.tol, self.max_steps, local_steps
                ):
                    self.env.reset()
                    self.state = self.env.state[0]
                    prev_reward = self.min_episode_reward
                    local_steps = 0

    def configure_optimizers(self) -> List[optim.optimizer.Optimizer]:
        """Configure Adam optimizer."""
        optimizer = optim.Adam(self.policy_net.parameters(), lr=self.gamma)
        return [optimizer]

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Pass in state x through the network and get q_values

        Parameters
        ---------
        x: torch.Tensor
            Environment state

        Returns
        -------
        torch.Tensor
            q values
        """
        return self.policy_net(x)

    def train_batch(self) -> Transition:
        """
        Contains the logic for generating a new batch of data to be passed
        to the DataLoader

        Yields
        ------
        Transition
        """

        episode_reward = 0
        episode_steps = 0
        prev_reward = self.min_episode_reward
        while True:
            self.total_steps += 1
            action = self.get_action(self.env, self.epsilon)
            self.env.step(action)
            next_state = self.env.state[0]
            reward = self.reward_func(self.env)
            is_done = self.env.is_done(
                prev_reward, reward, self.tol, self.max_steps, episode_steps
            )

            episode_reward += reward
            episode_steps += 1

            self.update_epsilon(self.global_step)
            self.memory.push(self.state, action, next_state, reward)
            self.state = next_state

            if is_done:
                self.done_episodes += 1
                self.total_rewards.append(episode_reward)
                self.total_episode_steps.append(episode_steps)
                self.avg_rewards = float(
                    np.mean(self.total_rewards[-self.avg_reward_len:])
                )
                episode_steps = 0
                episode_reward = 0
                prev_reward = self.min_episode_reward

            states, actions, rewards, dones, new_states = self.memory.sample(
                self.batch_size
            )
            for idx, _ in enumerate(dones):
                yield states[idx], actions[idx], rewards[idx], dones[idx], \
                      new_states[idx]

            if self.total_steps % self.batches_per_epoch == 0:
                break

    def training_step(self, batch: Tuple[torch.Tensor, torch.Tensor], _):
        """
        Carries out a single step through the environment to update
        the replay buffer. Then calculates loss based on the minibatch
        received. Returns training loss and logs metrics.

        Parameters
        ----------
        batch: tuple of tensors
            current mini batch of replay data
        _: int
            batch number, not used
        """

        loss = dqn_loss(batch, self.net, self.target_net, self.gamma)

        if self.trainer.use_dp or self.trainer.use_ddp2:
            loss = loss.unsqueeze(0)

        if self.global_step % self.sync_rate == 0:
            self.target_net.load_state_dict(self.policy_net.state_dict())

        self.log_dict({
            "total_reward": self.total_rewards[-1],
            "avg_reward": self.avg_rewards,
            "train_loss": loss,
            "episodes": self.done_episodes,
            "episode_steps": self.total_episode_steps[-1]
        })

        return OrderedDict({
            "loss": loss,
            "avg_reward": self.avg_rewards
        })

    def test_step(self, *args, **kwargs) -> Dict[str, torch.Tensor]:
        """Evaluate the agent for 10 episodes"""

        test_reward = self.run_n_episodes(self.test_env, 1, 0)
        avg_reward = sum(test_reward) / len(test_reward)
        return {"test_reward": avg_reward}

    def test_epoch_end(self, outputs) -> Dict[str, torch.Tensor]:
        """
        Log the avg of test results
        """

        test_reward = [x["test_reward"] for x in outputs]
        avg_reward = sum(test_reward) / len(test_reward)
        return {"test_reward": avg_reward}

    def _dataloader(self) -> DataLoader:
        """Initialize memory buffer"""

        self.memory = ReplayMemory(self.memory_size)
        self.populate(self.warm_start_size)

        self.dataset = ExperienceSourceDataset(self.train_batch)
        return DataLoader(dataset=self.dataset, batch_size=self.batch_size)

    def train_dataloader(self) -> DataLoader:
        return self._dataloader()

    def test_dataloader(self) -> DataLoader:
        return self._dataloader()
