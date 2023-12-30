from pypdevs.DEVS import AtomicDEVS
from components.messages import *
from components.helperfunctions import StateDict


class Collector(AtomicDEVS):
    def __init__(self, block_name):
        super(Collector, self).__init__(block_name)

        self.state: StateDict = StateDict({
            "total_time": 0.0,
            "n": 0,
            "time": 0.0
        })

        self.car_in = self.addInPort("car_in")

    def extTransition(self, inputs):
        self.state["time"] += self.elapsed
        if self.car_in in inputs:
            car: Car = inputs[self.car_in]
            self.state["n"] += 1
            self.state["total_time"] += self.state["time"] - car.departure_time
        return self.state
