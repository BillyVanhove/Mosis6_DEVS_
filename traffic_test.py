
from pypdevs.DEVS import AtomicDEVS, CoupledDEVS
from components.generator import Generator
from components.roadsegment import RoadSegment
from components.collector import Collector
from tests.helpers import PingPong

class Traffic(CoupledDEVS):
    def __init__(self, name):
        super(Traffic, self).__init__(name)

        # (self, block_name: str, IAT_min: float, IAT_max: float, v_pref_mu: float, v_pref_sigma: float, destinations: list, limit: int):
        # self.gen = self.addSubModel(Generator("gen", 1, 2, 8, 2, ["Temse", "Antwerpen", "Sint-Niklaas", "Borgerokko", "Doel"], 5))
        self.gen = self.addSubModel(Generator("gen", 2, 2, 8, 0, ["Temse", "Antwerpen", "Sint-Niklaas", "Borgerokko", "Doel"], 5))

        # (self, block_name: str, v_max: float)
        self.road = self.addSubModel(RoadSegment("road1", 10))

        # (self, block_name)
        self.col = self.addSubModel(Collector("col"))

        self.connectPorts(self.gen.car_out, self.road.car_in)
        self.connectPorts(self.gen.Q_send, self.road.Q_recv)
        self.connectPorts(self.road.Q_sack, self.gen.Q_rack)

        self.connectPorts(self.road.car_out, self.col.car_in)


class TrafficPingPongTest(CoupledDEVS):
    def __init__(self, name):
        super(TrafficPingPongTest, self).__init__(name)


if __name__ == "__main__":
    from pypdevs.simulator import Simulator

    model = Traffic("traffic")
    sim = Simulator(model)
    sim.setClassicDEVS()
    sim.setTerminationTime(5)
    sim.setVerbose(None)
    sim.simulate()