"""
Place mainly for making newer Python features available for older versions.
"""

class partial(object):
    def __init__(self, func, *args, **kw):
        self.func = func
        self.args = args
        self.kw = kw
    def __call__(self, *args, **kw):
        args = self.args + args
        self.kw.update(kw)
        return self.func(*args, **self.kw)

def sha1(s):
    import sha
    return sha.new(s)

if __name__ == "__main__":

    def f(a, b, c):
        return a, b, c
    
    fa = partial(f, 1)
    
    assert fa(2, 3) == (1, 2, 3)
    assert fa('x', 3) == (1, 'x', 3)

    h = sha1("test")
    h.update("Nobody inspects the spammish repetition")
    assert h.hexdigest() == 'c4a52ec2c4ee72a9add0cec6742a452b39811a1a'
