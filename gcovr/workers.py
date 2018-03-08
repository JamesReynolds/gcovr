# -*- coding:utf-8 -*-

# This file is part of gcovr <http://gcovr.com/>.
#
# Copyright 2013-2018 the gcovr authors
# This software is distributed under the BSD license.


from threading import Thread, Condition, Lock
from contextlib import contextmanager
from tempfile import mkdtemp

import sys
if sys.version_info[0] >= 3:
    from queue import Queue
else:
    from Queue import Queue


class LockedDirectories(object):
    """
    Class that keeps a list of locked directories
    """
    def __init__(self):
        self.dirs = set()
        self.cv = Condition()

    def run_in(self, dir_):
        """
        Start running in the directory and lock it
        """
        self.cv.acquire()
        while dir_ in self.dirs:
            self.cv.wait()
        self.dirs.add(dir_)
        self.cv.release()

    def done(self, dir_):
        """
        Finished with the directory, unlock it
        """
        self.cv.acquire()
        self.dirs.remove(dir_)
        self.cv.notify_all()
        self.cv.release()


@contextmanager
def locked_directory(dir_):
    """
    Context for doing something in a locked directory
    """
    locked_directory.global_object.run_in(dir_)
    yield
    locked_directory.global_object.done(dir_)


locked_directory.global_object = LockedDirectories()


def worker(queue, exceptions):
    """
    Run work items from the queue until the sentinal
    None value is hit
    """
    from threading import current_thread
    id = current_thread()
    workdir = mkdtemp()
    while True:
        work, args, kwargs = queue.get(True)
        if not work:
            break
        kwargs['workdir'] = workdir
        try:
            work(*args, **kwargs)
        except Exception as exn:
            import sys
            exceptions.append(sys.exc_info())
            break


    # On Windows the files may still be in use. This
    # is unlikely, the files are small, and are in a
    # temporary directory so we can skip this.
    import shutil
    shutil.rmtree(workdir, ignore_errors=True)


class Workers(object):
    """
    Create a thread-pool which can be given work via an
    add method and will run until work is complete
    """

    def __init__(self, number=1):
        assert(number >= 1)
        self.q = Queue()
        self.exceptions = []
        self.workers = [Thread(target=worker, args=(self.q,self.exceptions)) for _ in range(0, number)]
        for w in self.workers:
            w.start()

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

    def wait(self):
        """
        Wait until all work is complete
        """
        for w in self.workers:
            self.add(None)
        for w in self.workers:
            w.join()
        if self.exceptions:
            exc_type, exc_obj, exc_trace = self.exceptions[0]
            import traceback
            traceback.print_exception(exc_type, exc_obj, exc_trace)
            raise exc_obj



class LockedDictionary(object):
    """
    Locked coverage dictionary object
    """

    def __init__(self, clz):
        self.lock = Lock()
        self.clz = clz
        self.dict = dict()

    def update(self, key, **kwargs):
        """
        Update the dictionary with the supplied kwargs object
        by ensuring the key is present then updating the underlying
        object
        """
        with self.lock:
            if key not in self.dict:
                self.dict[key] = self.clz(key)
            self.dict[key].update(**kwargs)
