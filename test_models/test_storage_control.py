import datetime as dt

import pandas as pd
from matplotlib import pyplot as plt
from oemof import solph

date_time_index = pd.date_range(dt.datetime(2021, 1, 1), periods=10, freq="H")
# date_time_index = get_dt_range(self.year, self.selected_months)
energysystem = solph.EnergySystem(timeindex=date_time_index, infer_last_interval=True)


el_bus = solph.Bus(label="электроэнергия")
energysystem.add(el_bus)


expense_source = solph.components.Source(
    label="электроэнергия (source) expensive",
    outputs={el_bus: solph.Flow(nominal_value = 1500, variable_costs=10, nonconvex=solph.NonConvex(), min = 1)},
)
energysystem.add(expense_source)


control_storage = solph.components.GenericStorage(
    label="charger",
    nominal_storage_capacity=1000,
    inputs={el_bus: solph.Flow(nominal_value = 1500, variable_costs=10, nonconvex=solph.NonConvex(), min = 1)},
    outputs={el_bus: solph.Flow(nominal_value = 1500, variable_costs=10, nonconvex=solph.NonConvex(), min = 1)},
    balanced=False,
)
energysystem.add(control_storage)


cheap_source = solph.components.Source(
    label="электроэнергия (source) cheap",
    outputs={el_bus: solph.Flow(nominal_value = 1500, variable_costs=7)},
)
energysystem.add(cheap_source)


charger_for_storage = solph.components.Source(
    label="электроэнергия (source) expensive",
    outputs={control_storage.input_bus: solph.Flow(nominal_value = 1500, variable_costs=10, nonconvex=solph.NonConvex(), min = 1)},
)
energysystem.add(charger_for_storage)

sink =  solph.components.Sink(
        label="электроэнергия (sink)",
        inputs={el_bus: solph.Flow(nominal_value = 1500, fix = 1)},
)
energysystem.add(sink)


energysystem.solve(solver="cplex")

blocks = [charger_for_storage, cheap_source, expense_source]

results = solph.processing.results(energysystem)

el_results = solph.views.node(results, el_bus.label)["sequences"].dropna()

el_df = pd.DataFrame()

for block in blocks:
    el_df[block.label] = el_results[((block.label, el_bus.label), "flow")]


ax_el = el_df.plot(kind="area", ylim=(0, 2000))

plt.show(block=True)