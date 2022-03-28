"""
Class for defining and managing all components relative to Branching Dueling Q-Network - BDQN
This BDQN will consist of:
- Double Q-learning
- Dueling Q-network
- Branching Q-network
- Experience Replay
"""

import math
from collections import namedtuple, deque
import random
import numpy as np

import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F

""" 
-- Vanilla BDQN --
DQN:
Guides-
https://pytorch.org/tutorials/intermediate/reinforcement_q_learning.html
https://deeplizard.com/learn/video/PyQNfsGUnQA

Dueling DQN:
Guides-
https://www.youtube.com/watch?v=Odmeb3gkN0M&t=3s - Eden Meyer
Repos-
"""


class SequenceReplayMemory(object):
    """Manages a sequential replay memory, where data is stored as numpy arrays."""

    def __init__(self, capacity: int, batch_size: int, sequence_length: int, interaction_spacing: int = 1):
        self.capacity = capacity
        self.batch_size = batch_size
        self.sequence_length = sequence_length
        self.interaction_spacing = interaction_spacing

        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

        self.state_memory = None
        self.action_memory = None
        self.next_state_memory = None
        self.reward_memory = None
        self.terminal_memory = None

        self.interaction_count = 0
        self.first_sample = True

    def push(self, state, action, next_state, reward, terminal_flag):
        """Save a transition to replay memory"""

        if self.first_sample:
            self.state_memory = torch.zeros([self.capacity, len(state)]).to(self.device)
            self.action_memory = torch.zeros([self.capacity, len(action)]).to(self.device)
            self.next_state_memory = torch.zeros([self.capacity, len(next_state)]).to(self.device)
            self.reward_memory = torch.zeros([self.capacity, 1]).to(self.device)
            self.terminal_memory = torch.zeros([self.capacity, 1]).to(self.device)
            self.first_sample = False

        index = self.interaction_count % self.capacity

        self.state_memory[index] = torch.Tensor(state).to(self.device)
        self.action_memory[index] = torch.Tensor(action).to(self.device)
        self.next_state_memory[index] = torch.Tensor(next_state).to(self.device)
        self.reward_memory[index] = torch.Tensor([reward]).to(self.device)
        self.terminal_memory[index] = torch.Tensor([terminal_flag]).to(self.device)

        self.interaction_count += 1

    def sample(self):
        """Sample a transition randomly"""

        sample_width = self.interaction_count if self.interaction_count < self.capacity else self.capacity
        sample_indices = np.random.choice(range(sample_width), self.batch_size, replace=False)

        state_batch = self.state_memory[sample_indices].to(self.device)
        action_batch = self.action_memory[sample_indices].long().to(self.device)
        next_state_batch = self.next_state_memory[sample_indices].to(self.device)
        reward_batch = self.reward_memory[sample_indices].to(self.device)
        terminal_batch = self.terminal_memory[sample_indices].to(self.device)

        return state_batch, action_batch, next_state_batch, reward_batch, terminal_batch

    def can_provide_sample(self):
        """Check if replay memory has enough experience tuples to sample batch from"""

        enough_interactions = self.interaction_count >= self.batch_size
        enough_sequences = self.interaction_count >= (self.interaction_spacing * self.sequence_length)

        return enough_interactions and enough_sequences


class BranchingQNetwork(nn.Module):
    """BDQ network architecture."""

    def __init__(self, observation_dim, action_branches, action_dim,
                 shared_network_size, value_stream_size, advantage_streams_size):
        """
        Below, we define the BDQN architecture's network segments, consisting of a MLP shared representation,
        then a dueling state value module and individual advantage branches. At the end, the value and advantage streams
        are combined to get the branched Q-value output.
        """

        super().__init__()

        # -- Shared State Feature Estimator --
        layers = []
        prev_layer_size = observation_dim

        for i, layer_size in enumerate(shared_network_size):
            layers.append(nn.Linear(prev_layer_size, layer_size))
            # layers.append(nn.Relu)
            prev_layer_size = layer_size
        shared_final_layer = prev_layer_size

        self.shared_model = nn.Sequential(*layers)

        # --- Value Stream ---
        layers = []
        prev_layer_size = shared_final_layer
        for i, layer_size in enumerate(value_stream_size):
            layers.append(nn.Linear(prev_layer_size, layer_size))
            prev_layer_size = layer_size

        final_layer = nn.Linear(prev_layer_size, 1)  # output state-value
        self.value_stream = nn.Sequential(*layers, final_layer)

        # --- Advantage Streams ---
        layers = []
        prev_layer_size = shared_final_layer
        for i, layer_size in enumerate(advantage_streams_size):
            layers.append(nn.Linear(prev_layer_size, layer_size))
            prev_layer_size = layer_size

        final_layer = nn.Linear(prev_layer_size, action_dim)
        self.advantage_streams = nn.ModuleList(
            [nn.Sequential(*layers, final_layer) for i in range(action_branches)]
        )

    def forward(self, state_input):
        # Shared Network
        out = self.shared_model(state_input)
        # Value Branch
        value = self.value_stream(out)
        # Advantage Streams
        advs = torch.stack([advantage_stream(out) for advantage_stream in self.advantage_streams], dim=1)

        # Q-Value - Recombine Branches
        q_vals = value.unsqueeze(2) + advs - advs.mean(2, keepdim=True)  # identifiable method eqn #1

        return q_vals


