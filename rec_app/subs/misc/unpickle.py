import pickle

def unpickle(data):
    """
    this function checks if data is pickled and returns unpickled data
    if data is not pickled the data is returned as is

    Pickled data usually starts with b'\x80\x03' or b'\x80\x04' if using python 3.8
    """
    if isinstance(data, bytes):
        if data[0:2] in {b'\x80\x03', b'\x80\x04'}:
            data = pickle.loads(data)
    return data
