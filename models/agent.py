from numpy.linalg import norm
from numpy import array
from models.task import Task


class Agent:
    def __init__(self, agent_id, init_pos):
        self.id = agent_id
        self.pos = init_pos
        self.max_speed = 1
