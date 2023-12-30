from pypdevs.DEVS import AtomicDEVS
from components.messages import *
from components.helperfunctions import StateDict
from pypdevs.infinity import INFINITY
import random


class GasStation(AtomicDEVS):
    def __init__(self, block_name: str, observ_delay: float = 0.1):
        super(GasStation, self).__init__(block_name)

        self.observ_delay: float = observ_delay

        self.state: StateDict = StateDict({
            "car_list": [],
            "t_until_dep": 0.0,
            "time": 0.0,  # Keep track of the current simulation time
            "ack_is_received": False,
            "idle": False,
            "query": None,
            "send_query": False,
            "available": True,
        })

        # input port
        self.Q_rack = self.addInPort("Q_rack")
        self.car_in = self.addInPort("car_in")

        # output ports
        self.Q_send = self.addOutPort("Q_send")
        self.car_out = self.addOutPort("car_out")

    def generate_delay(self) -> float:
        return random.normalvariate(600, 130)

    def invariant(self):
        total = 0
        total += int(self.state["ack_is_received"] == True)
        total += int(self.state["idle"] == True)
        total += int(self.state["send_query"] == True)
        total += int(self.state["available"] == True)
        if total == 0:
            print("TOTAL 0")
        if total > 1:
            print("TOTAL HIGH")

    def car_enter(self, car: Car) -> None:
        # the delay needs to be at least 2 minutes otherwise set on 2 minutes
        delay: float = self.generate_delay()
        if delay < 120:
            delay = 120
        # hold the car with his own delay
        self.state["car_list"].append([car, delay])
        self.state["car_list"].sort(key=lambda x: x[1])

    def update_cars(self, t):
        for i in range(len(self.state["car_list"])):
            self.state["car_list"][i][1] -= t
            if self.state["car_list"][i][1] < 0.0:
                self.state["car_list"][i][1] = 0.0

    def timeAdvance(self):
        if self.state["ack_is_received"]:
            return self.state["t_until_dep"] if self.state["t_until_dep"] is not INFINITY else self.observ_delay

        if self.state["idle"] or len(self.state["car_list"]) == 0:
            return INFINITY

        if self.state["send_query"]:
            return 0.0  # queries are sent immediately

        return self.state["car_list"][0][1]

    def outputFnc(self):
        # if the car can't move yet (no ack received) but the car exist, send a Query
        if self.state["send_query"]:
            return {
                self.Q_send: self.state["query"]
            }

        # this code will only be ran after t_until_dep has already elapsed
        if self.state["ack_is_received"]:
            return {
                self.car_out: self.state["car_list"][0][0]
            }

        return {}

    def intTransition(self):
        self.state['time'] += self.timeAdvance()

        # this code runs right after query is sent
        if self.state["send_query"]:
            self.state["send_query"] = False
            self.state["idle"] = True

        # this code runs if no query or ack are present and if a car hasn't just departed
        elif self.state["available"]:
            # update cars with the delay of first car
            self.update_cars(self.state["car_list"][0][1])
            self.state["available"] = False

            # if delay == 0
            if self.state["car_list"][0][1] == 0.0:
                self.state["query"] = Query(ID=self.state["car_list"][0][0].ID)
                self.state["send_query"] = True
                self.state["idle"] = False
                self.state["ack_is_received"] = False

        # happens right after a car departed
        elif self.state["ack_is_received"] and not self.state["idle"]:

            # change the car's gas because its refilled
            self.state["car_list"][0][0].no_gas = False
            self.state["car_list"].pop(0)

            # change state to available again
            self.state["available"] = True

            # cars can leave after acks are received so reset if a car leaves
            self.state["ack_is_received"] = False
            self.state["idle"] = False

        # self.invariant()
        return self.state

    def extTransition(self, inputs):
        self.state['time'] += self.elapsed

        # Process external events (e.g., car arrival, acknowledgment reception)
        ack: QueryAck = inputs.get(self.Q_rack, None)
        car: Car = inputs.get(self.car_in, None)

        if car is not None:
            self.update_cars(t=self.elapsed)
            self.car_enter(car)

        if ack is not None:
            self.update_cars(t=self.elapsed)

            self.state["t_until_dep"] = ack.t_until_dep
            self.state["ack_is_received"] = True
            self.state["idle"] = False

        # self.invariant()
        return self.state

