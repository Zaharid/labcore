class CallableClass(object):
    def __init__(self, s):
        self.s = s
    
    def make_callable(self, caller):
        def f_factory(s, caller):
            def f():
                print "%s %s" %(caller, s)
            return f
        return f_factory(self.s, caller)
        
class Caller(object):
    def __init__(self, s):
        self.obj = CallableClass(s)
        setattr(self, "c",self.obj.make_callable(self))
        
mycaller = Caller("s")
mycaller.c()
mycaller.obj.s = "new s"

mycaller.c()