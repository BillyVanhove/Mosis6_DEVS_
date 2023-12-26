from pypdevs.DEVS import AtomicDEVS
from components.messages import *
from pypdevs.infinity import INFINITY
import random


class GasStation(AtomicDEVS):
    def __init__(self, block_name: str, observ_delay: float = 30):
        super(GasStation, self).__init__(block_name)

        self.observ_delay: float = observ_delay

        self.state = {
            "car_list": [],
            "t_until_dep": INFINITY,
            "time_until_next_event": INFINITY,
            "time": 0.0,  # Keep track of the current simulation time
            "ack_received": INFINITY,
            "query": False,
            "available": True,
            "should_output": False
        }

        # input port
        self.Q_rack = self.addInPort("Q_rack")
        self.car_in = self.addInPort("car_in")

        # output ports
        self.Q_send = self.addOutPort("Q_send")
        self.car_out = self.addOutPort("car_out")

    def generate_delay(self) -> float:
        return random.normalvariate(600, 130)

    def car_enter(self, car: Car) -> None:
        # the delay needs to be at least 2 minutes otherwise set on 2 minutes
        delay: float = self.generate_delay()
        if delay < 120:
            delay = 120
        # hold the car with his own delay
        departure_time = self.state["time"] + delay
        self.state["car_list"].append([car, departure_time])
        self.state["car_list"].sort(key=lambda x: x[1])
        # print(self.state["car_list"])

    def timeAdvance(self):
        # Simply return the stored time until the next event
        return min(self.observ_delay, self.state["time_until_next_event"])
        # return self.state["time_until_next_event"]

    def outputFnc(self):
        # if the car can't move yet (no ack received) but the car exist, send a Query
        if self.state["query"]:
            return {
                self.Q_send: self.state["query"]
            }

        if self.state["car_list"] and self.state["should_output"] and self.state["available"]:
            return {
                self.car_out: self.state["car_list"][0][0]
            }

        return {}

    def intTransition(self):
        self.state['time'] += self.timeAdvance()

        # Process internal transition (e.g., car departure, query event)
        self.state["time_until_next_event"] = INFINITY

        if not self.state["car_list"] or self.state["time"] > self.state["ack_received"] + self.state["t_until_dep"]:
            self.state["available"] = True

        else:
            # happens every 30s
            if not self.state["should_output"]:
                for i in range(len(self.state["car_list"])):
                    self.state["car_list"][i][1] -= self.observ_delay

                self.state["car_list"].sort(key=lambda x: x[1])

                if self.state["car_list"][0][1] < self.observ_delay:
                    # print("IF",self.state["car_list"][0][1])
                    self.state["time_until_next_event"] = self.state["car_list"][0][1]
                    self.state["should_output"] = True

            # happens right after a car departed
            else:
                # self.state["available"] = False
                self.state["should_output"] = False
                # print("ELSE",self.state["car_list"][0][1])
                self.state["time_until_next_event"] = self.observ_delay - self.state["car_list"][0][1]
                self.state["car_list"].pop(0)

        return self.state

    def extTransition(self, inputs):
        self.state['time'] += self.elapsed
        # Process external events (e.g., car arrival, acknowledgment reception)
        ack: QueryAck = inputs.get(self.Q_rack, None)
        car: Car = inputs.get(self.car_in, None)

        if car is not None:
            self.car_enter(car)

        if ack is not None:
            self.state["t_until_dep"] = ack.t_until_dep
            self.state["time_until_next_event"] = self.state["t_until_dep"]
            self.state["ack_received"] = self.state["time"]
            self.state["available"] = False

        return self.state
