from pypdevs.DEVS import AtomicDEVS, CoupledDEVS
from components.messages import *
import random



class CrossRoadSegment(AtomicDEVS):
    def __init__(self, block_name: str, IAT_min: float, IAT_max: float, v_pref_mu: float, v_pref_sigma: float,
                 destinations: list, limit: int):
        super(CrossRoadSegment, self).__init__(block_name)

        self.IAT_min: float = IAT_min
        self.IAT_max: float = IAT_max
        self.v_pref_mu: float = v_pref_mu
        self.v_pref_sigma: float = v_pref_sigma
        self.destinations: list = destinations
        self.limit: int = limit

        self.state = {
        }

        # input port
        self.Q_rack = self.addInPort("Q_rack")

        # output ports
        self.car_out = self.addOutPort("car_out")


    def generate_IAT(self) -> float:
        pass

    def generate_v_pref(self) -> float:
        pass

    def getDestination(self) -> str:
        pass

    def generateCar(self) -> Car:
        pass

    def timeAdvance(self):
        pass

    def outputFnc(self):
        if self.state["next_car"] is None:
            return {}

        if not self.state["car_can_move"] and self.state["next_car"] is not None:
            return {
                self.Q_send: Query(self.state["next_car"].ID)
            }

        return {
            self.car_out: self.state["next_car"]
        }

    def intTransition(self):
        self.state["time"] += self.timeAdvance()
        self.state["next_car"] = self.generateCar()
        self.state["current_car_id"] += 1
        self.state["next_time"] = self.generate_IAT()
        self.state["cars_generated"] += 1
        return self.state

    def extTransition(self, inputs):
        acks = inputs.get(self.Q_rack, [])

        ack: QueryAck
        for ack in acks:
            t_until_dep = max(0.0, ack.t_until_dep)


class CrossRoads (AtomicDEVS):
    def __init__(self, block_name: str, IAT_min: float, IAT_max: float, v_pref_mu: float, v_pref_sigma: float,
                 destinations: list, limit: int):
        super(CrossRoads, self).__init__(block_name)

        self.IAT_min: float = IAT_min
        self.IAT_max: float = IAT_max
        self.v_pref_mu: float = v_pref_mu
        self.v_pref_sigma: float = v_pref_sigma
        self.destinations: list = destinations
        self.limit: int = limit

        self.state = {
            "next_time": 0.0,
            "next_car": None,
            "time": 0.0,
            "cars_generated": 0,
            "current_car_id": 0,
            "car_can_move": False
        }

        # input port
        self.Q_rack = self.addInPort("Q_rack")

        # output ports
        self.car_out = self.addOutPort("car_out")
        self.Q_send = self.addOutPort("Q_send")

    def generate_IAT(self) -> float:
        return random.uniform(self.IAT_min, self.IAT_max)

    def generate_v_pref(self) -> float:
        return random.normalvariate(self.v_pref_mu, self.v_pref_sigma)

    def getDestination(self) -> str:
        return random.sample(self.destinations, 1)[0]

    def generateCar(self) -> Car:
        random_v = self.generate_v_pref()
        car = Car(ID=self.state["current_car_id"], v_pref=random_v, dv_pos_max=28, dv_neg_max=21,
                  departure_time=self.state["time"], distance_traveled=0.0, v=random_v, no_gas=False,
                  destination=self.getDestination())
        return car

    def timeAdvance(self):
        return self.state["next_time"]

    def outputFnc(self):
        if self.state["next_car"] is None:
            return {}

        if not self.state["car_can_move"] and self.state["next_car"] is not None:
            return {
                self.Q_send: Query(self.state["next_car"].ID)
            }

        return {
            self.car_out: self.state["next_car"]
        }

    def intTransition(self):
        self.state["time"] += self.timeAdvance()
        self.state["next_car"] = self.generateCar()
        self.state["current_car_id"] += 1
        self.state["next_time"] = self.generate_IAT()
        self.state["cars_generated"] += 1
        return self.state

    def extTransition(self, inputs):
        acks = inputs.get(self.Q_rack, [])

        ack: QueryAck
        for ack in acks:
            t_until_dep = max(0.0, ack.t_until_dep)
