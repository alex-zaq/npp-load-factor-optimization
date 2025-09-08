import numpy as np
import oemof.solph as solph

from src.npp_load_factor_calculator.utilites import (
    check_sequential_years,
    get_profile_by_period_for_charger,
    get_profile_with_first_day,
    get_risk_events_profile_for_all_repair_types,
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
        default_risk_options,
        allow_free_cover_peak_mode,
        min_up_time,
        min_down_time,
        max_risk_level,
        main_risk_all_types,
        repair_options,
    ):
        
        keyword_dict, custom_attributes = self._get_npp_keyword_dict_and_custom_attributes(label, repair_options)
        
        npp_block = solph.components.Source(
            label=label,
            outputs={
                output_bus: solph.Flow(
                    nominal_value=nominal_power,
                    max=1,
                    min=1,
                    variable_costs=var_cost,
                    nonconvex=solph.NonConvex(
                        minimum_uptime=min_up_time,
                        minimum_downtime=min_down_time
                        
                        ),
                    custom_attributes=custom_attributes,
                )
            },
        )
                
        npp_block.inputs_pair = None 
        npp_block.outputs_pair = [(npp_block, output_bus)]
        npp_block.npp_keyword_dict = keyword_dict
        npp_block.risk_mode = risk_mode
        npp_block.repair_mode = repair_mode
        npp_block.default_risk_mode = bool(default_risk_options)
        npp_block.main_risk_all_types = main_risk_all_types
        self.oemof_es.add(npp_block)
        
        if risk_mode:
            main_risk_nodes = self._get_storage_main_risk_dict(
                npp_block,
                max_risk_level
                )
            npp_block.main_risk_nodes = main_risk_nodes
            #  добавить присвоения npp из всех методов
            if default_risk_options:
                default_block_nodes = self._get_default_risk_blocks(
                    npp_block,
                    default_risk_options,
                    )
            npp_block.default_risk_nodes = default_block_nodes
        
            if repair_mode:
                repair_nodes = self._get_repair_nodes(
                    npp_block,
                    repair_options,
                    allow_free_cover_peak_mode,
                    main_risk_all_types,
                )
                npp_block.repair_nodes = repair_nodes
        
        return npp_block

    def _get_npp_keyword_dict_and_custom_attributes(self, label, repair_options):
        keyword_dict = {
            repair_name: {(label, repair_name, "npp_stop"): True}
            for repair_name in repair_options
            if repair_options[repair_name]["npp_stop"]
        }
        custom_attributes = {
            f"{k}_{list(v.keys())[0][2]}": True for k, v in keyword_dict.items()
        }
        return keyword_dict, custom_attributes
    
    
    def _get_default_risk_blocks(self, npp_block, default_risk_options):
        risk_bus_in = 0
        label = npp_block.label
        repair_name, default_risk_pow = default_risk_options.items()[0]
        main_risk_all_types = npp_block.main_risk_all_types
        all_repair_types = set(main_risk_all_types.keys())
        if repair_name not in all_repair_types:
            raise Exception("There is no such repair type")
        source_default_risk = self.create_source_nonconvex(
                set_label(label, "source_default_risk"),
                output_bus=risk_bus_in,
                power=default_risk_pow,
                min_val=1,
                max_val=1,
            )
        source_default_risk.outputs_pair = [(source_default_risk, risk_bus_in)]
        default_risk_nodes = {"source_default_risk": source_default_risk}
        self.constraints["default_risk_constr"].add((npp_block.outputs_pair[0], source_default_risk.outputs_pair[0]))
        return default_risk_nodes


    def _get_storage_main_risk_dict(self, npp_block, max_risk_level):
        storages = []
        main_risk_nodes = {}
        bus_factory = Generic_bus(self.oemof_es)
        storage_factory = Generic_storage(self.oemof_es)
        main_risk_all_types = npp_block.main_risk_all_types
        label = npp_block.label
        # можно поставить огр. одну storage
        # можно ли не задавать емкость
        for r_names_tuple, profile in main_risk_all_types.items():
            repairs_str = set_label(*r_names_tuple)
            main_risk_storage_in_bus = bus_factory.create_bus(set_label(label, "main_risk_bus", repairs_str))
            main_risk_storage_out_bus = bus_factory.create_bus(set_label(label, "risk_bus_out", repairs_str))
            source = self.create_source_fixed(
                set_label(label, "risk_source", repairs_str),
                main_risk_storage_out_bus,
                profile
            )
            storage = storage_factory.create_storage(
                label=set_label(label, "storage_main_risk", repairs_str),
                input_bus=main_risk_storage_in_bus,
                output_bus=main_risk_storage_out_bus,
                capacity=None,
            )
            main_risk_nodes[r_names_tuple] = {"source": source, "storage": storage, "profile": profile}
            storages.append(storage)
        self.constraints["max_risk_level_constr"] = max_risk_level
        self.constraints["storage_main_risk_lst"] = storages
        return main_risk_nodes


    def _get_repair_nodes(
        self,
        npp_block,
        repair_options,
        allow_free_cover_peak_mode,
    ):
       
        bus_factory = Generic_bus(self.oemof_es)   
        storage_factory = Generic_storage(self.oemof_es)
        converter_factory = Generic_converter(self.oemof_es)
        sink_factory = Generic_sink(self.oemof_es)
        label = npp_block.label
        s,e = self.start_year, self.end_year
           
        general_converters_bus = bus_factory.create_bus(set_label(label, "general_converters_bus"))
        sink_for_converters = sink_factory.create_sink(set_label(label, "sink_for_converters"), general_converters_bus)   
        repair_nodes = {"sink_for_converters": sink_for_converters}
        
           
        for repair_name in repair_options:
            
            repair_nodes[repair_name] = {}
            
            storage_repair_label = set_label(label, repair_name, "source_repair")
            storage_repair_label = set_label(label, repair_name, "storage_repair")
            
            
            max_count_status = repair_options[repair_name]["max_count_in_year"]["status"]
            
            max_power_profile_source = self._get_source_profile(s, e, repair_options[repair_name])
            repair_avail_profile = get_valid_profile_by_months(s, e, repair_options[repair_name]["avail_months"])
            power, startup_cost, minuptime, capacity = self._get_repair_block_options(repair_options, repair_name)

                       
            
            storage_repair_control_bus = bus_factory.create_bus(set_label(label, repair_name, "storage_repair_control_bus"))
            storage_repair_fuel_bus = bus_factory.create_bus(set_label(label, repair_name, "storage_repair_fuel_bus"))
            
            source_repair = self.create_source_with_max_profile(
                storage_repair_label,
                output_bus=storage_repair_fuel_bus,
                max_profile=max_power_profile_source,
                ) # доступные часы зарядки

            storage_repair = storage_factory.create_storage_for_npp(
                storage_repair_label,
                input_bus=storage_repair_fuel_bus,
                output_bus=storage_repair_control_bus,
                capacity=capacity,
            ) # constraint нельзя одновременно заряжать и разряжать

                
            if max_count_status:
                
                storage_period_label = set_label(label, repair_name, "storage_period")
                source_period_label = set_label(label, repair_name, "source_period")

                storage_period_fuel_bus = bus_factory.create_bus(set_label(label, repair_name, "storage_period_fuel_bus"))
                storage_period_control_bus = bus_factory.create_bus(set_label(label, repair_name, "storage_period_control_bus"))

                storage_period = storage_factory.create_storage_period_level(
                    storage_period_label,
                    input_bus=storage_period_fuel_bus,
                    output_bus=storage_period_control_bus,
                    repair_options_name=repair_options[repair_name]
                )

                max_profile_source_period = get_profile_with_first_day(s, e)

                source_period = self.create_source_with_max_profile(source_period_label, storage_period_fuel_bus, max_profile_source_period)
                sink_period = sink_factory.create_sink(set_label(label, "sink_for_source_period"), storage_period_fuel_bus)

                repair_nodes[repair_name] |= {
                    "storage_period": storage_period,
                    "source_period": source_period,
                    "sink_period": sink_period,
                }
                
                self.constraints["storage_charge_discharge_constr"].add(storage_period.keyword)

            else: 
                storage_period_control_bus = None
                

            converter_repair = converter_factory.create_converter_double_input(
                npp_block,
                repair_name,
                power,
                storage_repair_control_bus,
                storage_period_control_bus,
                general_converters_bus,
                repair_avail_profile,
                minuptime,
                startup_cost,
            )  # constraint нельзя одновременно ремонтировать несколько аэс, доступные месяцы работы


            if allow_free_cover_peak_mode:
                sink_peak_lst = self._get_sink_for_risk_peak(npp_block, repair_name, npp_block.main_risk_nodes)
                self.constraints["sink_peak_converter_constr"] = self.get_sink_peak_constraints(sink_peak_lst, converter_repair)
                repair_nodes[repair_name] |= {"sink_peak_lst": sink_peak_lst}



            repair_nodes[repair_name] |= {
                "storage_repair": storage_repair,
                "converter_repair": converter_repair,
                "source_repair": source_repair,
            }

            # начало ремонта в точные даты
            # check
            start_time_pairs_lst = get_time_pairs_lst(s, e, repair_options[repair_name])
            self.constraints["source_converter_n_n_plus_1_constr"].add(
                [source_repair.outputs_pair[0], converter_repair.outputs_pair[0], start_time_pairs_lst]) 
            # только в соседних точках (во всех нельзя т.к. во время ремонта несовм. статусы)
            
            self.constraints["repairing_type_for_different_npp"].add(converter_repair.keywords["no_parralel"])
            self.constraints["repairing_in_single_npp"].add(converter_repair.keywords["npp_stop"])
            self.constraints["storage_charge_discharge_constr"].add(storage_repair.keyword)
            
            
        return repair_nodes
    
    
    def _get_sink_peak_constraints(self, sink_peak_lst, converter_repair):
        res = set()
        for sink_peak in sink_peak_lst:
            res.add((sink_peak.inputs_pair[0], converter_repair.outputs_pair[0]))
        return res
    

    def _get_repair_block_options(self, repair_options, repair_name):
        converter_power = repair_options[repair_name]["risk_reducing"] / (repair_options[repair_name]["duration"] * 24)
        converter_startup_cost = repair_options[repair_name]["cost"]
        converter_minuptime = repair_options[repair_name]["duration"] * 24
        storage_capacity = converter_power * converter_minuptime
        return converter_power,converter_startup_cost,converter_minuptime,storage_capacity
    
    
    
    
    def _get_sink_for_risk_peak(self, npp_block, repair_name, main_risk_nodes):
        
        sink_peak_lst = []
        label = npp_block.label
        filtered_main_risk_nodes = {k:v for k,v in main_risk_nodes.items() if repair_name in k}

        for repair_types_tuple, data in filtered_main_risk_nodes.items():
            source_main_risk = data["source"]
            profile = data["profile"]
            main_risk_out_bus = source_main_risk["outputs_pair"][0][1]
            sink_peak = solph.components.Sink(
                label=set_label(label, "sink_peak", *repair_types_tuple),
                inputs={
                    main_risk_out_bus: solph.Flow(
                        nominal_value=1,
                        max=profile,
                        min=0,
                        nonconvex=solph.NonConvex(),
                    )
                },
            )
            sink_peak.inputs_pair = [(main_risk_out_bus, sink_peak)]
            sink_peak_lst.append(sink_peak)
            self.oemof_es.add(sink_peak)
        
        return sink_peak_lst
    
    
    def _get_source_profile(self, s, e, repair_options):
        start_day = repair_options["start_day"]
        source_profile_status = start_day["status"]
        if source_profile_status:
            source_profile = get_profile_by_period_for_charger(s, e, start_day)
        else:
            source_profile = np.full(hours_between_years(s, e), 1)
        return source_profile


    
