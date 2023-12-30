from pypdevs.DEVS import AtomicDEVS
from pprint import pprint

from components.helperfunctions import getTime, getDistance, StateDict
from components.messages import *
from pypdevs.infinity import INFINITY

class RoadSegment(AtomicDEVS):
    def __init__(self, block_name: str, L: float, v_max: float, observ_delay: float = 0.1, priority: bool = False, lane: int = 0):
        super(RoadSegment, self).__init__(block_name)
        self.c = 0
        self.destruct = {}
        self.L: float = L
        self.v_max: float = v_max
        self.observ_delay: float = observ_delay
        self.priority: bool = priority
        self.lane: int = lane

        self.state: StateDict = StateDict({
            "cars_present": [],
            "t_until_dep": 0.0,
            "arr_time": 0.0,
            "remaining_x": 0.0,
            "time": 0.0,
            "ack_id": -1,
            "next_ack": None,
            "send_ack": False,
            "next_query": None,
            "send_query": False,
            "resend_query": False,
            "collisions": 0
        })

        # input ports
        self.car_in = self.addInPort("car_in")
        self.Q_recv = self.addInPort("Q_recv")
        self.Q_rack = self.addInPort("Q_rack")

        # output ports
        self.car_out = self.addOutPort("car_out")
        self.Q_send = self.addOutPort("Q_send")
        self.Q_sack = self.addOutPort("Q_sack")

    def calc_v_new(self, car: Car):
        car_v_pref: float = car.v_pref
        car_v: float = car.v

        # car is faster than optimal speed -> decelerate
        if car_v > car_v_pref:
            difference = car_v - car_v_pref
            v_new = car_v - min(car.dv_neg_max, difference)

        # car is slower than optimal speed -> accelerate
        elif car_v < car_v_pref:
            difference = car_v_pref - car_v
            v_new = car_v + min(car.dv_pos_max, difference)

        # car is driving at optimal speed -> do nothing
        else:
            v_new = car_v

        return v_new

    def car_accelerate(self, car: Car, acceleration_rate: float, delay: float = 0.0):
        # car wants to accelerate but would go over the max speed
        if acceleration_rate + car.v > self.v_max >= car.v:
            acceleration_rate = self.v_max - car.v  # max acceleration rate to not go over max speed

            # make sure that this acceleration isn't above the max acceleration for 1 'tick'
            if acceleration_rate > car.dv_pos_max:
                acceleration_rate = car.dv_pos_max

        # car wants to accelerate but is already over the max speed -> decelerate
        elif acceleration_rate + car.v > self.v_max < car.v:
            difference = car.v - self.v_max  # difference in speed

            # car can decelerate to a value under max speed in 1 'tick' -> decelerate to this value
            if difference <= car.dv_neg_max:
                deceleration_rate = difference

            # car can't decelerate to a value under max speed in 1 'tick' -> decelerate as much as possible
            else:
                deceleration_rate = car.dv_neg_max

            # decelerate
            self.car_decelerate(car, deceleration_rate=deceleration_rate, delay=delay)
            return

        # calculate the distance covered from the time of arrival at the previous speed
        # (aka time between sending and receiving query)
        already_covered_distance = getDistance(car.v, self.state["time"] - self.state["arr_time"])
        self.state["remaining_x"] -= already_covered_distance

        self.state["arr_time"] = self.state["time"]

        # statement is allowed without checks as they happen before this
        car.v += acceleration_rate
        self.state["t_until_dep"] = getTime(self.state["remaining_x"], car.v) # + delay

    def car_decelerate(self, car: Car, deceleration_rate: float = None, delay: float = 0.0):
        if deceleration_rate is None:
            new_car_v: float = max(car.v - car.dv_neg_max, 0.0)  # max deceleration
        else:
            new_car_v: float = max(car.v - deceleration_rate, 0.0)  # custom deceleration

        # calculate the distance covered from the time of arrival at the previous speed
        # (aka time between sending and receiving query)
        already_covered_distance = getDistance(car.v, self.state["time"] - self.state["arr_time"])
        self.state["remaining_x"] -= already_covered_distance

        self.state["arr_time"] = self.state["time"]

        # now update car speed
        car.v = new_car_v
        if car.v == 0.0:
            self.state["t_until_dep"] = INFINITY
        else:
            self.state["t_until_dep"] = getTime(self.state["remaining_x"], car.v) # + delay

    def check_collision(self, v_new: float, t_no_coll: float, car: Car) -> bool:
        # calculate the time on the current roadsegment with new v
        # then, calculate the remaining_x for this roadsegment with this speed
        t_until_dep_with_new_speed = getDistance(v=v_new, t=getTime(self.state["remaining_x"], v_new))
        # t_until_dep_with_new_speed = getDistance(v=v_new, t=getTime(self.state["remaining_x"]-getDistance(car.v, self.state["time"] - self.state["arr_time"]), v_new))

        # collision happens when you depart before t_no_coll
        if t_until_dep_with_new_speed < t_no_coll:
            return True
        return False

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

    def car_enter(self, car: Car, intern: bool = None) -> None:
        # if a 2nd car arrives, they collide
        if len(self.state["cars_present"]) == 1:
            self.cars_crash()
            return

        car.distance_traveled += self.L
        self.state["cars_present"] += [car]
        self.state["t_until_dep"] = getTime(self.L, car.v)
        self.state["remaining_x"] = self.L
        self.state["next_query"] = Query(ID=car.ID)
        self.state["send_query"] = True
        self.state["arr_time"] = self.state["time"]

    def cars_crash(self):
        self.state["cars_present"] = []
        self.state["t_until_dep"] = 0.0
        self.state["remaining_x"] = 0.0
        self.state["arr_time"] = self.state["time"]
        self.state["collisions"] += 1

    def timeAdvance(self):
        self.destruct[self.c] = "timeAdvance"; self.c += 1
        if self.state["resend_query"]:
            return self.observ_delay  # sends query again because car is standing still

        if self.state["send_ack"]:
            return self.observ_delay  # send ack with delay

        if self.state["send_query"]:
            return 0.0  # send query instantly

        if len(self.state["cars_present"]) > 0:
            a = 2
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
            car: Car = self.state["cars_present"][0]
            if car is None:
               return self.state

            # a 2nd ACK for a car arrives
            if self.state["ack_id"] == ack.ID:
                measured_observer_delay = 0.0

            # an ACK for a new car arrives
            else:
                # indirect reading of the observer delay of the component in front
                measured_observer_delay = self.state["time"] - self.state["arr_time"]
                self.state["ack_id"] = ack.ID

            if not ack.sideways:
                v_new = self.calc_v_new(car=car)
                t_no_coll = ack.t_until_dep
                collision = self.check_collision(v_new=v_new, t_no_coll=t_no_coll, car=car)

                if not collision:
                    if car.v < v_new:  # old is lower than new
                        self.car_accelerate(car, acceleration_rate=v_new-car.v, delay=measured_observer_delay)
                    elif car.v > v_new:  # old is higher than new
                        self.car_decelerate(car, deceleration_rate=car.v-v_new, delay=measured_observer_delay)
                    else:  # old and new speed are the same
                        self.car_accelerate(car, acceleration_rate=0.0, delay=measured_observer_delay)  # needed because a car can be above max speed

                else:
                    self.car_decelerate(car, deceleration_rate=max(car.v - car.dv_neg_max, self.state["remaining_x"] - t_no_coll), delay=measured_observer_delay)

            else:
                if not self.priority:
                    self.car_decelerate(car=car, delay=measured_observer_delay)
                else:
                    a = 2
                pass


        return self.state

    def __del__(self):
        # print("ROAD SEGMENT")
        # pprint(self.destruct)
        pass
