import oemof.solph as solph

from src.npp_load_factor_calculator.utilites import (
    check_sequential_years,
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
        self.constraints = {
            "default_risk_constr": {"status": False, "constr_seq": []},
            "storage_charge_discharge_constr": {"status": False, "constr_seq": []},
            "source_converter_n_n_plus_1_constr": {"status": False, "constr_seq": []},
            "repairing_in_single_npp": {"status": False, "constr_seq": []},
            "repairing_type_for_different_npp": {"status": False, "constr_seq": []},
        }
                
    def set_years(self, years):
        
        if not check_sequential_years(years):
            raise Exception("Years are not sequential")
        if len(years) == 1:
            self.start_year = years[0]
            self.end_year = years[0] + 1
            return
        else:
            self.start_year = years[0]
            self.end_year = years[1]


    def get_npp_constraints(self):
        return self.constraints
    
    
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
        
    
    def create_source_nonconvex(self, label, output_bus, power, min_val, max_val):
        
        source = solph.components.Source(
            label = label,
            outputs = {output_bus: solph.Flow(
                nominal_value=power,
                min=min_val,
                max=max_val,
                nonconvex=solph.NonConvex()
            )}
        )
        source.inputs_pair = None
        source.outputs_pair = [(source, output_bus)]
        self.oemof_es.add(source)
        return source    
    
    
    
    def create_source_nonconvex_with_keyword(self, label, output_bus, power, min_val, max_val, keyword_1):
        
        
        keyword_2 = f"{label}_keyword_2"
        
        source = solph.components.Source(
            label = label,
            outputs = {output_bus: solph.Flow(
                nominal_value=power,
                min=min_val,
                max=max_val,
                nonconvex=solph.NonConvex(),
                custom_attributes={keyword_1: True, keyword_2: True},
            )}
        )
        source.inputs_pair = None
        source.outputs_pair = [(source, output_bus)]
        source.keyword_1 = keyword_1
        source.keyword_2 = keyword_2
        
        
        self.oemof_es.add(source)
        return source
    
    
    

    def create_npp_block(
        self,
        label,
        nominal_power,
        output_bus,
        var_cost,
        risk_mode,
        risk_per_hour,
        max_risk_level,
        fix_risk_lst,
        repair_options,
    ):
        
        
        keyword = f"{label}_keyword"
        
        npp_block = solph.components.Source(
            label=label,
            outputs={
                output_bus: solph.Flow(
                    nominal_value=nominal_power,
                    max=1,
                    min=0,
                    variable_costs=var_cost,
                    nonconvex=solph.NonConvex(),
                    custom_attributes={
                        keyword: True,

                        },
                )
            },
        )
        # constraint (когда работает аэс то ремонт не происходит/или происходит/опционально) npp_block и c_sinks_repair_dict)
                
                
        npp_block.inputs_pair = None 
        npp_block.outputs_pair = [(npp_block, output_bus)]
        npp_block.keyword = keyword
        self.oemof_es.add(npp_block)
        
        if risk_mode:
            
            bus_factory = Generic_bus(self.oemof_es)
            risk_bus_in = bus_factory.create_bus(set_label(label, "risk_bus_in"))
            main_risk_bus = bus_factory.create_bus(set_label(label, "risk_bus_out"))
            
            
            if risk_per_hour:
                default_risk_source = self.create_source_nonconvex(set_label(label, "default_risk_source"), risk_bus_in, risk_per_hour, 0, 1)
                npp_block.default_risk_mode = True
                npp_block.default_risk_source = default_risk_source
                self.constraints["default_risk_constr"]["constr_seq"].append(((npp_block, output_bus),(default_risk_source, risk_bus_in)))


            risk_source = self.create_source_fixed(set_label(label, "risk_source"), risk_bus_in, fix_risk_lst)
            storage_factory = Generic_storage(self.oemof_es)
            risk_storage_block = storage_factory.create_storage(
                input_bus=risk_bus_in,
                output_bus=main_risk_bus,
                capacity=max_risk_level,
            )
            npp_block.risk_mode = risk_mode
            npp_block.risk_source = risk_source
            npp_block.risk_storage = risk_storage_block
            
            
            repair_nodes = self._get_repair_nodes(label, npp_block, repair_options, main_risk_bus)
            npp_block.repair_nodes = repair_nodes
        
        
        return npp_block
    
    

    def _get_repair_nodes(self, label, npp_block, repair_options, converter_main_risk_in_bus):
       

        repair_nodes = {}
           
        bus_factory = Generic_bus(self.oemof_es)   
        storage_factory = Generic_storage(self.oemof_es)
        converter_factory = Generic_converter(self.oemof_es)
        sink_factory = Generic_sink(self.oemof_es)
        
           
        general_bus = bus_factory.create_bus(set_label(label, "source_control_output_bus"))   
        converter_out_bus = bus_factory.create_bus(set_label(label, "converter_out_bus"))
           
           

        c_sink_general = sink_factory.create_sink(set_label(label, "general_sink"), general_bus)
        c_sink_for_converters = sink_factory.create_sink(set_label(label, "sink_for_converters"), converter_out_bus)   
        
        
        repair_nodes = {"general_sink": c_sink_general, "sink_for_converters": c_sink_for_converters}
           
                                 
           
        for name in repair_options:
            
            c_source_label = set_label(label, name, "source_charge")
            c_converter_label = set_label(label, name, "converter_repair")
            c_storage_label = set_label(label, name, "storage_repair")
            converter_keyword = f"{name}_converter_keyword"
            
            max_power_profile_source = get_profile_by_period_for_charger(self.start_year, self.end_year, repair_options[name]["start_day"])
            converter_max_power_profile = get_valid_profile_by_months(self.start_year, self.end_year, repair_options[name]["avail_months"])
            converter_power = repair_options[name]["risk_reducing"] / (repair_options[name]["duration"] * 24)
            converter_startup_cost = repair_options[name]["cost"]
            converter_minuptime = repair_options[name]["duration"] * 24
            storage_capacity = converter_power * converter_minuptime

            # plot_array(max_power_profile_source)
            # plot_array(max_power_profile_converter)
                        
            # проверить и переименовать bus
                        
                        
            converter_limit_in_bus = bus_factory.create_bus(set_label(label, name, "converter_limit_in_bus"))

            
            c_source = self.create_source_with_max_profile(
                c_source_label,
                converter_out_bus,
                max_power_profile_source,
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
                converter_max_power_profile,
                converter_minuptime,
                converter_startup_cost,
                npp_block.keyword,
                converter_keyword,
                ) # constraint нельзя одновременно ремонтировать несколько аэс, доступные месяцы работы



            repair_nodes[name] = {"sources": c_source,"converters": c_converter,"storages": c_storage}

            # constraint converter и source работают одновременно на n и n + 1 (или нет если точное начало ремонта не важно)(опция)


            self.constraints["source_converter_n_n_plus_1_constr"]["constr_seq"].append((c_source.outputs_pair[0], c_converter.outputs_pair[0])) # начало ремонта в точные даты
            self.constraints["repairing_in_single_npp"].append(npp_block.keyword)
            # self.constraints["repairing_type_for_different_npp"].append(converter_keyword)
                        
            
        return repair_nodes



    def set_repair_type_set(self, repair_type_set):
            self.repair_type_set = repair_type_set


    
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
        ):

        # initial_content = 1

        keyword = f"{label}_keyword"

        storage = solph.components.GenericStorage(
            label=label,
            # initial_storage_level=
            nominal_storage_capacity=capacity,
            inputs={
                input_bus: solph.Flow(
                    nominal_value=1e8,
                    nonconvex=solph.NonConvex(),
                    custom_attributes={keyword : True},
                )
            },
            outputs={
                output_bus: solph.Flow(
                    nominal_value=1e8,
                    nonconvex=solph.NonConvex(),
                    custom_attributes={keyword : True},
                )
            },
            balanced=False
        )
        
        storage.inputs_pair = [(input_bus, storage)]
        storage.outputs_pair = [(storage, output_bus)]
        storage.keyword = keyword

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

    def create_converter_double_input(
        self,
        label,
        pow,
        input_bus_1,
        input_bus_2,
        output_bus,
        max_power_profile,
        minimum_uptime,
        startup_costs,
        keyword_npp,
        keyword_converter,
    ):
        converter = solph.components.Converter(
            label=label,
            inputs={
                input_bus_1: solph.Flow(),
                input_bus_2: solph.Flow(),
                },
            outputs={output_bus: solph.Flow(
                nominal_value=pow,
                max=max_power_profile,
                min=1,
                nonconvex=solph.NonConvex(
                    minimum_uptime=minimum_uptime,
                    startup_costs=startup_costs,
                ),
                custom_attributes={
                    keyword_npp: True,
                    keyword_converter: True,
                    },
                
                )},
        )
        
        converter.inputs_pair = [(input_bus_1, converter), (input_bus_2, converter)]
        converter.outputs_pair = [(converter, output_bus)]
        converter.keyword_nnpp = keyword_npp
        converter.keyword_converter = keyword_converter

        self.oemof_es.add(converter)
        return converter, keyword_npp
            
