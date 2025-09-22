from oemof import solph


class Generic_sink:

    def __init__(self, oemof_es):
        self.es = oemof_es
        
    def create_sink(self, label, input_bus):
        sink = solph.components.Sink(
            label=label,
            inputs={input_bus: solph.Flow()},
        )
        sink.inputs_pair = [(input_bus, sink)]
        self.es.add(sink)
        return sink
