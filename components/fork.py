from components.roadsegment import RoadSegment


class Fork(RoadSegment):
    def __init__(self, block_name, L, v_max):
        # Initialize the base class with the provided parameters
        super(Fork, self).__init__(block_name, L, v_max)



        # Adding a new output port for 'car_out2'
        self.car_out2 = self.addOutPort("car_out2")

    # Overriding the output method to include logic for the 'no_gas' attribute
    def outputFnc(self):
        self.destruct[self.c] = "outputFnc";
        self.c += 1
        if self.state["send_ack"]:
            return {
                self.Q_sack: self.state["next_ack"]
            }
        if self.state["send_query"]:
            return {
                self.Q_send: self.state["next_query"]
            }
        # if no gas is true the go to output 2
        if len(self.state["cars_present"]) > 0 and self.state["cars_present"][0].no_gas:
            #print("out2",self.state["cars_present"])
            return {
                self.car_out2: self.state["cars_present"][0]
            }
        elif len(self.state["cars_present"]) > 0:
            #print("out", self.state["cars_present"])
            return {
                self.car_out: self.state["cars_present"][0]
            }

        return {}

