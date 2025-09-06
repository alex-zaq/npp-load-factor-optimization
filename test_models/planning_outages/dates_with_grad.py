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
    outputs={el_bus: solph.Flow(nominal_value = 200, variable_costs=100)},
)
energysystem.add(source_1)


control_bus = solph.Bus(label="control_bus")
energysystem.add(control_bus)

source_control = solph.components.Source(
    label="source_control",
    outputs={control_bus: solph.Flow(nominal_value = 100, min=1, nonconvex=solph.NonConvex(
            minimum_uptime=5
        )
)},
)
energysystem.add(source_control)

max_lst = 20 * [1]

max_lst[0] = 0

converter_1 = solph.components.Converter(
    label="converter_1",
    inputs={control_bus: solph.Flow()},
    outputs={el_bus: solph.Flow(
        nominal_value = 100,
        min = 0,
        max=max_lst,
        nonconvex=solph.NonConvex(
            minimum_uptime=5,
            initial_status=0
            ),
        variable_costs=999,
        full_load_time_max=5,
        full_load_time_min=5,
        positive_gradient_limit=[0,0,0,0,0,  0,0,1,0,1,   1,0,0,0,0,  0,0,0,0,0],
        negative_gradient_limit=1
        # positive_gradient_limit=0,
        # negative_gradient_limit=[0,0,0,0,1,  0,0,0,0,0,   0,0,0,0,0,  0,0,0,0,0],
        # negative_gradient_limit=[0,0,0,1,1,  1,1,1,1,1,   1,1,1,1,1,  1,1,1,1,1],
        )},
)
energysystem.add(converter_1)

sink_el = solph.components.Sink(
    label="sink_el",
    inputs={el_bus: solph.Flow(nominal_value = 200, fix = 1)},
)
energysystem.add(sink_el)




model = solph.Model(energysystem)

model.solve(solver="cplex")
results = solph.processing.results(model)


el_results = solph.views.node(results, el_bus.label)["sequences"].dropna()


el_df = pd.DataFrame()


blocks = [
    converter_1,
    source_1,
    ]

for block in blocks:
    el_df[block.label] = el_results[((block.label, el_bus.label), "flow")]





ax_el_df = el_df.plot(kind="area", ylim=(0, 300))



plt.show(block=True)