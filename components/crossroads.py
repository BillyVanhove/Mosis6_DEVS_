from pypdevs.DEVS import CoupledDEVS
from components.messages import *
from components.helperfunctions import getTime
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

    def car_enter(self, car: Car, intern: bool) -> None:
        # print("enter", car)
        car.distance_traveled += self.L
        # clean seperation
        self.state["cars_present"].append([car, intern])
        self.state["t_until_dep"] = getTime(self.L, car.v)
        self.state["remaining_x"] = self.L
        self.state["next_query"] = Query(ID=car.ID)
        self.state["send_query"] = True
        self.state["arr_time"] = self.state["time"]

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
        self.destruct[self.c] = "intTransition";
        self.c += 1
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
        self.destruct[self.c] = "extTransition";
        self.c += 1
        self.state["time"] += self.elapsed
        query: Query = inputs.get(self.Q_recv, None)
        ack: QueryAck = inputs.get(self.Q_rack, None)
        # car out of crossroad
        car_in: Car = inputs.get(self.car_in, None)
        # car in crossroad
        car_in_cr: Car = inputs.get(self.car_in_cr, None)

        # add internal/external parameter in cars_present list
        if car_in is not None:
            self.car_enter(car_in, False)
        if car_in_cr is not None:
            self.car_enter(car_in_cr, True)

        if query is not None:
            sideways = False
            # if len(self.state["cars_present"]) == 0:
            #     ack: QueryAck = QueryAck(query.ID, self.observ_delay, self.lane, sideways)
            # else:
            #     ack: QueryAck = QueryAck(query.ID, self.state["t_until_dep"] + self.observ_delay, self.lane, sideways)
            self.state["next_ack"] = QueryAck(query.ID, self.calc_dep_time(), self.lane, sideways)
            self.state["send_ack"] = True

        if ack is not None:
            # say there is a car in front that departs in 3s and you can depart in 2s -> wait 1 more second
            # if there is a car in front that departs in 1s but you have 2s to go -> depart in 2s
            # => take max of those values to determine your time on the current segment
            dep_time_of_car_in_front = ack.t_until_dep
            self.state["t_until_dep"] = max(self.state["t_until_dep"], dep_time_of_car_in_front)

        return self.state


class CrossRoads(CoupledDEVS):
    def __init__(self, block_name: str, L: float, v_max: float, destinations: list, observ_delay: float):
        super(CrossRoads, self).__init__(block_name)


        self.L: float = L
        self.v_max: float = v_max
        self.destinations = destinations
        self.observ_delay: float = observ_delay

        # input ports
        self.car_in = self.addInPort("car_in")
        self.Q_recv = self.addInPort("Q_recv")
        self.Q_rack = self.addInPort("Q_rack")

        # output ports
        self.car_out = self.addOutPort("car_out")
        self.Q_send = self.addOutPort("Q_send")
        self.Q_sack = self.addOutPort("Q_sack")

        # (self, block_name: str, v_max: float)
        self.crossN = self.addSubModel(CrossRoadSegment("crossN", L, v_max, destinations))
        self.crossE = self.addSubModel(CrossRoadSegment("crossE", L, v_max, destinations))
        self.crossS = self.addSubModel(CrossRoadSegment("crossS", L, v_max, destinations))
        self.crossW = self.addSubModel(CrossRoadSegment("crossW", L, v_max, destinations))


