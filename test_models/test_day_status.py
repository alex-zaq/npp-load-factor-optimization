import datetime as dt

import pandas as pd
from matplotlib import pyplot as plt
from oemof import solph

date_time_index = pd.date_range(dt.datetime(2021, 1, 1), periods=20, freq="D")
energysystem = solph.EnergySystem(timeindex=date_time_index, infer_last_interval=True)


el_bus = solph.Bus(label="el_bus")
energysystem.add(el_bus)
 
power_val = 1500 * 24
cheap_min_uptime = 5



expense_source = solph.components.Source(
    label="expense_source",
    outputs={
        el_bus: solph.Flow(
            nominal_value = power_val,
            min=0,
            variable_costs=1000,
            nonconvex=solph.NonConvex(),
            custom_attributes={"keyword": True},
            
        )},
)
energysystem.add(expense_source)


cheap_converter = solph.components.Source(
    label="cheap_converter",
    outputs={el_bus: solph.Flow(
        nominal_value = power_val,
        min = 0,
        variable_costs=1,
        nonconvex=solph.NonConvex(minimum_uptime=cheap_min_uptime), 
        custom_attributes={"keyword": True},
        )},
)
energysystem.add(cheap_converter)

 

 


sink_demand=solph.components.Sink(
        label="sink_demand",
        inputs={el_bus: solph.Flow(nominal_value = 2 * power_val, fix = 1)},
)
energysystem.add(sink_demand)




model = solph.Model(energysystem)


# solph.constraints.limit_active_flow_count_by_keyword(
#     model, "keyword", lower_limit=0, upper_limit=1
# )





model.solve(solver="cplex")

blocks = [expense_source, cheap_converter]

results = solph.processing.results(model)

el_results = solph.views.node(results, el_bus.label)["sequences"].dropna()
 


el_df = pd.DataFrame()

for block in blocks:
    el_df[block.label] = el_results[((block.label, el_bus.label), "flow")]

 
 

ax_el = el_df.plot(kind="area",
                #    ylim=(0, 5000),
                   )

plt.show(block=True)
