

class WindowList:
    def __init__(self, n):
        self.n = n
        self._list = []

    def append(self, new):
        if len(self._list) < self.n:
            self._list.append(new)
        else:
            self._list[0:-1] = self._list[1:]
            self._list[self.n-1] = new

    def clear(self):
        self._list = []

    def list(self):
        return self._list


