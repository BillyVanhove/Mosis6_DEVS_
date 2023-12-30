from pypdevs.DEVS import CoupledDEVS
from components.messages import *
from components.helperfunctions import getTime
from components.roadsegment import RoadSegment


class CrossRoadSegment(RoadSegment):
    def __init__(self, block_name: str, L: float, v_max: float, destinations: list, observ_delay: float = None):
        # Initialize the base class with the provided parameters
        if observ_delay is None:
            super(CrossRoadSegment, self).__init__(block_name, L, v_max)
        else:
            super(CrossRoadSegment, self).__init__(block_name, L, v_max, observ_delay=observ_delay)

        self.destinations = destinations

        # Adding a new input port for 'car_in_cr'
        self.car_in_cr = self.addInPort("car_in_cr")

        # Adding a new output port for 'car_out_cr'
        self.car_out_cr = self.addOutPort("car_out_cr")

    def car_enter(self, car: Car, intern: bool = None) -> None:
        super().car_enter(car)
        self.state["cars_present"][-1] = [self.state["cars_present"][-1], intern]


    def outputFnc(self):
        if self.state["send_ack"]:
            return {
                self.Q_sack: self.state["next_ack"]
            }

        if self.state["send_query"]:
            return {
                self.Q_send: self.state["next_query"]
            }

        if len(self.state["cars_present"]) > 0:
            # check if the destination of the car is not in the CrossRoadSegment's destinations
            if self.state["cars_present"][0][0].destination not in self.destinations:
                return {
                    self.car_out_cr: self.state["cars_present"][0][0]
                }
            else:
                return {
                    self.car_out: self.state["cars_present"][0][0]
                }

        return {}

    def intTransition(self):
        self.state['time'] += self.timeAdvance()
        if self.state["send_ack"]:
            self.state["send_ack"] = False

        elif self.state["send_query"]:
            # print("enter", self.state["cars_present"])
            # edge case, the car isn't moving -> resend query every observer time
            if len(self.state["cars_present"]) > 0 and self.state["cars_present"][0][0].v == 0.0:
                self.state["resend_query"] = True

            # default case
            else:
                self.state["send_query"] = False
                self.state["resend_query"] = False

        else:
            if len(self.state["cars_present"]) > 0:
                self.state["cars_present"].pop(0)

        return self.state

    def extTransition(self, inputs):
        # self.state["time"] += self.elapsed
        # query: Query = inputs.get(self.Q_recv, None)
        # ack: QueryAck = inputs.get(self.Q_rack, None)
        # # car out of crossroad
        # car_in: Car = inputs.get(self.car_in, None)
        # car in crossroad
        super().extTransition(inputs)

        car_in_cr: Car = inputs.get(self.car_in_cr, None)
        if car_in_cr is not None:
            self.car_enter(car_in_cr, True)

        # add internal/external parameter in cars_present list
        # if car_in is not None:
        #     self.car_enter(car_in, False)

        # if query is not None:
        #     sideways = False
        #     # if len(self.state["cars_present"]) == 0:
        #     #     ack: QueryAck = QueryAck(query.ID, self.observ_delay, self.lane, sideways)
        #     # else:
        #     #     ack: QueryAck = QueryAck(query.ID, self.state["t_until_dep"] + self.observ_delay, self.lane, sideways)
        #     self.state["next_ack"] = QueryAck(query.ID, self.calc_dep_time(), self.lane, sideways)
        #     self.state["send_ack"] = True
        #
        # if ack is not None:
        #     # say there is a car in front that departs in 3s and you can depart in 2s -> wait 1 more second
        #     # if there is a car in front that departs in 1s but you have 2s to go -> depart in 2s
        #     # => take max of those values to determine your time on the current segment
        #     dep_time_of_car_in_front = ack.t_until_dep
        #     self.state["t_until_dep"] = max(self.state["t_until_dep"], dep_time_of_car_in_front)

        return self.state


