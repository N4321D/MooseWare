"""
This class saves data to h5 file
"""

# create logger
try:
    from subs.log import create_logger
    logger = create_logger()

except:
    logger = None

def log(message, level="info"):
    getattr(logger, level)(f"SAVER: {message}")  # change CLASSNAME here


import h5py
import threading as tr
import numpy as np
from datetime import datetime, timedelta

from subs.recording.buffer import SharedBuffer

from pathlib import Path
import tempfile

from shutil import rmtree


class Saver():
    paths = {"save_dir": Path("./data/"),                      # Dir to save completed files
             "temp_dir": Path("./data/temp/"),                 # Dir to save temp files
            }
    filename = "data"                           # filename (without path)
    extension = ".h5"                           # extension of filename
    full_file_name = ""                         # filename with name_date.extension
    date = ""                                   # file timestamp

    file = None                                 # place holder for file object
    
    shared_buffer = None                        # link to class shared memory
    buffer = {}                                 # buffer for data
    info = []                                   # shared list with info about pars etc

    attrs = {}
    dataset = {}                                # links to datasets in h5 file are stored here
    
    last_pos = {}                               # position (index) in data of last written data

    BLOCK_SIZE = 0x7FFF                         # items (in 1st dim) to buffer data before writing to file
    BLOCK_PAR = 'data'                          # parameter on which max items is tested
    save_block_lengths = {}                     # dictionary with buffer length for each save block

    NEW_FILE_INTERVAL = timedelta(days=1, 
                                  hours = 0,
                                  minutes=0,
                                  seconds=0,)   # time interval to create new file in timedelta

    STOP = tr.Event()                           # flag to indicate stop of recording
    SAVE_LOOP_INTERVAL = 1                      # time to wait before checking for new save data

    start_time = None                           # start time of recording

    compression = {'compression': "gzip",       # compression parameters for h5 file
                   'compression_opts': 5,       # 5 is optimal (higher number does not really make the file smaller)
                   'fletcher32': False,
                   'shuffle': False,            # Only shuffle if not linear data
                   }
    
    recname = ''

    save_tr = None                              # Save loop thread

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        
        # empty tempdir
        if self.paths['temp_dir'].exists():
            rmtree(self.paths['temp_dir'])

        # make paths
        for p in self.paths.values():
            p.mkdir(parents=True, exist_ok=True)
            p.chmod(0o777)                              # set ownership to everyone
        
        # create tempdir
        self.tempdir = tempfile.TemporaryDirectory(dir=self.paths['temp_dir'])
        self.paths['temp_dir'] = Path(self.tempdir.name)
        
        # clean tempdir
        
    def start(self, start_time=None):
        """
        Start the thread that saves the buffer to a file.

        Args:
            start_time (datetime.datetime, optional): The start time to be used for creating the file. 
                If not provided, the current time is used.
        
        Returns:
            None
        """
        self.STOP = tr.Event()
        self.link_buffer()

        if self.file is None:
            self.new_file(start_time)
        
        self.save_tr = tr.Thread(target=self.save_loop)
        self.save_tr.start()
        
    def stop(self):
        self.STOP.set()
        self.save_tr.join()
        self.save_buffer()
        self.close_file()
        self.tempdir.cleanup()                      # empty tempdir on clean stop

    def link_buffer(self):
        if self.shared_buffer is None:
            self.shared_buffer = SharedBuffer()
            self.data_structure = self.shared_buffer.data_structure
            self.buffer = self.shared_buffer.buffer
            self.update_buffer_links()
    
    def update_buffer_links(self):
        '''
        updates and links to shared memory if new parameters are added elsewhere
        '''
        self.shared_buffer.check_new()

    def new_file(self, start_time=None) -> h5py.File:
        if self.STOP.is_set():
            return                   # dont create new file if recording is stopped

        if self.file:
            self.close_file()

        self.start_time = start_time or datetime.now()

        self.date = self.start_time.strftime("_%Y%m%d_%H%M%S")
        
        # create file names
        self.full_file_name = f"{self.filename}{self.date}{self.extension}"
        filename = self.paths["temp_dir"] / self.full_file_name
        
        # create file
        self.file = h5py.File(filename, "w")
        filename.chmod(0o777)                                                    # set permission so that everyone car read / write      


        self.dataset = {}
        self.attrs = {"timezone": str(datetime.now().astimezone().tzinfo),
                      "time_offset_utc": round((datetime.now() - datetime.utcnow()).total_seconds()),
                      }         # attributes to write to file

        log("new file: {}".format(self.full_file_name), "debug")

    def close_file(self):
        self.file.attrs.update(self.attrs)
        self.file.close()
        self.file = None

        src = self.paths["temp_dir"] / self.full_file_name
        dst = self.paths["save_dir"] / self.recname

        dst.mkdir(parents=True, exist_ok=True)
        dst.chmod(0o777)                                                    # set permission so that everyone car read / write

        dst /= self.full_file_name                                              # add filename to destination        
        src.rename(dst)                                                         # Move file

        log("closed file: {}".format(self.full_file_name), "debug")

    def save_loop(self):
        """
        Run this loop to check if data needs to be saved
        """
        
        while not self.STOP.wait(self.SAVE_LOOP_INTERVAL):
            self.update_buffer_links()              # NOTE do only ondemand if taking too many resources
            
            for par in self.data_structure.parameters:
                if par not in self.save_block_lengths:
                    self.save_block_lengths[par] = self.BLOCK_SIZE

                try:
                    data_size = self.data_structure.get('dim0', par)
                    
                except IndexError:
                    # data structure not yet created by recorder
                    log(f"no data for parameter: {par}", 'warning')
                    continue

                if self.save_block_lengths[par] > data_size:
                    # limit buffer to half of the size of the data buffer and minimal 1
                    self.save_block_lengths[par] = int(data_size / 2) or 1


                n_items = self.shared_buffer.get_n_items('added', 'saved', par)

                if (n_items >= self.save_block_lengths[par]) and n_items > 0:
                    self.save_buffer()

                    # increase save block size if saving takes too long
                    if (data_size // 2) > n_items > (2 * self.save_block_lengths[par]):
                        self.save_block_lengths[par] *= 2
                        
                        log(f'Save loop too slow (or blocksize to small).'
                            f'increasing blocksize to {self.save_block_lengths[par]}', 
                            'warning')

    def save_buffer(self):
        ''' 
        call this method to save data
        '''
        
        for par in self.buffer:
            data, newest_pos = self.get_data(par)
            
            if data is not None:
                self.write(par, data)
                self.data_structure.set(newest_pos, 'saved', par)

        if self.file:
            self.file.flush()               # write all data to file

        # create new file each ... time interval
        if ((datetime.now() - self.start_time) >= self.NEW_FILE_INTERVAL
            and not self.STOP.is_set()):
            self.new_file()

    def get_data(self, par):
        """
        gets data for saving from shared memory

        """

        last_pos = self.data_structure.get('saved', par)
        n_items = self.shared_buffer.get_n_items('added', 'saved', par)

        # limit newest pos to last saved plus max items so that data stays in sync
        if n_items > self.BLOCK_SIZE:
            newest_pos = last_pos + self.BLOCK_SIZE
        else:
            newest_pos = self.data_structure.get('added', par)

        size = self.data_structure.get('dim0', par)
        newest_pos = (newest_pos) % size

        data = self.shared_buffer.get_buf(par, start=last_pos, end=newest_pos)

        newest_pos = (newest_pos + 1 % size)                                     # add one to prevent double saving end with next save

        return data, newest_pos

    def write(self, key, data):
        """
        this method writes data from buffer to file
        """
        items = data.shape[0]

        if key not in self.dataset:
            # create new data set entry
            self.create_dataset(key, data)
        
        else:
            # expand data set with new data
            dims = list(self.dataset[key].shape)
            dims[0] += items
            self.dataset[key].resize(dims)
            self.dataset[key][-items:] = data
        
    def create_dataset(self, key, data) -> dict:
        """
        creates a data set for the key with the data
        """
        datatype = data.dtype
        maxshape = list(data.shape)
        maxshape[0] = None
        self.dataset[key] = (self
                             .file
                             .create_dataset(key,
                                             data=data,
                                             dtype=datatype,
                                             maxshape=maxshape,
                                             # chunks=(32000,),
                                             chunks=True,
                                             **self.compression,
                                    )
                            )

# TODO: use shared dictionary for shared pars?

# TEST
if __name__ == "__main__":
    import time
    TEST_ITEMS = int(5e5)
    SAV_STEPS = TEST_ITEMS / 5
    sav = Saver()
    sav.NEW_FILE_INTERVAL = timedelta(minutes=1)
    print('started')
    sav.start()

    # create data
    if not sav.buffer:
        print('creating data')
        sav.shared_buffer.add_parameter('data', [('time', 'f8'), ('random1', 'f4'), ('lin1', 'i4')], TEST_ITEMS)
        sav.shared_buffer.add_parameter('linear', 'i8', TEST_ITEMS)
        sav.shared_buffer.add_parameter('random', 'f8', TEST_ITEMS)

        for i in range(int(TEST_ITEMS)): 
            sav.buffer['data']['time'][i] = time.time()
            sav.buffer['data']['random1'][i] = np.random.random()
            sav.buffer['data']['lin1'][i] = i
            sav.buffer['linear'][i] = i
            sav.buffer['random'][i] = np.random.random()
            sav.data_structure.set((sav.data_structure.get('added', ...) + 1) % TEST_ITEMS, 'added', ...)
       
            if i % SAV_STEPS == 0 and i > 1: 
                sav.new_file() 
            time.sleep(10/1e9)

    # sav.stop()
    # sav.shared_buffer.close_all()
    # sav.shared_buffer.unlink_all()
    # print('all done')


