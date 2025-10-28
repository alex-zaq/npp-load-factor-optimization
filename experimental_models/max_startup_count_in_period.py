import datetime as dt

import pandas as pd
import pyomo.environ as po
from matplotlib import pyplot as plt
from oemof import solph
from pyomo.environ import Binary, Constraint, Var

date_time_index = pd.date_range(dt.datetime(2025, 1, 1), periods=100, freq="H")
energysystem = solph.EnergySystem(timeindex=date_time_index, infer_last_interval=True)


el_bus = solph.Bus(label="el_bus")
energysystem.add(el_bus)


power_val = 1000


def get_avail_pattern(start_end_pairs, date_time_index):

    avail_pattern = [0] * len(date_time_index) 
    for start, end in start_end_pairs:
        for i in range(start, end):
            avail_pattern[i] = 1
    return avail_pattern



expense_source_1 = solph.components.Source(
    label="expense_source_1",
    outputs={el_bus: solph.Flow(
        nominal_value = power_val,
        min=1,
        variable_costs=1000,
        nonconvex=solph.NonConvex(),
    )},
)
energysystem.add(expense_source_1)






cheap_source = solph.components.Converter(
    label="cheap_source",
    outputs={el_bus: solph.Flow(
        nominal_value = power_val,
        min = 1,
        variable_costs=1,
        nonconvex=solph.NonConvex(), 
        )},
)
energysystem.add(cheap_source)


sink_demand=solph.components.Sink(
        label="sink_demand",
        inputs={el_bus: solph.Flow(nominal_value = power_val, fix = 1)},
)
energysystem.add(sink_demand)


model = solph.Model(energysystem)





start_end_pairs = [(25, 75)]
avail_pattern = get_avail_pattern(start_end_pairs, date_time_index)

items = [{
           "block_pair": (cheap_source, el_bus),
           "avail_pattern": avail_pattern
}]

def add_strict_status_by_pattern_constraint(model, items):
    def shutdown_rule(m, t, source, bus, avail_pattern):
         return m.NonConvexFlowBlock.status[source, bus, t] == avail_pattern[t]
    for item in items:
        source, bus = item["block_pair"]
        avail_pattern = item["avail_pattern"]
        setattr(model,
                f"forced_shutdown_by_pattern_{source.label}_{bus.label}",
                po.Constraint(
                    model.TIMESTEPS,
                    rule=lambda m, t, source=source, bus=bus, avail_pattern=avail_pattern: shutdown_rule(m, t, source, bus, avail_pattern),
                ))
        
add_strict_status_by_pattern_constraint(model, items)

items = [{
           "block_pair": (cheap_source, el_bus),
           "intervals_lst": [30]
}]


def add_strict_status_by_points(model, items):
    def shutdown_rule(m, point, source, bus):
         return m.NonConvexFlowBlock.status[source, bus, point] == 0
    for item in items:
        source, bus = item["block_pair"]
        intervals_lst = item["intervals_lst"]
        setattr(model,
                f"forced_shutdown_by_points_{source.label}_{bus.label}",
                po.Constraint(
                    [point for point in intervals_lst],
                    rule=lambda m, point, source=source, bus=bus: shutdown_rule(m, point, source, bus)
                ))
        
# add_strict_status_by_points(model, items)





items = [{
           "block_pair": (cheap_source, el_bus),
           "periods": start_end_pairs,
           "max_startup_count_in_every_period":1,
        }] 


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
        setattr(om, constraint_name_1, Constraint(om.TIMESTEPS, rule=switch_detection_rule))
        
        # Ограничение на количество включений для каждого периода
        for period_idx, (start, end) in enumerate(periods):
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
            setattr(om, constraint_name_2, Constraint(rule=switching_limit_rule))
    
    return om

add_switching_limits(model, items)


model.solve(
    solver="cplex",
    solve_kwargs={
        'tee': True,  
    })



blocks = [expense_source_1, cheap_source]

results = solph.processing.results(model)

el_results = solph.views.node(results, el_bus.label)["sequences"].dropna()


el_df = pd.DataFrame()
el_statuses_df = pd.DataFrame()

for block in blocks:
    el_df[block.label] = el_results[((block.label, el_bus.label), "flow")]
    
    el_statuses_df[block.label] = el_results[((block.label, el_bus.label), "status")]


fig, (ax_left, ax_right) = plt.subplots(1, 2, figsize=(13, 5))

el_df.index = range(el_df.shape[0])
el_statuses_df.index = range(el_statuses_df.shape[0])

ax_el = el_df.plot(kind="area", ylim=(0, 2000), ax=ax_left)

ax_el_statuses = el_statuses_df.plot(kind="line", ylim=(0, 2), ax=ax_right)

plt.show(block=True)
