"""
interface driver for RPi internal i2c / GPIO etc interface
"""
from subs.driver.interface_drivers.template import Controller
from subs.driver.internal_bus import InternalBus

import asyncio
import multiprocessing
from multiprocessing import Process


class AsyncQueueProcessor:
    """
    Reads multiprocessing Queue async
    """
    def __init__(self, queue, **kwargs):
        self.__dict__.update(kwargs)
        self.loop = asyncio.get_event_loop()
        self.queue = queue

    def process_queue(self):
        while not self.queue._closed:
            self.do(self.queue.get())

    async def run_loop(self):
        await self.loop.run_in_executor(None, self.process_queue)

    def do(self, data) -> None:
        """
        placeholder for function that is called when new data is in the queue

        Args:
            data (object): new data from queue
        """


class InternalController(Controller):
    # TODO: run complete interface (incl data processing in seperate process?)
    q_out = None                # placeholder for mp queue of internal bus
    q_in = None                 # placeholder for mp queue of internal bus
    _dev_proc = Process         # placeholder for mp Process that runs internal bus
    _queue_processor = AsyncQueueProcessor

    async def start(self) -> None:
        return asyncio.gather(self._queue_processor.run_loop(), 
                              self.on_connect_default(), 
                              return_exceptions=True)

        
    def write(self, data) -> None:
        if self.q_out:
            self.q_out.put(data)

    def _setup(self) -> None:
        """
        called on init
        """
        self.device = InternalBus()
        self.q_in = self.device.Serial.q_out
        self.q_out = self.device.Serial.q_in
        
        self._dev_proc = Process(target=self.device.start,)
        self._dev_proc.start()

        self._queue_processor = AsyncQueueProcessor(self.q_in,
                                                    do=self._preprocess_data)
    
    def exit(self, *args, **kwargs):
        if not self.q_out._closed:
            self.q_out.close()
        if not self.q_in._closed:
            self.q_in.close()
        self._dev_proc.join()


if __name__ == "__main__":

    c = InternalController()
