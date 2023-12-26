from pypdevs.DEVS import AtomicDEVS
from components.messages import *
from pypdevs.infinity import INFINITY
import random


class GasStation(AtomicDEVS):
    def __init__(self, block_name: str, observ_delay: float = 30):
        super(GasStation, self).__init__(block_name)

        self.observ_delay: float = observ_delay
        # new parameter thzt holds the time of the next quary
        self.time_of_next_query: float = observ_delay

        self.state = {
            "car_list": [],
            "t_until_dep": INFINITY,
            "time_until_next_event": INFINITY,
            "time": 0.0,  # Keep track of the current simulation time
            "query": False,
            "available": True
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
        self.state["car_list"].append((car, departure_time))
        self.state["car_list"].sort(key=lambda x: x[1])
        print(self.state["car_list"])

    def timeAdvance(self):
        # Simply return the stored time until the next event
        return self.state["time_until_next_event"]

    def outputFnc(self):
        # if the car can't move yet (no ack received) but the car exist, send a Query
        if self.state["query"]:
            self.time_of_next_query += self.observ_delay
            return {
                self.Q_send: self.state["query"]
            }

        if self.state["car_list"] and self.state["car_list"][0][1] <= self.state["time"] and self.state["available"]:
            self.state["available"] = False
            return {
                self.car_out: self.state["car_list"][0][0]
            }

        return {}

    def intTransition(self):
        # Process internal transition (e.g., car departure, query event)
        self.state["car_list"] = [(car, time) for car, time in self.state["car_list"] if time > self.state["time"]]
        if not self.state["car_list"]:
            self.state["available"] = True
        # Determine the time until the next event
        if self.state["car_list"]:
            self.state["time_until_next_event"] = self.state["car_list"][0][1] - self.state["time"]
        elif self.time_of_next_query > self.state["time"]:
            self.state["time_until_next_event"] = self.time_of_next_query - self.state["time"]
        else:
            self.state["time_until_next_event"] = INFINITY
        return self.state

    def extTransition(self, inputs):
        # Process external events (e.g., car arrival, acknowledgment reception)
        ack: QueryAck = inputs.get(self.Q_rack, None)
        car: Car = inputs.get(self.car_in, None)

        if car is not None:
            self.car_enter(car)
        if ack is not None:
            self.state["t_until_dep"] = max(self.state["time"], ack.t_until_dep)
            if self.state["time"] >= self.state["t_until_dep"]:
                self.state["available"] = True
        # Update the time for the next event after processing external events
        # Calculate the time until the next event based on the current state
        times = [event[1] for event in self.state["car_list"]] + [self.time_of_next_query]
        self.state["time_until_next_event"] =  min(times) - self.state["time"] if times else INFINITY
        return self.state
