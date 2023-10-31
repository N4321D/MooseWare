"""
interface driver for RPi internal i2c / GPIO etc interface
"""
from subs.driver.interface_drivers.template import Controller
from subs.driver.internal_bus import InternalBus

from multiprocessing import Process

class InternalController(Controller):
    # TODO: run complete interface (incl data processing in seperate process?)
    _dev_proc = Process         # placeholder for mp Process that runs internal bus

    def write(self, data) -> None:
        self.write_buffer.put(data)
    
    def read(self) -> None:
        print("todo make on_incomding async, see interface.py")
        return self.recv_buffer.get()

    def _setup(self) -> None:
        """
        called on init
        """
        self.device = InternalBus()
        self.recv_buffer = self.device.Serial.q_out
        self.write_buffer = self.device.Serial.q_in
        
        self._dev_proc = Process(target=self.device.start,)
        self._dev_proc.start()
    
    def exit(self, *args, **kwargs):
        if not self.recv_buffer._closed:
            self.recv_buffer.close()
        if not self.write_buffer._closed:
            self.write_buffer.close()
        self._dev_proc.join()


if __name__ == "__main__":

    c = InternalController()
