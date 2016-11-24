
class AttrWatcher(object):
    def __init__(self, Module):
        self._self_module = Module
        self._accessed_attrs = set()
    def __getattr__(self, attr):
        if attr.startswith("__") or attr in {"_self_module", "_accessed_attrs"}:
            return super(AttrWatcher, self).__getattr__(attr)
        Rtn = getattr(self._self_module, attr)
        if attr not in self._accessed_attrs:
            self._accessed_attrs.add(attr)
            print "ACCESSED %s.%s" % (self._self_module.__name__, attr)
        return Rtn
    def __setattr__(self, attr, value):
        if attr.startswith("__") or attr in {"_self_module", "_accessed_attrs"}:
            super(AttrWatcher, self).__setattr__(attr, value)
            return
        Rtn = setattr(self._self_module, attr, value)
        if attr not in self._accessed_attrs:
            self._accessed_attrs.add(attr)
            print "ACCESSED %s.%s" % (self._self_module.__name__, attr)
        return Rtn
    def __hasattr__(self, attr):
        if super(AttrWatcher, self).__hasattr__(attr):
            return True
        return hasattr(self._self_module, attr)
def RequireAttr(Module, k):
    if hasattr(Module, k):
        return True
    raw_input("%s does not have Attribute: %s"%(Module.__name__, k))
    return False