class BranchingDQN(nn.Module):
    """A branching, dueling, & double DQN algorithm."""

    def __init__(self, observation_dim: int, action_branches: int, action_dim: int,
                 shared_network_size: list, value_stream_size: list, advantage_streams_size: list,
                 target_update_freq: int, learning_rate: float, gamma: float, td_target: str,
                 gradient_clip_norm: float, rescale_shared_grad_factor: float = None):

        super().__init__()

        self.observation_space = observation_dim
        self.action_branches = action_branches
        self.action_dim = action_dim
        self.shared_network_size = shared_network_size
        self.advantage_streams_size = advantage_streams_size
        self.value_stream_size = value_stream_size
        self.gamma = gamma  # discount factor
        self.learning_rate = learning_rate
        self.gradient_clip_norm = gradient_clip_norm
        self.rescale_shared_grad_factor = rescale_shared_grad_factor

        self.policy_network = BranchingQNetwork(observation_dim, action_branches, action_dim, shared_network_size,
                                                value_stream_size, advantage_streams_size)
        self.target_network = BranchingQNetwork(observation_dim, action_branches, action_dim, shared_network_size,
                                                value_stream_size, advantage_streams_size)
        self.target_network.load_state_dict(self.policy_network.state_dict())  # copy params

        self.optimizer = optim.Adam(self.policy_network.parameters(), lr=self.learning_rate)  # learned policy

        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.policy_network.to(self.device)
        self.target_network.to(self.device)

        self.target_update_freq = target_update_freq
        self.update_count = 0
        self.step_count = 0

        self.td_target = td_target

    def get_greedy_action(self, state_tensor):
        x = state_tensor.to(self.device).T  # single action row vector
        with torch.no_grad():
            out = self.policy_network(x).squeeze(0)
            action = torch.argmax(out, dim=1)  # argmax within each branch

        return action.detach().cpu().numpy()  # action.numpy()

    @staticmethod
    def get_current_qval(bdq_network, states, actions):
        qvals = bdq_network(states)
        return qvals.gather(2, actions.unsqueeze(2)).squeeze(-1)

    def get_next_double_qval(self, next_states):
        # double q learning
        with torch.no_grad():
            argmax = torch.argmax(self.policy_network(next_states), dim=2)
            return self.target_network(next_states).gather(2, argmax.unsqueeze(2)).squeeze(-1)

    def update_target_net(self):
        self.update_count += 1
        if self.update_count % self.target_update_freq == 0:
            self.update_count = 0
            self.target_network.load_state_dict(self.policy_network.state_dict())

    def update_policy(self, batch):
        # get converted batch of tensors
        batch_states, batch_actions, batch_next_states, batch_rewards, batch_terminals = batch

        # Bellman TD update
        current_Q = self.get_current_qval(self.policy_network, batch_states, batch_actions)
        next_Q = self.get_next_double_qval(batch_next_states)

        # Get global target across branches, if desired
        if self.td_target:
            with torch.no_grad():
                if self.td_target == 1:  # mean
                    next_Q = next_Q.mean(1, keepdim=True)
                elif self.td_target == 0:  # max
                    next_Q, _ = next_Q.max(1, keepdim=True)
                else:
                    raise ValueError(f'Either "mean" or "max" must be entered to td_target keyword of BranchingDQN.'
                                     f'You entered {self.td_target}')

            # duplicate columns from reduction op, so current_Q size is same as next_Q for loss function
            next_Q = torch.repeat_interleave(next_Q, current_Q.shape[1], 1)  # TODO should this be done with hooks?

        expected_Q = batch_rewards + next_Q * self.gamma * (1 - batch_terminals)  # target

        loss = F.mse_loss(expected_Q, current_Q)  # minimize TD error with Mean-Squared-Error

        self.optimizer.zero_grad()
        loss.backward()

        # -- Modify Gradients --
        if self.gradient_clip_norm != 0:
            # If 0, don't clip norm
            nn.utils.clip_grad_norm_(self.policy_network.parameters(), max_norm=self.gradient_clip_norm)

        # Normalize gradients converging at shared network from action branches and value stream
        if self.rescale_shared_grad_factor is not None:
            for layer in self.policy_network.shared_model:
                layer.weight.grad = layer.weight.grad * self.rescale_shared_grad_factor

        # -- Optimize --
        self.optimizer.step()

        # -- Update --
        self.update_target_net()
        self.step_count += 1

        return loss.detach().cpu()

    def import_model(self, model_path: str):
        """
        Loads a serialized/pickled model from Path, and sets it to the policy and target network.
        :param model_path: Path to pickled PyTorch model
        """
        self.policy_network.load_state_dict(torch.load(model_path))
        # self.policy_network.load_state_dict(torch.load(model_path).state_dict())  # used to save wrong
        self.target_network.load_state_dict(self.policy_network.state_dict())


class EpsilonGreedyStrategy:
    """ Epsilon Greedy action selection strategy, with epsilon decay."""

    def __init__(self, start, end, decay):
        self.start = start
        self.end = end
        self.decay = decay
        self.current_exploration_rate = 0

    def get_exploration_rate(self, current_step, fixed_epsilon: float = None):
        if fixed_epsilon is not None:
            self.current_exploration_rate = fixed_epsilon
            return fixed_epsilon
        self.current_exploration_rate = self.end + (self.start - self.end) * math.exp(-1. * current_step * self.decay)
        return self.current_exploration_rate
