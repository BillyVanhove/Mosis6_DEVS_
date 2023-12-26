
from pypdevs.DEVS import AtomicDEVS, CoupledDEVS
from components.generator import Generator
from components.roadsegment import RoadSegment
from components.collector import Collector
from components.gasstation import GasStation
from tests.helpers import PingPong

class Traffic(CoupledDEVS):
    def __init__(self, name):
        super(Traffic, self).__init__(name)

        # (self, block_name: str, IAT_min: float, IAT_max: float, v_pref_mu: float, v_pref_sigma: float, destinations: list, limit: int):
        # self.gen = self.addSubModel(Generator("gen", 1, 2, 8, 2, ["Temse", "Antwerpen", "Sint-Niklaas", "Borgerokko", "Doel"], 5))
        self.gen = self.addSubModel(Generator("gen", 2, 2, 8, 0, ["Temse", "Antwerpen", "Sint-Niklaas", "Borgerokko", "Doel"], 5))

        # (self, block_name: str, L: float, v_max: float)
        self.road = self.addSubModel(RoadSegment("road1", 20, 10))

        # (self, block_name)
        self.col = self.addSubModel(Collector("col"))

        self.connectPorts(self.gen.car_out, self.road.car_in)
        self.connectPorts(self.gen.Q_send, self.road.Q_recv)
        self.connectPorts(self.road.Q_sack, self.gen.Q_rack)

        self.connectPorts(self.road.car_out, self.col.car_in)


class TrafficMultipleRoads(CoupledDEVS):
    def __init__(self, name):
        super(TrafficMultipleRoads, self).__init__(name)

        self.gen = self.addSubModel(
            Generator("gen", 2, 2, 8, 0, ["Temse", "Antwerpen", "Sint-Niklaas", "Borgerokko", "Doel"], 5))

        self.road1 = self.addSubModel(RoadSegment("road1", 20, 10))
        self.road2 = self.addSubModel(RoadSegment("road2", 20, 10))

        self.col = self.addSubModel(Collector("col"))

        # gen to road1
        self.connectPorts(self.gen.car_out, self.road1.car_in)
        self.connectPorts(self.gen.Q_send, self.road1.Q_recv)
        self.connectPorts(self.road1.Q_sack, self.gen.Q_rack)

        # road1 to road2
        self.connectPorts(self.road1.car_out, self.road2.car_in)
        self.connectPorts(self.road1.Q_send, self.road2.Q_recv)
        self.connectPorts(self.road2.Q_sack, self.road1.Q_rack)

        # road2 to col
        self.connectPorts(self.road2.car_out, self.col.car_in)


class TrafficWithGasStation(CoupledDEVS):
    def __init__(self, name):
        super(TrafficWithGasStation, self).__init__(name)

        self.gen = self.addSubModel(
            Generator("gen", 2, 2, 8, 0, ["Temse", "Antwerpen", "Sint-Niklaas", "Borgerokko", "Doel"], 1))

        self.road = self.addSubModel(RoadSegment("road1", 20, 10))

        self.gasstation = self.addSubModel(GasStation("gas"))

        self.col = self.addSubModel(Collector("col"))

        # gen to road
        self.connectPorts(self.gen.car_out, self.road.car_in)
        self.connectPorts(self.gen.Q_send, self.road.Q_recv)
        self.connectPorts(self.road.Q_sack, self.gen.Q_rack)

        # road to gas
        self.connectPorts(self.road.car_out, self.gasstation.car_in)

        # gas to col
        self.connectPorts(self.gasstation.car_out, self.col.car_in)


if __name__ == "__main__":
    from pypdevs.simulator import Simulator

    # model = Traffic("traffic")
    # model = TrafficMultipleRoads("traffic2")
    model = TrafficWithGasStation("traffic_with_gasstation")
    sim = Simulator(model)
    sim.setClassicDEVS()
    sim.setTerminationTime(600)
    sim.setVerbose(None)
    sim.simulate()