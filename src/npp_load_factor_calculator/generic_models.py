import oemof.solph as solph


class Generic_bus:

    def __init__(self, oemof_es):
        self.oemof_es = oemof_es
        
    def create_bus(self, label):
        bus = solph.Bus(label = label)
        self.oemof_es.add(bus)
        return bus
        

    def create_bus_with_flow_constraints(self, label, input_flow, output_flow):
        pass    


class Generic_sink:

    def __init__(self, oemof_es):
        self.oemof_es = oemof_es
        
    def create_sink(self, label, input_bus):
        
        sink = solph.components.Sink(
            label = label,
            inputs = {input_bus: solph.Flow()}
        )
        
        sink.inputs_pair = [(input_bus, sink)]
        sink.outputs_pair = None
        
        self.oemof_es.add(sink)
        
        return sink
    
        
class Generic_source:

    def __init__(self, oemof_es):
        self.oemof_es = oemof_es
        self.npp_constraints = {}

    def get_npp_constraints(self):
        return self.npp_constraints
    
    def create_npp_block(self, label, nominal_power, output_bus, lcoe):
        
        
        block = solph.components.Source(
            label = label,
            outputs = {output_bus: solph.Flow(nominal_value=nominal_power, min=0, variable_costs=lcoe, nonconvex=solph.NonConvex())}
        )
        
        
        block.inputs_pair = None 
        block.outputs_pair = [(block, output_bus)]
        
        
        self.oemof_es.add(block)
        
        return block
    
        
    
class Generic_storage:

    def __init__(self, oemof_es):
        self.oemof_es = oemof_es
    
 
    
    def create_storage(
        self,
        input_bus,
        output_bus,
        capacity,
    ):
              
        # keyword = "storage_keyword"
        
        # max_storage_level = np.append(max_storage_level, max_storage_level[-1])
           
        storage = solph.components.GenericStorage(
            label="аккумулятор риска",
            nominal_storage_capacity=capacity,
            inputs={input_bus: solph.Flow()},
            outputs={output_bus: solph.Flow()},
        )
        
        storage.inputs_pair = [(input_bus, storage)]
        storage.outputs_pair = [(storage, output_bus)]

        self.es.add(storage)
        return storage
    
    
    
class Generic_converter:

    def __init__(self, oemof_es):
        self.oemof_es = oemof_es
    
    def create_converter(self, label, input_bus, output_bus):
        pass
