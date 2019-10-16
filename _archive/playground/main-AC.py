import os
import time
import numpy as np
import tensorflow as tf
from multiprocessing import Process, Manager
import sys

sys.path.append('..')

from core.machine import MachineConfig
from _archive.playground.algorithm import RandomAlgorithm
from _archive.playground.algorithm import Tetris
from _archive.playground.algorithm import FirstFitAlgorithm
from _archive.playground.algorithm import RLAlgorithm
from _archive.playground.algorithm import Agent
from _archive.playground.algorithm.smart.brain import Brain

from _archive.playground.algorithm import AverageCompletionRewardGiver

from _archive.playground.utils.csv_reader import CSVReader
from _archive.playground import features_extract_func_ac, features_normalize_func_ac
from _archive.playground.utils.tools import multiprocessing_run, average_completion, average_slowdown
from _archive.playground.utils.episode import Episode

os.environ['CUDA_VISIBLE_DEVICES'] = ''

np.random.seed(41)
tf.random.set_random_seed(41)
# ************************ Parameters Setting Start ************************
machines_number = 5
jobs_len = 10
n_iter = 50 # Original code was 100
n_episode = 12
jobs_csv = './workflows.csv'

brain = Brain(9)
reward_giver = AverageCompletionRewardGiver()
features_extract_func = features_extract_func_ac
features_normalize_func = features_normalize_func_ac

name = '%s-%s-m%d' % (reward_giver.name, brain.name, machines_number)
model_dir = './agents/%s' % name
# ************************ Parameters Setting End ************************

if not os.path.isdir(model_dir):
    os.makedirs(model_dir)

agent = Agent(name, brain, 1, reward_to_go=True, nn_baseline=True, normalize_advantages=True,
              model_save_path='%s/model.ckpt' % model_dir)

machine_configs = [MachineConfig(64, 1, 1) for i in range(machines_number)]
csv_reader = CSVReader(jobs_csv)
jobs_configs = csv_reader.generate(0, jobs_len)

tic = time.time()
algorithm = RandomAlgorithm()
episode = Episode(machine_configs, jobs_configs, algorithm, None)
episode.run()
print("Randome Algorithm")
print(episode.env.now, time.time() - tic, average_completion(episode), average_slowdown(episode))

tic = time.time()
algorithm = FirstFitAlgorithm()
episode = Episode(machine_configs, jobs_configs, algorithm, None)
episode.run()
print("First Fit Algorithm")
print(episode.env.now, time.time() - tic, average_completion(episode), average_slowdown(episode))

tic = time.time()
algorithm = Tetris()
episode = Episode(machine_configs, jobs_configs, algorithm, None)
episode.run()
print(episode.env.now, time.time() - tic, average_completion(episode), average_slowdown(episode))

for itr in range(n_iter):
    tic = time.time()
    print("********** Iteration %i ************" % itr)
    processes = []

    manager = Manager()
    trajectories = manager.list([])
    makespans = manager.list([])
    average_completions = manager.list([])
    average_slowdowns = manager.list([])
    for i in range(n_episode):
        algorithm = RLAlgorithm(agent, reward_giver, features_extract_func=features_extract_func,
                                features_normalize_func=features_normalize_func)
        episode = Episode(machine_configs, jobs_configs, algorithm, None)
        algorithm.reward_giver.attach(episode.simulation)
        p = Process(target=multiprocessing_run,
                    args=(episode, trajectories, makespans, average_completions, average_slowdowns))

        processes.append(p)

    for p in processes:
        p.start()

    for p in processes:
        p.join()

    agent.log('makespan', np.mean(makespans), agent.global_step)
    agent.log('average_completions', np.mean(average_completions), agent.global_step)
    agent.log('average_slowdowns', np.mean(average_slowdowns), agent.global_step)

    toc = time.time()

    print(np.mean(makespans), toc - tic, np.mean(average_completions), np.mean(average_slowdowns))

    all_observations = []
    all_actions = []
    all_rewards = []
    for trajectory in trajectories:
        observations = []
        actions = []
        rewards = []
        for node in trajectory:
            observations.append(node.observation)
            actions.append(node.action)
            rewards.append(node.reward)

        all_observations.append(observations)
        all_actions.append(actions)
        all_rewards.append(rewards)

    all_q_s, all_advantages = agent.estimate_return(all_rewards)

    agent.update_parameters(all_observations, all_actions, all_advantages)

agent.save()
