import logging
import math

import numpy as np
import math

from models.activity import Activity
from models.cbba import CBBA, CBBA_Agent


class CCBBA(CBBA):
    def __init__(self, activities, dependencies, temporals, *args, **kwargs):
        try:
            self.logging
        except AttributeError:
            self.logging = logging.getLogger('CCBBA')
            self.logging.setLevel(logging.INFO)

        self.activities = []
        self.duplicates = dict()
        super(CCBBA, self).__init__(*args, **kwargs)

        self.init_activities(activities, dependencies, temporals)
        self.init_duplicates()

    def init_agents(self, agents_pos):
        self.logging.debug('Initializing agents')
        for i in range(len(agents_pos)):
            self.agents.append(CCBBA_Agent(i, agents_pos[i]))
            self.agents[-1].tasks = self.tasks
            self.agents[-1].activities = self.activities
            self.agents[-1].logging.setLevel(self.logging.level)

    def init_activities(self, activities, dependencies, temporals):
        for a in range(len(activities)):
            self.activities.append(Activity(a, activities[a], dependencies[a], temporals[a]))
            for task_id in activities[a]:
                self.tasks[task_id].activity = a

    def init_duplicates(self):
        for q in range(len(self.tasks)):
            if q not in self.duplicates:
                self.duplicates[q] = dict()

            for u in range(len(self.tasks)):
                if u not in self.duplicates:
                    self.duplicates[u] = dict()

                if u == q:
                    self.duplicates[q][u] = 0
                    self.duplicates[u][q] = 0
                    continue

                if (self.tasks[q].pos == self.tasks[u].pos) and (self.tasks[q].target == self.tasks[u].target):
                    self.duplicates[q][u] = 1
                    self.duplicates[u][q] = 1
                else:
                    self.duplicates[q][u] = 0
                    self.duplicates[u][q] = 0

        for i in range(len(self.agents)):
            self.agents[i].duplicates = self.duplicates

    def run(self):
        self.logging.info('Running CCBBA')
        auction_timer = 0
        while True:

            for agent in self.agents:

                last_violations = agent.violations



                agent.build_bundle()
                agent.calc_arrival_times()
                agent.check_violations()

                for neighbor_id in agent.neighbors:
                    last_prices = agent.prices
                    last_bidders = agent.bidders
                    neighbor = self.agents[neighbor_id]
                    neighbor_data = {
                        'id': neighbor.id,
                        'prices': neighbor.prices,
                        'bidders': neighbor.bidders,
                        'timestamps': neighbor.timestamps,
                        'neighbors': neighbor.neighbors,
                        'arrival_times': neighbor.arrival_times
                    }
                    agent.conflict_res(neighbor_data)
                    agent.enforce_strategy()
                    agent.enforce_mutex()
                    agent.enforce_temporal()

                    if not (
                            agent.prices == last_prices and agent.bidders == last_bidders and agent.violations == last_violations):
                        auction_timer = 0

            if auction_timer >= 20:
                break
            auction_timer = auction_timer + 1

        self.logging.info('Finished auction')

    def calc_total_reward(self):
        total_reward = 0
        for agent in self.agents:
            path_str = ''
            for task_id in agent.path:
                path_str = '%s%d (%.2fs) ' % (path_str, task_id, agent.arrival_times[task_id])
            self.logging.info('Agent %d Path: %s' % (agent.id, path_str))
            total_reward = total_reward + agent.calc_reward()
        self.logging.info('Total reward: %.2f' % total_reward)
        return total_reward

    def get_activity(self, task_id):
        for activity in self.activities:
            if task_id in activity.tasks_id:
                return activity
        return None
        # return self.activities[self.tasks[task_id].activity]


