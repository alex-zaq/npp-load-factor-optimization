import datetime as dt

import pandas as pd
import pyomo.environ as po
from matplotlib import pyplot as plt
from oemof import solph

date_time_index = pd.date_range(dt.datetime(2021, 1, 1), periods=20, freq="H")
energysystem = solph.EnergySystem(timeindex=date_time_index, infer_last_interval=True)


el_bus = solph.Bus(label="el_bus")
energysystem.add(el_bus)

heat_bus = solph.Bus(label="heat_bus")
energysystem.add(heat_bus)


power_val = 1000



expense_source_el = solph.components.Source(
    label="expense_source",
    outputs={
        el_bus: solph.Flow(
            nominal_value = power_val,
            min=1,
            variable_costs=1000,
            nonconvex=solph.NonConvex()
            )},
)
energysystem.add(expense_source_el)



cheap_converter_el = solph.components.Source(
    label="cheap_converter",
    outputs={
            el_bus: solph.Flow(
            nominal_value = power_val,
            min = 1,
            variable_costs=1,
            nonconvex=solph.NonConvex(), 
        )},
)
energysystem.add(cheap_converter_el)



expense_source_heat = solph.components.Source(
    label="expense_source_heat",
    outputs={
        heat_bus: solph.Flow(
            nominal_value = power_val,
            min=1,
            variable_costs=1000,
            nonconvex=solph.NonConvex()
            )},
)
energysystem.add(expense_source_heat)



cheap_converter_heat = solph.components.Source(
    label="cheap_converter_heat",
    outputs={
            heat_bus: solph.Flow(
            nominal_value = power_val,
            min = 1,
            variable_costs=1,
            nonconvex=solph.NonConvex(), 
        )},
)
energysystem.add(cheap_converter_heat)






sink_demand_el=solph.components.Sink(
        label="sink_demand_el",
        inputs={el_bus: solph.Flow(nominal_value = power_val, fix = 1)},
)
energysystem.add(sink_demand_el)



sink_demand_heat=solph.components.Sink(
        label="sink_demand_heat",
        inputs={heat_bus: solph.Flow(nominal_value = power_val, fix = 1)},
)
energysystem.add(sink_demand_heat)




model = solph.Model(energysystem)


        
item_shutdown = (cheap_converter_el, el_bus, 10)
items_shutdown = [(item_shutdown)]        
        




model.constraint_forced_shutdown = po.Constraint(
    [item for item in items_shutdown],
    rule = lambda m, block, bus, tt: m.NonConvexFlowBlock.status[block, bus, tt] == 0
)



main_blocks_group = [(cheap_converter_el, el_bus)]
dependence_blocks_group = [(cheap_converter_heat, heat_bus)]

groups = [(main_blocks_group, dependence_blocks_group)]


def direct_coupled_shutdown(model, t, main_block, main_bus, dependence_block, dependence_bus):
    if t == model.TIMESTEPS.first():
        return po.Constraint.Skip
    
    source1_status_prev = model.NonConvexFlowBlock.status[main_block, main_bus, t-1]
    source1_status_curr = model.NonConvexFlowBlock.status[main_block, main_bus, t]
        # source2_status_prev = model.NonConvexFlowBlock.status[dependence_block, dependence_bus, t-1]
    source2_status_curr = model.NonConvexFlowBlock.status[dependence_block, dependence_bus, t]
    
    shutdown1 = source1_status_prev - source1_status_curr
    
    return source2_status_curr <= 1 - shutdown1

for main_group, dependence_group in groups:
    model.direct_coupled = po.Constraint(
        model.TIMESTEPS,
        [(main_item, dependence_item) for main_item in main_group for dependence_item in dependence_group],
        rule=direct_coupled_shutdown,
        )



model.solve(
    solver="cplex",
    solve_kwargs={
        'tee': True,  
        # 'logfile': 'cplex_solve.log',  
        # 'keepfiles': False, 
    }
    )



el_blocks = [expense_source_el, cheap_converter_el]
heat_blocks = [expense_source_heat, cheap_converter_heat]

results = solph.processing.results(model)

el_results = solph.views.node(results, el_bus.label)["sequences"].dropna()
heat_results = solph.views.node(results, heat_bus.label)["sequences"].dropna()




el_df = pd.DataFrame()
for block in el_blocks:
    el_df[block.label] = el_results[((block.label, el_bus.label), "flow")]

heat_df = pd.DataFrame()
for block in heat_blocks:
    heat_df[block.label] = heat_results[((block.label, heat_bus.label), "flow")]


fig, (ax_left, ax_right) = plt.subplots(1, 2, figsize=(13, 6))

max_y = 2 * power_val


el_colors = ["blue", "gray"]

heat_colors = ["green", "orange"]

ax_el = el_df.plot(kind="area", ylim=(0, max_y), ax=ax_left, color=el_colors)
ax_heat = heat_df.plot(kind="area", ylim=(0, max_y), ax=ax_right, color=heat_colors)

plt.show(block=True)
