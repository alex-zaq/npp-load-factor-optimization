from src.npp_load_factor_calculator.generic_models.generic_bus import Generic_bus
from src.npp_load_factor_calculator.generic_models.generic_storage import (
    Generic_storage,
)
from src.npp_load_factor_calculator.utilites import (
    check_sequential_years,
    get_avail_months_profile,
    get_every_year_first_step_mask,
    get_fix_months_profile,
    get_last_step_mask,
    get_months_start_points,
    plot_array,
)
from src.npp_load_factor_calculator.wrappers.wrapper_sink import Wrapper_sink
from src.npp_load_factor_calculator.wrappers.wrapper_source import Wrapper_source


class NPP_builder:

    def __init__(self, oemof_es):
        self.es = oemof_es
                
              
    def add_outage_options(self, npp_block_builder, outage_options):
        
        if not outage_options["status"]:
            return
        
        timeindex = self.es.custom_time_index

        if outage_options["fixed_outage_month"]:
            fix_profile = get_fix_months_profile(timeindex, outage_options["fixed_outage_month"])
            npp_block_builder.update_options({"fix": fix_profile })
            return
        
        startup_cost_mask = None
        if outage_options["start_of_month"]:
            startup_cost_mask = get_months_start_points(timeindex)

            
        duration = outage_options["planning_outage_duration"]
        max_power_profile = get_avail_months_profile(timeindex, outage_options["allow_months"])
        max_profile_mask = get_every_year_first_step_mask(timeindex)
        npp_block_builder.add_specific_status_duration_in_period(
            duration,
            max_profile_mask,
            mode = "non_active",
            max_profile = max_power_profile,
            startup_cost_mask = startup_cost_mask
            )



    def add_risk_options(self, npp_block_builder, risk_options):
        
        if not risk_options["status"]:
            npp_block_builder.set_info("risk_out_bus_dict", {})
            npp_block_builder.set_info("risks_storages", {})
            return
        
        
        bus_factory = Generic_bus(self.es)
        storage_factory = Generic_storage(self.es)
        
        risk_lst = risk_options["risks"]
        risks_storages = {}
        
        risk_out_bus_dict = {}
        for risk_name, risk_data in risk_lst.items():
            npp_label = npp_block_builder.label
            risk_bus = bus_factory.create_bus(f"{npp_label}_{risk_name}_input_bus")           
            risk_source_builder = Wrapper_source(self.es, f"{npp_label}_{risk_name}_source")
            risk_source_builder.update_options({
                "nominal_power": risk_data["value"],
                "output_bus": risk_bus,
                "min": 1,
            })
            npp_block_builder.create_pair_equal_status(risk_source_builder)
            risk_source_builder.build()
            risk_out_bus = bus_factory.create_bus(f"{npp_label}_{risk_name}_outbus")
            risk_out_bus_dict[risk_name] = risk_out_bus  
            storage = storage_factory.create_storage(
                label = f"{npp_label}_{risk_name}_storage",
                input_bus = risk_bus,
                output_bus = risk_out_bus,
                capacity = risk_data["max"],
            )
            risk_data[risk_name] = storage
            
        npp_block_builder.set_info("risk_out_bus_dict", risk_out_bus_dict)
        npp_block_builder.set_info("risks_storages", risks_storages)

    
    def add_repair_options(self, npp_block_builder, repair_options):
    
        if not repair_options["status"]:
            npp_block_builder.set_info("repairs_blocks", {})
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
            
        all_risk_set = set(risk_out_bus_dict.keys())
        bus_factory = Generic_bus(self.es)
        bufer_bus = bus_factory.create_bus(f"{npp_block_builder.label}_bufer_bus", balanced=False)
            
        repair_blocks = {}
            
        if repairs_npp_stop:

            control_npp_stop_source = Wrapper_source(self.es, f"{npp_block_builder.label}_control_npp_stop_converter" )
            control_npp_stop_source.update_options({"output_bus": bufer_bus, "nominal_power": 1, "min": 0})
            control_npp_stop_source.create_pair_no_equal_status(npp_block_builder)
            control_npp_stop_source.add_keyword_no_equal_status("single_npp_stop_model")
            control_npp_stop_source.build()
                        
            if repairs_npp_stop_reset:
                for name, options in repairs_npp_stop_reset.items():
                    selected_risk_bus_set = all_risk_set & options["risk_reset"].keys()
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
                    repair_source_builder.set_info("forced_in_period", options.get("forced_in_period"))
                    repair_source_builder.set_info("startup_cost", options["startup_cost"])
                    repair_source_builder.set_info("npp_stop_required", True)
                    self._add_forced_active_if_required(repair_source_builder, options.get("forced_in_period"))
                    block = repair_source_builder.build()
                    repair_blocks[options["id"]] = block

                    for selected_risk_bus in selected_risk_bus_set:
                        sink_builder = Wrapper_sink(self.es, f"{npp_block_builder.label}_{name}_{selected_risk_bus}_sink")
                        sink_builder.update_options({
                            "input_bus": risk_out_bus_dict[selected_risk_bus], "nominal_power": 1e10, "min": 0})
                        sink_builder.create_pair_equal_status(repair_source_builder)
                        sink_builder.build()
            
    
            if repairs_npp_stop_reducing:
                for name, options in repairs_npp_stop_reducing.items():
                    selected_risk_bus_set = all_risk_set & options["risk_reducing"].keys()
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
                    repair_source_builder.set_info("forced_in_period", options.get("forced_in_period"))
                    repair_source_builder.set_info("startup_cost", options["startup_cost"])
                    repair_source_builder.set_info("npp_stop_required", True)
                    self._add_forced_active_if_required(repair_source_builder, options.get("forced_in_period"))
                    block = repair_source_builder.build()
                    repair_blocks[options["id"]] = block

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
                    selected_risk_bus_set = all_risk_set & options["risk_reset"].keys()
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
                    repair_source_builder.set_info("forced_in_period", options.get("forced_in_period"))
                    self._add_forced_active_if_required(repair_source_builder, options.get("forced_in_period"))
                    repair_source_builder.set_info("startup_cost", options["startup_cost"])
                    repair_source_builder.set_info("npp_stop_required", False)
                    block = repair_source_builder.build()
                    repair_blocks[options["id"]] = block

                    for selected_risk_bus in selected_risk_bus_set:
                        sink_builder = Wrapper_sink(self.es, f"{npp_block_builder.label}_{name}_{selected_risk_bus}_sink")
                        sink_builder.update_options({
                            "input_bus": risk_out_bus_dict[selected_risk_bus], "nominal_power": 1e10, "min": 0})
                        sink_builder.create_pair_equal_status(repair_source_builder)
                        sink_builder.build()
                    
    
            if repairs_npp_no_stop_reducing:
                for name, options in repairs_npp_no_stop_reducing.items():
                    selected_risk_bus_set = all_risk_set & options["risk_reducing"].keys()
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
                    repair_source_builder.set_info("forced_in_period", options.get("forced_in_period"))
                    repair_source_builder.set_info("startup_cost", options["startup_cost"])
                    repair_source_builder.set_info("npp_stop_required", False)
                    self._add_forced_active_if_required(repair_source_builder, options.get("forced_in_period"))
                    block = repair_source_builder.build()
                    repair_blocks[options["id"]] = block

                    for selected_risk_bus in selected_risk_bus_set:
                        sink_builder = Wrapper_sink(self.es, f"{npp_block_builder.label}_{name}_{selected_risk_bus}_sink")
                        power =  options["risk_reducing"][selected_risk_bus] / options["duration"]
                        sink_builder.update_options({
                            "input_bus": risk_out_bus_dict[selected_risk_bus], "nominal_power": power, "min": 1})
                        sink_builder.create_pair_equal_status(repair_source_builder)
                        sink_builder.build()
                        
        npp_block_builder.set_info("repairs_blocks", repair_blocks)
        
    def _add_forced_active_if_required(self, repair_source_builder, forced_in_period):
        if forced_in_period:
            mask = get_last_step_mask(self.es.time_index)
            repair_source_builder.add_specific_status_durarion_in_period(mask, mode = "active")
            

    def create(
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
        
        npp_block_builder.set_info("nominal_power", nominal_power)        

        npp_block = npp_block_builder.build()
        
        return npp_block


    

    

