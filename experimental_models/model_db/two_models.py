import datetime as dt

import pandas as pd
from matplotlib import pyplot as plt
from oemof import solph



###########################################################################################
date_time_index = pd.date_range(dt.datetime(2021, 1, 1), periods=4, freq="H")
energysystem = solph.EnergySystem(timeindex=date_time_index, infer_last_interval=True)
el_bus = solph.Bus(label="электроэнергия")
energysystem.add(el_bus)

source_expensed = solph.components.Source(
    label="source_expensed",
    outputs={el_bus: solph.Flow(variable_costs=999)},
    
)
energysystem.add(source_expensed)

sink_el = solph.components.Sink(
    label="sink_el",
    inputs={el_bus: solph.Flow(nominal_value = 1, fix = [25,50,75,100])},
)
energysystem.add(sink_el)
model = solph.Model(energysystem)
model.solve(solver="cplex")
results = solph.processing.results(model)

el_results = solph.views.node(results, el_bus.label)["sequences"].dropna()
res_df = pd.DataFrame()

res_df[source_expensed.label] = el_results[((source_expensed.label, el_bus.label), "flow")]

ax_res_df = res_df.plot(kind="area")

plt.show(block=True)
###############################################################################################
date_time_index = pd.date_range(dt.datetime(2021, 1, 1), periods=20, freq="H")
energysystem = solph.EnergySystem(timeindex=date_time_index, infer_last_interval=True)
el_bus = solph.Bus(label="электроэнергия")
energysystem.add(el_bus)

source_expensed = solph.components.Source(
    label="source_expensed",
    outputs={el_bus: solph.Flow(variable_costs=999)},
    
)
energysystem.add(source_expensed)

sink_el = solph.components.Sink(
    label="sink_el",
    inputs={el_bus: solph.Flow(nominal_value = 1000, fix = 1)},
)
energysystem.add(sink_el)
model = solph.Model(energysystem)
model.solve(solver="cplex")
results = solph.processing.results(model)

el_results = solph.views.node(results, el_bus.label)["sequences"].dropna()
res_df = pd.DataFrame()

res_df[source_expensed.label] = el_results[((source_expensed.label, el_bus.label), "flow")]

ax_res_df = res_df.plot(kind="area")

plt.show(block=True)