"""
Records stuff
"""
# create logger

from subs.log import create_logger
logger = create_logger()
def log(message, level="info"):
    cls_name = "RECORDER"
    getattr(logger, level)(f"{cls_name}: {message}")  # change CLASSNAME here

import time
import numpy as np
from multiprocessing import Process, Queue

from subs.recording.buffer import SharedBuffer
from subs.misc.shared_mem_np_dict import SharedTable, clear_queue


# import sensors from driver
try:
    from subs.driver.sensors import (sensTest, get_pars, chip_d, chip_d_short_name,
                                     datatypes,
                                     get_connected_chips_and_pars, get_connected_chips,
                                     shared_vars, ReadWrite, TESTING)

except Exception as e:
    log("Sensor import error: {}".format(e), "warning")
    from driver.sensors import (sensTest, get_pars, chip_d, datatypes, get_connected_chips_and_pars, shared_vars,
                                ReadWrite, TESTING)

class Recorder():
    """
    A class for recording data from connected chips.

    This class uses the shared memory mechanism to store the recorded data in a shared
    memory buffer. The class also uses a separate process to run the main loop that samples
    the connected chips.

    Attributes:
    start_rate (int): The start rate for recording data.
    buffer_length (int): The length of the buffer.
    MAX_MEM (int): The maximum memory that the buffer can use.
    buffer (dict): A placeholder for a dict with shared memory items for saving.
    q_in (Queue): A placeholder for a mp queue for instruction to chips and recorder.
    chip_d (dict): A database of the connected chips.
    pars (NoneType): A placeholder for the shared recording parameters.
    d_idx (int): The index of data in the data structure.
    data_name (str): The name of the data block in the shared memory and saved files.
    pars_name (str): The name of the shared table with recording parameters.
    process (Process): The multiprocessing Process for recording.

    Methods:
    __init__(self, **kwargs) -> None:
        Initializes the class instance by updating the instance dictionary with the
        keyword arguments, creates the recording parameters, initializes the shared
        buffer, loads the connected chips, creates the memory block, and sets the
        start values.
    start(self) -> Process:
        Starts the recording process.
    stop(self):
        Stops the recording process.
    load_chips(self):
        Adds parameters for the connected chips to memory.
    create_mem_block(self):
        Creates the memory block for the shared buffer.
    set_start_vals(self):
        Sets the start values for the recording parameters.
    loop(self):
        The main loop for recording data from the connected chips.
    """

    MAX_MEM = 200 * 1.024e6    # Max memory buffer can use, can be overwritten by  IO class with actual mem limit defined in vars.py

    start_rate = 256
    buffer_length = 0          # length of buffer (will be calculated from buffer_time * startrate)
    buffer = {}                # placeholder for dict with shared memory items for saving

    q_in = Queue    # placeholder for mp queue for instruction to chips and recorder

    chip_d = {}               # chip database with connected chips
    pars = None               # placeholder for SHARED_REC_PARS
    

    d_idx = 0                 # index of data in datastructure (to easily find parameters and iterators)

    data_name = 'data'                          # name for datablock in shared memory and saved files
    pars_name = 'recorder_pars'                 # name for shared table with recorder pars

    process = None             # mp Process for recording

    def __init__(self, **kwargs) -> None:
        """
        use kwargs to set start rate
        """
        self.__dict__.update(kwargs)
        self._create_pars()

        self.shared_buffer = SharedBuffer()
        
        self.data_structure = self.shared_buffer.data_structure
        self.buffer = self.shared_buffer.buffer

        if self.data_name in self.buffer:
            # clear existing data
            self.shared_buffer.reset(par=self.data_name)

        self.load_chips()
        self.create_mem_block()
        self.set_start_vals()
        self.q_in = Queue()
    
    def start(self) -> Process:
        """
        call to start recording in serperate process

        Returns:
            Process: running recording process
        """
        if not self.chip_d:
            # do not record if no chips connected
            self.process = Process()
        else:
            self.process = Process(target=self.loop)
        self.process.start()
        return self.process

    def stop(self):
        """
        stop recording
        also stops chips and clears queue
        """
        self.pars.set(False, 'run', 0)
        # force stop all chips
        [chip_d[chip].stop() for chip in self.chip_d]
        clear_queue(self.q_in)

    def load_chips(self):
        """
        add parameters for connected chips to memory
        """
        # check which chips are connected and add them to database
        [chip.whois() for chip in self.chip_d.values()]
        self.chip_d = {name: chip for name, chip in chip_d.items()
                       if (not chip.disconnected) and chip.record}
        
        # link stim
        for chip in self.chip_d.values():
            if hasattr(chip, "stim_control"):
                for sc in chip.stim_control.values():
                    name = str(chip.name)
                    sc.do_stim = lambda dur, amp: self.q_in.put((name, 'do_stim', (dur, amp), {}))
                    
    def create_mem_block(self):
        dtypes = [('time', 'f8'), 
                  *[(par, datatypes.get(par, datatypes['default'])) 
                       for chip in self.chip_d.values() 
                       for par in chip.out_vars]]  

        # bytes_per_samplepoint = sum([np.dtype(i[1]).itemsize for i in dtypes])
        bytes_per_samplepoint = np.empty(1, dtype=dtypes).nbytes                # make one example row and count nbytes

        self.buffer_length = int(self.MAX_MEM / bytes_per_samplepoint)
        if self.chip_d:
            self.shared_buffer.add_parameter(self.data_name, dtypes, self.buffer_length)

    def set_start_vals(self):
        # set max rate to lowest maxrate of chip or if none are found to startrate
        max_rate = min([rate for chip in self.chip_d.values()
                        if (rate := chip.settings['maxrate'])] or (self.start_rate,)
                        )
        self.pars.set(max_rate, 'maxrate', 0)

        # set sample rate
        self.pars.set(min(self.start_rate, self.pars.get('maxrate', 0)), 'samplerate', 0)
        self.pars.set(self.pars.get('samplerate', 0), 'emarate', 0)                             # exponetial average of sample rate
        self.guidestep = (1 / self.pars.get('samplerate', 0))                                   # step to sync time with guide time        


    def loop(self):
        '''
        MAIN LOOP: samples the sensors
        NOTE: runs in seperate process
        '''
        self.pars.set(True, 'run', 0)
        
        # create temp data dictionary (writing all pars as tuple at once is faster than indidually)
        data = {i: None for i in self.buffer[self.data_name].dtype.names}

        # Set pars:
        guidetime = time.time()                               # target time for each loop, used to sync

        # init chips if needed
        [chip.init() for chip in self.chip_d.values()]

        while self.pars.get('run', 0) == True:
            # start timers:
            t0 = time.perf_counter()
            
            # add expected looptime to guide time:
            guidetime += self.guidestep

            # set vars
            reset = []                  # list with chips that need to be resetted
            samplerate = self.pars.get('samplerate', 0)
            ema = self.pars.get('emarate', 0)

            # save time:
            data['time'] = time.time()

            # check for new instructions
            if not self.q_in.empty():
                self._chip_command()

            # add chips which need a trigger to the trigger list
            [chip.start() for chip in self.chip_d.values() 
                if chip.trigger_required]

            # SEND / RECEIVE chip data
            for chip in self.chip_d.values():
                # Read data from sensors
                data.update(chip.readself())
                    
                # if chip.disconnected:
                if chip.disconnected:
                    reset.append(chip)
                
            # save data in memory
            self.shared_buffer.add_1_to_buffer(self.data_name, 
                                               tuple(data.values()))

            # Reset sensors if disconnected
            if reset:
                [self._reset(chip) for chip in reset]
                        
            # ----------------------------------
            # calc delay & adjust sample rate: 
            # n = number of samples to take EMA
            n = samplerate * 64
            looptime = (time.perf_counter() - t0)
            ema = (ema - (ema / n)) + ((1 / looptime) / n)

            # double sample rate if possible (loop is fast enough)
            if ema >= (2 * samplerate):
                if (samplerate <= (self.pars.get('maxrate', 0) / 2)):
                    # do only if doubling would not exeed target rate
                    self._change_sample_rate('up')
            
            # reduce sample rate if loop is too slow
            if ema < samplerate:
                if samplerate >= (self.pars.get('minrate', 0) * 2):
                    # reduce sample rate:
                    self._change_sample_rate('down')

            # saved to shared mem
            self.pars.set(ema, 'emarate', 0)

            # wait for resting time until guidetime is reached,
            # use active loop with small wait times to prevent overshoot:'
            while time.time() < guidetime:
                time.sleep(0)

        self.buffer[self.data_name]._shm.close()                # close link to buffer from seperate processes
        self.stop()

 
    def _reset(self, chip):
        # resets sensors if non-responding
        chip.reset()

    def _change_sample_rate(self, rate):
        """
        double or half the sample rate
        or set any other value for rate
        """
        if rate == 'up':
            rate = self.pars.get('samplerate', 0) * 2

        elif rate == 'down':
            rate = max(self.pars.get('samplerate', 0) // 2, 0.1)   # limit to 0.1 Hz

        self.pars.set(rate, 'samplerate', 0)

        # adjust guidestep to match higher samplerate
        self.guidestep = (1 / self.pars.get('samplerate'))

    def _create_pars(self):
        self.pars = SharedTable()
        self.pars.from_dict(
            self.pars_name,
            {'run': False,
             'samplerate': np.float32(0),
             'minrate': np.float32(1),
             'maxrate': np.float32(0),
             'emarate': np.float32(0),
            }
        )
    
    def _chip_command(self):
        """
        get commands for chips from q_in
        and send to chips
        """
        #TODO: set time limit for max amount of instructions to process from queue?
        #      for example use maximal sample rate - emarate
        while not self.q_in.empty():
            chip, method, args, kwargs = self.q_in.get()
            if chip in self.chip_d:
                getattr(self.chip_d[chip], method)(*args, **kwargs)


#TESTING
if __name__ == "__main__":
    import multiprocessing as mp
    
    chip_d['OIS'].disconnected = False
    chip_d['Motion'].disconnected = False

    r = Recorder(start_rate=25600)
    proc = r.start()

    TIME = 2
    print(f'Recording for {TIME} seconds')
    time.sleep(TIME)
    r.stop()
    proc.join()