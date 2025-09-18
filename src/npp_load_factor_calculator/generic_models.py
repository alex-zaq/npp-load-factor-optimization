import numpy as np
import oemof.solph as solph

from src.npp_load_factor_calculator.utilites import (
    check_sequential_years,
)
from src.npp_load_factor_calculator.wrappers.wrapper_converter import Wrapper_converter
from src.npp_load_factor_calculator.wrappers.wrapper_sink import Wrapper_sink
from src.npp_load_factor_calculator.wrappers.wrapper_source import Wrapper_source


class Generic_bus:

    def __init__(self, oemof_es):
        self.es = oemof_es
        
    def create_bus(self, label, balanced = True):
        bus = solph.Bus(label = label, balanced = balanced)
        self.es.add(bus)
        return bus

    
        
class Generic_source:

    def __init__(self, oemof_es):
        self.es = oemof_es
                
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

    
            #     "capital": {
            #     "id": 5,
            #     "status": False,
            #     "cost": 50e6,
            #     "duration": days_to_hours(25),
            #     "min_downtime": days_to_hours(30),
            #     "risk_reset": ("r1", "r2", "r3"),
            #     "risk_reducing": {},
            #     "npp_stop": True,
            #     "forced_freq_year": 1,
            # },
            # "risk_options": {
            #     "r1": {"value": get_r(0.1), "max": 1},
            #     "r2": {"value": get_r(0.1), "max": 1},
            #     "r3": {"value": get_r(0.1), "max": 1},
            #     },
            # "outage_options": {
            #     "start_of_month": False,
            #     "allow_months": all_months - set("jan"),
            #     "fixed_outage_months": "june",
            #     "planning_outage_duration": days_to_hours(30),
            # },
            
              
    def add_outage_options(self, npp_block_builder, outage_options):
        
        if not outage_options["status"]:
            return
        
        s, e = self.start_year, self.end_year

        if outage_options["fixed_outage_month"]:
            fix_profile = get_selected_month_profile(s, e, outage_options["fixed_outage_months"])
            npp_block_builder.update_options({"fixed_outage_months": fix_profile })
            return
        
        max_power_profile = get_max_power_profile_by_month(s, e, outage_options["allow_months"])
        npp_block_builder.update_options({"max_profile_output": max_power_profile})
        
        if outage_options["start_of_month"]:
            mask_profile = get_month_start_points(s, e)
            npp_block_builder.add_status_on_intervals(mask_profile)
        

        planning_outage_duration = outage_options["planning_outage_duration"]
        min_inactive_intervals = {(first_year_hour(y), last_year_hour(y)): planning_outage_duration for y in range(s, e)}
        
        for first_hour, last_hour, planning_outage_duration in min_inactive_intervals.items():
            # bad
            npp_block_builder.add_min_inactive_time_in_period(first_hour, last_hour, planning_outage_duration)



    def add_risk_options(self, npp_block_builder, risk_options):
        
        if not risk_options["status"]:
            return
        
        
        bus_factory = Generic_bus(self.es)
        storage_factory = Generic_storage(self.es)
        
        risk_out_bus_dict = {}
        for risk_name, risk_data in risk_options.items():
            npp_label = npp_block_builder.label
            risk_bus = bus_factory.create_bus(f"{npp_label}_{risk_name}")           
            risk_source_builder = Wrapper_source(self.es, f"{npp_label}_{risk_name}")
            risk_source_builder.update_options({
                "nominal_power": risk_data["value"],
                "output_bus": risk_bus,
            })
            npp_block_builder.create_pair_equal_status(risk_source_builder)
            risk_source_builder.build()
            
            risk_out_bus = bus_factory.create_bus(f"{npp_label}_{risk_name}_outbus")
            risk_out_bus_dict[risk_name] = risk_out_bus  
            storage_factory.create_storage(
                label = f"{npp_label}_{risk_name}_storage",
                input_bus = risk_bus,
                output_bus = risk_out_bus,
                capacity = risk_data["max_risk"],
            )
            
        npp_block_builder.set_info("risk_out_bus_lst", risk_out_bus_dict)
            
            #     "capital": {
            #     "id": 5,
            #     "status": False,
            #     "cost": 50e6,
            #     "duration": days_to_hours(25),
            #     "min_downtime": days_to_hours(30),
            #     "risk_reset": ("r1", "r2", "r3"),
            #     "risk_reducing": {},
            #     "npp_stop": True,
            #     "forced_freq_year": 1,
            # },
    
    def add_repair_options(self, npp_block_builder, repair_options):
    
        if not repair_options["status"]:
            return
    
        repairs_active = {k: v for k, v in repair_options.items() if v["status"]}
        # сделать обязательную работу за период опционально

        repairs_npp_stop = {k: v for k, v in repairs_active.items() if v["npp_stop"]}
        repairs_npp_no_stop = {k: v for k, v in repairs_active.items() if  not v["npp_stop"]}
    
        repairs_npp_stop_reset = {k: v for k, v in repairs_npp_stop.items() if v["risk_reset"]}
        repairs_npp_stop_reducing = {k: v for k, v in repairs_npp_stop.items() if v["risk_reducing"]}
        repairs_npp_no_stop_reset = {k: v for k, v in repairs_npp_no_stop.items() if v["risk_reset"]}
        repairs_npp_no_stop_reducing = {k: v for k, v in repairs_npp_no_stop.items() if v["risk_reducing"]}
    
    
        risk_out_bus_dict = npp_block_builder.get_info("risk_out_bus_dict")
            
        all_risk_set = set(risk_out_bus_dict.keys())
        bus_factory = Generic_bus(self.es)
        bufer_bus = bus_factory.create_bus(f"{npp_block_builder.label}_bufer_bus", balanced=False)
            
        repair_types_dict = {"npp_stop": {}, "npp_no_stop": {}}
            
        if repairs_npp_stop:

            control_npp_stop_source = Wrapper_source(self.es, f"{npp_block_builder.label}_control_npp_stop_converter" )
            control_npp_stop_source.update_options({"output_bus": bufer_bus, "nominal_power": 1, "min": 0})
            control_npp_stop_source.create_pair_keywords_no_equal_status(npp_block_builder)
            control_npp_stop_source.add_keyword_no_equal_status("single_npp_stop_model")
            control_npp_stop_source.build()
                        
            if repairs_npp_stop_reset:
                for name, options in repairs_npp_stop_reset.items():
                    selected_risk_bus_set = all_risk_set & set(options["risk_reset"])
                    repair_source_builder = Wrapper_source(self.es, f"{npp_block_builder.label}_{name}_repair_source" )
                    repair_source_builder.update_options({
                        "output_bus": bufer_bus,
                        "nominal_power": 1,
                        "min": 0,
                        "minup_time": options["duration"],
                        "startup_cost": options["startup_cost"]
                    })
                    repair_source_builder.add_max_up_time(options["duration"])
                    repair_source_builder.create_pair_equal_status(control_npp_stop_source)
                    repair_source_builder.build()

                    for selected_risk_bus in selected_risk_bus_set:
                        sink_builder = Wrapper_sink(self.es, f"{npp_block_builder.label}_{name}_{selected_risk_bus}_sink")
                        sink_builder.update_options({
                            "input_bus": risk_out_bus_dict[selected_risk_bus], "nominal_power": 1e10, "min": 0})
                        sink_builder.create_pair_equal_status(repair_source_builder)
                        sink_builder.build()
            
    
            if repairs_npp_stop_reducing:
                for name, options in repairs_npp_stop_reducing.items():
                    selected_risk_bus_set = all_risk_set & set(options["risk_reducing"])
                    repair_source_builder = Wrapper_source(self.es, f"{npp_block_builder.label}_{name}_repair_source")
                    repair_source_builder.update_options({
                        "output_bus": bufer_bus,
                        "nominal_power": 1,
                        "min": 0,
                        "minup_time": options["duration"],
                        "startup_cost": options["startup_cost"]
                    })
                    repair_source_builder.add_max_up_time(options["duration"])
                    repair_source_builder.create_pair_equal_status(control_npp_stop_source)
                    repair_source_builder.build()

                    for selected_risk_bus in selected_risk_bus_set:
                        sink_builder = Wrapper_sink(self.es, f"{npp_block_builder.label}_{name}_{selected_risk_bus}_sink")
                        power =  options["risk_reducing"][selected_risk_bus] / options["duration"]
                        sink_builder.update_options({
                            "input_bus": risk_out_bus_dict[selected_risk_bus], "nominal_power": power, "min": 1})
                        sink_builder.create_pair_equal_status(repair_source_builder)
                        sink_builder.build()
    
    
        if repairs_npp_no_stop:
            
            if repairs_npp_no_stop_reset:
                for name, options in repairs_npp_no_stop_reset.items():
                    selected_risk_bus_set = all_risk_set & set(options["risk_reset"])
                    repair_source_builder = Wrapper_source(self.es, f"{npp_block_builder.label}_{name}_repair_source" )
                    repair_source_builder.update_options({
                        "output_bus": bufer_bus,
                        "nominal_power": 1,
                        "min": 0,
                        "minup_time": options["duration"],
                        "startup_cost": options["startup_cost"]
                    })
                    repair_source_builder.add_max_up_time(options["duration"])
                    repair_source_builder.create_pair_equal_status(npp_block_builder)
                    repair_source_builder.build()

                    for selected_risk_bus in selected_risk_bus_set:
                        sink_builder = Wrapper_sink(self.es, f"{npp_block_builder.label}_{name}_{selected_risk_bus}_sink")
                        sink_builder.update_options({
                            "input_bus": risk_out_bus_dict[selected_risk_bus], "nominal_power": 1e10, "min": 0})
                        sink_builder.create_pair_equal_status(repair_source_builder)
                        sink_builder.build()
                    
    
            if repairs_npp_no_stop_reducing:
                for name, options in repairs_npp_no_stop_reducing.items():
                    selected_risk_bus_set = all_risk_set & set(options["risk_reducing"])
                    repair_source_builder = Wrapper_source(self.es, f"{npp_block_builder.label}_{name}_repair_source" )
                    repair_source_builder.update_options({
                        "output_bus": bufer_bus,
                        "nominal_power": 1,
                        "min": 0,
                        "minup_time": options["duration"],
                        "startup_cost": options["startup_cost"]
                    })
                    repair_source_builder.add_max_up_time(options["duration"])
                    repair_source_builder.create_pair_equal_status(npp_block_builder)
                    repair_source_builder.build()

                    for selected_risk_bus in selected_risk_bus_set:
                        sink_builder = Wrapper_sink(self.es, f"{npp_block_builder.label}_{name}_{selected_risk_bus}_sink")
                        power =  options["risk_reducing"][selected_risk_bus] / options["duration"]
                        sink_builder.update_options({
                            "input_bus": risk_out_bus_dict[selected_risk_bus], "nominal_power": power, "min": 1})
                        sink_builder.create_pair_equal_status(repair_source_builder)
                        sink_builder.build()
    

            npp_block_builder.set_info("repair_data", repair_types_dict)
            
            
               

                


    def create_npp_block(
        self,
        label,
        nominal_power,
        output_bus,
        var_cost,
        risk_options,
        repair_options,
        outage_options,
    ):
        
        npp_block_builder = Wrapper_source(self.es, label)
        npp_block_builder.update_options({
            "nominal_power": nominal_power,
            "output_bus": output_bus,
            "var_cost": var_cost
        })
        
        self.add_outage_options(npp_block_builder, outage_options)
        
        self.add_risk_options(npp_block_builder, risk_options)
        
        self.add_repair_options(npp_block_builder, repair_options)
        
        npp_block = npp_block_builder.build()
        
        return npp_block


    

    
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
                    min=0,
                    nonconvex=solph.NonConvex(),
                    custom_attributes={keyword : True},
                )
            },
            outputs={
                output_bus: solph.Flow(
                    nominal_value=1e8,
                    min=0,
                    nonconvex=solph.NonConvex(),
                    custom_attributes={keyword : True},
                )
            },
            balanced=False
        )
        
        storage.inputs_pair = [(input_bus, storage)]
        storage.outputs_pair = [(storage, output_bus)]
        storage.keyword = keyword

        self.es.add(storage)
        return storage
 
 
    
    def create_storage(
        self,
        label,
        input_bus,
        output_bus,
        capacity,
        # initial_storage_level,
    ):
              
           
        storage = solph.components.GenericStorage(
            label=label,
            nominal_storage_capacity=capacity,
            # initial_storage_level=initial_storage_level,
            inputs={input_bus: solph.Flow()},
            outputs={output_bus: solph.Flow()},
            balanced=False
        )
        
        storage.inputs_pair = [(input_bus, storage)]
        storage.outputs_pair = [(storage, output_bus)]

        self.es.add(storage)
        return storage