class CrossRoads(CoupledDEVS):
    def __init__(self, block_name: str, L: float, v_max: float, destinations: list, observ_delay: float = 0.1):
        super(CrossRoads, self).__init__(block_name)


        self.L: float = L
        self.v_max: float = v_max
        self.destinations = destinations
        self.observ_delay: float = observ_delay

        # car input ports
        self.car_in_N = self.addInPort("car_in_N")
        self.car_in_E = self.addInPort("car_in_E")
        self.car_in_S = self.addInPort("car_in_S")
        self.car_in_W = self.addInPort("car_in_W")

        # query receiver ports
        self.Q_recv_N = self.addInPort("Q_recv_N")
        self.Q_recv_E = self.addInPort("Q_recv_E")
        self.Q_recv_S = self.addInPort("Q_recv_S")
        self.Q_recv_W = self.addInPort("Q_recv_W")

        # acknowledgement receiver ports
        self.Q_rack_N = self.addInPort("Q_rack_N")
        self.Q_rack_E = self.addInPort("Q_rack_E")
        self.Q_rack_S = self.addInPort("Q_rack_S")
        self.Q_rack_W = self.addInPort("Q_rack_W")

        # car output ports
        self.car_out_N = self.addOutPort("car_out_N")
        self.car_out_E = self.addOutPort("car_out_E")
        self.car_out_S = self.addOutPort("car_out_S")
        self.car_out_W = self.addOutPort("car_out_W")

        # query output ports
        self.Q_send_N = self.addOutPort("Q_send_N")
        self.Q_send_E = self.addOutPort("Q_send_E")
        self.Q_send_S = self.addOutPort("Q_send_S")
        self.Q_send_W = self.addOutPort("Q_send_W")

        # acknowledgement output ports
        self.Q_sack_N = self.addOutPort("Q_sack_N")
        self.Q_sack_E = self.addOutPort("Q_sack_E")
        self.Q_sack_S = self.addOutPort("Q_sack_S")
        self.Q_sack_W = self.addOutPort("Q_sack_W")

        # subModels
        self.crossN = self.addSubModel(CrossRoadSegment("crossN", L, v_max, destinations, observ_delay=self.observ_delay))
        self.crossE = self.addSubModel(CrossRoadSegment("crossE", L, v_max, destinations, observ_delay=self.observ_delay))
        self.crossS = self.addSubModel(CrossRoadSegment("crossS", L, v_max, destinations, observ_delay=self.observ_delay))
        self.crossW = self.addSubModel(CrossRoadSegment("crossW", L, v_max, destinations, observ_delay=self.observ_delay))

        # interconnect all CrossRoadSegment objects car in-out
        self.connectPorts(self.crossE.car_out_cr, self.crossN.car_in_cr)
        self.connectPorts(self.crossS.car_out_cr, self.crossE.car_in_cr)
        self.connectPorts(self.crossW.car_out_cr, self.crossS.car_in_cr)
        self.connectPorts(self.crossN.car_out_cr, self.crossW.car_in_cr)

        # interconnect all CrossRoadSegment objects query send-recv
        self.connectPorts(self.crossN.Q_send, self.crossW.Q_recv)
        self.connectPorts(self.crossE.Q_send, self.crossN.Q_recv)
        self.connectPorts(self.crossS.Q_send, self.crossE.Q_recv)
        self.connectPorts(self.crossW.Q_send, self.crossS.Q_recv)

        # interconnect all CrossRoadSegment objects query sack-rack
        self.connectPorts(self.crossN.Q_sack, self.crossE.Q_rack)
        self.connectPorts(self.crossE.Q_sack, self.crossS.Q_rack)
        self.connectPorts(self.crossS.Q_sack, self.crossW.Q_rack)
        self.connectPorts(self.crossW.Q_sack, self.crossN.Q_rack)

        # connect all outgoing ports regarding north
        self.connectPorts(self.crossN.car_out, self.car_out_W)
        self.connectPorts(self.crossN.Q_send, self.Q_send_W)
        self.connectPorts(self.crossN.Q_sack, self.Q_sack_N)

        # connect all incoming ports regarding north
        self.connectPorts(self.car_in_N, self.crossN.car_in)
        self.connectPorts(self.Q_recv_N, self.crossN.Q_recv)
        self.connectPorts(self.Q_rack_W, self.crossN.Q_rack)

        # connect all outgoing ports regarding east
        self.connectPorts(self.crossE.car_out, self.car_out_N)
        self.connectPorts(self.crossE.Q_send, self.Q_send_N)
        self.connectPorts(self.crossE.Q_sack, self.Q_sack_E)

        # connect all incoming ports regarding east
        self.connectPorts(self.car_in_E, self.crossE.car_in)
        self.connectPorts(self.Q_recv_E, self.crossE.Q_recv)
        self.connectPorts(self.Q_rack_N, self.crossE.Q_rack)

        # connect all outgoing ports regarding south
        self.connectPorts(self.crossS.car_out, self.car_out_E)
        self.connectPorts(self.crossS.Q_send, self.Q_send_E)
        self.connectPorts(self.crossS.Q_sack, self.Q_sack_S)

        # connect all incoming ports regarding south
        self.connectPorts(self.car_in_S, self.crossS.car_in)
        self.connectPorts(self.Q_recv_S, self.crossS.Q_recv)
        self.connectPorts(self.Q_rack_E, self.crossS.Q_rack)

        # connect all outgoing ports regarding west
        self.connectPorts(self.crossW.car_out, self.car_out_S)
        self.connectPorts(self.crossW.Q_send, self.Q_send_S)
        self.connectPorts(self.crossW.Q_sack, self.Q_sack_W)

        # connect all incoming ports regarding west
        self.connectPorts(self.car_in_W, self.crossW.car_in)
        self.connectPorts(self.Q_recv_W, self.crossW.Q_recv)
        self.connectPorts(self.Q_rack_S, self.crossW.Q_rack)
