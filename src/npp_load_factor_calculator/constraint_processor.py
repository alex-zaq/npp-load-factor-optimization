import pyomo.environ as po


class Constraint_processor:
    def __init__(self, model, constraints):
        self.model = model
        self.count = len(model.timeincrement)
        self.constraints = constraints
        # self._change_wrappers_to_blocks()
        
        
    # def _change_wrappers_to_blocks(self):
    #     constraints_copy = self.constraints.copy()
    #     constraints_copy.clear()
    #     for constraint_name, group_dict in self.constraints.items():
    #         for wrapper_main, depend_wrapper_lst in group_dict.items():
    #             block_main = wrapper_main.build()
    #             depend_block_lst = [block.build() for block in depend_wrapper_lst]
    #             constraints_copy[constraint_name][block_main] = depend_block_lst  
    #     self.constraints = constraints_copy        
        

    def _get_pairs_lst(self, groups_dict):
        global_groups_lst = []
        for main_block in groups_dict:
            local_group_lst = []
            for sub_block in groups_dict[main_block]:
                main_block_pair = main_block.get_pair_after_building()
                sub_block_pair = sub_block.get_pair_after_building()
                local_group_lst+=[main_block_pair]
                local_group_lst+=[sub_block_pair]
            global_groups_lst.append(local_group_lst)
        return global_groups_lst
    
    
    def _get_pairs_dict(self, groups_dict):
        global_groups_dict = {}
        for main_block in groups_dict:
            local_group_dict = []
            for sub_block in groups_dict[main_block]:
                main_block_pair = main_block.get_pair_after_building()
                sub_block_pair = sub_block.get_pair_after_building()
                local_group_dict.append(sub_block_pair)
            global_groups_dict[main_block_pair] = local_group_dict
        return global_groups_dict
            
    
    def apply_equal_status(self):
        model = self.model
        constraints = self.constraints["equal_status"]
        global_groups_dict = self._get_pairs_dict(constraints) or {}
        
        def rule(m, t, item_1, item_2, item_3, item_4):
             return m.NonConvexFlowBlock.status[item_1, item_2, t] == m.NonConvexFlowBlock.status[item_3, item_4, t]        

        for i, (main_pair, depend_pairs) in enumerate(global_groups_dict.items()):

            items = [ (main_pair[0], main_pair[1], depend_pair[0], depend_pair[1]) for depend_pair in depend_pairs]
            setattr(
                model,
                f'equal_status_group_{i}',
                po.Constraint(
                    model.TIMESTEPS,
                    [item for item in items],
                    rule=rule
                )
            )
                
                
    def apply_no_equal_status_lower_0(self):
        model = self.model
        constraints = self.constraints["no_equal_status_lower_0"]
        global_groups_lst = self._get_pairs_lst(constraints) or []


        def rule(m, t, current_group):
            sum_of_statuses = sum(
                m.NonConvexFlowBlock.status[pair[0], pair[1], t]
                for pair in current_group
            )
            return sum_of_statuses <= 1

        for i, group in enumerate(global_groups_lst):
             setattr(
                    model,
                    f'no_equal_lower_0_status_group_{i}',
                    po.Constraint(
                        model.TIMESTEPS,
                        rule=lambda model, t, current_group=group:
                            rule(model, t, current_group)
                    )
                )
                
        
                
    def apply_no_equal_lower_1_status(self):
        
        model = self.model
        constraints = self.constraints["no_equal_status_lower_1"]
        global_groups_lst = self._get_pairs_lst(constraints) or []
                
        def rule(m, t, current_group):
            sum_of_statuses = sum(
                m.NonConvexFlowBlock.status[pair[0], pair[1], t]
                for pair in current_group
            )
            return sum_of_statuses >= 1

        for i, group in enumerate(global_groups_lst):
             setattr(
                    model,
                    f'no_equal_lower_1_status_group_{i}',
                    po.Constraint(
                        model.TIMESTEPS,
                        rule=lambda model, t, current_group=group:
                            rule(model, t, current_group)
                    )
                )
                
                
    def apply_no_equal_status_equal_1(self):
        
        model = self.model
        constraints = self.constraints["no_equal_status_equal_1"]
        global_groups_lst = self._get_pairs_lst(constraints) or []

        def rule(m, t, current_group):
            sum_of_statuses = sum(
                m.NonConvexFlowBlock.status[pair[0], pair[1], t]
                for pair in current_group
            )
            return sum_of_statuses == 1

        for i, group in enumerate(global_groups_lst):
             setattr(
                    model,
                    f'no_equal_status_equal_1_group_{i}',
                    po.Constraint(
                        model.TIMESTEPS,
                        rule=lambda model, t, current_group=group:
                            rule(model, t, current_group)
                    )
                )

                
    def apply_strict_order(self):
        
        model = self.model
        constraints = self.constraints["strict_order"]
        global_groups_dict = self._get_pairs_dict(constraints) or {}
        
        def rule(m, t, item_1, item_2, item_3, item_4):
             return m.NonConvexFlowBlock.status[item_1, item_2, t] <= m.NonConvexFlowBlock.status[item_3, item_4, t]

        for i, (main_pair, depend_pairs) in enumerate(global_groups_dict.items()):
            
            items = [(depend_pair[0], depend_pair[1], main_pair[0], main_pair[1]) for depend_pair in depend_pairs]
                
            setattr(
                model,
                f'strict_order_group_{i}',
                po.Constraint(
                    model.TIMESTEPS,
                    [item for item in items],
                    rule=rule
                )
            )
        
        
    def add_group_equal_1(self):
        model = self.model
        constraints = self.constraints["group_equal_1"]
        global_groups_dict = self._get_pairs_dict(constraints) or {}
        
        def rule_1(model, t, cheap_block_pair, expense_group_pairs):
            sum_of_group_statuses = sum(
                model.NonConvexFlowBlock.status[pair[0], pair[1], t]
                for pair in expense_group_pairs
            )
            return model.NonConvexFlowBlock.status[cheap_block_pair[0], cheap_block_pair[1], t] <= sum_of_group_statuses

        def rule_2(model, t, expense_group_pairs):
            sum_of_group_statuses = sum(
                model.NonConvexFlowBlock.status[pair[0], pair[1], t]
                for pair in expense_group_pairs
            )
            return sum_of_group_statuses <= 1
                    

        for i, (cheap_block_pair, expense_group_pairs) in enumerate(global_groups_dict.items()):
            setattr(
                model,
                f'group_equal_1_dependency_constraint_{i}',
                po.Constraint(
                    model.TIMESTEPS,
                    rule=lambda model, t, cheap_block_pair=cheap_block_pair, expense_group_pairs=expense_group_pairs:
                        rule_1(model, t, cheap_block_pair, expense_group_pairs)
                )
            )

            setattr(
                model,
                f'group_equal_1_mutual_exclusion_constraint_{i}',
                po.Constraint(
                    model.TIMESTEPS,
                    rule=lambda model, t, expense_group_pairs=expense_group_pairs:
                        rule_2(model, t, expense_group_pairs)
                )
            )
                    
        
    def group_equal_or_greater_1(self):
        model = self.model
        constraints = self.constraints["group_equal_or_greater_1"]
        global_groups_dict = self._get_pairs_dict(constraints) or {}
        
        def rule_1(model, t, cheap_block_pair, expense_group_pairs):
            sum_of_group_statuses = sum(
                model.NonConvexFlowBlock.status[pair[0], pair[1], t]
                for pair in expense_group_pairs
            )
            return model.NonConvexFlowBlock.status[cheap_block_pair[0], cheap_block_pair[1], t] <= sum_of_group_statuses

        # def rule_2(model, t, expense_group_pairs):
        #     sum_of_group_statuses = sum(
        #         model.NonConvexFlowBlock.status[pair[0], pair[1], t]
        #         for pair in expense_group_pairs
        #     )
        #     return sum_of_group_statuses <= 1
                    

        for i, (cheap_block_pair, expense_group_pairs) in enumerate(global_groups_dict.items()):
            setattr(
                model,
                f'group_equal_or_greater_1_dependency_constraint_{i}',
                po.Constraint(
                    model.TIMESTEPS,
                    rule=lambda model, t, cheap_block_pair=cheap_block_pair, expense_group_pairs=expense_group_pairs:
                        rule_1(model, t, cheap_block_pair, expense_group_pairs)
                )
            )

            # setattr(
            #     model,
            #     f'group_equal_or_greater_1_mutual_exclusion_constraint_{i}',
            #     po.Constraint(
            #         model.TIMESTEPS,
            #         rule=lambda model, t, expense_group_pairs=expense_group_pairs:
            #             rule_2(model, t, expense_group_pairs)
            #     )
            # )
            


