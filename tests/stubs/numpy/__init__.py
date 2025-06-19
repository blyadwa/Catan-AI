import random as _random

class _Random:
    def permutation(self, seq):
        seq = list(seq)
        _random.shuffle(seq)
        return seq

    def randint(self, low, high=None):
        if high is None:
            high = low
            low = 0
        # numpy randint is [low, high)
        return _random.randint(low, high - 1)

    def choice(self, seq):
        return _random.choice(seq)

random = _Random()
