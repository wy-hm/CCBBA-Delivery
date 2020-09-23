from models.cbba import CBBA
from models.ccbba import CCBBA

import logging
import time
from math import sqrt
import numpy as np

bases_pos = [[1, 2], [5, 1], [5, 4], [10, 4], [2, 6], [5, 8]]
agents_pos = [[2, 1], [4, 6], [7, 1]]
delivery_pos = [0, 4]
delivery_target = [3, 3]
delivery_reward = [100, 100]

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
from matplotlib import pyplot as plt

logging.getLogger().setLevel(logging.INFO)
fig = plt.figure()
ax = fig.gca()

ax.set_xticks(np.arange(0, 11))
ax.set_yticks(np.arange(0, 11))
plt.grid()

for base_pos in bases_pos:
    plt.scatter(base_pos[0], base_pos[1], marker='s', s=1000, c='#dddddd')

for d in range(len(delivery_pos)):
    if d == 0:
        label = 'Delivery'
    else:
        label = None
    plt.scatter(bases_pos[delivery_pos[d]][0], bases_pos[delivery_pos[d]][1], marker='o', c='#000000', s=100, label=label)

for agent in ccbba.agents:
    if agent.id == 0:
        label = 'Agent'
    else:
        label = None
    plt.scatter(agent.pos[0], agent.pos[1], marker='s', s=100, label=label)

for agent in ccbba.agents:
    path = agent.path

    x = [agent.pos[0]]
    y = [agent.pos[1]]
    for task_id in path:
        x.append(agent.tasks[task_id].pos[0])
        y.append(agent.tasks[task_id].pos[1])

        x.append(agent.tasks[task_id].target[0])
        y.append(agent.tasks[task_id].target[1])

    if agent.id == 0:
        label = 'Hybrid (CCBBA)'
    else:
        label = None
    line = plt.plot(x, y, label=label)[0]
    if len(path) > 0:
        plt.arrow(x[-2], y[-2], x[-1]-x[-2], y[-1]-y[-2], color=line.get_color(), head_length=0.25, head_width=0.25, length_includes_head=True)

ax.set_prop_cycle(None)

for agent in cbba.agents:
    path = agent.path

    x = [agent.pos[0]]
    y = [agent.pos[1]]
    for task_id in path:
        x.append(agent.tasks[task_id].pos[0])
        y.append(agent.tasks[task_id].pos[1])

        x.append(agent.tasks[task_id].target[0])
        y.append(agent.tasks[task_id].target[1])

    if agent.id == 0:
        label = 'Direct (CBBA)'
    else:
        label = None
    line = plt.plot(x, y, linestyle='dashed', label=label)[0]
    if len(path) > 0:
        plt.arrow(x[-1]-0.01*(x[-1]-x[-2]), y[-1]-0.01*(y[-1]-y[-2]), 0.01*(x[-1]-x[-2]), 0.01*(y[-1]-y[-2]), color=line.get_color(), head_length=0.25, head_width=0.25, length_includes_head=True)

plt.legend()
plt.show()


