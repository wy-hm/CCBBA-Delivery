import logging
import math
import time

import numpy as np

from models.agent import Agent
from models.base import Base
from models.task import Task


class CBBA:

    def __init__(self, bases_pos, agents_pos, tasks_pos, tasks_target, tasks_reward):
        try:
            self.logging
        except AttributeError:
            self.logging = logging.getLogger('CBBA')
            self.logging.setLevel(logging.INFO)

        self.bases = []
        self.agents = []
        self.tasks = []

        self.init_bases(bases_pos)
        self.init_tasks(tasks_pos, tasks_target, tasks_reward)
        self.init_agents(agents_pos)
        self.init_neighbors()

    def init_bases(self, bases_pos):
        self.logging.debug('Initializing bases')
        for m in range(len(bases_pos)):
            self.bases.append(Base(m, bases_pos[m]))

    def init_tasks(self, tasks_pos, tasks_target, tasks_reward):
        self.logging.debug('Initializing tasks')
        for j in range(len(tasks_pos)):
            self.tasks.append(Task(j, self.bases[tasks_pos[j]].pos, self.bases[tasks_target[j]].pos, tasks_reward[j]))

    def init_agents(self, agents_pos):
        self.logging.debug('Initializing agents')
        for i in range(len(agents_pos)):
            self.agents.append(CBBA_Agent(i, agents_pos[i]))
            self.agents[-1].tasks = self.tasks
            self.agents[-1].logging.setLevel(self.logging.level)

    def init_neighbors(self):
        for i in range(len(self.agents)):
            for k in range(len(self.agents)):
                if i == k:
                    continue
                self.agents[i].neighbors.append(k)

    def run(self):
        self.logging.debug('Running CBBA')
        auction_timer = 0
        while True:

            for agent in self.agents:
                agent.build_bundle()
                for neighbor_id in agent.neighbors:
                    last_prices = agent.prices
                    last_bidders = agent.bidders

                    neighbor = self.agents[neighbor_id]
                    neighbor_data = {
                        'id': neighbor.id,
                        'prices': neighbor.prices,
                        'bidders': neighbor.bidders,
                        'timestamps': neighbor.timestamps,
                        'neighbors': neighbor.neighbors
                    }
                    agent.conflict_res(neighbor_data)

                    if not (agent.prices == last_prices and agent.bidders == last_bidders):
                        auction_timer = 0

            if auction_timer >= 20:
                break
            auction_timer = auction_timer + 1

        self.logging.info('Finished auction')
        total_reward = 0
        done_tasks = []
        for agent in self.agents:
            path_str = ''
            for task_id in agent.path:
                path_str = '%s%d ' % (path_str, task_id)
            self.logging.info('Agent %d Path: %s' % (agent.id, path_str))
            total_reward = total_reward + agent.calc_reward()
        self.logging.info('Total reward: %.2f' % total_reward)


