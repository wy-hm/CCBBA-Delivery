from models.cbba import CBBA
import logging
import time

bases_pos = [[1, 2], [5, 1], [5, 4], [10, 4], [2, 6], [5, 8]]
agents_pos = [[2, 1], [4, 6], [7, 1]]
tasks_pos = [0, 4]
tasks_target = [3, 3]
tasks_reward = [100, 100, 100]

time_start = time.time()
logging.getLogger().setLevel(logging.DEBUG)
logging.debug('Starting Test Program')
cbba = CBBA(bases_pos=bases_pos, agents_pos=agents_pos, tasks_pos=tasks_pos, tasks_target=tasks_target, tasks_reward=tasks_reward)
cbba.run()
time_end = time.time()
logging.info('Running time: %.2f', time_end - time_start)