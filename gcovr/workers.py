# -*- coding:utf-8 -*-

# This file is part of gcovr <http://gcovr.com/>.
#
# Copyright 2013-2018 the gcovr authors
# Copyright 2013 Sandia Corporation
# This software is distributed under the BSD license.


from threading import Thread

import sys
if sys.version_info[0] >= 3:
    from queue import Queue, Empty
else:
    from Queue import Queue, Empty


class WorkThread(Thread):
    """
    The work thread class continuously gets work and
    completes it
    """
    def __init__(self, pool):
        """
        Initialise with a reference to the pool object
        which houses the queue
        """
        super(WorkThread, self).__init__()
        self.pool = pool

    def run(self):
        """
        Run until the queue is empty
        """
        while True:
            try:
                work, args, kwargs = self.pool.get()
            except Empty:
                break
            work(*args, **kwargs)


class Workers(object):
    """
    Create a thread-pool which can be given work via an
    add method and will run until work is complete
    """

    def __init__(self, number=0):
        """
        Initialise with a number of workers
        """
        self.q = Queue()
        if number == 0:
            from multiprocessing import cpu_count
            number = cpu_count()
        self.workers = [WorkThread(self) for _ in range(0, number)]

    def add(self, work, *args, **kwargs):
        """
        Add in a method and the arguments to be used
        when running it
        """
        self.q.put((work, args, kwargs))

    def size(self):
        """
        Run the size of the thread pool
        """
        return len(self.workers)

    def get(self):
        """
        Get the next piece of work
        """
        return self.q.get(False, 5)

    def wait(self):
        """
        Wait until all work is complete
        """
        for w in self.workers:
            w.start()
        for w in self.workers:
            w.join()