class CBBA_Agent(Agent):

    def __init__(self, agent_id, init_pos):
        super(CBBA_Agent, self).__init__(agent_id=agent_id, init_pos=init_pos)
        try:
            self.logging
        except AttributeError:
            self.logging = logging.getLogger('Agent %d' % self.id)
            self.logging.setLevel(logging.INFO)

        self.neighbors = []
        self.bundle = []
        self.path = []
        self.tasks = []
        self.prices = dict()
        self.bidders = dict()
        self.timestamps = dict()

    def build_bundle(self):

        while True:
            avail_tasks = [task.id for task in self.tasks if task.id not in self.bundle]
            if not avail_tasks:
                self.logging.debug('No available task. Finish building bundle')
                break

            max_score = 0
            max_task_id = -1
            max_path_index = -1

            cur_reward = self.calc_reward(self.path)
            assert cur_reward >= 0, 'Current reward is less than zero'

            for task_id in avail_tasks:
                # self.logging.debug('Computing task %d' % task_id)

                score = 0
                path_index = -1

                # Finds path_index resulting in maximum score
                for n in range(len(self.bundle) + 1):
                    new_path = self.path.copy()
                    new_path.insert(n, task_id)

                    new_reward = self.calc_reward(new_path)
                    assert new_reward >= 0, 'New reward is less than zero'

                    reward_diff = new_reward - cur_reward
                    if reward_diff > score:
                        score = reward_diff
                        path_index = n

                can_bid = self.can_bid(task_id=task_id, score=score)

                if path_index < 0:
                    # self.logging.debug('No task with nonzero score. Continue')
                    continue

                # self.logging.debug('Score for task %d: %.2f > %.2f' % (task_id, score, score * can_bid))

                if score * can_bid > max_score:
                    max_score = score * can_bid
                    max_task_id = task_id
                    max_path_index = path_index

            if max_task_id < 0:
                # self.logging.debug('No task with nonzero score. Finish building bundle')
                break

            self.logging.debug('Task %d is added to bundle with score %.2f' % (max_task_id, max_score))
            self.bundle.append(max_task_id)
            self.path.insert(max_path_index, max_task_id)

            self.prices[max_task_id] = max_score
            self.bidders[max_task_id] = self.id

        self.logging.debug('Path: [' + ', '.join(map(str, self.path)) + ']')

    def conflict_res(self, neighbor):
        self.logging.debug('Resolving conflict with Agent %d' % neighbor['id'])
        for task_id in neighbor['prices'].keys():
            if task_id not in self.prices:
                self.prices[task_id] = 0
                self.bidders[task_id] = -1

            if neighbor['bidders'][task_id] == -1:
                if self.bidders[task_id] == -1:
                    # LEAVE
                    pass
                elif self.bidders[task_id] == self.id:
                    # LEAVE
                    pass
                elif self.bidders[task_id] == neighbor['id']:
                    # UPDATE
                    self.update_task(task_id, neighbor)
                    pass
                else:
                    m_id = self.bidders[task_id]
                    if (m_id in neighbor['timestamps']) and neighbor['timestamps'][m_id] > self.timestamps[m_id]:
                        # UPDATE
                        self.update_task(task_id, neighbor)
                        pass
            elif neighbor['bidders'][task_id] == neighbor['id']:
                if self.bidders[task_id] == -1:
                    # UPDATE
                    self.update_task(task_id, neighbor)
                    pass
                elif self.bidders[task_id] == self.id:
                    if neighbor['prices'][task_id] > self.prices[task_id]:
                        # UPDATE & RELEASE
                        self.update_task(task_id, neighbor)
                        self.release_bundle(task_id)
                        pass
                elif self.bidders[task_id] == neighbor['id']:
                    # UPDATE
                    self.update_task(task_id, neighbor)
                    pass
                else:
                    m_id = self.bidders[task_id]
                    if ((m_id in neighbor['timestamps']) and neighbor['timestamps'][m_id] > self.timestamps[m_id]) or \
                            (neighbor['prices'][task_id] > self.prices[task_id]):
                        # UPDATE
                        self.update_task(task_id, neighbor)
                        pass
            elif neighbor['bidders'][task_id] == self.id:
                if self.bidders[task_id] == -1:
                    # LEAVE
                    pass
                elif self.bidders[task_id] == self.id:
                    # LEAVE
                    pass
                elif self.bidders[task_id] == neighbor['id']:
                    # RESET
                    self.reset_task(task_id)
                    pass
                else:
                    m_id = self.bidders[task_id]
                    if (m_id in neighbor['timestamps']) and neighbor['timestamps'][m_id] > self.timestamps[m_id]:
                        # RESET
                        self.reset_task(task_id)
                        pass
            else:
                m_id = neighbor['bidders'][task_id]
                if m_id not in self.timestamps:
                    self.timestamps[m_id] = 0

                if self.bidders[task_id] == -1:
                    if neighbor['timestamps'][m_id] > self.timestamps[m_id]:
                        # UPDATE
                        self.update_task(task_id, neighbor)
                        pass
                elif self.bidders[task_id] == self.id:
                    if (neighbor['timestamps'][m_id] > self.timestamps[m_id]) and \
                            (neighbor['prices'][task_id] > self.prices[task_id]):
                        # UPDATE & RELEASE
                        self.update_task(task_id, neighbor)
                        self.release_bundle(task_id)
                        pass

                elif self.bidders[task_id] == neighbor['id']:
                    if neighbor['timestamps'][m_id] > self.timestamps[m_id]:
                        # UPDATE
                        self.update_task(task_id, neighbor)
                        pass
                    else:
                        # RESET
                        self.reset_task(task_id)
                        pass
                elif self.bidders[task_id] == m_id:
                    if neighbor['timestamps'][m_id] > self.timestamps[m_id]:
                        # UPDATE
                        self.update_task(task_id, neighbor)
                        pass
                else:
                    n_id = self.bidders[task_id]
                    if (neighbor['timestamps'][m_id] > self.timestamps[m_id]) and \
                            ((n_id in neighbor['timestamps']) and neighbor['timestamps'][n_id] > self.timestamps[n_id]):
                        # UPDATE
                        self.update_task(task_id, neighbor)
                        pass
                    if (neighbor['timestamps'][m_id] > self.timestamps[m_id]) and \
                            (neighbor['prices'][task_id] > self.prices[task_id]):
                        # UPDATE
                        self.update_task(task_id, neighbor)
                        pass
                    if (neighbor['timestamps'][m_id] < self.timestamps[m_id]) and \
                            ((n_id in neighbor['timestamps']) and neighbor['timestamps'][n_id] > self.timestamps[n_id]):
                        # RESET
                        self.reset_task(task_id)
                        pass

        if neighbor['id'] in self.neighbors:
            self.timestamps[neighbor['id']] = time.time()

        for m_id, m_timestamp in neighbor['timestamps'].items():
            if m_id in neighbor['neighbors']:
                self.timestamps[m_id] = m_timestamp

        self.logging.debug('Path: [' + ', '.join(map(str, self.path)) + ']')

    def update_task(self, task_id, neighbor):
        self.logging.debug('Updating task %d with price %.2f and bidder %d' % (
        task_id, neighbor['prices'][task_id], neighbor['bidders'][task_id]))
        self.prices[task_id] = neighbor['prices'][task_id]
        self.bidders[task_id] = neighbor['bidders'][task_id]

    def reset_task(self, task_id):
        self.logging.debug('Resetting task %d', task_id)
        self.prices[task_id] = 0
        self.bidders[task_id] = -1

    def release_bundle(self, task_id):
        bundle_index_start = self.bundle.index(task_id)
        for m in range(len(self.bundle) - 1, bundle_index_start - 1, -1):
            next_task_id = self.bundle[m]
            self.logging.debug('Releasing task %d', next_task_id)
            del self.bundle[m]

            n = self.path.index(next_task_id)
            del self.path[n]

            if m > bundle_index_start:
                self.reset_task(next_task_id)

    def calc_reward(self, path=None):
        if not path:
            path = self.path

        cum_dist = 0
        cum_time = 0
        reward = 0
        last_pos = self.pos

        for task_id in path:
            task = self.get_task(task_id)

            dist, start_time, finish_time = self.calc_dist_time(task, last_pos, cum_time)
            cum_time = finish_time
            cum_dist = cum_dist + dist
            last_pos = task.target

            reward = reward + task.reward * math.exp(-0.01 * cum_time)

        reward = reward - 3 * cum_dist
        reward = max(reward, 0)

        return reward

    def calc_dist_time(self, task, last_pos, cum_time):

        # dist = norm(np.array(task.pos) - np.array(last_pos))
        dist = math.sqrt((task.pos[0] - last_pos[0]) ** 2 + (task.pos[1] - last_pos[1]) ** 2)
        cum_dist = dist
        start_time = cum_time + dist / self.max_speed

        # dist = norm(np.array(task.target) - np.array(task.pos))
        dist = math.sqrt((task.target[0] - task.pos[0]) ** 2 + (task.target[1] - task.pos[1]) ** 2)
        cum_dist = cum_dist + dist
        finish_time = start_time + dist / self.max_speed

        return cum_dist, start_time, finish_time

    def can_bid(self, task_id, score):
        if task_id in self.prices:
            return score > self.prices[task_id]
        else:
            return 1

    def get_task(self, task_id):
        # for task in self.tasks:
        #     if task.id == task_id:
        #         return task
        # return None
        return self.tasks[task_id]
