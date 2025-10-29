import collections
import pyomo.environ as po
from pyomo.environ import Binary, Var


class Constraint_processor:
    def __init__(self, model, constraints):
        self.model = model
        self.count = len(model.timeincrement)
        self.constraints = constraints
        

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
    
    
    def _get_pairs_for_max_uptime(self, groups_dict):
        result = []
        for block, max_uptime in groups_dict.items():
            local_group_lst = []
            local_group_lst.append(  (*block.get_pair_after_building(), max_uptime))
            result.append(local_group_lst)
        return result
    
    
    
    def _get_pairs_lst_cg(self, groups_lst):
        result = []
        for group_lst in groups_lst["group_lst"]:
            local_group_lst = []
            for block in group_lst:
                local_group_lst.append(block.get_pair_after_building())
            result.append(local_group_lst)
        return result
    
    
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
            
            
    def _get_pairs_for_min_status_in_period(self, contraints):
        items_main = []
        for block, data in contraints.items():
            item_loc = {"periods": data["periods"], "block": block.get_pair_after_building(), "min_required_time": data["min_required_time"]}
            items_main.append(item_loc)        
        return items_main
    
    
    def _get_pairs_for_delayed_max_uptime(self, contraints):
        items = []
        for delayed_block, data in contraints.items():
            item = {
                "triggered_pair": data["triggered_block"].get_pair_after_building(),
                "delayed_pair": delayed_block.get_pair_after_building(),
                "delay": data["delay"],
            }
            items.append(item)
        return items
    
    
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
            
    def cg_group_no_equal_lower_0(self):
        model = self.model
        constraints = self.constraints["cg_group_no_equal_status_lower_0"]
        groups_lst = self._get_pairs_lst_cg(constraints) or []
                
        def rule(m, t, current_group):
            sum_of_statuses = sum(
                m.NonConvexFlowBlock.status[pair[0], pair[1], t]
                for pair in current_group
            )
            return sum_of_statuses <= 1

        for i, group in enumerate(groups_lst):
                setattr(
                    model,
                    f'cg_group_no_equal_status_lower_0_{i}',
                    po.Constraint(
                        model.TIMESTEPS,
                        rule=lambda model, t, current_group=group:
                            rule(model, t, current_group)
                    ))
                
                
    def apply_max_uptime(self):
        model = self.model
        contraints = self.constraints["max_uptime"]
        items = self._get_pairs_for_max_uptime(contraints) or [] 
        
        def rule(m, t, block, bus, N):
            if t < N:
                return po.Constraint.Skip
            else:
                return po.quicksum(m.NonConvexFlowBlock.status[block, bus, k] for k in range(t - N, t + 1)) <= N

        if items:
            model.max_uptime_constraint = po.Constraint(
                model.TIMESTEPS,
                [item for item in items],
                rule=rule)


    
    def apply_delayed_max_uptime(self):
        
        model = self.model
        contraints = self.constraints["delayed_startup_by_shutdown"]
        items = self._get_pairs_for_delayed_max_uptime(contraints) or []
         
        def add_delayed_startup_efficient(m, items):
            timesteps_list = list(m.TIMESTEPS)
            
            for idx, item in enumerate(items):
                triggered_block_a, bus_a = item["triggered_pair"]
                delayed_block_b, bus_b = item["delayed_pair"]
                delay = item["delay"]
                
                # Создаем набор пар (t_shutdown, t_potential_startup)
                constraint_pairs = []
                
                for t_shutdown_idx in range(1, len(timesteps_list)):
                    # Окно блокировки после shutdown в момент t_shutdown_idx
                    for t_startup_idx in range(t_shutdown_idx, min(len(timesteps_list), t_shutdown_idx + delay + 1)):
                        if t_startup_idx > 0:  # Нужен предыдущий момент для определения startup
                            constraint_pairs.append((t_shutdown_idx, t_startup_idx))
                
                def delayed_startup_rule(model, t_shutdown_idx, t_startup_idx):
                    t_shutdown = timesteps_list[t_shutdown_idx]
                    t_shutdown_prev = timesteps_list[t_shutdown_idx - 1]
                    
                    t_startup = timesteps_list[t_startup_idx]
                    t_startup_prev = timesteps_list[t_startup_idx - 1]
                    
                    # Определяем shutdown triggered source в момент t_shutdown
                    status_a_curr = model.NonConvexFlowBlock.status[triggered_block_a, bus_a, t_shutdown]
                    status_a_prev = model.NonConvexFlowBlock.status[triggered_block_a, bus_a, t_shutdown_prev]
                    shutdown_indicator = status_a_prev - status_a_curr
                    
                    # Определяем startup delayed source в момент t_startup
                    status_b_curr = model.NonConvexFlowBlock.status[delayed_block_b, bus_b, t_startup]
                    status_b_prev = model.NonConvexFlowBlock.status[delayed_block_b, bus_b, t_startup_prev]
                    startup_indicator = status_b_curr - status_b_prev
                    
                    # Ограничение: если был shutdown, то startup запрещен
                    # startup_indicator + shutdown_indicator <= 1
                    # Это означает: не могут быть оба равны 1 одновременно
                    
                    return startup_indicator + shutdown_indicator <= 1
                
                constraint_name = f'delayed_startup_{idx}_{delayed_block_b.label}_after_{triggered_block_a.label}'
                setattr(m, constraint_name, po.Constraint(constraint_pairs, rule=delayed_startup_rule))

        add_delayed_startup_efficient(model, items)
    
    
    def apply_min_status_in_period(self):
   
        model = self.model    
        contraints = self.constraints["min_status_in_period"]
        periods_data = self._get_pairs_for_min_status_in_period(contraints) or {}    
        
        # periods_data = {((10,50), (60,90)) : [(expense_source, el_bus), 10]}  - страый вариант
        # periods_data = [{"periods": ((10,50), (60,90)), "block": (expense_source, el_bus), "min_required_time": 10},] - новый вариант          

        def mandatory_single_run_simple(m, periods_data):
            
            timesteps_list = list(m.TIMESTEPS)
            
            for i, data_dict in enumerate(periods_data):
                required_uptime = data_dict["min_required_time"]
                start_finish_pairs_lst = data_dict["periods"]
                flow_tuple = data_dict["block"]

                for j, (start_t, end_t) in enumerate(start_finish_pairs_lst):
                    period_length = end_t - start_t
                    
                    if period_length < required_uptime:
                        print(f"Warning: Period {i}_{j} too short")
                        continue
                    
                    period_timesteps = timesteps_list[start_t:end_t]
                    
                    # Ограничение 1: Общее время работы
                    setattr(m, f'total_uptime_{i}_{j}',
                        po.Constraint(
                            expr=sum(m.NonConvexFlowBlock.status[flow_tuple, t] 
                                    for t in period_timesteps) >= required_uptime
                        ))
                    
                    # Ограничение 2: Максимум один старт (переход 0->1)
                    def max_one_startup_rule(model):
                        startups = []
                        
                        for idx in range(len(period_timesteps)):
                            t = period_timesteps[idx]
                            
                            if idx == 0:
                                if start_t > 0:
                                    prev_t = timesteps_list[start_t - 1]
                                    startup = (model.NonConvexFlowBlock.status[flow_tuple, t] - 
                                            model.NonConvexFlowBlock.status[flow_tuple, prev_t])
                                else:
                                    startup = model.NonConvexFlowBlock.status[flow_tuple, t]
                            else:
                                prev_t = period_timesteps[idx - 1]
                                startup = (model.NonConvexFlowBlock.status[flow_tuple, t] - 
                                        model.NonConvexFlowBlock.status[flow_tuple, prev_t])
                            
                            startups.append(startup)
                        
                        # Сумма всех стартов <= 1 (но с учетом первого ограничения будет = 1)
                        return sum(startups) <= 1
                    
                    setattr(m, f'max_one_startup_{i}_{j}',
                        po.Constraint(rule=max_one_startup_rule))




        mandatory_single_run_simple(model, periods_data)
            

    def _get_pairs_for_strict_status_off_by_pattern(self, contraints):
        items = []
        for block, avail_pattern in contraints.items():
            items.append({
                "block_pair": block.get_pair_after_building(),
                "avail_pattern": avail_pattern
            }) if isinstance(avail_pattern, collections.abc.Iterable) else None
        return items


    
    def apply_strict_status_off_by_pattern(self):
        
        model = self.model
        constraints = self.constraints["strict_status_off_by_pattern"]
        items = self._get_pairs_for_strict_status_off_by_pattern(constraints) or []
        
        # start_end_pairs = [(25, 75)]
        # avail_pattern = get_avail_pattern(start_end_pairs, date_time_index)

        # items = [{
        #         "block_pair": (cheap_source, el_bus),
        #         "avail_pattern": avail_pattern
        # }]

        def add_strict_status_by_pattern_constraint(model, items):
            def shutdown_rule(m, point , source, bus):
                return m.NonConvexFlowBlock.status[source, bus, point] == 0
            for item in items:
                source, bus = item["block_pair"]
                avail_pattern = item["avail_pattern"]
                points = set(point for point in range(len(avail_pattern)) if avail_pattern[point] == 0)
                setattr(model,
                        f"forced_shutdown_by_pattern_{source.label}_{bus.label}",
                        po.Constraint(
                            [point for point in points],
                            rule=lambda m, point, source=source, bus=bus: shutdown_rule(m, point, source, bus),
                        ))

        add_strict_status_by_pattern_constraint(model, items) if items else None
    
    
    def _get_pairs_for_max_startup_by_periods(self, constraints):
        items = []
        for block, constraint in constraints.items():
            periods = constraint["periods"]
            max_startup_count_in_every_period = constraint["max_startup_count_in_every_period"]
            items.append({"block_pair": block.get_pair_after_building(), "periods": periods, "max_startup_count_in_every_period": max_startup_count_in_every_period})
        return items
    
    
    def apply_max_startup_by_periods(self):
        
        model = self.model
        constraints = self.constraints["max_startup_by_periods"]
        items = self._get_pairs_for_max_startup_by_periods(constraints) or []
        
        # items = [{
        #    "block_pair": (cheap_source, el_bus),
        #    "periods": start_end_pairs,
        #    "max_startup_count_in_every_period":1,
        # }] 

        def add_switching_limits(om, items):

            
            for idx, item in enumerate(items):
                source, bus = item["block_pair"]
                periods = item["periods"]
                max_switches = item["max_startup_count_in_every_period"]
                
                # Создаем переменную для фиксации момента включения
                switch_var_name = f'switch_on_{source.label}_{bus.label}_{idx}'
                setattr(om, switch_var_name, Var(om.TIMESTEPS, within=Binary))
                switch_on = getattr(om, switch_var_name)
                
                # Определяем включение как переход 0->1
                def switch_detection_rule(m, t):
                    timesteps_list = list(m.TIMESTEPS)
                    t_idx = timesteps_list.index(t)
                    
                    if t_idx == 0:
                        # На первом шаге всей модели: включение = статус
                        return switch_on[t] >= m.NonConvexFlowBlock.status[source, bus, t]
                    else:
                        t_prev = timesteps_list[t_idx - 1]
                        return switch_on[t] >= m.NonConvexFlowBlock.status[source, bus, t] - m.NonConvexFlowBlock.status[source, bus, t_prev]
                
                constraint_name_1 = f'switch_detection_{source.label}_{bus.label}_{idx}'
                setattr(om, constraint_name_1, po.Constraint(om.TIMESTEPS, rule=switch_detection_rule))
                
                # Ограничение на количество включений для каждого периода
                for period_idx, (start, end) in enumerate(periods):
                    if max_switches == 0:
                        # Если max_switches = 0, просто запрещаем включение в этом периоде
                        def no_startup_rule(m):
                            timesteps_list = list(m.TIMESTEPS)
                            period_times = timesteps_list[start:end+1]
                            
                            # Запрещаем статус = 1 на всех шагах периода
                            return sum(m.NonConvexFlowBlock.status[source, bus, t] for t in period_times) == 0
                        
                        constraint_name_2 = f'no_startup_{source.label}_{bus.label}_{idx}_period_{period_idx}'
                        setattr(om, constraint_name_2, po.Constraint(rule=no_startup_rule))
                    else:
                        # Обычная логика для max_switches > 0
                        def switching_limit_rule(m):
                            timesteps_list = list(m.TIMESTEPS)
                            
                            # Если период начинается не с нулевого шага, 
                            # проверяем включение на первом шаге периода отдельно
                            if start > 0:
                                t_start = timesteps_list[start]
                                t_before_start = timesteps_list[start - 1]
                                
                                # Включение на первом шаге периода
                                first_step_switch = m.NonConvexFlowBlock.status[source, bus, t_start] - m.NonConvexFlowBlock.status[source, bus, t_before_start]
                                
                                # Включения внутри периода (со второго шага периода)
                                period_times = timesteps_list[start+1:end+1]
                                
                                return first_step_switch + sum(switch_on[t] for t in period_times) <= max_switches
                            else:
                                # Период начинается с нулевого шага
                                period_times = timesteps_list[start:end+1]
                                return sum(switch_on[t] for t in period_times) <= max_switches
                        
                        constraint_name_2 = f'switching_limit_{source.label}_{bus.label}_{idx}_period_{period_idx}'
                        setattr(om, constraint_name_2, po.Constraint(rule=switching_limit_rule))
            
            return om

        add_switching_limits(model, items) if items else None

