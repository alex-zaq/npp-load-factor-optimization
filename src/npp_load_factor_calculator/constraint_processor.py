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
        
        
    def add_group_equal_1(self):
        
        block_associations = self.constraints["group_equal_1"]
        model = self.model
        
        def dependency_rule_generalized(model, t, cheap_block_pair, expense_group_pairs, bus):
            sum_of_group_statuses = sum(
                model.NonConvexFlowBlock.status[pair[0], pair[1], t]
                for pair in expense_group_pairs
            )
            return model.NonConvexFlowBlock.status[cheap_block_pair[0], cheap_block_pair[1], t] <= sum_of_group_statuses

        def mutual_exclusion_rule_generalized(model, t, expense_group_pairs):
            sum_of_group_statuses = sum(
                model.NonConvexFlowBlock.status[pair[0], pair[1], t]
                for pair in expense_group_pairs
            )
            return sum_of_group_statuses <= 1
                    

        for i, (cheap_block_pair, expense_group_pairs) in enumerate(block_associations):
            setattr(
                model,
                f'dependency_constraint_{i}',
                po.Constraint(
                    model.TIMESTEPS,
                    rule=lambda model, t, cheap_block_pair=cheap_block_pair, expense_group_pairs=expense_group_pairs:
                        dependency_rule_generalized(model, t, cheap_block_pair, expense_group_pairs)
                )
            )

            setattr(
                model,
                f'mutual_exclusion_constraint_{i}',
                po.Constraint(
                    model.TIMESTEPS,
                    rule=lambda model, t, expense_group_pairs=expense_group_pairs:
                        mutual_exclusion_rule_generalized(model, t, expense_group_pairs)
                )
            )
            


