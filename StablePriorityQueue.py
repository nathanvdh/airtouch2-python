from queue import PriorityQueue
from sys import maxsize as MAX_INT

# To make PriorityQueue stable, see: https://docs.python.org/3/library/heapq.html#priority-queue-implementation-notes
# The item in the queue is: (priority, count, Message)
class StablePriorityQueue(PriorityQueue):
    def __init__(self):
        super().__init__()
        self.count = 0

    def put(self, item, priority: int, block=True, timeout=None):
        super().put((priority, self.count, item), block=block, timeout=timeout)
        self.count = (self.count + 1) % MAX_INT # force overflow to prevent count growing infinitely, not sure if necessary

    def get(self, block=True, timeout=None):
        item = super().get(block=block, timeout=timeout)
        return item[2] # return the actual item that was put()