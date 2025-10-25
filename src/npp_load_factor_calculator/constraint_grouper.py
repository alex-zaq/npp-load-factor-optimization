

from collections import defaultdict


class Constraint_grouper:
    
    def __init__(self, oemof_es):
        self.oemof_es = oemof_es
        self.init_constraints_for_es()
        
    def init_constraints_for_es(self):
        if not hasattr(self.oemof_es, "constraints"):
            self.oemof_es.constraints = defaultdict(lambda: defaultdict(list))
        
    def add_group_no_equal_status_lower_0(self, wrapper_block_lst):
        self.oemof_es.constraints["cg_group_no_equal_status_lower_0"]["group_lst"].append(wrapper_block_lst)
                
    def add_group_no_equal_starus(self, first_group, second_group, lower = 0):
        pass    
        
    def add_max_uptime(self, block, max_uptime):
        self.oemof_es.constraints["max_uptime"][block] = max_uptime
    
    def add_strict_order(self, base_group, dependence_group):
        self.oemof_es.constraints["strict_order"]["group_lst"].append((base_group, dependence_group))
        
    def add_sync_shutdown(self, main_group, dependence_group):
        self.oemof_es.constraints["forced_shutdown"]["group_lst"].append((main_group, dependence_group))
        
    def add_sync_startup(self, main_group, dependence_group):
        self.oemof_es.constraints["forced_startup"]["group_lst"].append((main_group, dependence_group))

    def add_forced_shutdown(self, group, intervals):
        self.oemof_es.constraints["forced_shutdown"]["group_lst"].append((group, intervals))
        
    def add_forced_startup(self, group, intervals):
        self.oemof_es.constraints["forced_startup"]["group_lst"].append((group, intervals))
        
    def _generic_constraint(
        self,
        main_group,
        status,  # equal, not_equal, base_for
        dependence_group,
        where,
        *,
        lower = None,
        upper = None,
        intervals = None,
        ):
        pass
    
    # Для опциональной (обязательной) работы блока (группы) нужен  группа (хотя бы один или только один блок,все блоки) включенных (выключенных) источников с учетом совпадающих (несовпадающих) временных интервалов 