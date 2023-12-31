from pypdevs.infinity import INFINITY

class StateDict(dict):
    """
    generated by AI
    """
    def __getattr__(self, key):
        # If the key is present, return the corresponding value
        if key in self:
            return self[key]
        # Otherwise, raise an AttributeError
        raise AttributeError(f"'StateDict' object has no attribute '{key}'")

    def __setattr__(self, key, value):
        # Set the value for the given key
        self[key] = value

def getDistance(v, t) -> float:
    return v * t


def getVelocity(d, t) -> float:
    return d / t


def getTime(d, v) -> float:
    if v == 0.0:
        return INFINITY
    return d / v
