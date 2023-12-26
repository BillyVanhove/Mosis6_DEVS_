from dataclasses import dataclass


@dataclass
class Car:
    ID: int
    v_pref: float
    dv_pos_max: float
    dv_neg_max: float
    departure_time: float = 0.0
    distance_traveled: float = 0.0
    v: float = 0.0
    no_gas: bool = False
    destination: str = "Antwerp"


@dataclass
class Query:
    ID: int  # ID of the car that queried the data


@dataclass
class QueryAck:
    ID: int  # ID of the car that queried the data
    t_until_dep: float
    lane: int = 0
    sideways: bool = False
