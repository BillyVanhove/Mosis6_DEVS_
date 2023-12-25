from pypdevs.DEVS import AtomicDEVS
from components.messages import *
from pypdevs.infinity import INFINITY
import random


class Generator(AtomicDEVS):
    def __init__(self, block_name: str, IAT_min: float, IAT_max: float, v_pref_mu: float, v_pref_sigma: float,
                 destinations: list, limit: int):
        super(Generator, self).__init__(block_name)

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
            "car_can_move": True,  # start on True because no cars are in the system at t=0
            "car_id_to_move": -1,
            "t_until_dep": INFINITY,
            "query": None
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

    def getGasStatus(self) -> bool:
        return random.sample([True, False], 1)[0]

    def generateCar(self) -> Car:
        random_v = self.generate_v_pref()
        car = Car(ID=self.state["current_car_id"], v_pref=random_v, dv_pos_max=28, dv_neg_max=21,
                  departure_time=self.state["time"], distance_traveled=0.0, v=random_v, no_gas=self.getGasStatus(),
                  destination=self.getDestination())
        return car

    def timeAdvance(self):
        if self.state["cars_generated"] > self.limit:
            return INFINITY

        # if a car can't move, return 0.0 to send a Query immediately
        if not self.state["car_can_move"] and self.state["query"] is not None:
            return 0.0

        if self.state["t_until_dep"] != INFINITY:
            return self.state["t_until_dep"]

        # if a car can move or a query was sent, follow the normal procedure
        return self.state["next_time"]

    def outputFnc(self):
        if self.state["next_car"] is None:
            return {}

        # if the id of the car to move is the id of the current car -> move it
        if self.state["car_id_to_move"] == self.state["next_car"].ID:
            return {
                self.car_out: self.state["next_car"]
            }

        # if the car can't move yet (no ack received) but the car exist, send a Query
        if not self.state["car_can_move"] and self.state["next_car"] is not None and self.state["query"] is not None:
            return {
                self.Q_send: self.state["query"]
            }

        return {}

    def intTransition(self):
        if self.state["t_until_dep"] != INFINITY:
            self.state["t_until_dep"] = INFINITY

        # make new car
        elif self.state["car_can_move"] and self.state["t_until_dep"] == INFINITY:  # if car_can_move is False, then we shouldn't make a 2nd car yet
            self.state["car_can_move"] = False  # a car is to enter the system so set to False
            # self.state["time"] += self.timeAdvance()
            self.state["current_car_id"] += 1
            self.state["next_car"] = self.generateCar()
            self.state["next_time"] = self.generate_IAT()
            self.state["cars_generated"] += 1
            self.state["query"] = Query(self.state["next_car"].ID)


        # handle query related stuff
        else:
            self.state["query"] = None

        return self.state

    def extTransition(self, inputs):
        ack: QueryAck = inputs.get(self.Q_rack, [])

        if ack is not None:
            t_until_dep = max(0.0, ack.t_until_dep)

            # next action can happen at the scheduled time OR if the car is still on the segment in
            # front of it, it must wait for t_until_dep seconds to make sure the car is gone
            self.state["next_time"] = max(self.state["next_time"], self.state["time"] + t_until_dep)

            # set the delay between now and the car to depart
            self.state["t_until_dep"] = ack.t_until_dep

            # use this delay to adjust the generator to create a new car on the right moment
            self.state["next_time"] = self.state["next_time"] - self.state["t_until_dep"]

            self.state["time"] += self.elapsed
            self.state[
                "car_can_move"] = True  # we know when the car can move now so we can already set the flag to true
            self.state["car_id_to_move"] = ack.ID

        return self.state