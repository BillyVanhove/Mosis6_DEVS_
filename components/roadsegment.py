from pypdevs.DEVS import AtomicDEVS, CoupledDEVS
import random


class RoadSegment(AtomicDEVS):
    def __init__(self, block_name: str, v_max: float):
        super(RoadSegment, self).__init__(block_name)

        self.L: float = 5
        self.v_max: float = v_max
        self.observ_delay: float = 0.1
        self.priority: bool = False
        self.lane: int = 0

        self.state = {
            "cars_present": [],
            "t_until_dep": 0.0,
            "remaining_x": 0.0,
            "time": 0.0,
            "next_ack": None,
            "send_ack": False
        }

        # input ports
        self.car_in = self.addInPort("car_in")
        self.Q_recv = self.addInPort("Q_recv")
        self.Q_rack = self.addInPort("Q_rack")

        # output ports
        self.car_out = self.addOutPort("car_out")
        self.Q_send = self.addOutPort("Q_send")
        self.Q_sack = self.addOutPort("Q_sack")

    def car_enter(self, car: Car) -> None:
        self.state["cars_present"] += [car]
        self.state["t_until_dep"] = getTime(self.L, car.v)
        self.state["remaining_x"] = self.L

    def timeAdvance(self):
        if self.state["send_ack"]:
            return 0.0  # send ack instantly
        if len(self.state["cars_present"]) > 0:
            return self.state["t_until_dep"]
        return INFINITY

    def outputFnc(self):
        if self.state["send_ack"]:
            return {
                self.Q_sack: self.state["next_ack"]
            }

        if len(self.state["cars_present"]) > 0:
            return {
                self.car_out: self.state["cars_present"][0]
            }

        return {}

    def intTransition(self):
        if self.state["send_ack"]:
            self.state["send_ack"] = False
        else:
            if len(self.state["cars_present"]) > 0:
                self.state["cars_present"].pop(0)
        return self.state

    def extTransition(self, inputs):
        query: Query = inputs.get(self.Q_recv, None)
        car: Car = inputs.get(self.car_in, None)

        if car is not None:
            self.car_enter(car)

        if query is not None:
            sideways = False
            if len(self.state["cars_present"]) == 0:
                ack: QueryAck = QueryAck(query.ID, self.observ_delay, self.lane, sideways)
            else:
                ack: QueryAck = QueryAck(query.ID, self.state["t_until_dep"] + self.observ_delay, self.lane, sideways)
            self.state["next_ack"] = ack
            self.state["send_ack"] = True

        return self.state