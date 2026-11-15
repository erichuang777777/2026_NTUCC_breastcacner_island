"""Wake connected displays after committed changes, without a growing event queue."""
import threading

class ResidentUpdates:
    def __init__(self):
        self.condition=threading.Condition()
        self.version=0
        self.slots=threading.BoundedSemaphore(32)
    def changed(self):
        with self.condition:
            self.version+=1
            self.condition.notify_all()
    def wait(self,version,timeout=5):
        with self.condition:
            self.condition.wait_for(lambda:self.version!=version,timeout)
            return self.version
