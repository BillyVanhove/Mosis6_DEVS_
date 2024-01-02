from pypdevs.DEVS import CoupledDEVS
from components.messages import *
from components.generator import Generator
from components.roadsegment import RoadSegment
from components.fork import Fork
from components.gasstation import GasStation
from components.sidemarker import SideMarker
from components.collector import Collector


class RoadStretch(CoupledDEVS):
    def __init__(self, block_name: str, number_of_RS_left: int, number_of_RS_right: int, number_of_cars_to_generate: int):
        super(RoadStretch, self).__init__(block_name)

        self.rs_left: int = max(number_of_RS_left, 1)
        self.rs_right: int = max(number_of_RS_right, 1)
        self.nr_cars: int = max(number_of_cars_to_generate, 1)

        self.RS_LENGTH = 20
        self.RS_V_MAX = 15
        self.OBSERV_DELAY = 0.0
        self.FORK_V_MAX = 15

        self.generator = self.addSubModel(
            Generator("generator", 5, 5, 12, 1, ["Temse", "Antwerpen", "Sint-Niklaas", "Doel", "Gent"], self.nr_cars))

        self.fork = self.addSubModel(Fork("fork", L=self.RS_LENGTH, v_max=self.FORK_V_MAX))
        self.gas_station = self.addSubModel(GasStation("gas_station", observ_delay=self.OBSERV_DELAY))
        self.sidemarker = self.addSubModel(SideMarker("sidemarker"))
        self.collector = self.addSubModel(Collector("collector"))

        prev = self.generator
        for i in range(self.rs_left):
            rs = self.addSubModel(RoadSegment("rs_left_"+str(i), L=self.RS_LENGTH, v_max=self.RS_V_MAX))

            # link prev with current
            self.connectPorts(prev.car_out, rs.car_in)
            self.connectPorts(prev.Q_send, rs.Q_recv)
            self.connectPorts(rs.Q_sack, prev.Q_rack)

            prev = rs

        # link prev to fork
        self.connectPorts(prev.car_out, self.fork.car_in)
        self.connectPorts(prev.Q_send, self.fork.Q_recv)
        self.connectPorts(self.fork.Q_sack, prev.Q_rack)

        # make 3 'top' road segments
        self.top_rs_1 = self.addSubModel(RoadSegment("top_rs_1", L=self.RS_LENGTH, v_max=self.RS_V_MAX))
        self.top_rs_2 = self.addSubModel(RoadSegment("top_rs_2", L=self.RS_LENGTH, v_max=self.RS_V_MAX))
        self.top_rs_3 = self.addSubModel(RoadSegment("top_rs_3", L=self.RS_LENGTH, v_max=self.RS_V_MAX, priority=True))

        # make 2 'bottom' road segments
        self.bottom_rs_1 = self.addSubModel(RoadSegment("bottom_rs_1", L=self.RS_LENGTH, v_max=self.RS_V_MAX))
        self.bottom_rs_2 = self.addSubModel(RoadSegment("bottom_rs_2", L=self.RS_LENGTH, v_max=self.RS_V_MAX))

        # link fork with the top_rs_1 road segment
        self.connectPorts(self.fork.car_out, self.top_rs_1.car_in)
        self.connectPorts(self.fork.Q_send, self.top_rs_1.Q_recv)
        self.connectPorts(self.top_rs_1.Q_sack, self.fork.Q_rack)

        # link top_rs_1 with top_rs_2
        self.connectPorts(self.top_rs_1.car_out, self.top_rs_2.car_in)
        self.connectPorts(self.top_rs_1.Q_send, self.top_rs_2.Q_recv)
        self.connectPorts(self.top_rs_2.Q_sack, self.top_rs_1.Q_rack)

        # link top_rs_2 with top_rs_3
        self.connectPorts(self.top_rs_2.car_out, self.top_rs_3.car_in)
        self.connectPorts(self.top_rs_2.Q_send, self.top_rs_3.Q_recv)
        self.connectPorts(self.top_rs_3.Q_sack, self.top_rs_2.Q_rack)

        # link fork with the bottom_rs_1 road segment
        self.connectPorts(self.fork.car_out2, self.bottom_rs_1.car_in)
        self.connectPorts(self.fork.Q_send, self.bottom_rs_1.Q_recv)
        self.connectPorts(self.bottom_rs_1.Q_sack, self.fork.Q_rack)

        # link bottom_rs_1 with gas_station
        self.connectPorts(self.bottom_rs_1.car_out, self.gas_station.car_in)

        # link gas_station with bottom_rs_2
        self.connectPorts(self.gas_station.car_out, self.bottom_rs_2.car_in)
        self.connectPorts(self.gas_station.Q_send, self.bottom_rs_2.Q_recv)
        self.connectPorts(self.bottom_rs_2.Q_sack, self.gas_station.Q_rack)

        # integrate sidemarker
        self.connectPorts(self.top_rs_3.Q_sack, self.sidemarker.mi)
        self.connectPorts(self.sidemarker.mo, self.bottom_rs_2.Q_rack)

        # link bottom with top
        self.connectPorts(self.bottom_rs_2.Q_send, self.top_rs_3.Q_recv)

        prev = [self.top_rs_3, self.bottom_rs_2]
        for i in range(self.rs_left):
            rs = self.addSubModel(RoadSegment("rs_right_"+str(i), L=self.RS_LENGTH, v_max=self.RS_V_MAX))

            if i == 0:
                # link both the top and bottom with the first segment
                for p in prev:
                    self.connectPorts(p.car_out, rs.car_in)
                    self.connectPorts(p.Q_send, rs.Q_recv)
                    self.connectPorts(rs.Q_sack, p.Q_rack)

            else:
                # link prev with current
                self.connectPorts(prev.car_out, rs.car_in)
                self.connectPorts(prev.Q_send, rs.Q_recv)
                self.connectPorts(rs.Q_sack, prev.Q_rack)

            prev = rs

        # link the last road segment with collector
        self.connectPorts(prev.car_out, self.collector.car_in)

if __name__ == "__main__":
    from pypdevs.simulator import Simulator

    model = RoadStretch("road_stretch", number_of_RS_left=2, number_of_RS_right=3, number_of_cars_to_generate=20)

    sim = Simulator(model)
    sim.setClassicDEVS()
    sim.setTerminationTime(1500)
    sim.setVerbose(None)
    sim.simulate()
