from pypdevs.DEVS import CoupledDEVS
from components.messages import *
from components.helperfunctions import getTime
from components.roadsegment import RoadSegment
from components.generator import Generator
from components.collector import Collector
from components.crossroads import CrossRoadSegment, CrossRoads

class Crossing(CoupledDEVS):
    def __init__(self, block_name: str, mode: int = 0):
        super(Crossing, self).__init__(block_name)

        self.nr_cars = 0
        self.RS_LENGTH = 20
        self.RS_V_MAX = 15
        self.destinations = ["N", "E", "S", "W"]
        self.mode = mode

        self.generator1 = self.addSubModel(
            Generator("generator_N", 5, 7, 12, 1, self.destinations, self.nr_cars+1))

        self.generator2 = self.addSubModel(
            Generator("generator_E", 4, 8, 14, 0, self.destinations, self.nr_cars+1))

        self.generator3 = self.addSubModel(
            Generator("generator_S", 5, 6, 12, 1, self.destinations, self.nr_cars))

        self.generator4 = self.addSubModel(
            Generator("generator_W", 6, 8, 12, 1, self.destinations, self.nr_cars))

        generator_list = [self.generator1, self.generator2, self.generator3, self.generator4]

        self.collector1 = self.addSubModel(Collector("collector_N"))
        self.collector2 = self.addSubModel(Collector("collector_E"))
        self.collector3 = self.addSubModel(Collector("collector_S"))
        self.collector4 = self.addSubModel(Collector("collector_W"))

        collector_list = [self.collector1, self.collector2, self.collector3, self.collector4]

        self.cross_road = self.addSubModel(CrossRoads("cross_road", self.RS_LENGTH, self.RS_V_MAX, self.destinations, mode=self.mode))

        previous = []
        for gen in generator_list:
            prev = gen
            for i in range(3):
                rs = self.addSubModel(RoadSegment("rs_" + gen.name + "_" + str(i), L=self.RS_LENGTH, v_max=self.RS_V_MAX))

                # link prev with current
                self.connectPorts(prev.car_out, rs.car_in)
                self.connectPorts(prev.Q_send, rs.Q_recv)
                self.connectPorts(rs.Q_sack, prev.Q_rack)

                prev = rs

            previous.append(prev)

        # connect rs with north
        # print(previous[0].car_out.type(), self.cross_road.car_in_N.type())
        self.connectPorts(previous[0].car_out, self.cross_road.car_in_N)
        self.connectPorts(previous[0].Q_send, self.cross_road.Q_recv_N)
        self.connectPorts(self.cross_road.Q_sack_N, previous[0].Q_rack)

        # connect rs with east
        self.connectPorts(previous[1].car_out, self.cross_road.car_in_E)
        self.connectPorts(previous[1].Q_send, self.cross_road.Q_recv_E)
        self.connectPorts(self.cross_road.Q_sack_E, previous[1].Q_rack)

        # connect rs with south
        self.connectPorts(previous[2].car_out, self.cross_road.car_in_S)
        self.connectPorts(previous[2].Q_send, self.cross_road.Q_recv_S)
        self.connectPorts(self.cross_road.Q_sack_S, previous[2].Q_rack)

        # connect rs with west
        self.connectPorts(previous[3].car_out, self.cross_road.car_in_W)
        self.connectPorts(previous[3].Q_send, self.cross_road.Q_recv_W)
        self.connectPorts(self.cross_road.Q_sack_W, previous[3].Q_rack)

        rs_list = [self.addSubModel(RoadSegment("rs_" + col.name + "_" + str(0), L=self.RS_LENGTH, v_max=self.RS_V_MAX)) for col in collector_list]

        # connect north with rs
        self.connectPorts(self.cross_road.car_out_N, rs_list[0].car_in)
        self.connectPorts(self.cross_road.Q_send_N, rs_list[0].Q_recv)
        self.connectPorts(rs_list[0].Q_sack, self.cross_road.Q_rack_N)

        # connect east with rs
        self.connectPorts(self.cross_road.car_out_E, rs_list[1].car_in)
        self.connectPorts(self.cross_road.Q_send_E, rs_list[1].Q_recv)
        self.connectPorts(rs_list[1].Q_sack, self.cross_road.Q_rack_E)

        # connect south with rs
        self.connectPorts(self.cross_road.car_out_S, rs_list[2].car_in)
        self.connectPorts(self.cross_road.Q_send_S, rs_list[2].Q_recv)
        self.connectPorts(rs_list[2].Q_sack, self.cross_road.Q_rack_S)

        # connect west with rs
        self.connectPorts(self.cross_road.car_out_W, rs_list[3].car_in)
        self.connectPorts(self.cross_road.Q_send_W, rs_list[3].Q_recv)
        self.connectPorts(rs_list[3].Q_sack, self.cross_road.Q_rack_W)


        for r in range(len(rs_list)):
            prev = rs_list[r]
            col = collector_list[r]
            for i in range(2):
                rs = self.addSubModel(
                    RoadSegment("rs_" + col.name + "_" + str(i), L=self.RS_LENGTH, v_max=self.RS_V_MAX))

                # connect the road segments
                self.connectPorts(prev.car_out, rs.car_in)
                self.connectPorts(prev.Q_send, rs.Q_recv)
                self.connectPorts(rs.Q_sack, prev.Q_rack)

                prev = rs

            # link the last road segment with collector
            self.connectPorts(prev.car_out, col.car_in)



if __name__ == "__main__":
    from pypdevs.simulator import Simulator

    model = Crossing("crossing", mode=1)

    sim = Simulator(model)
    sim.setClassicDEVS()
    sim.setTerminationTime(5000)
    sim.setVerbose(None)
    sim.simulate()