from models.cbba import CBBA
from models.ccbba import CCBBA
import logging
import time
from numpy.random import randint, choice, seed
from numpy import exp
from math import sqrt
import numpy as np

num_bases = 5
num_agents = 3
num_deliveries = 20

# seed(10)

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

    delv_pos = bases_pos[delivery_pos[d]]
    delv_target = bases_pos[delivery_target[d]]

    delv_dist = sqrt( (delv_target[0] - delv_pos[0])**2 + (delv_target[1] - delv_pos[1])**2 )

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


            distance = []
            total_distance = 0
            for j in range(1, len(task_path)):
                path_pos = bases_pos[task_path[j-1]]
                path_target = bases_pos[task_path[j]]

                path_dist = sqrt( (path_target[0] - path_pos[0])**2 + (path_target[1] - path_pos[1])**2 )
                if path_dist > delv_dist:
                    is_feasible = False
                    break
                total_distance = total_distance + path_dist

                distance.append(path_dist)

            if is_feasible:
                print(task_path)
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
cbba = CBBA(bases_pos=bases_pos, agents_pos=agents_pos, tasks_pos=delivery_pos, tasks_target=delivery_target, tasks_reward=delivery_reward)
cbba.run()
ccbba = CCBBA(activities=activities, dependencies=dependencies, temporals=temporals, bases_pos=bases_pos,
              agents_pos=agents_pos, tasks_pos=tasks_pos, tasks_target=tasks_target, tasks_reward=tasks_reward)
ccbba.run()

time_end = time.time()
logging.info('Running time: %.2f', time_end - time_start)

#%%
logging.info('===  CBBA   ============================================')
for d in range(len(activities)):
    str = 'Activity %d: ' % d
    for agent in cbba.agents:
        for task_id in agent.path:
            if task_id == d:
                str = '%s%d (%d)' % (str, task_id, agent.id)

    logging.info(str)

logging.info('===  CCBBA   ============================================')
for d in range(len(activities)):
    str = 'Activity %d: ' % d
    for agent in ccbba.agents:
        for task_id in agent.path:
            if task_id in activities[d]:
                str = '%s%d (%d)' % (str, task_id, agent.id)

    logging.info(str)

#%%
from matplotlib import pyplot as plt

logging.getLogger().setLevel(logging.INFO)
fig = plt.figure()
ax = fig.gca()

ax.set_xticks(np.arange(0, 10))
ax.set_yticks(np.arange(0, 10))
plt.grid()

for base_pos in bases_pos:
    plt.scatter(base_pos[0], base_pos[1], marker='s', s=1000, c='#dddddd')

for d in range(len(delivery_pos)):
    plt.scatter(bases_pos[delivery_pos[d]][0], bases_pos[delivery_pos[d]][1], marker='o', c='#000000', s=100)

for agent in ccbba.agents:
    plt.scatter(agent.pos[0], agent.pos[1], marker='^', s=200)

for agent in ccbba.agents:
    path = agent.path

    x = [agent.pos[0]]
    y = [agent.pos[1]]
    for task_id in path:
        x.append(agent.tasks[task_id].pos[0])
        y.append(agent.tasks[task_id].pos[1])

        x.append(agent.tasks[task_id].target[0])
        y.append(agent.tasks[task_id].target[1])

    plt.plot(x, y)

plt.show()