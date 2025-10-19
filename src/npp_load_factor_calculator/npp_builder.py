import numpy as np

from src.npp_load_factor_calculator.generic_models.generic_bus import Generic_bus
from src.npp_load_factor_calculator.generic_models.generic_storage import (
    Generic_storage,
)
from src.npp_load_factor_calculator.utilites import (
    filter_dates_dict_by_npp_stop,
    filter_dates_dict_by_year,
    plot_array,
)
from src.npp_load_factor_calculator.wrappers.wrapper_converter import Wrapper_converter
from src.npp_load_factor_calculator.wrappers.wrapper_sink import Wrapper_sink
from src.npp_load_factor_calculator.wrappers.wrapper_source import Wrapper_source


class NPP_builder:

    def __init__(self, oemof_es, resolution_strategy):
        self.es = oemof_es
        self.resolution_strategy = resolution_strategy
        
                    
    def add_outage_options(self, npp_block_builder, outage_options):
        
        if not outage_options["status"]:
            return
        
        
        bus_factory = Generic_bus(self.es)
        bufer_bus = bus_factory.create_bus(f"{npp_block_builder.label}_bufer_bus", balanced=False)
        control_npp_stop_source = Wrapper_source(self.es, f"{npp_block_builder.label}_control_npp_stop_converter" )
        control_npp_stop_source.update_options({"output_bus": bufer_bus, "nominal_power": 1, "min": 1})

        # control_npp_stop_source.create_pair_no_equal_status_lower_0(npp_block_builder)

        npp_block_builder.create_pair_no_equal_status_equal_1(control_npp_stop_source)
        

        
        
        npp_block_builder.set_info("bufer_bus", bufer_bus)
        npp_block_builder.set_info("control_npp_stop_source", control_npp_stop_source)
        npp_block_builder.set_info("allow_months", outage_options["allow_months"])
        
        start_days_mask = None
        if outage_options["start_of_month"]:
            start_days_mask = self.resolution_strategy.get_months_start_points()
            
        min_outage_duration = self.resolution_strategy.convert_time(outage_options["min_duration"])
        max_outage_duration = self.resolution_strategy.convert_time(outage_options["max_duration"])
        
        mask_for_storage = self.resolution_strategy.get_every_year_first_step_mask()
        coeff = self.resolution_strategy.coeff
            
            
        allow_months = outage_options["allow_months"]
        avail_months_mask = self.resolution_strategy.get_mask_from_first_day_of_months(allow_months, max_outage_duration)
        # plot_array(avail_months_mask, self.resolution_strategy.timeindex)
        grad_mask_min_outage = self.resolution_strategy.get_grad_mask(allow_months, min_outage_duration)
        grad_mask_max_outage = self.resolution_strategy.get_grad_mask(allow_months, max_outage_duration)
        
        # plot_array(grad_mask_min_outage, self.resolution_strategy.timeindex)
        # plot_array(grad_mask_max_outage, self.resolution_strategy.timeindex)
        
        mask = grad_mask_max_outage | grad_mask_min_outage
        
        
        # plot_array(mask, self.resolution_strategy.timeindex)
        
        npp_block_builder.update_options({
            "positive_gradient_limit": mask,
            "negative_gradient_limit": mask,
            })
        
        # npp_block_builder.add_shutdown_cost_by_mask(mask)
    
        
        
        
        control_npp_stop_source.add_specific_status_duration_in_period(
            mode="active",
            min_duration=min_outage_duration,
            avail_months_mask=avail_months_mask,
            start_days_mask=start_days_mask,
            mask=mask_for_storage,
            coeff=coeff,
            max_duration=max_outage_duration
            )
        




    def add_risk_options(self, npp_block_builder, risk_options):
        
        if not risk_options["status"]:
            npp_block_builder.set_info("risk_out_bus_dict", {})
            npp_block_builder.set_info("risks", {})
            return
        
        
        bus_factory = Generic_bus(self.es)
        storage_factory = Generic_storage(self.es)
        
        risk_lst = risk_options["risks"]
        risks = {}
        
        risk_out_bus_dict = {}
        events_sources = {}
        for risk_name, risk_data in risk_lst.items():
            npp_label = npp_block_builder.label
            risk_bus = bus_factory.create_bus(f"{npp_label}_{risk_name}_input_bus")           
            risk_source_builder = Wrapper_source(self.es, f"{npp_label}_{risk_name}_source")
            nominal_power = self.resolution_strategy.convert_risk(risk_data["value"])
            risk_source_builder.update_options({
                "nominal_power": nominal_power,
                "output_bus": risk_bus,
                "min": 1,
            })
            npp_block_builder.create_pair_equal_status(risk_source_builder)
            # risk_source_builder.build()
            risk_out_bus = bus_factory.create_bus(f"{npp_label}_{risk_name}_outbus")
            risk_out_bus_dict[risk_name] = risk_out_bus  
            storage = storage_factory.create_storage(
                label = f"{npp_label}_{risk_name}_storage",
                input_bus = risk_bus,
                output_bus = risk_out_bus,
                capacity = risk_data["max"],
                initial_storage_level=risk_data["start_risk_rel"],
            )
            risks[risk_name] = storage
            
            if risk_data["events"]:
                valid_events = filter_dates_dict_by_year(risk_data["events"], self.es.years)
                valid_events = filter_dates_dict_by_npp_stop(valid_events, npp_block_builder.get_info("allow_months"))
                events_fix_profile = self.resolution_strategy.get_profile_by_events(valid_events)
                events_source_builder = Wrapper_source(self.es, f"{npp_label}_{risk_name}_events_source")
                events_source_builder.update_options({
                    "nominal_power": 1,
                    "output_bus": risk_bus,
                    "fix": events_fix_profile,
                })
                # events_source = events_source_builder.build()
                events_sources[risk_name] = events_source_builder
                
                
        npp_block_builder.set_info("events_sources", events_sources)
        npp_block_builder.set_info("risk_out_bus_dict", risk_out_bus_dict)
        npp_block_builder.set_info("risks", risks)

    
    def add_repair_options(self, npp_block_builder, repair_options):
    
        if not repair_options["status"]:
            npp_block_builder.set_info("repairs_blocks", {})
            npp_block_builder.set_info("repairs_blocks_npp_stop", [])
            npp_block_builder.set_info("repairs_blocks_npp_no_stop", [])
            return
        
        options = repair_options["options"]
    
        repairs_active = {k: v for k, v in options.items() if v["status"]}

        repairs_npp_stop = {k: v for k, v in repairs_active.items() if v["npp_stop"]}
        repairs_npp_no_stop = {k: v for k, v in repairs_active.items() if  not v["npp_stop"]}
    
        repairs_npp_stop_reset = {k: v for k, v in repairs_npp_stop.items() if v["risk_reset"]}
        repairs_npp_stop_reducing = {k: v for k, v in repairs_npp_stop.items() if v["risk_reducing"]}
        repairs_npp_no_stop_reset = {k: v for k, v in repairs_npp_no_stop.items() if v["risk_reset"]}
        repairs_npp_no_stop_reducing = {k: v for k, v in repairs_npp_no_stop.items() if v["risk_reducing"]}
    
    
        risk_out_bus_dict = npp_block_builder.get_info("risk_out_bus_dict")
        risks = npp_block_builder.get_info("risks")
        bufer_bus = npp_block_builder.get_info("bufer_bus")
        control_npp_stop_source = npp_block_builder.get_info("control_npp_stop_source")
        # allow_months = npp_block_builder.get_info("allow_months")
        allow_parallel_repairs_npp_level = repair_options["allow_parallel_repairs_npp_stop_npp_level"]
        
        
            
            
            
        all_risk_set = set(risk_out_bus_dict.keys())
        
        repair_blocks = {}
            
        if repairs_npp_stop:
                        
            if repairs_npp_stop_reset:
                for name, options in repairs_npp_stop_reset.items():
                    repair_risks_dict = dict.fromkeys(options["risk_reset"])
                    selected_risk_bus_set = all_risk_set & repair_risks_dict.keys()
                    repair_converter_builder = Wrapper_converter(self.es, f"{npp_block_builder.label}_{name}_repair_converter" )
                    repair_converter_builder.update_options({
                        "output_bus": bufer_bus,
                        "nominal_power": 1,
                        "min": 1,
                        "min_uptime": self.resolution_strategy.convert_time(options["duration"]),
                        "min_downtime": self.resolution_strategy.convert_time(options["duration"]),
                        "startup_cost": options["startup_cost"],
                        "max_startup": options["max_startup"],
                        "initial_status": 0,
                    })
                    duration = self.resolution_strategy.convert_time(options["duration"])
                    coeff = self.resolution_strategy.coeff
                    repair_converter_builder.add_max_uptime(duration, coeff)
                    
                    
                    control_npp_stop_source.add_base_block_for(repair_converter_builder)
                    if allow_parallel_repairs_npp_level:
                        control_npp_stop_source.add_group_equal_or_greater_1(repair_converter_builder)
                    else:
                        control_npp_stop_source.add_group_equal_1(repair_converter_builder)
                    
                    
                    repair_converter_builder.set_info("forced_in_period", options.get("forced_in_period"))
                    repair_converter_builder.set_info("startup_cost", options["startup_cost"])
                    repair_converter_builder.set_info("npp_stop_required", True)
                    self._add_start_days_if_required(repair_converter_builder, options.get("start_day"))
                    self._add_forced_active_if_required(repair_converter_builder, options.get("forced_in_period"))
                    repair_converter_builder.repair_id = options["id"]
                    repair_blocks[options["id"]] = repair_converter_builder

                    sinks = {}
                    for selected_risk_bus in selected_risk_bus_set:
                        sink_builder = Wrapper_sink(self.es, f"{npp_block_builder.label}_{name}_{selected_risk_bus}_sink")
                        sink_power = risks[selected_risk_bus].nominal_storage_capacity
                        sink_power = self.resolution_strategy.convert_power(sink_power)
                        min_val = options["min"]
                        sink_builder.update_options({
                            "input_bus": risk_out_bus_dict[selected_risk_bus], "nominal_power": sink_power, "min": min_val})
                        sink_builder.create_pair_equal_status(repair_converter_builder)
                        sinks[selected_risk_bus] = sink_builder
                    repair_converter_builder.sinks = sinks
            
    
            if repairs_npp_stop_reducing:
                for name, options in repairs_npp_stop_reducing.items():
                    selected_risk_bus_set = all_risk_set & options["risk_reducing"].keys()
                    repair_converter_builder = Wrapper_converter(self.es, f"{npp_block_builder.label}_{name}_repair_converter" )
                    repair_converter_builder.update_options({
                        "output_bus": bufer_bus,
                        "nominal_power": 1,
                        "min": 1,
                        "min_uptime": self.resolution_strategy.convert_time(options["duration"]),
                        "min_downtime": self.resolution_strategy.convert_time(options["duration"]),
                        "startup_cost": options["startup_cost"],
                        "max_startup": options["max_startup"],
                        "initial_status": 0,
                    })
                    duration = self.resolution_strategy.convert_time(options["duration"])
                    coeff = self.resolution_strategy.coeff
                    repair_converter_builder.add_max_uptime(duration, coeff)
                    
                    
                    control_npp_stop_source.add_base_block_for(repair_converter_builder)
                    
                    if allow_parallel_repairs_npp_level:
                        control_npp_stop_source.add_group_equal_or_greater_1(repair_converter_builder)
                    else:
                        control_npp_stop_source.add_group_equal_1(repair_converter_builder)
                    


                    repair_converter_builder.set_info("forced_in_period", options.get("forced_in_period"))
                    repair_converter_builder.set_info("startup_cost", options["startup_cost"])
                    repair_converter_builder.set_info("npp_stop_required", True)
                    self._add_start_days_if_required(repair_converter_builder, options.get("start_day"))
                    self._add_forced_active_if_required(repair_converter_builder, options.get("forced_in_period"))
                    repair_blocks[options["id"]] = repair_converter_builder

                    sinks = {}
                    for selected_risk_bus in selected_risk_bus_set:
                        sink_builder = Wrapper_sink(self.es, f"{npp_block_builder.label}_{name}_{selected_risk_bus}_sink")
                        risk_reducing = options["risk_reducing"][selected_risk_bus]
                        duration = self.resolution_strategy.convert_time(options["duration"])
                        # grad = self.resolution_strategy.add_one_by_devider(allow_months, options["duration"], 5)
                        # print(len(grad))
                        # plot_array(grad)
                        sink_power =  risk_reducing / duration
                        sink_power = sink_power / coeff
                        min_val = options["min"]
                        sink_builder.update_options({
                            "input_bus": risk_out_bus_dict[selected_risk_bus],
                            "nominal_power": sink_power,
                            "min": min_val,
                            # "positive_gradient_limit": grad,
                            # "negative_gradient_limit": grad
                            })
                        sink_builder.create_pair_equal_status(repair_converter_builder)
                        sinks[selected_risk_bus] = sink_builder
                    repair_converter_builder.sinks = sinks
    
    
        if repairs_npp_no_stop:
            if repairs_npp_no_stop_reset:
                for name, options in repairs_npp_no_stop_reset.items():
                    repair_risks_dict = dict.fromkeys(options["risk_reset"])
                    selected_risk_bus_set = all_risk_set & repair_risks_dict.keys()
                    repair_converter_builder = Wrapper_converter(self.es, f"{npp_block_builder.label}_{name}_repair_converter" )
                    repair_converter_builder.update_options({
                        "output_bus": bufer_bus,
                        "nominal_power": 1,
                        "min": 1,
                        "min_uptime": self.resolution_strategy.convert_time(options["duration"]),
                        "min_downtime": self.resolution_strategy.convert_time(options["duration"]),
                        "startup_cost": options["startup_cost"],
                        "max_startup": options["max_startup"],
                        "initial_status": 0,
                    })
                    duration = self.resolution_strategy.convert_time(options["duration"])
                    repair_converter_builder.add_max_uptime(duration)
                    
                    control_npp_stop_source.create_pair_no_equal_status_lower_0(repair_converter_builder)
                    
                    repair_converter_builder.set_info("forced_in_period", options.get("forced_in_period"))
                    self._add_start_days_if_required(repair_converter_builder, options.get("start_day"))
                    self._add_forced_active_if_required(repair_converter_builder, options.get("forced_in_period"))
                    repair_converter_builder.set_info("startup_cost", options["startup_cost"])
                    repair_converter_builder.set_info("npp_stop_required", False)
                    repair_blocks[options["id"]] = repair_converter_builder

                    sinks = {}
                    for selected_risk_bus in selected_risk_bus_set:
                        sink_builder = Wrapper_sink(self.es, f"{npp_block_builder.label}_{name}_{selected_risk_bus}_sink")
                        sink_power = risks[selected_risk_bus].nominal_storage_capacity
                        min_val = options["min"]
                        sink_builder.update_options({
                            "input_bus": risk_out_bus_dict[selected_risk_bus], "nominal_power": sink_power, "min": min_val})
                        sink_builder.create_pair_equal_status(repair_converter_builder)
                        sinks[selected_risk_bus] = sink_builder
                    repair_converter_builder.sinks = sinks
                    
    
            if repairs_npp_no_stop_reducing:
                for name, options in repairs_npp_no_stop_reducing.items():
                    selected_risk_bus_set = all_risk_set & options["risk_reducing"].keys()
                    repair_converter_builder = Wrapper_converter(self.es, f"{npp_block_builder.label}_{name}_repair_converter" )
                    repair_converter_builder.update_options({
                        "output_bus": bufer_bus,
                        "nominal_power": 1,
                        "min": 1,
                        "min_uptime": self.resolution_strategy.convert_time(options["duration"]),
                        "min_downtime": self.resolution_strategy.convert_time(options["duration"]),
                        "startup_cost": options["startup_cost"],
                        "max_startup": options["max_startup"],
                        "initial_status": 0,
                    })
                    duration = self.resolution_strategy.convert_time(options["duration"])
                    coeff = self.resolution_strategy.coeff
                    repair_converter_builder.add_max_uptime(duration, coeff)
                    
                    control_npp_stop_source.create_pair_no_equal_status_lower_0(repair_converter_builder)
                    
                    repair_converter_builder.set_info("forced_in_period", options.get("forced_in_period"))
                    repair_converter_builder.set_info("startup_cost", options["startup_cost"])
                    repair_converter_builder.set_info("npp_stop_required", False)
                    self._add_start_days_if_required(repair_converter_builder, options.get("start_day"))
                    self._add_forced_active_if_required(repair_converter_builder, options.get("forced_in_period"))
                    repair_blocks[options["id"]] = repair_converter_builder

                    sinks = {}
                    for selected_risk_bus in selected_risk_bus_set:
                        sink_builder = Wrapper_sink(self.es, f"{npp_block_builder.label}_{name}_{selected_risk_bus}_sink")
                        risk_reducing = options["risk_reducing"][selected_risk_bus]
                        duration = self.resolution_strategy.convert_time(options["duration"])
                        sink_power =  risk_reducing / duration
                        sink_power = sink_power / coeff
                        min_val = options["min"]
                        sink_builder.update_options({
                            "input_bus": risk_out_bus_dict[selected_risk_bus], "nominal_power": sink_power, "min": min_val})
                        sink_builder.create_pair_equal_status(repair_converter_builder)
                        sinks[selected_risk_bus] = sink_builder
                    repair_converter_builder.sinks = sinks
        
        
        repair_blocks_npp_stop = [block for block in repair_blocks.values() if block.info["npp_stop_required"]]
        repair_blocks_npp_no_stop = [block for block in repair_blocks.values() if not block.info["npp_stop_required"]]
        
        npp_block_builder.set_info("repairs_blocks", repair_blocks)
        npp_block_builder.set_info("repairs_blocks_npp_stop", repair_blocks_npp_stop)
        npp_block_builder.set_info("repairs_blocks_npp_no_stop", repair_blocks_npp_no_stop)
        
        
    def _add_start_days_if_required(self, repair_source_builder, start_day):
        if not start_day:
            return
        if not start_day["status"]:
            return
        
        startup_mask = self.resolution_strategy.get_start_points(start_day["days"])
        repair_source_builder.add_startup_cost_by_mask(startup_mask)
          
        
        
    def _add_forced_active_if_required(self, repair_source_builder, forced_in_period):
        if forced_in_period:
            last_step_mask = self.resolution_strategy.get_last_step_mask()
            coeff = self.resolution_strategy.coeff
            repair_duration = repair_source_builder.options["min_uptime"]
            repair_source_builder.add_specific_status_duration_in_period(
                mode = "active",
                min_duration = repair_duration,
                avail_months_mask = 1,
                start_days_mask = None,
                mask = last_step_mask,
                coeff = coeff
                )
            

    def create(
        self,
        label,
        nominal_power,
        output_bus,
        var_cost,
        min_uptime,
        risk_options,
        repair_options,
        outage_options,
    ):
        

        min_uptime = self.resolution_strategy.convert_time(min_uptime)
        
        npp_block_builder = Wrapper_source(self.es, label)
        npp_block_builder.update_options({
            "nominal_power": nominal_power,
            "output_bus": output_bus,
            "var_cost": var_cost,
            "min": 1,
            "min_uptime": min_uptime,
        })
        
        self.add_outage_options(npp_block_builder, outage_options)
        
        self.add_risk_options(npp_block_builder, risk_options)
        
        self.add_repair_options(npp_block_builder, repair_options)
        
        npp_block_builder.set_info("nominal_power", nominal_power)        

        return npp_block_builder


    

    

