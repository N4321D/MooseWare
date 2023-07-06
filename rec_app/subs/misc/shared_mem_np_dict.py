from multiprocessing import shared_memory
import queue
import numpy as np

from queue import Empty

def clear_queue(q):
    """
    clears multiprocessing queue
    """
    try:
        while True:
            q.get_nowait()
    except Empty:
        pass

class NpArrayWithShm(np.ndarray):
    _shm = None

def create_shared_np(name, shape, dtype, fill=None):
    """
    create or link to exisiting shared data array
    shm item is saved as array._shm

    - name:         name for shared buffer
    - shape:        shape of array as list/tuple: (dim0, dim1, ...)

    - dtype:        dtype for array, for structured array, dtypes should be 
                    [('key', 'dtype'), ('key', 'dtype')] or np.dtype
                    e.g. [('keys', 'U8'), ('data', 'f8'))]
    - fill:         fill array with value
    """
    dtype = np.dtype(dtype)
    nbytes = np.prod(shape) * dtype.itemsize

    if isinstance(name, bytes):
        name = name.decode()

    name = name.replace('/', "_")

    new = False

    try:
        # link to existing buffer
        shm = shared_memory.SharedMemory(name=name)

    except FileNotFoundError:
        shm = shared_memory.SharedMemory(create=True, 
                                            name=name, 
                                            size=int(nbytes),)
        new = True
    shared_array = NpArrayWithShm(shape,
                                  dtype=dtype, 
                                  buffer=shm.buf)
    if new:        
        if fill is None:
            pass
        
        elif fill == 0:
            # this method also sets str arrays to ''
            shared_array[:] = np.zeros(shared_array.shape, 
                                    dtype=shared_array.dtype)

        else:
            shared_array.fill(fill)

    shared_array._shm = shm

    return shared_array


