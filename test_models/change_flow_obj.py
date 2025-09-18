import datetime as dt

import pandas as pd
from matplotlib import pyplot as plt
from oemof import solph

date_time_index = pd.date_range(dt.datetime(2021, 1, 1), periods=20, freq="H")
energysystem = solph.EnergySystem(timeindex=date_time_index, infer_last_interval=True)
# ######################### create energysystem components ################

el_bus = solph.Bus(label="электроэнергия")
energysystem.add(el_bus)

control_bus = solph.Bus(label="control_bus", balanced=False)
energysystem.add(control_bus)


source_1 = solph.components.Source(
    label="source_1",
    outputs={el_bus: solph.Flow(
        nominal_value = 300,
        variable_costs=-10,
        custom_attributes={"source_1": True}
        )},
)
energysystem.add(source_1)




source_2_flow = solph.Flow(
        nominal_value = 300,
        variable_costs=999,
        # custom_attributes={"source_1": True}
)

# working


source_2 = solph.components.Source(
    label="source_2",
    outputs={
        
        control_bus: source_2_flow },
    # outputs={el_bus: flow},
)

source_2_flow.source_2 = True
# source_2.outputs[control_bus].custom["source_2"] = True

energysystem.add(source_2)



sink_el = solph.components.Sink(
    label="sink_el",
    inputs={el_bus: solph.Flow(nominal_value = 300, fix = 1)},
)
energysystem.add(sink_el)




model = solph.Model(energysystem)


solph.constraints.equate_flows_by_keyword(
    model,
    "source_1",
    "source_2",
    factor1=1,
    name="equate_flows",
    )


model.solve(solver="cplex")
results = solph.processing.results(model)


el_results = solph.views.node(results, el_bus.label)["sequences"].dropna()
control_results = solph.views.node(results, control_bus.label)["sequences"].dropna()

res_df = pd.DataFrame()


block = source_1
res_df[block.label] = el_results[((block.label, el_bus.label), "flow")]


block = source_2
res_df[block.label] = control_results[((block.label, control_bus.label), "flow")]



ax_el_df = res_df.plot(kind="area", ylim=(0, 1000))



plt.show(block=True)