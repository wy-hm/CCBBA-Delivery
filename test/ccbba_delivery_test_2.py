from models.ccbba import CCBBA
import logging
import time
from numpy.random import randint, choice, seed
from numpy import exp
from numpy.linalg import norm
from math import sqrt

num_bases = 5
num_agents = 3
num_deliveries = 10

seed(0)

bases_pos = randint(1, 10, [num_bases, 2]).tolist()
agents_pos = randint(1, 10, [num_agents, 2]).tolist()

delivery_pos = []
delivery_target = []
delivery_reward= []

for d in range(num_deliveries):
    pos_target = choice(num_bases, 2, replace=False)
    delivery_pos.append(pos_target[0])
    delivery_target.append(pos_target[1])
    delivery_reward.append(100)

max_transit = 1

tasks_pos = []
tasks_target = []
tasks_reward = []
activities = []
dependencies = []
temporals = []

num_task = 0
for d in range(len(delivery_pos)):
    activities.append([])
    dependencies.append([])
    temporals.append([])

    tasks_pos.append(delivery_pos[d])
    tasks_target.append(delivery_target[d])
    tasks_reward.append(delivery_reward[d])
    activities[d].append(num_task)

    num_task = num_task + 1

    transit_index = [0]
    while True:
        task_path = [delivery_target[d], delivery_pos[d]]

        is_feasible = True
        is_done = False

        for n in range(len(transit_index)):
            if transit_index[n] in task_path:
                is_feasible = False

            if transit_index[n] >= len(bases_pos):
                transit_index[n] = 0
                if n == len(transit_index) - 1:
                    if len(transit_index) == max_transit:
                        is_done = True
                        break
                    transit_index.append(0)
                else:
                    transit_index[n+1] = transit_index[n+1] + 1

            if is_feasible:
                task_path.append(transit_index[n])

        if is_done:
            break

        if is_feasible:
            del task_path[0]
            task_path.append(delivery_target[d])

            print(task_path)
            distance = []
            total_distance = 0
            for j in range(1, len(task_path)):
                path_pos = bases_pos[task_path[j-1]]
                path_target = bases_pos[task_path[j]]

                path_dist = sqrt( (path_target[0] - path_pos[0])**2 + (path_target[1] - path_pos[1])**2 )
                total_distance = total_distance + path_dist

                distance.append(path_dist)

            for j in range(1, len(task_path)):
                activities[d].append(num_task)
                tasks_pos.append(task_path[j - 1])
                tasks_target.append(task_path[j])
                tasks_reward.append(delivery_reward[d] * distance[j-1] / total_distance)
                num_task = num_task + 1

            for q in range(len(activities[d])):
                if len(dependencies[d]) <= q:
                    dependencies[d].append([])
                    temporals[d].append([])

                for u in range(len(activities[d])):
                    if len(dependencies[d][q]) <= u:
                        dependencies[d][q].append(-1)
                        temporals[d][q].append(1e+10)

                    if q == u:
                        dependencies[d][q][u] = 0
                        temporals[d][q][u] = 0
                        continue

                    if q > len(activities[d]) - len(task_path) and u > len(activities[d]) - len(task_path):
                        dependencies[d][q][u] = 1

                    if u > len(activities[d]) - len(task_path) + 1 and q == u - 1:
                        temporals[d][q][u] = 0

        transit_index[0] = transit_index[0] + 1

time_start = time.time()
logging.getLogger().setLevel(logging.DEBUG)
logging.debug('Starting Test Program')
cbba = CCBBA
ccbba = CCBBA(activities=activities, dependencies=dependencies, temporals=temporals, bases_pos=bases_pos,
              agents_pos=agents_pos, tasks_pos=tasks_pos, tasks_target=tasks_target, tasks_reward=tasks_reward)
ccbba.run()

time_end = time.time()
logging.info('Running time: %.2f', time_end - time_start)