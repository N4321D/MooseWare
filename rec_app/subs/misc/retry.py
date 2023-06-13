"""
retry function until it worked


"""

def retry(f:callable,
          args,
          kwargs,
          exceptions={}):

    for args, kwargs in zip(args, kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            error_f = exceptions.get(type(e), None)
            if error_f is None:
                continue
            else:
                error_f(*args, **kwargs)