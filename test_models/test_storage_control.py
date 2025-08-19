import datetime as dt

import pandas as pd
from matplotlib import pyplot as plt
from oemof import solph

date_time_index = pd.date_range(dt.datetime(2021, 1, 1), periods=20, freq="H")
energysystem = solph.EnergySystem(timeindex=date_time_index, infer_last_interval=True)


el_bus = solph.Bus(label="электроэнергия")
energysystem.add(el_bus)
alt_control_bus = solph.Bus(label="alt контроль")
energysystem.add(alt_control_bus)
control_bus = solph.Bus(label="контроль")
energysystem.add(control_bus)


power_val = 1500
cheap_min_uptime = 5
capacity_val = 5 * power_val
high_var_cost = 1000
low_var_cost = 1


# low_var_cost, high_var_cost = high_var_cost, low_var_cost


expense_source = solph.components.Source(
    label="электроэнергия (source) expensive",
    outputs={el_bus: solph.Flow(nominal_value = power_val, variable_costs=high_var_cost)},
)
energysystem.add(expense_source)


cheap_converter = solph.components.Converter(
    label="электроэнергия (converter) cheap",
    inputs={control_bus: solph.Flow()},
    outputs={el_bus: solph.Flow(nominal_value = 1500, variable_costs=low_var_cost, min = 1, nonconvex=solph.NonConvex(minimum_uptime=cheap_min_uptime))},
)
energysystem.add(cheap_converter)





control_storage = solph.components.GenericStorage(
    initial_storage_level=0,
    label="charger",
    nominal_storage_capacity=capacity_val,
    inputs={alt_control_bus: solph.Flow()},
    outputs={control_bus: solph.Flow()},
    balanced=False,
)
energysystem.add(control_storage)



max_charge_lst = [0,0,0,0,1, 0,0,0,0,0,     0,0,0,0,0, 0,0,0,0,0]

charger_for_storage = solph.components.Source(
    label="блока зарядки (source)",
    outputs={alt_control_bus: solph.Flow(nominal_value = power_val * cheap_min_uptime, nonconvex=solph.NonConvex(), min = 0 , max = max_charge_lst)},
)
energysystem.add(charger_for_storage)




sink =  solph.components.Sink(
        label="электроэнергия (sink)",
        inputs={el_bus: solph.Flow(nominal_value = power_val, fix = 1)},
)
energysystem.add(sink)




model = solph.Model(energysystem)


solph.constraints.equate_variables(
    model,
    model.NonConvexFlowBlock.status[charger_for_storage, alt_control_bus, 4],
    model.NonConvexFlowBlock.status[cheap_converter, el_bus, 5],
)



model.solve(solver="cplex")

blocks = [expense_source, cheap_converter]

results = solph.processing.results(model)

el_results = solph.views.node(results, el_bus.label)["sequences"].dropna()

alt_control_bus_results = solph.views.node(results, alt_control_bus.label)["sequences"].dropna()



el_df = pd.DataFrame()

for block in blocks:
    el_df[block.label] = el_results[((block.label, el_bus.label), "flow")]


storage_results = solph.views.node(results, control_storage.label)["sequences"].dropna()
storage_content_df = pd.DataFrame()
storage_content_df["заряд"] = storage_results[(control_storage.label, "None"), "storage_content"]

charger_df = pd.DataFrame()
charger_df["charger"] = alt_control_bus_results[((charger_for_storage.label, alt_control_bus.label), "flow")]

ax_charger = charger_df.plot(kind="line", ylim=(0, 5000))

ax_storage_content = storage_content_df.plot(kind="line", ylim=(0, 5000), ax=ax_charger)

ax_el = el_df.plot(kind="area", ylim=(0, 5000), ax=ax_storage_content)

plt.show(block=True)