import numpy as np
import oemof.solph as solph

from src.npp_load_factor_calculator.utilites import (
    check_sequential_years,
    get_profile_by_period_for_charger,
    get_profile_with_first_day,
    get_time_pairs_lst,
    get_valid_profile_by_months,
    hours_between_years,
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
            "default_risk_constr": set(),
            "storage_charge_discharge_constr": set(),
            "source_converter_n_n_plus_1_constr": set(),
            "repairing_in_single_npp":  set(),
            "repairing_type_for_different_npp": set(),
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


    def get_constraints(self):
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
                nominal_value=1,
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
    
    

    

    def create_npp_block(
        self,
        label,
        nominal_power,
        output_bus,
        var_cost,
        risk_mode,
        repair_mode,
        risk_per_hour,
        max_risk_level,
        fix_risk_lst,
        repair_options,
    ):
        
        keyword_dict = {repair_name: {(label, repair_name,"npp_stop"): True} for repair_name in repair_options if repair_options[repair_name]["npp_stop"]}
        custom_attributes = {f"{k}_{list(v.keys())[0][2]}" : True for k, v in keyword_dict.items()}
        
        npp_block = solph.components.Source(
            label=label,
            outputs={
                output_bus: solph.Flow(
                    nominal_value=nominal_power,
                    max=1,
                    min=1,
                    variable_costs=var_cost,
                    nonconvex=solph.NonConvex(),
                    custom_attributes=custom_attributes,
                )
            },
        )
                
        npp_block.inputs_pair = None 
        npp_block.outputs_pair = [(npp_block, output_bus)]
        npp_block.npp_keyword_dict = keyword_dict
        self.oemof_es.add(npp_block)
        
        if risk_mode:
            bus_factory = Generic_bus(self.oemof_es)
            risk_bus_in = bus_factory.create_bus(set_label(label, "risk_bus_in"))
            main_risk_bus = bus_factory.create_bus(set_label(label, "risk_bus_out"))
            main_risk_source = self.create_source_fixed(set_label(label, "risk_source"), risk_bus_in, fix_risk_lst)
            storage_factory = Generic_storage(self.oemof_es)
            main_risk_storage = storage_factory.create_storage(
                input_bus=risk_bus_in,
                output_bus=main_risk_bus,
                capacity=max_risk_level,
                initial_storage_level=0
            )
            npp_block.repair_mode = repair_mode
            npp_block.risk_source = main_risk_source
            npp_block.risk_storage = main_risk_storage

            if risk_per_hour:
                default_risk_source = self.create_source_nonconvex(
                    set_label(label, "default_risk_source"),
                    output_bus=risk_bus_in,
                    power=risk_per_hour,
                    min_val = 1,
                    max_val = 1)
                npp_block.default_risk_mode = True
                npp_block.default_risk_source = default_risk_source
                self.constraints["default_risk_constr"].add(((npp_block, output_bus),(default_risk_source, risk_bus_in)))
        
            if repair_mode:
                repair_nodes = self._get_repair_nodes(label, npp_block, repair_options, main_risk_bus)
                npp_block.repair_nodes = repair_nodes
        
        
        return npp_block
    

    def _get_repair_nodes(self, label, npp_block, repair_options, converter_main_risk_in_bus):
       
        bus_factory = Generic_bus(self.oemof_es)   
        storage_factory = Generic_storage(self.oemof_es)
        converter_factory = Generic_converter(self.oemof_es)
        sink_factory = Generic_sink(self.oemof_es)
           
        general_bus = bus_factory.create_bus(set_label(label, "source_control_output_bus"))   
        converter_out_bus = bus_factory.create_bus(set_label(label, "converter_out_bus"))

        sink_for_source_period = sink_factory.create_sink(set_label(label, "sink_for_source_period"), general_bus)
        sink_for_repair_converters = sink_factory.create_sink(set_label(label, "sink_for_repair_converters"), converter_out_bus)   
        
        # sink for repair one for model
        repair_nodes = {"sink_for_source_period": sink_for_source_period, "sink_for_repair_converters": sink_for_repair_converters}
           
        npp_keyword_dict = npp_block.npp_keyword_dict
                       
        s,e = self.start_year, self.end_year
           
        for name in repair_options:
            
            repair_nodes[name] = {}
            
            source_repair_label = set_label(label, name, "source_repair")
            converter_label = set_label(label, name, "converter_repair")
            storage_repair_label = set_label(label, name, "storage_repair")
            converter_keyword = f"{name}_converter_keyword"
            
            max_count_status = repair_options[name]["max_count_in_year"]["status"]
            
            max_power_profile_source = self._get_source_profile(s, e, repair_options[name])
            converter_max_power_profile = get_valid_profile_by_months(s, e, repair_options[name]["avail_months"])
            converter_power = repair_options[name]["risk_reducing"] / (repair_options[name]["duration"] * 24)
            converter_startup_cost = repair_options[name]["cost"]
            converter_minuptime = repair_options[name]["duration"] * 24
            storage_capacity = converter_power * converter_minuptime

            # plot_array(max_power_profile_source)
            # plot_array(max_power_profile_converter)
                        
            # проверить и переименовать bus
                        
                        
            converter_limit_in_bus = bus_factory.create_bus(set_label(label, name, "converter_limit_in_bus"))
            
            source_repair = self.create_source_with_max_profile(
                source_repair_label,
                converter_out_bus,
                max_power_profile_source,
                ) # доступные часы зарядки

            storage_repair = storage_factory.create_storage_for_npp(
                storage_repair_label,
                converter_out_bus,
                converter_limit_in_bus,
                storage_capacity,
                ) # constraint нельзя одновременно заряжать и разряжать

                
            if max_count_status:
                
                storage_period_label = set_label(label, name, "storage_period")
                source_period_label = set_label(label, name, "source_period")

                storage_period = storage_factory.create_storage_period_level(storage_period_label, repair_options[name])
                
                storage_perios_bus_in = storage_period.inputs_pair[0][0]
                storage_period_bus_out = storage_period.outputs_pair[0][1]

                max_power_profile_source_period = get_profile_with_first_day(s, e)

                source_period = self.create_source_with_max_profile(source_period_label, storage_perios_bus_in, max_power_profile_source_period)

                repair_nodes[name] |= {"storage_period": storage_period,"source_period": source_period}
                
                self.constraints["storage_charge_discharge_constr"].add(storage_period.keyword)

            else: 
                storage_period_bus_out = None


            npp_keyword, converter_keyword = self._get_npp_converter_keywords(name, npp_keyword_dict)

            # переделать на source.output_bus
            converter_repair = converter_factory.create_converter_double_input(
                converter_label,
                converter_power,
                converter_main_risk_in_bus,
                converter_limit_in_bus,
                storage_period_bus_out,
                converter_out_bus,
                converter_max_power_profile,
                converter_minuptime,
                converter_startup_cost,
                npp_keyword,
                converter_keyword,
                )  # constraint нельзя одновременно ремонтировать несколько аэс, доступные месяцы работы


            # переделать
            repair_nodes[name] |= {
                "storage_repair": storage_repair,
                "converter_repair": converter_repair,
                "source_repair": source_repair,
            }

            # начало ремонта в точные даты

            time_pair_lst = get_time_pairs_lst(s, e, repair_options[name])
            self.constraints["source_converter_n_n_plus_1_constr"].add(
                [source_repair.outputs_pair[0],
                 converter_repair.outputs_pair[0], time_pair_lst]
                ) 
            # только в соседних точках (во всех нельзя т.к. во время ремонта несовм. статусы)
            
            self.constraints["repairing_type_for_different_npp"].add(converter_keyword)
            self.constraints["repairing_in_single_npp"].add(npp_keyword)
            self.constraints["storage_charge_discharge_constr"].add(storage_repair.keyword)
            
            
        return repair_nodes
    
    
    def _get_source_profile(self, s, e, repair_options):
        start_day = repair_options["start_day"]
        source_profile_status = start_day["status"]
        if source_profile_status:
            source_profile = get_profile_by_period_for_charger(s, e, start_day)
        else:
            source_profile = np.full(hours_between_years(s, e), 1)
        return source_profile


    def _get_npp_converter_keywords(self, name, npp_keyword_dict):

        if name in npp_keyword_dict:
            npp_keyword = npp_keyword_dict[name]
            converter_keyword = {set_label(name,"converter_keyword"): True}
        else:
            npp_keyword = converter_keyword = None

        return npp_keyword, converter_keyword


    
class Generic_storage:

    def __init__(self, oemof_es):
        self.es = oemof_es
        self.constraints = {}
    
    
    def create_storage_period_level(self, label, repair_options_name):

        bus_factory = Generic_bus(self.oemof_es)
        
        input_bus = bus_factory.create_bus(set_label(label, "input_bus"))
        output_bus = bus_factory.create_bus(set_label(label, "output_bus"))
        
        converter_power = repair_options_name["risk_reducing"] / (repair_options_name["duration"] * 24)
        capacity = (converter_power * repair_options_name["duration"] * repair_options_name["max_count_in_year"]["count"] * 24) * converter_power
        
        
        
        keyword = f"{label}_keyword"

        storage = solph.components.GenericStorage(
            label=label,
            nominal_storage_capacity=capacity,
            inputs={
                input_bus: solph.Flow(
                    nominal_value=1e8,
                    nonconvex=solph.NonConvex(),
                    custom_attributes={keyword: True},
                )
            },
            outputs={
                output_bus: solph.Flow(
                    nominal_value=1e8,
                    nonconvex=solph.NonConvex(),
                    custom_attributes={keyword: True},
                )
            },
            balanced=False,
        )
    
        storage.inputs_pair = [(input_bus, storage)]
        storage.outputs_pair = [(storage, output_bus)]
        storage.keyword = keyword
    
        return storage
    
    
 
    def create_storage_for_npp(
        self,
        label,
        input_bus,
        output_bus,
        capacity,
        ):



        keyword = f"{label}_keyword"

        storage = solph.components.GenericStorage(
            label=label,
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
        initial_storage_level,
    ):
              
        # keyword = "storage_keyword"
        
        # max_storage_level = np.append(max_storage_level, max_storage_level[-1])
           
        storage = solph.components.GenericStorage(
            label="аккумулятор риска",
            nominal_storage_capacity=capacity,
            initial_storage_level=initial_storage_level,
            inputs={input_bus: solph.Flow()},
            outputs={output_bus: solph.Flow()},
            balanced=False
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
        main_risk_bus,
        repair_limit_risk_bus,
        storage_repair_bus,
        output_bus,
        max_power_profile,
        minimum_uptime,
        startup_costs,
        keyword_npp,
        keyword_converter,
    ):
        
        inputs = self._get_inputs(main_risk_bus, repair_limit_risk_bus, storage_repair_bus)
        
        converter = solph.components.Converter(
            label=label,
            inputs=inputs,
            outputs={output_bus: solph.Flow(
                nominal_value=pow,
                max=max_power_profile,
                min=0,
                nonconvex=solph.NonConvex(
                    minimum_uptime=minimum_uptime,
                    startup_costs=startup_costs,
                ),
                custom_attributes={
                    keyword_npp: True,
                    keyword_converter: True,
                    } if keyword_npp else None,
                # если приводит к отлючению аэс то есть keyword_npp поэтому нельзя одновременно проводить данные типы реморнтов и поэтому есть keyword_converter
                )},
        )
        
        converter.inputs_pair = [(main_risk_bus, converter), (repair_limit_risk_bus, converter), (storage_repair_bus, converter)]
        converter.outputs_pair = [(converter, output_bus)]
        converter.keyword_npp = keyword_npp
        converter.keyword_converter = keyword_converter
        converter.startup_costs = startup_costs

        self.oemof_es.add(converter)
        return converter, keyword_npp

    def _get_inputs(self, input_bus_1, input_bus_2, input_bus_3):
        inputs = {input_bus_1: solph.Flow(),
                  input_bus_2: solph.Flow(),
                  input_bus_3: solph.Flow()} if input_bus_3 else {
                      input_bus_1: solph.Flow(),
                      input_bus_2: solph.Flow()}
                      
        return inputs
            
