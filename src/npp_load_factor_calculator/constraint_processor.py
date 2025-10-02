import pyomo.environ as po
from oemof import solph


class Constraint_processor:
    def __init__(self, model, constraints):
        self.model = model
        self.count = len(model.timeincrement)
        self.constraints = constraints


    def apply_equal_status(self):
        items = self.constraints["equal_status"]
        model = self.model
        for item in items:
            pair_1, pair_2  = item
            for i in range(self.count):
                solph.constraints.equate_variables(
                    model,
                    model.NonConvexFlowBlock.status[pair_1[0], pair_1[1], i],
                    model.NonConvexFlowBlock.status[pair_2[0], pair_2[1], i],
                )
                
    def apply_no_equal_status(self):
        keywords = self.constraints["no_equal_status"]
        model = self.model
        keywords = list(set(keywords))
        for keyword in keywords:
                solph.constraints.limit_active_flow_count_by_keyword(
                model, keyword, lower_limit=0, upper_limit=1
            )
                
                
    def apply_no_equal_lower_1_status(self):
        keywords = self.constraints["no_equal_lower_1_status"]
        model = self.model
        keywords = list(set(keywords))
        for keyword in keywords:
                solph.constraints.limit_active_flow_count_by_keyword(
                model, keyword, lower_limit=1, upper_limit=10
            )
                
                
    def apply_strict_order(self):
        
        items = self.constraints["strict_order"]
        model = self.model
        
        def sequential_loading_rule(m, t, item_1, item_2, item_3, item_4):
             return m.NonConvexFlowBlock.status[item_1, item_2, t] <= m.NonConvexFlowBlock.status[item_3, item_4, t]

        model.sequential_loading_constraint = po.Constraint(
            model.TIMESTEPS,
            [item for item in items],
            rule=sequential_loading_rule
        )
                

   
            


