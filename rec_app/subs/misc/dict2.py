class Dict2(dict):
    """
    dictionary with deep_get function to
    use get in nested dictionaries

    usage:
    Dict2().deep_get("key1", "key2", ..., default=8, full_depth=True)

    for more info see Dict2.deep_get method doc
    """

    def deep_get(self, *args, default=None, full_depth=True):
        """
        default: what is returned if keys are not found
    
        full_depth: True: go through all keys in args and returns
                          default if last key is not found.
                    False: return the values from the last key
                           in args that had data. This is useful 
                           if not all nested dict have the same depth.
        """
        _empty_dict = {}
        out = self

        for key in args:
            if not isinstance(out, dict):
                if full_depth:
                    out = _empty_dict
                break
            out = out.get(key, _empty_dict)

        return out if out is not _empty_dict else default

    
    def deep_set(self, val, *keys, default={}):
        # DOES NOT WORK!!!

        """
        This method 'deep sets' args as keys.
        This is useful to create nested within nested dicts 
        based on a list of keys

        val:     value to set

        keys:    list of keys from undeep to deep

        default: is set whenever key is not found
        """
        _d = [self]

        for key in keys:
            _d[-1].setdefault(key, default)
            _d.append(_d[-1][key])
        _d[-2][key] =  val
