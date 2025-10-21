

from itertools import groupby
from src.npp_load_factor_calculator.block_db import Block_db
from src.npp_load_factor_calculator.constraint_grouper import Constraint_grouper
from src.npp_load_factor_calculator.generic_models.generic_bus import Generic_bus
from src.npp_load_factor_calculator.generic_models.generic_sink import Generic_sink
from src.npp_load_factor_calculator.npp_builder import NPP_builder
from src.npp_load_factor_calculator.resolution_strategy import Resolution_strategy


class Custom_model:

    def __init__(self, scenario, oemof_es):
        self.scenario = scenario
        self.oemof_es = oemof_es
        self.bus_factory = Generic_bus(oemof_es)
        self.sink_factory = Generic_sink(oemof_es)
        self.block_db = Block_db()
        self.oemof_es.constraint_grouper = Constraint_grouper(oemof_es)
        resolution_strategy = Resolution_strategy.create_strategy(self.scenario["freq"], self.oemof_es.custom_timeindex)
        self.npp_builder = NPP_builder(oemof_es, resolution_strategy)
        

    def add_electricity_demand(self):
        self.el_bus = self.bus_factory.create_bus("электроэнергия (bus)")
        self.el_sink = self.sink_factory.create_sink("электроэнергия (sink)", self.el_bus) 
        self.block_db.add_block("потребитель ээ", self.el_sink)
        
        
    def build_blocks(self):
        [block.build() for block in self.oemof_es.block_build_lst]
        
        
    # def add_model_level_constraints(self):
        
    #     allow_npp_stop_for_model_level = self.scenario["allow_parallel_repairs_npp_stop_for_model_level"]
    #     allow_npp_no_stop_model_level = self.scenario["allow_parallel_repairs_npp_no_stop_model_level"]
        
        
    #     b_1 = self.block_db.get_bel_npp_block_1()
    #     b_2 = self.block_db.get_bel_npp_block_2()
    #     b_3 = self.block_db.get_new_npp_block_1()
    #     blocks = [b_1, b_2, b_3]
    #     active_blocks = [b for b in blocks if b]
    
    #     if not allow_npp_stop_for_model_level:
    #         all_npp_stop_repair_blocks = [repair for active_b in active_blocks for repair in active_b.get_info("repairs_blocks_npp_stop")]
    #         self.oemof_es.constraint_grouper.group_no_equal_status_lower_0(all_npp_stop_repair_blocks)
            
    #     if not allow_npp_no_stop_model_level:
    #         all_no_npp_stop_repair_blocks = [repair for active_b in active_blocks for repair in active_b.get_info("repairs_blocks_npp_no_stop")]
    #         self.oemof_es.constraint_grouper.group_no_equal_status_lower_0(all_no_npp_stop_repair_blocks)
        
    def get_groupes_npp_level(self, block):
        repairs_blocks = block.get_info("repairs_blocks")
        repair_blocks_with_tag = [repair_block for repair_block in repairs_blocks.values() if repair_block.get_info("no_parallel_tag_for_npp")]
        repair_blocks_with_tag.sort(key=lambda x: x.get_info("no_parallel_tag_for_npp"))    
        groups_by_npp_level_with_tag = groupby(
            repair_blocks_with_tag,
            key=lambda x: x.get_info("no_parallel_tag_for_npp")) if repair_blocks_with_tag else []
        return groups_by_npp_level_with_tag

    
    def get_groupes_model_level(self, active_blocks):
        all_repair_blocks = []
        for block in active_blocks:
            all_repair_blocks+= [*block.get_info("repairs_blocks").values()]
        repair_blocks_with_tag = [repair_block for repair_block in all_repair_blocks if repair_block.get_info("no_parallel_tag_for_model")]
        repair_blocks_with_tag.sort(key=lambda x: x.get_info("no_parallel_tag_for_model"))
        groups_by_model_lelvel_with_tag = groupby(repair_blocks_with_tag, key=lambda x: x.info["no_parallel_tag_for_model"]) if repair_blocks_with_tag else []
        return groups_by_model_lelvel_with_tag
             
                
    def add_model_level_constraints(self):
        b_1 = self.block_db.get_bel_npp_block_1()
        b_2 = self.block_db.get_bel_npp_block_2()
        b_3 = self.block_db.get_new_npp_block_1()
        blocks = [b_1, b_2, b_3]
        active_blocks = [b for b in blocks if b]
        
        for block in active_blocks:
            groups_by_npp_level_with_tag = self.get_groupes_npp_level(block)
            if groups_by_npp_level_with_tag:
                for _, repair_blocks in groups_by_npp_level_with_tag:
                    repair_blocks = list(repair_blocks)
                    self.oemof_es.constraint_grouper.group_no_equal_status_lower_0(repair_blocks)
        
        groups_model_level = self.get_groupes_model_level(active_blocks)
        for _, repair_blocks in groups_model_level:
            repair_blocks = list(repair_blocks)
            self.oemof_es.constraint_grouper.group_no_equal_status_lower_0(repair_blocks)
        
        
    def add_bel_npp(self):

        status_1 = self.scenario["bel_npp_block_1"]["status"]
        status_2 = self.scenario["bel_npp_block_2"]["status"]
        
        if status_1:
            power_1 = self.scenario["bel_npp_block_1"]["nominal_power"]
            var_cost_1 = self.scenario["bel_npp_block_1"]["var_cost"]
            min_uptime_1 = self.scenario["bel_npp_block_1"]["min_uptime"]
            risk_options_1 = self.scenario["bel_npp_block_1"]["risk_options"]
            repair_options_1 = self.scenario["bel_npp_block_1"]["repair_options"]
            outage_options_1 = self.scenario["bel_npp_block_1"]["outage_options"]

        if status_2:
            power_2 = self.scenario["bel_npp_block_2"]["nominal_power"]
            var_cost_2 = self.scenario["bel_npp_block_2"]["var_cost"]
            min_uptime_2 = self.scenario["bel_npp_block_2"]["min_uptime"]
            risk_options_2 = self.scenario["bel_npp_block_2"]["risk_options"]
            repair_options_2 = self.scenario["bel_npp_block_2"]["repair_options"]
            outage_options_2 = self.scenario["bel_npp_block_2"]["outage_options"]
           
           
        if status_1:
            bel_npp_block_1 = self.npp_builder.create(
                label="БелАЭС (блок 1)",
                nominal_power=power_1,
                output_bus=self.el_bus,
                var_cost=var_cost_1,
                min_uptime=min_uptime_1,
                risk_options=risk_options_1,
                repair_options=repair_options_1,
                outage_options=outage_options_1
            )
            self.block_db.add_block("аэс", bel_npp_block_1)
        
        if status_2:
            bel_npp_block_2 = self.npp_builder.create(
                label = "БелАЭС (блок 2)",
                nominal_power = power_2,
                output_bus = self.el_bus,
                var_cost = var_cost_2,
                min_uptime = min_uptime_2,
                risk_options = risk_options_2,
                repair_options = repair_options_2,
                outage_options = outage_options_2
            )
            self.block_db.add_block("аэс", bel_npp_block_2)
            
            
        # npp_block_builder.set_info("repairs_blocks_npp_stop", repair_blocks_npp_stop)
        # npp_block_builder.set_info("repairs_blocks_npp_no_stop", repair_blocks_npp_no_stop)

       
    
    def add_new_npp(self):
        
        status_1 = self.scenario["new_npp_block_1"]["status"]
        
        if status_1:
            power_1 = self.scenario["bel_npp_block_1"]["nominal_power"]
            var_cost_1 = self.scenario["bel_npp_block_1"]["var_cost"]
            min_uptime_1 = self.scenario["bel_npp_block_1"]["min_uptime"]
            risk_options_1 = self.scenario["bel_npp_block_1"]["risk_options"]
            repair_options_1 = self.scenario["bel_npp_block_1"]["repair_options"]
            outage_options_1 = self.scenario["bel_npp_block_1"]["outage_options"]
  
                
        if status_1:
            new_npp_block_1 = self.npp_builder.create(
                label="Новая АЭС (блок 1)",
                nominal_power=power_1,
                output_bus=self.el_bus,
                var_cost=var_cost_1,
                min_uptime=min_uptime_1,
                risk_options=risk_options_1,
                repair_options=repair_options_1,
                outage_options=outage_options_1
            )
            self.block_db.add_block("аэс", new_npp_block_1)
        

    def get_constraints(self):
        npp_constraints = self.npp_builder.get_constraints()
        return npp_constraints
        
