import datetime as dt

import pandas as pd
import pyomo.environ as po
from matplotlib import pyplot as plt
from oemof import solph

date_time_index = pd.date_range(dt.datetime(2021, 1, 1), periods=20, freq="H")
energysystem = solph.EnergySystem(timeindex=date_time_index, infer_last_interval=True)


el_bus = solph.Bus(label="el_bus")
energysystem.add(el_bus)


power_val = 1500
cheap_min_uptime = 5



expense_source = solph.components.Source(
    label="expense_source",
    outputs={el_bus: solph.Flow(nominal_value = power_val, min=1, variable_costs=1000, nonconvex=solph.NonConvex())},
)
energysystem.add(expense_source)





cheap_converter = solph.components.Converter(
    label="cheap_converter",
    outputs={el_bus: solph.Flow(
        nominal_value = power_val,
        variable_costs=1,
        min = 1,

        nonconvex=solph.NonConvex(), 
        )},
)
energysystem.add(cheap_converter)


 


sink_demand=solph.components.Sink(
        label="sink_demand",
        inputs={el_bus: solph.Flow(nominal_value = power_val, fix = 1)},
)
energysystem.add(sink_demand)




model = solph.Model(energysystem)

item_startup = (expense_source, el_bus, 5)
items_startup = [(item_startup)] 
        
item_shutdown = (cheap_converter, el_bus, 15)
items_shutdown = [(item_shutdown)]        
        
         
def rule_forced_startup(m, block, bus, tt):
    return m.NonConvexFlowBlock.status[block, bus, tt] == 1


model.constraint_forced_startup = po.Constraint(
    [item for item in items_startup],
    rule = rule_forced_startup
)


def rule_forced_shutdown(m, block, bus, tt):
    return m.NonConvexFlowBlock.status[block, bus, tt] == 0


model.constraint_forced_shutdown = po.Constraint(
    [item for item in items_shutdown],
    rule = rule_forced_shutdown
)


model.solve(
    solver="cplex",
    solve_kwargs={
        'tee': True,  
        'logfile': 'cplex_solve.log',  
        'keepfiles': False, 
    }
    )



blocks = [expense_source, cheap_converter]

results = solph.processing.results(model)

el_results = solph.views.node(results, el_bus.label)["sequences"].dropna()




el_df = pd.DataFrame()

for block in blocks:
    el_df[block.label] = el_results[((block.label, el_bus.label), "flow")]


ax_el = el_df.plot(kind="area", ylim=(0, 5000))

plt.show(block=True)