class Generic_storage:

    def __init__(self, oemof_es):
        self.es = oemof_es
        self.constraints = {}
    
    
    def create_storage_period_level(self, label, input_bus, output_bus, repair_options_name):

        # bus_factory = Generic_bus(self.oemof_es)
        
        # input_bus = bus_factory.create_bus(set_label(label, "input_bus"))
        # output_bus = bus_factory.create_bus(set_label(label, "output_bus"))
        
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
        label,
        input_bus,
        output_bus,
        capacity,
        initial_storage_level,
    ):
              
           
        storage = solph.components.GenericStorage(
            label=label,
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
        npp_block,
        repair_name,
        power,
        storage_repair_control_bus,
        storage_period_control_bus,
        general_converters_bus,
        repair_avail_profile,
        minimum_uptime,
        startup_costs,
    ):
        
        converter_label = set_label(npp_block.label, repair_name, "converter_repair")

        # bad
        npp_stop_keyword, no_parralel_keyword = self._get_npp_converter_keywords(repair_name, npp_block.npp_keyword_dict)
        custom_attributes = self._get_custom_attributes(npp_stop_keyword, no_parralel_keyword)
        
        bus_factory = Generic_bus(self.oemof_es)
        main_input_bus = bus_factory.create_bus(set_label(converter_label, "main_input_bus"))
        
        inner_converters = self._add_converter_different_output_bus(converter_label, main_input_bus, repair_name, npp_block.main_risk_nodes)
        
        inputs = {}
        inputs[main_input_bus] = solph.Flow()
        if storage_period_control_bus is not None:
            inputs[storage_period_control_bus] = solph.Flow()
        
        converter = solph.components.Converter(
            label=converter_label,
            inputs=inputs,
            outputs={
                general_converters_bus: solph.Flow(
                    nominal_value=power,
                    max=repair_avail_profile,
                    min=repair_avail_profile,
                    nonconvex=solph.NonConvex(
                        minimum_uptime=minimum_uptime,
                        startup_costs=startup_costs,
                    ),
                    custom_attributes=custom_attributes,
                )
            },
        )
        
        converter.inputs_pair = [(input_bus, converter) for input_bus,_ in converter.inputs.items()]
        converter.outputs_pair = [(converter, general_converters_bus)]
        converter.startup_costs = startup_costs
        converter.inner_converters = inner_converters
        converter.keywords = {"npp_stop": npp_stop_keyword, "no_parralel": no_parralel_keyword}

        self.oemof_es.add(converter)
        return converter
    
    
    def _add_converter_different_output_bus(self, converter_label, main_input_bus, repair_name, main_risk_nodes):
        converters = []
        filtered_main_risk_nodes = {k:v for k,v in main_risk_nodes.items() if repair_name in k}
        for repair_names_tuple, data in filtered_main_risk_nodes.items():
            storage_output_bus = data["storage"].outputs_pair[0][1]
            converter = solph.components.Converter(
                label=set_label(converter_label, *repair_names_tuple),
                inputs={storage_output_bus: solph.Flow()},
                outputs={main_input_bus: solph.Flow()},
            )
            converter.inputs_pair = [(storage_output_bus, converter)]
            converter.outputs_pair = [(converter, main_input_bus)]
            converters.append(converter)
            self.oemof_es.add(converter)
        return converters
    
    
    def _get_npp_converter_keywords(self, repair_name, npp_keyword_dict):

        if repair_name in npp_keyword_dict:
            npp_keyword = npp_keyword_dict[repair_name]
            converter_keyword = {set_label(repair_name,"converter_keyword"): True}
        else:
            npp_keyword = converter_keyword = None

        return npp_keyword, converter_keyword
    
    
    def _get_custom_attributes(self, keyword_npp_stop, keyword_converter):
        # если приводит к отлючению аэс то есть keyword_npp поэтому нельзя одновременно проводить данные типы ремонтов и поэтому есть keyword_converter
        if keyword_npp_stop:
            res = {keyword_npp_stop: True, keyword_converter: True}
        else:
            res = None
        return res


    def _get_converter_inputs(self, input_bus_1, input_bus_2, input_bus_3):
        inputs = {input_bus_1: solph.Flow(), input_bus_2: solph.Flow()}
        if input_bus_3:
            inputs[input_bus_3] = solph.Flow()
        return inputs
            
