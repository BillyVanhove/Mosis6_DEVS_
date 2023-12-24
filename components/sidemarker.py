from pypdevs.DEVS import AtomicDEVS
from components.messages import *


class SideMarker(AtomicDEVS):
    def __init__(self, block_name: str, v_max: float):
        super(SideMarker, self).__init__(block_name)

        self.L: float = 5
        self.v_max: float = v_max
        self.observ_delay: float = 0.1
        self.priority: bool = False
        self.lane: int = 0

        self.state = {
            "cars_present": [],
            "t_until_dep": 0.0,
            "remaining_x": 0.0,
            "time": 0.0
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
        pass

    def timeAdvance(self):
        return 0.0

    def outputFnc(self):
        return {}

    def intTransition(self):
        return self.state

    def extTransition(self, inputs):
        queries = inputs.get(self.Q_recv, [])

        query: Query
        for query in queries:
            sideways = False
            if len(self.state["cars_present"]) == 0:
                ack: QueryAck = QueryAck(query.ID, self.observ_delay, self.lane, sideways)
            else:
                ack: QueryAck = QueryAck(query.ID, self.state["t_until_dep"] + self.observ_delay, self.lane, sideways)

        return self.state