class CCBBA_Agent(CBBA_Agent):
    def __init__(self, *args, **kwargs):
        self.W_VIOLATE = 1
        self.V_TIMEOUT = 3

        super(CCBBA_Agent, self).__init__(*args, **kwargs)
        self.activities = []
        self.w_solo = dict()
        self.w_any = dict()
        self.timeout = dict()
        self.arrival_times = dict()
        self.violations = dict()
        self.duplicates = dict()

    def can_bid(self, task_id, score):
        val = True
        if task_id in self.prices:
            val = val and (score > self.prices[task_id])
        if val:
            val = val and self.can_bid_strategy(task_id)
        if val:
            val = val and self.can_bid_mutex(task_id, score)
        return val

    def can_bid_strategy(self, task_id):
        activity = self.get_activity(task_id)
        if activity.strategies[task_id] == activity.PESSIMISTIC:
            return self.num_satisfied(task_id) == activity.requirements[task_id]
        else:
            return ((task_id not in self.w_any or self.w_any[task_id] < self.W_VIOLATE) and self.num_satisfied(
                task_id) > 0) or \
                   (task_id not in self.w_solo or self.w_solo[task_id] < self.W_VIOLATE) or \
                   (self.num_satisfied(task_id) == activity.requirements[task_id])

    def can_bid_mutex(self, q, score):
        activity = self.get_activity(q)
        for u in activity.tasks_id:
            if not (u not in self.prices or score > self.prices[u] or (activity.dependency[u][q] != -1)):
                return False
        return True

    def num_satisfied(self, q):
        activity = self.get_activity(q)
        val = 0
        for u in activity.tasks_id:
            if u == q:
                continue
            if (u in self.bidders and self.bidders[u] >= 0) and (activity.dependency[u][q] == 1):
                val = val + 1
        return val

    def update_task(self, task_id, neighbor):
        super(CCBBA_Agent, self).update_task(task_id, neighbor)
        if task_id in neighbor['arrival_times']:
            self.arrival_times[task_id] = neighbor['arrival_times'][task_id]
        else:
            self.arrival_times[task_id] = 0

    def reset_task(self, task_id):
        super(CCBBA_Agent, self).reset_task(task_id)
        self.arrival_times[task_id] = 0
        # self.violations[task_id] = 0
        # self.increase_w(task_id)

    def release_bundle(self, task_id):
        super(CCBBA_Agent, self).release_bundle(task_id)
        self.calc_arrival_times()

    def release_one(self, task_id):
        self.bundle.remove(task_id)
        self.path.remove(task_id)

    def calc_reward(self, path=None):
        if not path:
            path = self.path

        cum_dist = 0
        cum_time = 0
        reward = 0
        last_pos = self.pos
        last_task_id = -1

        for task_id in path:
            task = self.get_task(task_id)

            if last_task_id >= 0 and self.duplicates[task_id][last_task_id]:
                dist = 0
            else:
                dist, start_time, finish_time = self.calc_dist_time(task, last_pos, cum_time)
                cum_time = finish_time
                last_pos = task.target

            cum_dist = cum_dist + dist

            reward = reward + task.reward * math.exp(-0.1 * cum_time)

            last_task_id = task_id

        reward = reward - 3 * cum_dist
        reward = max(reward, 0)

        return reward

    def calc_arrival_times(self):
        cum_dist = 0
        cum_time = 0
        reward = 0
        last_pos = self.pos
        last_task_id = -1

        for task_id in self.path:
            task = self.get_task(task_id)

            if last_task_id >= 0 and self.duplicates[task_id][last_task_id]:
                dist = 0
            else:
                dist, start_time, finish_time = self.calc_dist_time(task, last_pos, cum_time)
                cum_time = finish_time
                last_pos = task.target

            cum_dist = cum_dist + dist
            self.arrival_times[task_id] = cum_time

            last_task_id = task_id

        return reward

    def calc_dist_time(self, task, last_pos, cum_time):
        t_min, _ = self.get_temporal_const(task.id)

        # dist = norm(np.array(task.pos) - np.array(last_pos))
        dist = math.sqrt((task.pos[0] - last_pos[0]) ** 2 + (task.pos[1] - last_pos[1]) ** 2)
        cum_dist = dist
        start_time = cum_time + dist / self.max_speed
        start_time = max(t_min, start_time)

        # dist = norm(np.array(task.target) - np.array(task.pos))
        dist = math.sqrt((task.target[0] - task.pos[0]) ** 2 + (task.target[1] - task.pos[1]) ** 2)
        cum_dist = cum_dist + dist
        finish_time = start_time + dist / self.max_speed

        return cum_dist, start_time, finish_time

    def check_violations(self):
        for task_id in self.bundle:
            activity = self.get_activity(task_id)
            if task_id in self.violations and self.violations[task_id] > self.V_TIMEOUT:
                self.logging.debug('Violation timeout for task %d' % task_id)
                self.increase_w(task_id)
                self.reset_task(task_id)
                self.release_bundle(task_id)

            if activity.strategies[task_id] == activity.OPTIMISTIC and self.num_satisfied(task_id) != \
                    activity.requirements[task_id]:
                if task_id in self.violations:
                    self.violations[task_id] = self.violations[task_id] + 1
                else:
                    self.violations[task_id] = 1

    def get_temporal_const(self, q):
        t_min = self.tasks[q].start_time
        t_max = self.tasks[q].deadline

        activity = self.get_activity(q)
        for u in activity.tasks_id:
            if u == q:
                continue
            if u in self.bidders and self.bidders[u] >= 0 and activity.dependency[u][q] > 0:
                if u in self.arrival_times:
                    t_min_const = self.arrival_times[u] - activity.temporal[u][q]
                    t_max_const = self.arrival_times[u] + activity.temporal[q][u]
                else:
                    t_min_const = activity.temporal[u][q]
                    t_max_const = activity.temporal[q][u]

                if t_min_const > t_min:
                    t_min = t_min_const
                if t_max_const < t_max:
                    t_max = t_max_const

        return t_min, t_max

    def increase_w(self, task_id):
        if task_id in self.w_solo:
            self.w_solo[task_id] = self.w_solo[task_id] + 1
        else:
            self.w_solo[task_id] = 1

        if task_id in self.w_any:
            self.w_any[task_id] = self.w_any[task_id] + 1
        else:
            self.w_any[task_id] = 1

    def enforce_strategy(self):
        for q in self.bundle:
            activity = self.get_activity(q)
            if activity.strategies[q] == activity.PESSIMISTIC and self.num_satisfied(q) < activity.requirements[q]:
                self.logging.debug('Enforcing strategy for task %d' % q)
                self.reset_task(q)
                self.release_bundle(q)
                break

    def enforce_mutex(self):
        for q in self.bundle:
            activity = self.get_activity(q)
            for u in activity.tasks_id:
                if q == u:
                    continue
                if not (u not in self.prices or (q in self.prices and self.prices[q] > self.prices[u]) or
                        activity.dependency[u][q] != -1):
                    self.logging.debug('Enforcing mutex for task %d with violation to task %d' % (q, u))
                    self.reset_task(q)
                    self.release_bundle(q)
                    self.increase_w(q)
                    break

    def enforce_temporal(self):
        for q in self.bundle:
            activity = self.get_activity(q)
            for u in activity.tasks_id:
                if q == u:
                    continue
                if u in self.bidders and self.bidders[u] >= 0:
                    if u not in self.arrival_times:
                        self.arrival_times[u] = 0
                    if q not in self.arrival_times:
                        self.arrival_times[q] = 0
                    if activity.strategies[q] == activity.PESSIMISTIC:
                        if not (((self.arrival_times[q] <= self.arrival_times[u] + activity.temporal[q][u]) and
                                 (self.arrival_times[u] <= self.arrival_times[q] + activity.temporal[u][q])) or
                                activity.dependency[u][q] <= 0):
                            self.logging.debug('Enforcing temporal for task %d with violation to task %d' % (q, u))
                            self.reset_task(q)
                            self.release_bundle(q)
                            self.increase_w(q)
                            continue
                    else:
                        if not (((self.arrival_times[q] <= self.arrival_times[u] + activity.temporal[q][u]) and
                                 (self.arrival_times[u] <= self.arrival_times[q] + activity.temporal[u][q])) or (
                                        self.arrival_times[q] - self.tasks[q].start_time <= self.arrival_times[u] -
                                        self.tasks[u].start_time) or activity.dependency[u][q] <= 0):
                            self.logging.debug('Enforcing temporal for task %d with violation to task %d' % (q, u))
                            self.reset_task(q)
                            self.release_bundle(q)
                            self.increase_w(q)
                            continue
                    # if not ((self.arrival_times[q] <= self.arrival_times[u] + activity.temporal[q][u]) and
                    #         (self.arrival_times[u] <= self.arrival_times[q] + activity.temporal[u][q])):
                    #     self.logging.debug('Arrival time %d: %.2f. Arrival time %d: %.2f' % (
                    #         q, self.arrival_times[q], u, self.arrival_times[u]))
                    #     if activity.dependency[u][q] == 1:
                    #         if activity.dependency[q][u] == 1:
                    #             if self.arrival_times[q] - self.tasks[q].start_time <= self.arrival_times[u] - \
                    #                     self.tasks[u].start_time:
                    #                 self.logging.debug(
                    #                     'Enforcing temporal for task %d with violation to task %d' % (q, u))
                    #                 self.reset_task(q)
                    #                 self.release_bundle(q)
                    #                 self.increase_w(q)
                    #                 break
                    #         else:
                    #             self.logging.debug('Enforcing temporal for task %d with violation to task %d' % (q, u))
                    #             self.reset_task(q)
                    #             self.release_bundle(q)
                    #             self.increase_w(q)
                    #             break

    def get_activity(self, task_id):
        for activity in self.activities:
            if task_id in activity.tasks_id:
                return activity
        return None