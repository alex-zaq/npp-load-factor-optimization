import datetime as dt
import os

import pandas as pd
from matplotlib import pyplot as plt

# sys.path.insert(0, "./")
# from custom_modules.excel_operations import create_res_scheme
# from custom_modules.generic_blocks import Generic_blocks
from oemof import solph

date_time_index = pd.date_range(dt.datetime(2021, 1, 1), periods=24, freq="H")

es = solph.EnergySystem(timeindex=date_time_index, infer_last_interval=True)



el_bus = solph.Bus(label="electricity (energysystem level)")
es.add(el_bus)



expensive_block = solph.components.Source(
    label="expensive_block",
    outputs={
        el_bus: solph.Flow(
            min=0.4,
            nominal_value=200,
            variable_costs=999,
            nonconvex=solph.NonConvex(),
            custom_attributes={"expensive_block": True},
        ),
        # control_bus_npp: Flow(custom_attributes={npp_key_word_2: True}),
    },
)
es.add(expensive_block)


cheap_block = solph.components.Source(
    label="cheap_block",
    outputs={el_bus: solph.Flow(
        nominal_value=1000,
        min=0.1,
        variable_costs=-999,
        nonconvex=solph.NonConvex(),
        custom_attributes={"cheap_block": True},
        )}, 
)
es.add(cheap_block)



el_sink = solph.components.Sink(
    label="el_sink consumer",
    inputs={el_bus: solph.Flow(nominal_value=1000, fix=1)},
)
es.add(el_sink)


script_name = os.path.splitext(os.path.basename(__file__))[0]
# create_res_scheme(es, f"{os.path.dirname(os.path.abspath(__file__))}/{script_name}" )

model = solph.Model(energysystem=es)



model.solve(solver="cplex")
results = solph.processing.results(model)


el_results = solph.views.node(results, el_bus.label)["sequences"].dropna()



el_blocks = [expensive_block, cheap_block]



el_df = pd.DataFrame()
for el_block in el_blocks:
    el_df[el_block.label] = el_results[((el_block.label, el_bus.label), "flow")]


ax_el = el_df.plot(kind="area", ylim=(0, 1500))
 

 
plt.show(block=True)

 