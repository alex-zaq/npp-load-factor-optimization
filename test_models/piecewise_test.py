import datetime as dt

import pandas as pd
from matplotlib import pyplot as plt
from oemof import solph

date_time_index = pd.date_range(dt.datetime(2021, 1, 1), periods=24, freq="H")
energysystem = solph.EnergySystem(timeindex=date_time_index, infer_last_interval=True)
# ######################### create energysystem components ###############


gas_bus = solph.Bus(label="gas_bus")
energysystem.add(gas_bus)

el_bus = solph.Bus(label="электроэнергия")
energysystem.add(el_bus)


gas_source = solph.components.Source(
    label="gas_source",
    outputs={gas_bus: solph.Flow()},
)
energysystem.add(gas_source)


source_expensed = solph.components.Source(
    label="source_expensed",
    outputs={el_bus: solph.Flow(variable_costs=999)},
    
)
energysystem.add(source_expensed)


source_1 = solph.components.experimental.PiecewiseLinearConverter( 
   label='piecewise',
   inputs={gas_bus: solph.Flow(nominal_capacity=100)},
   outputs={el_bus: solph.Flow()},
   in_breakpoints=[0,25,50,75,100],
   conversion_function=lambda x: x**0.5,
   pw_repn='CC',
)
energysystem.add(source_1)



sink_el = solph.components.Sink(
    label="sink_el",
    inputs={el_bus: solph.Flow(nominal_value = 1, fix = 150)},
)
energysystem.add(sink_el)




model = solph.Model(energysystem)



model.solve(solver="cplex",  solve_kwargs={"tee": True},)
results = solph.processing.results(model)


el_results = solph.views.node(results, el_bus.label)["sequences"].dropna()
gas_results = solph.views.node(results, gas_bus.label)["sequences"].dropna()

res_df = pd.DataFrame()


blocks = [source_1, source_expensed]

for block in blocks:
    res_df[block.label] = el_results[((block.label, el_bus.label), "flow")]


gas_df = pd.DataFrame()
gas_df["gas_source"] = gas_results[((gas_source.label, gas_bus.label), "flow")]

res_df[res_df < 0] = 0

ax_el_df = res_df.plot(kind="area", ylim=(0, 500))

# ax_gas_df = gas_df.plot(kind="area")


# eff_df = pd.DataFrame()
# eff_df["eff"] = res_df["l_source_1"] / gas_df["gas_source"]

# ax_eff_df = eff_df.plot(kind="area")

plt.show(block=True)