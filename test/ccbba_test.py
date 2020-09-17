from models.ccbba import CCBBA
import logging

bases_pos = [[1, 2], [5, 1], [5, 4], [10, 4], [2, 6], [5, 8]]
agents_pos = [[2, 1], [4, 6], [7, 1]]
tasks_pos = [0, 4]
tasks_target = [3, 3]
tasks_reward = [100, 100]
activities = [[0, 1]]
dependencies = [[[0, 1],
                 [1, 0]]]
temporals =  [[[0, 1e+10],
               [1e+10, 0]]]

logging.getLogger().setLevel(logging.DEBUG)
logging.debug('Starting Test Program')
ccbba = CCBBA(activities=activities, dependencies=dependencies, temporals=temporals, bases_pos=bases_pos,
              agents_pos=agents_pos, tasks_pos=tasks_pos, tasks_target=tasks_target, tasks_reward=tasks_reward)
ccbba.run()
