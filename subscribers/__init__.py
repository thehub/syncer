import os, imp
__all__ = []

all_mods = [mod.replace('.py', '') for mod in os.listdir(__path__[0]) if mod.endswith('.py') and  mod[0] is not '_']
for mod in all_mods:
    globals()[mod] = imp.load_module("subscribers.%s" % mod, *imp.find_module("subscribers/" + mod ))
    print "Subscriber found: %s" % mod
    __all__.append(mod)
