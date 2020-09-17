import numpy as np


class Activity:
    def __init__(self, activity_id, tasks_id, dependency, temporal):
        self.OPTIMISTIC = 1
        self.PESSIMISTIC = 0

        self.id = activity_id
        self.tasks_id = tasks_id
        self.dependency = dict()
        self.temporal = dict()
        self.strategies = dict()
        self.requirements = dict()
        self.duplicates = dict()

        for q in range(len(self.tasks_id)):
            self.dependency[self.tasks_id[q]] = dict()
            for u in range(len(self.tasks_id)):
                self.dependency[self.tasks_id[q]][self.tasks_id[u]] = dependency[q][u]

        for q in range(len(self.tasks_id)):
            self.temporal[self.tasks_id[q]] = dict()
            for u in range(len(self.tasks_id)):
                self.temporal[self.tasks_id[q]][self.tasks_id[u]] = temporal[q][u]

        for q in tasks_id:
            is_dependent = False
            for u in tasks_id:
                if (self.dependency[u][q] >= 1) and (self.dependency[q][u] == 1):
                    is_dependent = True
                    break
            if is_dependent:
                self.strategies[q] = self.OPTIMISTIC
            else:
                self.strategies[q] = self.PESSIMISTIC

        for q in tasks_id:
            self.requirements[q] = 0
            for u in tasks_id:
                if self.dependency[u][q] == 1:
                    self.requirements[q] = self.requirements[q] + 1