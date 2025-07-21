import oemof.solph as solph

from src.npp_load_factor_calculator.utilites import (
    get_profile_by_period_for_charger,
    get_valid_profile_by_months,
    plot_array,
    set_label,
)


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
                
    def set_years(self, start_year, end_year):
        self.start_year = start_year
        self.end_year = end_year

    def get_npp_constraints(self):
        return self.npp_constraints
    
    
    def create_source_with_max_profile(self, label, output_bus, max_profile):
        
        source = solph.components.Source(
            label = label,
            outputs = {output_bus: solph.Flow(nominal_value=1e6, min=0, max=max_profile, nonconvex=solph.NonConvex())}
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
        # min_pow_lst,
        # max_pow_lst,
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
        # constraint (когда работает аэс то ремонт не происходит/или происходит/опционально) npp_block и c_sinks_repair_dict)
        # constraint (если есть другие аэс то одновременно не чинить) 
                
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
                 # constraint когда работает аэс то есть дефолтный риск npp_block и default_risk_source 

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
            # по типам элементов или по видам ремонта
        
        
            npp_block.c_sinks_excess = c_sinks_excess_dict
            npp_block.c_sources_charge_dict = c_sources_charge_dict
            npp_block.c_storages_dict = c_storages_repair_dict        
            npp_block.c_converters_repair_dict = c_converters_repair_dict
        
        
        return npp_block
    
    
    def _get_repair_nodes(self, label, repair_options, converter_main_risk_in_bus):
       
        c_converters_repair_dict = {}
        c_sources_charge_dict = {}
        c_sinks_excess_dict = {}
        c_storages_repair_dict = {}
           
        bus_factory = Generic_bus(self.oemof_es)   
        storage_factory = Generic_storage(self.oemof_es)
        converter_factory = Generic_converter(self.oemof_es)
        sink_factory = Generic_sink(self.oemof_es)
           
        for name in repair_options:
            
            
            converter_limit_in_bus = bus_factory.create_bus(set_label(label, name, "risk_bus_out_2"))
            converter_out_bus = bus_factory.create_bus(set_label(label, name, "risk_bus_out_3"))
            
            
            c_source_label = set_label(label, name, "source_charge")
            c_sink_label = set_label(label, name, "sink_excess")
            c_converter_label = set_label(label, name, "converter_repair")
            c_storage_label = set_label(label, name, "storage_repair")
            
                        
            
            max_power_profile_source = get_profile_by_period_for_charger(self.start_year, self.end_year, repair_options[name]["start_day"])




            max_power_profile_converter = get_valid_profile_by_months(self.start_year, self.end_year, repair_options[name]["avail_months"])
            converter_power = repair_options[name]["risk_reducing"] / (repair_options[name]["duration"] * 24)
            converter_startup_cost = repair_options[name]["cost"]
            converter_minuptime = repair_options[name]["duration"] * 24


            storage_capacity = converter_power * converter_minuptime



            # plot_array(max_power_profile_source)
            # plot_array(max_power_profile_converter)
                        
                        
            c_sink = sink_factory.create_sink(
                c_sink_label,
                converter_out_bus
                )
            
            c_source = self.create_source_with_max_profile(
                c_source_label,
                converter_out_bus,
                max_power_profile_source
                ) # доступные часы зарядки

            c_storage = storage_factory.create_storage_for_npp(
                c_storage_label,
                converter_out_bus,
                converter_limit_in_bus,
                storage_capacity,


                ) # constraint нельзя одновременно заряжать и разряжать рассчитать емкость


            c_converter = converter_factory.create_converter_double_input(
                    c_converter_label,
                    converter_power,
                    converter_main_risk_in_bus,
                    converter_limit_in_bus,
                    converter_out_bus,
                    max_power_profile_converter,
                    converter_minuptime,
                    converter_startup_cost,
                ) # constraint нельзя одновременно ремонтировать несколько аэс, доступные месяцы работы

            # constraint converter и source работают одновременно на n и n + 1 (или нет если точное начало ремонта не важно)




    
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

        # initial_content = 1

        storage = solph.components.GenericStorage(
            label=label,
            nominal_storage_capacity=capacity,
            inputs={input_bus: solph.Flow(nominal_value=1e8, nonconvex=solph.NonConvex())},
            outputs={output_bus: solph.Flow(nominal_value=1e8, nonconvex=solph.NonConvex())},
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
    
    
    def create_converter_double_input(self, label, pow, input_bus_1, input_bus_2, output_bus, max_power_profile, minimum_uptime, startup_costs):
        
        
        converter = solph.components.Converter(
            label=label,
            inputs={input_bus_1: solph.Flow(), input_bus_2: solph.Flow()},
            outputs={output_bus: solph.Flow(
                nominal_value=pow,
                max=max_power_profile,
                min=1,
                nonconvex=solph.NonConvex(
                    minimum_uptime=minimum_uptime,
                    startup_costs=startup_costs,
                ))},
        )
        
        converter.inputs_pair = [(input_bus_1, converter), (input_bus_2, converter)]
        converter.outputs_pair = [(converter, output_bus)]

        self.oemof_es.add(converter)
        return converter
            
