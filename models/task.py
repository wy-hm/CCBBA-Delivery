import numpy as np

class Task:
    def __init__(self, task_id, init_pos, target_pos, reward):
        self.id = task_id
        self.pos = init_pos
        self.target = target_pos
        self.reward = reward
        self.start_time = -1e+10
        self.deadline = 1e+10