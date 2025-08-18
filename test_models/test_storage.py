import datetime as dt

import pandas as pd
from matplotlib import pyplot as plt
from oemof import solph

date_time_index = pd.date_range(dt.datetime(2021, 1, 1), periods=10, freq="H")
# date_time_index = get_dt_range(self.year, self.selected_months)
energysystem = solph.EnergySystem(timeindex=date_time_index, infer_last_interval=True)
# ######################### create energysystem components ################

# gas_bus = solph.Bus(label="природный газ")
el_bus = solph.Bus(label="электроэнергия")

# energysystem.add(gas_bus)
energysystem.add(el_bus)


var_cost_lst = 5 * [1] + 5 * [10]

blocks = []
source = solph.components.Source(
    label="электроэнергия (source)",
    outputs={el_bus: solph.Flow(nominal_value = 1500, variable_costs=var_cost_lst)},
)
energysystem.add(source)
blocks.append(source)

sink = solph.components.Sink(
    label="электроэнергия (sink)",
    inputs={el_bus: solph.Flow(nominal_value = 1000, fix = 1)},
)
energysystem.add(sink)

storage = solph.components.GenericStorage(
    label="аккумулятор (storage)",
    nominal_storage_capacity=800,
    
    inputs={el_bus: solph.Flow(variable_costs=0.001, nominal_value= 300)},
    outputs={el_bus: solph.Flow(variable_costs=0.001, nominal_value=300)},
    balanced=True
)
energysystem.add(storage)
blocks.append(storage)



model = solph.Model(energysystem)

model.solve(solver="cplex")
results = solph.processing.results(model)


el_results = solph.views.node(results, el_bus.label)["sequences"].dropna()


el_df = pd.DataFrame()

for block in blocks:
    el_df[block.label] = el_results[((block.label, el_bus.label), "flow")]

storage_input_df = pd.DataFrame()
storage_input_df["зарядка"] = el_results[((el_bus.label, storage.label), "flow")]



storage_results = solph.views.node(results, storage.label)["sequences"].dropna()
storage_content_df = pd.DataFrame()
storage_content_df["заряд"] = storage_results[(storage.label, "None"), "storage_content"]

print(storage_content_df)


ax_storage_input = storage_input_df.plot(kind="line", ylim=(0, 1500))

ax_storage_content = storage_content_df.plot(kind="line", ylim=(0, 1500), ax=ax_storage_input)


ax_el = el_df.plot(kind="area", ylim=(0, 1500), ax=ax_storage_content)

plt.show(block=True)