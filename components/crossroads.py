from pypdevs.DEVS import CoupledDEVS



from components.roadsegment import RoadSegment


class CrossRoadSegment(RoadSegment):
    def __init__(self, block_name, L, v_max, destinations):
        # Initialize the base class with the provided parameters
        super(CrossRoadSegment, self).__init__(block_name, L, v_max)

        self.destinations = destinations

        # Adding a new input port for 'car_in_cr'
        self.car_in_cr = self.addInPort("car_in_cr")

        # Adding a new output port for 'car_out_cr'
        self.car_out_cr = self.addOutPort("car_out_cr")

    def outputFnc(self):
        self.destruct[self.c] = "outputFnc";
        self.c += 1
        if self.state["send_ack"]:
            return {
                self.Q_sack: self.state["next_ack"]
            }

        if self.state["send_query"]:
            return {
                self.Q_send: self.state["next_query"]
            }

        if len(self.state["cars_present"]) > 0:
            return {
                self.car_out: self.state["cars_present"][0]
            }

        return {}



class CrossRoads(CoupledDEVS):
    def __init__(self, block_name: str, destinations: list, L: float, v_max: float, observ_delay: float):
        super(CrossRoads, self).__init__(block_name)

        self.destinations = destinations
        self.L: float = L
        self.v_max: float = v_max
        self.observ_delay: float = observ_delay

        # input ports
        self.car_in = self.addInPort("car_in")
        self.Q_recv = self.addInPort("Q_recv")
        self.Q_rack = self.addInPort("Q_rack")

        # output ports
        self.car_out = self.addOutPort("car_out")
        self.Q_send = self.addOutPort("Q_send")
        self.Q_sack = self.addOutPort("Q_sack")
    def timeAdvance(self):
        pass

    def outputFnc(self):
        pass

    def intTransition(self):
        pass

    def extTransition(self, inputs):
        pass
