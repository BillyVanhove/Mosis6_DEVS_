from pypdevs.DEVS import AtomicDEVS
from pypdevs.infinity import INFINITY
from components.messages import *


class SideMarker(AtomicDEVS):
    def __init__(self, block_name: str):
        super(SideMarker, self).__init__(block_name)

        self.state = {
            "should_forward": False,
            "queryAck": None
        }

        # input ports
        self.mi = self.addInPort("mi")

        # output ports
        self.mo = self.addOutPort("mo")


    def timeAdvance(self):
        # if a QueryAck is received, forward it immediately
        if self.state["should_forward"]:
            return 0.0

        # else, wait indefinitely
        return INFINITY

    def outputFnc(self):
        if self.state["queryAck"] is not None:
            return {
                self.mo: self.state["queryAck"]
            }
        return {}

    def intTransition(self):
        # after forwarding, set values to default
        if self.state["should_forward"]:
            self.state["should_forward"] = False
            self.state["queryAck"] = None

        return self.state

    def extTransition(self, inputs):
        ack: QueryAck = inputs.get(self.mi, None)

        if ack is not None:
            ack.sideways = True
            self.state["should_forward"] = True
            self.state["queryAck"] = ack

        return self.state
