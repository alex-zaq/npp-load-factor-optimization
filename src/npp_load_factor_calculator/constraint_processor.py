from oemof import solph


class Constraint_processor:
    def __init__(self, model, constraints):
        self.model = model
        self.count = len(model.timeincrement)
        self.constraints = constraints


    def apply_default_risk_constr(self):
        constr = self.constraints["default_risk_constr"]
        model = self.model
        for elem in constr:
            (npp_block, output_bus), (default_risk_block, risk_bus)  = elem
            for i in range(self.count):
                solph.constraints.equate_variables(
                    model,
                    model.NonConvexFlowBlock.status[npp_block, output_bus, i],
                    model.NonConvexFlowBlock.status[default_risk_block, risk_bus, i],
                )
    
    def apply_storage_charge_discharge_constr(self):
        keywords = self.constraints["storage_charge_discharge_constr"]
        model = self.model
        for keyword in keywords:
                solph.constraints.limit_active_flow_count_by_keyword(
                model, keyword, lower_limit=0, upper_limit=1
            )
                    
                    
    def apply_sink_peak_converter_constr(self):
        constr = self.constraints["sink_peak_converter_constr"]
        model = self.model
        for elem in constr:
            (input_bus, sink_block), (converter_block, output_bus) = elem
            for i in range(self.count):
                solph.constraints.equate_variables(
                    model,
                    model.NonConvexFlowBlock.status[input_bus, sink_block, i],
                    model.NonConvexFlowBlock.status[converter_block, output_bus, i],
                )

                
                
                
                
    def apply_source_converter_n_n_plus_1_constr(self):
        constr = self.constraints["source_converter_n_n_plus_1_constr"]
        model = self.model
        for elem in constr:
            (source_block, bus_1), (converter_block, bus_2), time_pair_lst  = elem
            for source_t, converter_t in time_pair_lst:
                solph.constraints.equate_variables(
                    model,
                    model.NonConvexFlowBlock.status[source_block, bus_1, source_t],
                    model.NonConvexFlowBlock.status[converter_block, bus_2, converter_t],
                )
    
    
    def apply_repairing_in_single_npp(self):
        keywords = self.constraints["repairing_in_single_npp"]
        model = self.model
        for keyword in keywords:
                solph.constraints.limit_active_flow_count_by_keyword(
                model, keyword, lower_limit=0, upper_limit=1
            )
    
    
    def apply_repairing_type_for_different_npp(self):
        keywords = self.constraints["repairing_type_for_different_npp"]
        model = self.model
        for keyword in keywords:
                solph.constraints.limit_active_flow_count_by_keyword(
                model, keyword, lower_limit=0, upper_limit=1
            )
                
    
    def apply_max_risk_value(self):
        max_risk_value = self.constraints["max_risk_value"]["value"]
        storages_lst = self.constraints["max_risk_value"]["storages_lst"]
        model = self.model
        solph.constraints.shared_limit(
            model,
            model.GenericStorageBlock.storage_content,
            "limit_storage",
            storages_lst,
            [1, 1],
            upper_limit=max_risk_value,
        )

                
            


