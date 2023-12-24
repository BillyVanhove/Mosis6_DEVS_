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