class SharedTable():
    """
    Creates a shared table (or dictionary) like numpy array
    data can be retrieved with column and index name
    if index is not passed index will be (0 - n)

    - create:    create new, name must be unique
    - from_dict: create new from template dictionary
    """
    name = 'shared_np_dict'
    array = None                        # np array with data
    
    index_lookup = {}                   # lookup dictionary with index: row number
    
    index = []                       # shared list wiht index names
    dtype = []                     # shared list with dtypes
    shape = []                     # shared list with shape
    
    shms = {'index': None,
            'array': None,
            'shape': None,
            'dtype': None,}

    def __init__(self) -> None:
        pass
    
    def create(self, name, columns, shape, index=[]):
        """
        create shared dataframe like object
        - columns:     [('column_name', 'dtype'), ...] for all pars
        - index:       optional: names of rows for 2d lookup by parname
        """
        self.name = name
        self.array = create_shared_np(name, shape, 
                                      dtype=columns)
        self.shms['array'] = self.array._shm
       
        if not self.shape:
            self.create_shape_list(shape)
        if not self.dtype:
            self.create_dtype_list(columns)

        if not self.index:
            self.create_index_list(index)
        
        self.create_index_loopup()
    
    def from_dict(self, name, dic, index=[]):
        """
        create shared dictionary from dict
        """
        self.name = name
        dtypes = []
        shape = [1, ]
        for k, v in dic.items():
            if hasattr(v, "__iter__"):
                shape[0] = max(len(v), shape[0])
                dtypes.append((k, np.dtype(type(v[0]))))
            else:
                dtypes.append((k, np.dtype(type(v))))
        
        self.create(self.name, columns=dtypes, shape=shape, index=index)

        # copy data to array
        for k, v in dic.items():
            self.array[k] = v

    def load(self, name):
        """
        load existing shared table from memory
        by name of shared mem object
        
        to update: run this with self.name as name
        """
        self.name = name
        self.create_shape_list()
        self.create_dtype_list()
        self.create_index_list()
        dts = list(self.dtype)
        dtypes = list(zip(dts[::2], dts[1::2]))
        self.create(name, dtypes, list(self.shape), list(self.index))
        self.create_index_loopup()

    def get(self, par, index=...):
        """
        par:        parameter to get use ... for all pars (e.g. for specific index point)
        index:      index name or position to get, use ... for everything in that column
        """
        if par is None: par = ...                                # replace None with elipsis for indexing
        index = self.index_lookup.get(index, index)
        if isinstance(index, str):
            # lookup failed
            return
        return self.array[par][index]
            
    
    def set(self, value, par, index=...):
        """
        value:   value to save (use tuple for multiple, not list -> crash)
        par:     parameter to save value to, use ...f or all pars (e.g. for specific index point)
        index:   index name or position to save to, use ... for everything in that column (e.g. when saving a list)
        """
        if par is None: par = ...                                # replace None with elipsis for indexing
        index = self.index_lookup.get(index, index)
        self.array[par][index] = value

    def create_shape_list(self, shape=[]):
        name = f'{self.name}_shape'
        if not shape:
            # load existing
            self.shape = (shared_memory
                                .ShareableList(name=name))
        else:
            # create new
            try:
                # close existing items in memory
                shared_memory.ShareableList(name=name).shm.unlink()
            except FileNotFoundError:
                pass
            self.shape = (shared_memory
                            .ShareableList(shape, name=name))
        self.shms['shape'] = self.shape.shm

    def create_dtype_list(self, dtypes=[]):
        name = f'{self.name}_dtypes'
        if not dtypes:
            # load existing
            self.dtype = (shared_memory
                            .ShareableList(name=name))
        else:
            # create new
            try:
                # close if any still open items in memory 
                shared_memory.ShareableList(name=name).shm.unlink()
            except FileNotFoundError:
                pass

            _dt = []
            [_dt.extend((name, str(dtype))) for name, dtype in dtypes]
            self.dtype = (shared_memory
                          .ShareableList(_dt, name=name))
        self.shms['dtype'] = self.dtype.shm
    
    def create_index_list(self, index=[]):
        name = f'{self.name}_index'
        if not index:
            # load 
            try:
                self.index = (shared_memory
                                .ShareableList(name=name))    
            except FileNotFoundError:
                # no index defined
                pass
        else:
            # create new
            try:
                shared_memory.ShareableList(name=name).shm.unlink()
            except FileNotFoundError:
                pass
            self.index = (shared_memory
                            .ShareableList(index, name=name))

        self.shms['index'] = self.index.shm if hasattr(self.index, 'shm') else None
    
    def create_index_loopup(self):
        """
        creates or updates the index loopup table
        run if new pars are added
        """
        self.index_lookup = {name: i for i, name in enumerate(self.index)}
        
        self.parameters = set(self.index_lookup.keys()) - {""}

    def clear(self, par=..., index=...):
        """
        empties data for parameter, parameter keeps existing
        """
        old_data = self.get(par, index)
        shape, dtype = (old_data.shape or (1, ), old_data.dtype)
        self.set(np.zeros(shape, dtype=dtype), par, index)

    def close(self):
        for shm in self.shms.values():
            try:
                shm.close()
            except FileNotFoundError:
                pass
    
    def unlink(self):
        for shm in self.shms.values():
            try:
                shm.unlink()
            except FileNotFoundError:
                pass


# TODO: creating a dictionary to refer to np arrays faster than struct array for getting and setting? (also maybe for buffer.py in recording?)
#       can even update self.__dict__ to add pars as class variables. Use lookup = {i: data[i,...] or data[i] for i in range(data.size) or data.dtype.names}


from multiprocessing import Queue
# Testing
if __name__ == "__main__":
    tbl = SharedTable()
    try:
        tbl.from_dict("test", {str(i): [i, i ** 2] for i in range(10)}, index=["normal", "sqrd"])
        
        tbl.set(888, '2', 'normal')
    except FileExistsError:
        tbl.load('test')

    print(tbl.get('2', 'normal'))