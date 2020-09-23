from models.ccbba import CCBBA
import logging

bases_pos = [[1, 2], [5, 1], [5, 4], [10, 4], [2, 6], [5, 8]]
agents_pos = [[2, 1], [4, 6], [7, 1]]
tasks_pos = [0, 0, 1, 0, 2, 0, 4, 0, 5, 4, 4, 0, 4, 1, 4, 2, 4, 5]
tasks_target = [3, 1, 3, 2, 3, 4, 3, 5, 3, 3, 0, 3, 1, 3, 2, 3, 5, 3]
tasks_reward = [1000, 500, 500, 500, 500, 500, 500, 500, 500, 1000, 500, 500, 500, 500, 500, 500, 500, 500]
activities = [[0, 1, 2, 3, 4, 5, 6, 7, 8], [9, 10, 11, 12, 13, 14, 15, 16, 17]]
dependencies = [[[0, -1, -1, -1, -1, -1, -1, -1, -1],
                 [-1, 0, 1, -1, -1, -1, -1, -1, -1],
                 [-1, 1, 0, -1, -1, -1, -1, -1, -1],
                 [-1, -1, -1, 0, 1, -1, -1, -1, -1],
                 [-1, -1, -1, 1, 0, -1, -1, -1, -1],
                 [-1, -1, -1, -1, -1, 0, 1, -1, -1],
                 [-1, -1, -1, -1, -1, 1, 0, -1, -1],
                 [-1, -1, -1, -1, -1, -1, -1, 0, 1],
                 [-1, -1, -1, -1, -1, -1, -1, 1, 0]],
                [[0, -1, -1, -1, -1, -1, -1, -1, -1],
                 [-1, 0, 1, -1, -1, -1, -1, -1, -1],
                 [-1, 1, 0, -1, -1, -1, -1, -1, -1],
                 [-1, -1, -1, 0, 1, -1, -1, -1, -1],
                 [-1, -1, -1, 1, 0, -1, -1, -1, -1],
                 [-1, -1, -1, -1, -1, 0, 1, -1, -1],
                 [-1, -1, -1, -1, -1, 1, 0, -1, -1],
                 [-1, -1, -1, -1, -1, -1, -1, 0, 1],
                 [-1, -1, -1, -1, -1, -1, -1, 1, 0]]
                ]
temporals = [[[0, 1e+10, 1e+10, 1e+10, 1e+10, 1e+10, 1e+10, 1e+10, 1e+10],
              [1e+10, 0, 0, 1e+10, 1e+10, 1e+10, 1e+10, 1e+10, 1e+10],
              [1e+10, 1e+10, 0, 1e+10, 1e+10, 1e+10, 1e+10, 1e+10, 1e+10],
              [1e+10, 1e+10, 1e+10, 0, 0, 1e+10, 1e+10, 1e+10, 1e+10],
              [1e+10, 1e+10, 1e+10, 1e+10, 0, 1e+10, 1e+10, 1e+10, 1e+10],
              [1e+10, 1e+10, 1e+10, 1e+10, 1e+10, 0, 0, 1e+10, 1e+10],
              [1e+10, 1e+10, 1e+10, 1e+10, 1e+10, 1e+10, 0, 1e+10, 1e+10],
              [1e+10, 1e+10, 1e+10, 1e+10, 1e+10, 1e+10, 1e+10, 0, 0],
              [1e+10, 1e+10, 1e+10, 1e+10, 1e+10, 1e+10, 1e+10, 1e+10, 0]],
             [[0, 1e+10, 1e+10, 1e+10, 1e+10, 1e+10, 1e+10, 1e+10, 1e+10],
              [1e+10, 0, 0, 1e+10, 1e+10, 1e+10, 1e+10, 1e+10, 1e+10],
              [1e+10, 1e+10, 0, 1e+10, 1e+10, 1e+10, 1e+10, 1e+10, 1e+10],
              [1e+10, 1e+10, 1e+10, 0, 0, 1e+10, 1e+10, 1e+10, 1e+10],
              [1e+10, 1e+10, 1e+10, 1e+10, 0, 1e+10, 1e+10, 1e+10, 1e+10],
              [1e+10, 1e+10, 1e+10, 1e+10, 1e+10, 0, 0, 1e+10, 1e+10],
              [1e+10, 1e+10, 1e+10, 1e+10, 1e+10, 1e+10, 0, 1e+10, 1e+10],
              [1e+10, 1e+10, 1e+10, 1e+10, 1e+10, 1e+10, 1e+10, 0, 0],
              [1e+10, 1e+10, 1e+10, 1e+10, 1e+10, 1e+10, 1e+10, 1e+10, 0]]
             ]

logging.getLogger().setLevel(logging.DEBUG)
logging.debug('Starting Test Program')
ccbba = CCBBA(activities=activities, dependencies=dependencies, temporals=temporals, bases_pos=bases_pos,
              agents_pos=agents_pos, tasks_pos=tasks_pos, tasks_target=tasks_target, tasks_reward=tasks_reward)
ccbba.run()


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