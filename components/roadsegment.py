from pypdevs.DEVS import AtomicDEVS
from pprint import pprint

from components.helperfunctions import getTime
from components.messages import *
from pypdevs.infinity import INFINITY


class RoadSegment(AtomicDEVS):
    def __init__(self, block_name: str, L: float, v_max: float):
        super(RoadSegment, self).__init__(block_name)
        self.c = 0
        self.destruct = {}
        self.L: float = L
        self.v_max: float = v_max
        self.observ_delay: float = 0.1
        self.priority: bool = False
        self.lane: int = 0

        self.state = {
            "cars_present": [],
            "t_until_dep": 0.0,
            "arr_time": 0.0,
            "remaining_x": 0.0,
            "time": 0.0,
            "next_ack": None,
            "send_ack": False,
            "next_query": None,
            "send_query": False,
            "resend_query": False,
        }

        # input ports
        self.car_in = self.addInPort("car_in")
        self.Q_recv = self.addInPort("Q_recv")
        self.Q_rack = self.addInPort("Q_rack")

        # output ports
        self.car_out = self.addOutPort("car_out")
        self.Q_send = self.addOutPort("Q_send")
        self.Q_sack = self.addOutPort("Q_sack")

    def calc_dep_time(self) -> float:
        until_dep_time = 0.0
        if len(self.state["cars_present"]) == 0:
            # until_dep_time += self.observ_delay
            until_dep_time += 0.0
        else:
            # until_dep_time += self.state["t_until_dep"] + self.observ_delay
            until_dep_time += self.state["t_until_dep"]

        # reasoning: Say you arrive at t=28 and you are expected to depart in 3.5s
        # scenario: t=30 and the segment before this wants to know when you leave
        # calculation: 30s - 28s = 2s so 3.5s - 2s = 1.5s left
        until_dep_time -= (self.state["time"] - self.state["arr_time"])

        return until_dep_time

    def car_enter(self, car: Car) -> None:
        car.distance_traveled += self.L
        self.state["cars_present"] += [car]
        self.state["t_until_dep"] = getTime(self.L, car.v)
        self.state["remaining_x"] = self.L
        self.state["next_query"] = Query(ID=car.ID)
        self.state["send_query"] = True
        self.state["arr_time"] = self.state["time"]

    def timeAdvance(self):
        self.destruct[self.c] = "timeAdvance"; self.c += 1
        if self.state["resend_query"]:
            return self.observ_delay  # sends query again because car is standing still

        if self.state["send_ack"]:
            return self.observ_delay  # send ack with delay

        if self.state["send_query"]:
            return 0.0  # send query instantly

        if len(self.state["cars_present"]) > 0:
            return self.calc_dep_time() # - self.observ_delay  # observer delay is only useful when sending acknowledgements
            # return self.state["t_until_dep"]

        return INFINITY

    def outputFnc(self):
        self.destruct[self.c] = "outputFnc";self.c += 1
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

    def intTransition(self):
        self.destruct[self.c] = "intTransition";self.c += 1
        self.state['time'] += self.timeAdvance()
        if self.state["send_ack"]:
            self.state["send_ack"] = False

        elif self.state["send_query"]:
            # edge case, the car isn't moving -> resend query every observer time
            if len(self.state["cars_present"]) > 0 and self.state["cars_present"][0].v == 0.0:
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
        self.destruct[self.c] = "extTransition";self.c += 1
        self.state["time"] += self.elapsed
        query: Query = inputs.get(self.Q_recv, None)
        ack: QueryAck = inputs.get(self.Q_rack, None)
        car: Car = inputs.get(self.car_in, None)

        if car is not None:
            self.car_enter(car)

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

    def __del__(self):
        # print("ROAD SEGMENT")
        # pprint(self.destruct)
        pass
