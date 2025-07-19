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
    
    
    def create_source(self, label, output_bus):
        
        source = solph.components.Source(
            label = label,
            outputs = {output_bus: solph.Flow()}
        )
        source.inputs_pair = None
        source.outputs_pair = [(source, output_bus)]
        self.oemof_es.add(source)
        return source
    
    
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
        risk_per_hour,
        max_risk_level,
        fix_risk_lst,
        repair_options,
    ):
        
        
        npp_block = solph.components.Source(
            label=label,
            outputs={
                output_bus: solph.Flow(
                    nominal_value=nominal_power,
                    # min=min_pow_lst,
                    # max=max_pow_lst,
                    variable_costs=var_cost,
                    # positive_gradient_limit=grad,
                    # negative_gradient_limit=grad,
                    nonconvex=solph.NonConvex(
                    #   minimum_uptime=uptime,  
                        ),
                )
            },
        )
        # constraint (когда работает аэс то ремонт не происходит/или происходит/опционально) npp_block и c_sinks_repair_dict
                
        npp_block.inputs_pair = None 
        npp_block.outputs_pair = [(npp_block, output_bus)]
        self.oemof_es.add(npp_block)
        
        if risk_mode:
            
            bus_factory = Generic_bus(self.oemof_es)
            risk_bus_in = bus_factory.create_bus(set_label(label, "risk_bus_in"))
            risk_bus_out = bus_factory.create_bus(set_label(label, "risk_bus_out"))
            
            
            if risk_per_hour:
                default_risk_source = self.create_source_nonconvex(set_label(label, "default_risk_source"), risk_bus_in, risk_per_hour)
                npp_block.default_risk_mode = True
                npp_block.default_risk_source = default_risk_source
                 # constraint когда работает аэс то есть дефотлный риск npp_block и default_risk_source 

            risk_source = self.create_source_fixed(set_label(label, "risk_source"), risk_bus_in, fix_risk_lst)
            storage_factory = Generic_storage(self.oemof_es)
            risk_storage_block = storage_factory.create_storage(
                input_bus=risk_bus_in,
                output_bus=risk_bus_out,
                capacity=max_risk_level,
            )
            npp_block.risk_mode = risk_mode
            npp_block.risk_source = risk_source
            npp_block.risk_storage = risk_storage_block
            
        
            (c_sinks_excess_dict,
             c_sources_charge_dict,
             c_storages_repair_dict,
             c_converters_repair_dict)  = self._get_repair_nodes(label, repair_options, risk_bus_out)
        
            npp_block.c_sinks_excess = c_sinks_excess_dict
            npp_block.c_sources_charge_dict = c_sources_charge_dict
            npp_block.c_storages_dict = c_storages_repair_dict        
            npp_block.c_converters_repair_dict = c_converters_repair_dict
        
        
        return npp_block
    
    
    def _get_repair_nodes(self, label, repair_options, risk_bus_out):
       
        c_converters_repair_dict = {}
        c_sources_charge_dict = {}
        c_sinks_excess_dict = {}
        c_storages_repair_dict = {}
           
        bus_factory = Generic_bus(self.oemof_es)   
        storage_factory = Generic_storage(self.oemof_es)
        converter_factory = Generic_converter(self.oemof_es)
           
        for name in repair_options:
            
            
            risk_bus_out_2 = bus_factory.create_bus(set_label(label, name, "risk_bus_out_2"))
            risk_bus_out_3 = bus_factory.create_bus(set_label(label, name, "risk_bus_out_3"))
            
            
            c_source_label = set_label(label, name, "source_charge")
            c_sink_label = set_label(label, name, "sink_excess")
            c_converter_label = set_label(label, name, "converter_repair")
            c_storage_label = set_label(label, name, "storage_repair")
            
                        
            c_sink_excess = self.create_sink(c_sink_label, risk_bus_out_3)
            c_source_charge = self.create_source(c_source_label, risk_bus_out_3)
            c_storage_repair = storage_factory.create_storage_for_npp(c_storage_label)
            c_converter_repair = converter_factory.create_converter_double_input(c_converter_label, risk_bus_out, risk_bus_out_2, risk_bus_out_3)








# for i in range(24):
#     solph.constraints.equate_variables(
#         model,
#         model.NonConvexFlowBlock.status[cpp, el_bus, i],
#         model.NonConvexFlowBlock.status[control_bus_npp, control_sink_npp, i],
#     )

# repair_options = {
#     "npp_light_repair": {"cost": 0.1, "duration_days": 7, "start_day": (1, 15), "allow_months": all_months},
#     "npp_heavy_repair": {"cost": 0.2, "duration_days": 14, "start_day": (1, 15), "allow_months": all_months},
#     "npp_capital_repair": {"cost": 0.3, "duration_days": 21, "start_day": (1, 15), "allow_months": all_months},
# }   
        
    
class Generic_storage:

    def __init__(self, oemof_es):
        self.oemof_es = oemof_es
        self.constraints = {}
    
 
    def create_storage_for_npp(
        self,
        label,
        input_bus,
        output_bus,
        capacity,
        max_storage_level,
        in_min_pow_lst,
        in_max_pow_lst
        ):

        storage = solph.components.GenericStorage(
            label=label,
            nominal_storage_capacity=capacity,
            inputs={input_bus: solph.Flow()},
            outputs={output_bus: solph.Flow()},
        )
        
        storage.inputs_pair = [(input_bus, storage)]
        storage.outputs_pair = [(storage, output_bus)]

        self.oemof_es.add(storage)
        return storage
 
 
    
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
    
    
    def create_converter_double_input(self, label, input_bus_1, input_bus_2, output_bus):
        
        converter = solph.components.Converter(
            label=label,
            inputs={input_bus_1: solph.Flow(), input_bus_2: solph.Flow()},
            outputs={output_bus: solph.Flow()},
        )
        
        converter.inputs_pair = [(input_bus_1, converter), (input_bus_2, converter)]
        converter.outputs_pair = [(converter, output_bus)]

        self.oemof_es.add(converter)
        return converter
            
