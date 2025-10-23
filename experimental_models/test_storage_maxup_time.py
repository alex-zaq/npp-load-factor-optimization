import datetime as dt

import pandas as pd
from matplotlib import pyplot as plt
from oemof import solph

date_time_index = pd.date_range(dt.datetime(2021, 1, 1), periods=20, freq="H")
energysystem = solph.EnergySystem(timeindex=date_time_index, infer_last_interval=True)


el_bus = solph.Bus(label="el_bus")
energysystem.add(el_bus)
storage_in_bus = solph.Bus(label="storage_in_bus")
energysystem.add(storage_in_bus)
storage_out_bus = solph.Bus(label="storage_out_bus")
energysystem.add(storage_out_bus)


power_val = 1500
cheap_min_uptime = 5



expense_source = solph.components.Source(
    label="expense_source",
    outputs={el_bus: solph.Flow(nominal_value = power_val, variable_costs=1000)},
)
energysystem.add(expense_source)





cheap_converter = solph.components.Converter(
    label="cheap_converter",
    inputs={storage_out_bus: solph.Flow()},
    outputs={el_bus: solph.Flow(
        nominal_value = power_val,
        variable_costs=1,
        min = 1,
        nonconvex=solph.NonConvex(minimum_uptime=cheap_min_uptime), 
        custom_attributes={"keyword": True},
        )},
)
energysystem.add(cheap_converter)





control_storage = solph.components.GenericStorage(
    initial_storage_level=0,
    label="control_storage",
    nominal_storage_capacity=cheap_min_uptime * power_val,
    inputs={storage_in_bus: solph.Flow()},
    outputs={storage_out_bus: solph.Flow()},
    balanced=False,
)
energysystem.add(control_storage)




charger_for_storage = solph.components.Source(
    label="charger_for_storage",
    outputs={
        storage_in_bus: solph.Flow(nominal_value=1e8, nonconvex=solph.NonConvex(), min = 0, max = 1, custom_attributes={"keyword": True})},
)
energysystem.add(charger_for_storage)




sink_demand=solph.components.Sink(
        label="sink_demand",
        inputs={el_bus: solph.Flow(nominal_value = power_val, fix = 1)},
)
energysystem.add(sink_demand)




model = solph.Model(energysystem)


solph.constraints.limit_active_flow_count_by_keyword(
    model, "keyword", lower_limit=0, upper_limit=1
)





model.solve(solver="cplex")

blocks = [expense_source, cheap_converter]

results = solph.processing.results(model)

el_results = solph.views.node(results, el_bus.label)["sequences"].dropna()

alt_control_bus_results = solph.views.node(results, storage_in_bus.label)["sequences"].dropna()



el_df = pd.DataFrame()

for block in blocks:
    el_df[block.label] = el_results[((block.label, el_bus.label), "flow")]


storage_results = solph.views.node(results, control_storage.label)["sequences"].dropna()
storage_content_df = pd.DataFrame()
storage_content_df["заряд"] = storage_results[(control_storage.label, "None"), "storage_content"]

charger_df = pd.DataFrame()
charger_df["charger"] = alt_control_bus_results[((charger_for_storage.label, storage_in_bus.label), "flow")]

ax_charger = charger_df.plot(kind="line", ylim=(0, 5000))

ax_storage_content = storage_content_df.plot(kind="line", ylim=(0, 5000), ax=ax_charger)

ax_el = el_df.plot(kind="area", ylim=(0, 5000), ax=ax_storage_content)

plt.show(block=True)
