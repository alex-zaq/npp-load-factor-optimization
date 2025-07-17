import oemof.solph as solph

from src.npp_load_factor_calculator.utilites import set_label


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
    
    
    
    def create_source_fixed(self, label, output_bus, fixed_pow_lst):
        
        source = solph.components.Source(
            label = label,
            outputs = {output_bus: solph.Flow(
                fix=fixed_pow_lst
            )}
        )
        source.inputs_pair = None
        source.outputs_pair = [(source, output_bus)]
        self.oemof_es.add(source)
        return source
        
    
    def create_source_nonconvex(self, label, output_bus, power):
        
        source = solph.components.Source(
            label = label,
            outputs = {output_bus: solph.Flow(
                nominal_value=power,
                min=0,
                max=1,
                nonconvex=solph.NonConvex()
            )}
        )
        source.inputs_pair = None
        source.outputs_pair = [(source, output_bus)]
        self.oemof_es.add(source)
        return source
    
    

    def create_npp_block(
        self,
        label,
        nominal_power,
        output_bus,
        var_cost,
        min_pow_lst,
        max_pow_lst,
        risk_mode,
        default_risk_per_hour,
        max_risk_level,
        fix_risk_lst,
    ):
        
        
        npp_block = solph.components.Source(
            label=label,
            outputs={
                output_bus: solph.Flow(
                    nominal_value=nominal_power,
                    min=min_pow_lst,
                    max=max_pow_lst,
                    variable_costs=var_cost,
                    # positive_gradient_limit=grad,
                    # negative_gradient_limit=grad,
                    nonconvex=solph.NonConvex(
                    #   minimum_uptime=uptime,  
                        ),
                )
            },
        )
                
        npp_block.inputs_pair = None 
        npp_block.outputs_pair = [(npp_block, output_bus)]
        self.oemof_es.add(npp_block)
        
        if risk_mode:
            
            bus_factory = Generic_bus(self.oemof_es)
            risk_bus = bus_factory.create_bus(set_label(label, "risk_bus"))
            
            if default_risk_per_hour:
                default_risk_source = self.create_source_nonconvex(set_label(label, "default_risk_source"), risk_bus, default_risk_per_hour)
                npp_block.default_risk_mode = True
                npp_block.default_risk_source = default_risk_source
                 # constraint

            risk_source = self.create_source_fixed(set_label(label, "risk_source"), risk_bus, fix_risk_lst)
            storage_factory = Generic_storage(self.oemof_es)
            storage = storage_factory.create_storage(
                input_bus = risk_source,
                output_bus = output_bus,
                capacity = max_risk_level,
            )
            
            npp_block.risk_mode = risk_mode
            npp_block.risk_source = risk_source
            npp_block.risk_storage = storage
            
        
        return npp_block
    
        
        
# for i in range(24):
#     solph.constraints.equate_variables(
#         model,
#         model.NonConvexFlowBlock.status[cpp, el_bus, i],
#         model.NonConvexFlowBlock.status[control_bus_npp, control_sink_npp, i],
#     )

        
        
    
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
