import datetime as dt

import pandas as pd
from matplotlib import pyplot as plt
from oemof import solph

date_time_index = pd.date_range(dt.datetime(2021, 1, 1), periods=10, freq="H")
# date_time_index = get_dt_range(self.year, self.selected_months)
energysystem = solph.EnergySystem(timeindex=date_time_index, infer_last_interval=True)
# ######################### create energysystem components ################

el_bus = solph.Bus(label="электроэнергия")
energysystem.add(el_bus)


el_source = solph.components.Source(
    label="электроэнергия (source)",
    outputs={el_bus: solph.Flow(nominal_value = 1500, variable_costs=7)},
)
energysystem.add(el_source)



el_expense_source = solph.components.Source(
    label="электроэнергия (source) expensive",
    outputs={el_bus: solph.Flow(nominal_value = 1500, variable_costs=10, nonconvex=solph.NonConvex(), min = 1)},
)
energysystem.add(el_expense_source)


el_cheap_avail = 3 * [0] + 4 * [1] + 3 * [0]
el_cheap_source = solph.components.Source(
    label="электроэнергия (source) cheap",
    outputs={el_bus: solph.Flow(nominal_value = 1500, variable_costs=-10, max=el_cheap_avail, nonconvex=solph.NonConvex())},
)
energysystem.add(el_cheap_source)

el_sink = solph.components.Sink(
    label="электроэнергия (sink)",
    inputs={el_bus: solph.Flow(nominal_value = 1500, fix = 1)},
)
energysystem.add(el_sink)


model = solph.Model(energysystem)

solph.constraints.equate_variables(
    model,
    model.NonConvexFlowBlock.status[el_cheap_source, el_bus, 5],
    model.NonConvexFlowBlock.status[el_expense_source, el_bus, 0])


blocks = [el_source, el_cheap_source, el_expense_source]

model.solve(solver="cplex")
results = solph.processing.results(model)

el_results = solph.views.node(results, el_bus.label)["sequences"].dropna()

el_df = pd.DataFrame()

for block in blocks:
    el_df[block.label] = el_results[((block.label, el_bus.label), "flow")]


ax_el = el_df.plot(kind="area", ylim=(0, 2000))

plt.show(block=True)