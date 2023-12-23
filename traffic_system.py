
def getDistance(v, t) -> float:
	return v*t

def getVelocity(d, t) -> float:
	return d/t

def getTime(d, v) -> float:
	return d/v

from dataclasses import dataclass

@dataclass
class Car:
	ID: int
	v_pref: float
	dv_pos_max: float
	dv_neg_max: float
	departure_time: float
	distance_traveled: float
	v: float
	no_gas: bool
	destination: str


@dataclass
class Query:
	ID: int  # ID of the car that queried the data


@dataclass
class QueryAck:
	ID: int  # ID of the car that queried the data
	t_until_dep: float
	lane: int
	sideways: bool



from pypdevs.DEVS import AtomicDEVS, CoupledDEVS
from pypdevs.infinity import INFINITY
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
		self.state["cars_present"] += [car]
		self.state["t_until_dep"] = getTime(self.L, car.v)
		self.state["remaining_x"] = self.L


	def timeAdvance(self):
		return 0.0

	def outputFnc(self):
		return {}

	def intTransition(self):
		return self.state

	def extTransition(self, inputs):
		return self.state


class Generator(AtomicDEVS):
	def __init__(self, block_name: str, IAT_min: float, IAT_max: float, v_pref_mu: float, v_pref_sigma: float, destinations: list, limit: int):
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
			"current_car_id": 0
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
				  departure_time=self.state["time"], distance_traveled=0.0, v=random_v, no_gas=False, destination=self.getDestination())
		return car

	def timeAdvance(self):
		return self.state["next_time"]

	def outputFnc(self):
		if self.state["next_car"] is None:
			return {}
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


if __name__ == '__main__':
	from pypdevs.simulator import Simulator

	# model = Supermarket("market")
	# sim = Simulator(model)
	# sim.setClassicDEVS()
	# sim.setTerminationTime(100)
	# sim.setVerbose(None)
	# sim.simulate()
