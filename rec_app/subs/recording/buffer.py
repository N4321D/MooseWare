"""
Shared memory for recording

use create shared np function to quickly create a shared np array or link to it


"""

# create logger
try:
    from subs.log import create_logger
    logger = create_logger()

except:
    logger = None

def log(message, level="info"):
    cls_name = "SHARED_MEMORY"
    try:
        getattr(logger, level)(f"{cls_name}: {message}")  # change CLASSNAME here
    except AttributeError:
        print(f"{cls_name} - {level}: {message}")


from subs.misc.shared_mem_np_dict import SharedTable, create_shared_np
import numpy as np
import pickle
from bisect import bisect_left

class SharedBuffer():
    """
    - buffer:                   Dictionary with shared numpy arrays
    - data structure_format:    shared list with info about data structure
    - data_structure:           Shared np.recarray with par names write position, 
                                dtype, dimensions etc
    - shms:                     Dictionary with links to shared memory for buffer 
                                (name of each shm is the name of the par)
    """
    name = "Shared_Memory"          # change name on init if using multiple of these classes

    MAX_PARS = 128                  # Maximum number of parameters
    MAX_DIMS = 5                    # max dims for data par
    MAX_PAR_NAME_LEN = 128          # Max number of characters for par name

    buffer = {}                     # dictionary with with numpy arrays for main data as values and par name as key
    data_structure_format = []      # list with shape and dtypes of data structure
    data_structure = None           # np.recarray with structure of the buffers

    defaults = {'added': -1,
                'saved': 0,
                'sent': 0}         # defaults for some paramters

    def __init__(self, *args, **kwargs) -> None:
        """
        use kwargs to override maxpars or max dims if needed
        e.g. buff = SharedBuffer(MAX_PARS=10)
        """
        self.__dict__.update(kwargs)

        self._create_shared_np = create_shared_np
        self.data_structure_format = ([('parname', f'<U{self.MAX_PAR_NAME_LEN}'), 
                              ('added', 'i8'), ('saved', 'i8'), ('network', 'i8'),
                              ('type', '<S1024'),] 
                              + [(f'dim{i}', 'i8') for i in range(self.MAX_DIMS)]
                              )
        self._create_data_structure()
        self.check_new()            # link to existing if any

    def add_parameter(self, parname, dtype, *shape):
        """
        add parameter to shared memory

        NOTE: dont forget to call check new in other processes to link to
              the new shared parameter
        """
        dtype = pickle.dumps(dtype)
        shape = shape + ((0,) * (self.MAX_DIMS - len(shape)))  # pad shape with zeros

        idx_new_par = self.data_structure.index.index('')
        self.data_structure.array[idx_new_par] = (parname, self.defaults['added'], self.defaults['saved'], self.defaults['sent'], 
                                                  dtype, *shape)
        self.data_structure.index[idx_new_par] = parname
        self.data_structure.create_index_loopup()
        self._make_buffer(parname, dtype, shape)
    
    def remove_parameter(self, parameter):
        """
        removes parameter
        """
        if parameter in self.buffer:
            self.buffer[parameter]._shm.unlink()
            self.buffer[parameter]._shm.close()
            del self.buffer[parameter]

            self.data_structure.clear(index=parameter)

            idx = self.data_structure.index.index(parameter)
            self.data_structure.index[idx] = ''
    
    def clear_parameter(self, parameter, fill=None):
        """
        empties parameter and sets counter to 0
        """
        self.data_structure.set(self.defaults['added'], 'added', parameter)
        self.data_structure.set(self.defaults['saved'], 'saved', parameter)
        self.buffer[parameter][:] = np.empty(self.buffer[parameter].shape,
                                             dtype=self.buffer[parameter].dtype)
        if fill is not None:
            self.buffer[parameter].fill(fill)

    def check_new(self):
        """
        checks and return if new parameters added to the datastructure 
        """
        self.data_structure.load(self.data_structure.name)

        pars = set(self.buffer)
        new_pars = set(self.data_structure.get('parname', ...)) - pars
        new_pars.discard('')

        # make or link buffer for each new parameter
        for par in new_pars:
            dtype, *shape = self.data_structure.get(
                ['type'] + [i for i in self.data_structure.dtype 
                                        if i.startswith('dim')], 
                par)
            shape = shape[:shape.index(0)]                                      # remove dims with 0
            self._make_buffer(par, dtype, shape)

        return new_pars
    
    def get_buf(self,  par, 
                start=None, end=None, subpar=..., n_items=None,
                decimated_out_len=None):
        """
        get data slice from buffer,
        concatenate if end is lower than start -> circular buffer

        - par: parameter to get
        - start: start of data block, if not defined, the last saved position will be chosen
        - end: end of the data block, if not defined the last added position will be chosen
        - n_items: if defined: number items back to get from end
        - decimated_out_len: desired length of output (achieved by decimation)
        """
        if start is None: start = self.data_structure.get('saved', par)
        if end is None: end = self.data_structure.get('added', par)

        end += 1

        if n_items is not None:
            start = (end - n_items)
        
        size = self.buffer[par][subpar].shape[0]
        start %= size  # rotate over total length for circular buffer
        end %= size

        # DECMIMATE (if needed)
        step = 1
        if decimated_out_len is not None:
            n_items = ((end - start) % size)
            if n_items > decimated_out_len:
                step = n_items // decimated_out_len
        
        # return empty array with same structure when requesting 0 items
        if n_items == 0:
            return self.buffer[par][subpar][0:0]

        # return as much as possible if start and end are the same
        if (start == end):
            # log(f"{par}: start idx {start} == end idx {end},"
            #     "returning as much as possible", "warning")
            # TODO: check why this happens so often
            start += 1

        if start < end:
            return self.buffer[par][subpar][start:end:step]
        
        elif start > end:
            remaining = (size - start) % step               # remaining to adjust start of seconds part: e.g. if first part is 3 long and step is 2 we need to start at pos 1 instead of 0
            return np.concatenate(
                (self.buffer[par][subpar][start::step],
                 self.buffer[par][subpar][remaining:end:step]))
    
    def get_time_back(self, par, seconds_back, 
                      time_sub_par="time", 
                      subpar=...,
                      decimated_out_len=None):
        """
        get x secondsback from end
        - par: parameter where time is / par to return
        - time_sub_par: optional if time is a subpar from par e.g. par is data and time is within data
        - sub_par: sub parameter to return
        - seconds_back: time window to return from end in seconds
        - decimated_out_len: desired length of output (achieved by decimation)



        """
        end_idx = self.data_structure.get('added', par)            # index of last recorded data
        if end_idx == -1:                                          # no data added yet
            log('No data in buffer (yet?)', "debug")
            return

        end_time = self.buffer[par][time_sub_par][end_idx]          # time of last recorded data
        start_time = end_time - seconds_back                        # time of first timepoint
            
        # find start time idx:
        if start_time < self.buffer[par][time_sub_par][0]:
            # buffer has looped or not enough data recorded yet
            if start_time > self.buffer[par][time_sub_par][-1]:
                # there is not enough data recorded yet to cover full secondsback
                start_idx = 0   # limit to first position in buffer

            else:
                # end index looped in circular buffer search for start after loop
                start_idx = bisect_left(self.buffer[par][time_sub_par], 
                                        start_time, lo=end_idx)
        else:
            start_idx = bisect_left(self.buffer[par][time_sub_par], 
                                    start_time, hi=end_idx) # index of first timepoint for plot
        
        if start_idx == end_idx:
            log(f'Start {start_idx} and end {end_idx} of data have same index', 'warning')
            start_idx += 1         # return full buffer
            # return
        
        return self.get_buf(par=par, subpar=subpar, 
                            start=start_idx, end=end_idx,
                            decimated_out_len=decimated_out_len)

    
    def add_to_buf(self, par, data):
        """
        write data (block) to buffer
        NOTE: data should have same structure as buffer[par]
        """
        n_items = data.shape[0]
        
        start = self.data_structure.get('added', par) + 1
        end = start + n_items
        
        buff_size = self.data_structure.get('dim0', par)

        if end <= buff_size:
            self.buffer[par][start:end] = data

        else:
            # circular write
            mid = buff_size - start
            self.buffer[par][start:] = data[:buff_size - start]
            end %= buff_size
            self.buffer[par][:end] = data[mid:]
        
        self.data_structure.set(end, 'added', par)
    
    def add_1_to_buffer(self, par, data):
        """
        adds one value to the buffer (should be tuple with values for all columns if buffer is struct array)
        """              
        pos = ((self.data_structure.get('added', par) + 1) 
                    % self.data_structure.get('dim0', par))
        self.buffer[par][pos] = data
        self.data_structure.set(pos, 'added', par)


    def get_n_items(self, i1, i2, par):
        """
        calculates n items between iterator 1 and iterator 2
        (names of the iterators in data_structure)
        """
        return ((self.data_structure.get(i1, par) 
                 - self.data_structure.get(i2, par)) 
                % self.data_structure.get('dim0', par))

    def close_all(self):
        """
        closes this proceses links to shared memory blocks

        Warning trying to open data again will lead to segmentation fault 
        and dump core

        """
        for v in self.buffer.values():
            v._shm.close()
        self.buffer.clear()

    def unlink_all(self):
        """
        destroys data block

        """
        for v in self.buffer.values():
            try:
                v._shm.unlink()
            except FileNotFoundError:
                pass # already unlinked
    
    def reset(self, par=...):
        """
        reset and clear data structure
        - par:   only reset specific par (is index in data_structure)
        """
        self.data_structure.clear(index=par)
        self.data_structure.set(-1, 'added', par)


    def _create_data_structure(self):
        """
        Creates info list (or links to it if already existing)

        data_structure_format:  a iterable with dtypes of the data structure table
        """
        name=f'{self.name}_dat_struc'
        # create rec array for data structure
        self.data_structure = SharedTable()
        try:
            self.data_structure.load(name)
        
        except FileNotFoundError:
            self.data_structure.create(name, 
                                       self.data_structure_format, 
                                       (self.MAX_PARS,),
                                       index=[' ' * self.MAX_PAR_NAME_LEN] * self.MAX_PARS)
            # set index to empty:
            for i in range(len(self.data_structure.index)):
                self.data_structure.index[i] = ''

        
    def _make_buffer(self, parname, dtype, shape):
        if not parname:
            return
        shape = [i for i in shape if i != 0]
        dtype = pickle.loads(dtype)

        self.buffer[parname] = self._create_shared_np(f"{self.name}_{parname}", 
                                                                          shape, 
                                                                          dtype, 
                                                                          )

