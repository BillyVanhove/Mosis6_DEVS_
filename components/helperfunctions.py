from pypdevs.infinity import INFINITY

def getDistance(v, t) -> float:
    return v * t


def getVelocity(d, t) -> float:
    return d / t


def getTime(d, v) -> float:
    if v == 0.0:
        return INFINITY
    return d / v
