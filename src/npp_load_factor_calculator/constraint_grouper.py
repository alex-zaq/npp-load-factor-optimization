

from collections import defaultdict


class Constraint_grouper:
    
    def __init__(self, oemof_es):
        self.oemof_es = oemof_es
        self.init_constraints_for_es()
        
    def init_constraints_for_es(self):
        if not hasattr(self.oemof_es, "constraints"):
            self.oemof_es.constraints = defaultdict(lambda: defaultdict(list))
        
    def group_no_equal_status_lower_0(self, wrapper_block_lst):
        self.oemof_es.constraints["cg_group_no_equal_status_lower_0"]["group_lst"].append(wrapper_block_lst)