if __name__ == '__main__':
    '''
    testing
    run in 2 different terminals to test
    changing something in buff should change value in both
    '''

    b = SharedBuffer()

    if not b.data_structure.get('parname',0):
        # create new
        [b.add_parameter(f"test{i}", "i8", 50, ) for i in range(4)]
        b.add_parameter("time", "i8", 40, )
        b.add_parameter("notes", "S128", 40,)
        b.add_parameter("other", [('time', 'f8'), ('labels', 'S128')], 40,)
    
"""

NOTE: Strings should have S as dtype in buffer, otherwise saving h5 causes issues

    info array structure example:

                                0         1         2      3                    type:
        parname               |        |         |        |       |               str        Name of the parameter
        added                 |        |         |        |       |               int        iterator (location of last added data)      
        saved                 |        |         |        |       |               int        iterator (location of last saved data)  
        network               |        |         |        |       |               int        iterator (location of last sent/receveived(over network) data)  
        array type            |        |         |        |       |               str        array time (ndarray or recarray)
        dtype                 |        |         |        |       |               str        dtype(s) of array
        dim0                  |        |         |        |       |               int        size of dim 0
        dim1
        dim2
        dim3
        dim4

NOTES

load np.recarray from h5py with:
f = h5py.File(filename, 'r')
data = np.recarray(f['data'].shape, dtype=f['data'].dtype
data[:] = f['data']

"""