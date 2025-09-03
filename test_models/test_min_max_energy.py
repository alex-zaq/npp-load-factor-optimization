import datetime as dt

import pandas as pd
from matplotlib import pyplot as plt
from oemof import solph

date_time_index = pd.date_range(dt.datetime(2021, 1, 1), periods=20, freq="H")
energysystem = solph.EnergySystem(timeindex=date_time_index, infer_last_interval=True)
# ######################### create energysystem components ################

el_bus = solph.Bus(label="электроэнергия")
energysystem.add(el_bus)




source_1 = solph.components.Source(
    label="source_1",
    outputs={el_bus: solph.Flow(nominal_value = 100, variable_costs=-100)},
)
energysystem.add(source_1)

source_2 = solph.components.Source(
    label="source_2",
    outputs={el_bus: solph.Flow(
        nominal_value = 50,
        min = 0,
        nonconvex=solph.NonConvex(
            # positive_gradient_limit=0,
            # negative_gradient_limit=1
            ),
        variable_costs=999,
        full_load_time_max=4,
        full_load_time_min=4,
        max= 3 * [0] + 2 * [1] + [0]  + 14 * [1],
        # positive_gradient_limit=0,
        # negative_gradient_limit=0
        )},
)
energysystem.add(source_2)

sink_el = solph.components.Sink(
    label="sink_el",
    inputs={el_bus: solph.Flow(nominal_value = 100, fix = 1)},
)
energysystem.add(sink_el)




model = solph.Model(energysystem)

model.solve(solver="cplex")
results = solph.processing.results(model)


el_results = solph.views.node(results, el_bus.label)["sequences"].dropna()


el_df = pd.DataFrame()


blocks = [
    source_2,
    source_1,
    ]

for block in blocks:
    el_df[block.label] = el_results[((block.label, el_bus.label), "flow")]





ax_el_df = el_df.plot(kind="area", ylim=(0, 150))



plt.show(block=True)