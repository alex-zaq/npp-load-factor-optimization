import datetime as dt

import pandas as pd
from matplotlib import pyplot as plt
from oemof import solph

date_time_index = pd.date_range(dt.datetime(2021, 1, 1), periods=(count:=10), freq="H")
energysystem = solph.EnergySystem(timeindex=date_time_index, infer_last_interval=True)
# ######################### create energysystem components ################

el_bus = solph.Bus(label="электроэнергия")
energysystem.add(el_bus)



source_1 = solph.components.Source(
    label="source_1",
    outputs={el_bus: solph.Flow(
        nominal_value = 300,
        variable_costs=100,
        nonconvex=solph.NonConvex(
            initial_status=0,
            minimum_uptime=count-1,
        ),
        min = 1,
        max= [0, 1, 1, 1, 1,    1, 1, 1, 1, 1],
        )},
)
energysystem.add(source_1)

source_2 = solph.components.Source(
    label="source_2",
    outputs={el_bus: solph.Flow(
        nominal_value = 300,
        variable_costs=-100,
        nonconvex=solph.NonConvex(),
        max= [1, 1, 1, 1, 1,    0, 1, 1, 1, 1],
        )},
)
energysystem.add(source_2)


 


sink_el = solph.components.Sink(
    label="sink_el",
    inputs={el_bus: solph.Flow(
        nominal_value = 300,
        fix = [0, 1, 1, 1, 1,    1, 1, 1, 1, 1],
        )},
)
energysystem.add(sink_el)




model = solph.Model(energysystem)




model.solve(solver="cplex")
results = solph.processing.results(model)


el_results = solph.views.node(results, el_bus.label)["sequences"].dropna()

res_df = pd.DataFrame()


blocks = [source_1, source_2]

for block in blocks:
    res_df[block.label] = el_results[((block.label, el_bus.label), "flow")]

 

ax_el_df = res_df.plot(kind="area", ylim=(0, 1000))



plt.show(block=True)