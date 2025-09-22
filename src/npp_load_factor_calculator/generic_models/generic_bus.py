from oemof import solph


class Generic_bus:

    def __init__(self, oemof_es):
        self.es = oemof_es
        
    def create_bus(self, label, balanced = True):
        bus = solph.Bus(label = label, balanced = balanced)
        self.es.add(bus)
        return bus
