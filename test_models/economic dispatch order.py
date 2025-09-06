import datetime as dt
import os

import pandas as pd
from matplotlib import pyplot as plt

# sys.path.insert(0, "./")
# from custom_modules.excel_operations import create_res_scheme
# from custom_modules.generic_blocks import Generic_blocks
from oemof import solph
from oemof.solph import Bus, Flow, Model
from oemof.solph.components import Sink, Source

date_time_index = pd.date_range(dt.datetime(2021, 1, 1), periods=24, freq="H")

es = solph.EnergySystem(timeindex=date_time_index, infer_last_interval=True)




gas_bus = Bus(label="natural gas (energysystem level)")
el_bus = Bus(label="electricity (energysystem level)")


control_bus_npp = Bus(label="control flow (npp)")


es.add(gas_bus)
es.add(el_bus)


es.add(control_bus_npp)


gas_tr = Source(
    label="source of natural gas", outputs={gas_bus: Flow(variable_costs=0)}
)
es.add(gas_tr)


npp_power = 400
cpp_power = 300
npp_key_word_1 = "npp_1"
npp_key_word_2 = "npp_2"


min_npp = 0.5

npp = solph.components.Source(
    label="NPP",
    outputs={
        el_bus: Flow(
            min=min_npp,
            nominal_value=npp_power,
            variable_costs=999,
            nonconvex=solph.NonConvex(),
            custom_attributes={npp_key_word_1: True},
        ),
        # control_bus_npp: Flow(custom_attributes={npp_key_word_2: True}),
    },
)
es.add(npp)

control_source_npp = solph.components.Source(
    label="control source (npp)",
    outputs={control_bus_npp: Flow(custom_attributes={npp_key_word_2: True})},
)
es.add(control_source_npp)



cpp = solph.components.Converter(
    label="CPP",
    inputs={gas_bus: Flow()},
    outputs={el_bus: Flow(
        nominal_value=cpp_power,
        min=0.1,
        variable_costs=-10,
        nonconvex=solph.NonConvex(),
        )}, 
)
es.add(cpp)






cpp_cheap = solph.components.Converter(
    label="cpp_cheap",
    inputs={gas_bus: Flow()},
    outputs={el_bus: Flow(
        nominal_value=cpp_power,
        variable_costs=-5,
        nonconvex=solph.NonConvex(),
        )}, 
)
es.add(cpp_cheap)


excess_sink_npp = Sink(
    label="excess sink (npp)",
    inputs={control_bus_npp: Flow(
        nominal_value= npp_power*(1-min_npp)
        )},
)
es.add(excess_sink_npp)


control_sink_npp = Sink(
    label="sink (npp)",
    inputs= {control_bus_npp: Flow(
        nominal_value=npp_power*(1-min_npp),
        min = 1,
        nonconvex= solph.NonConvex(),
        )}
    )
es.add(control_sink_npp)







el_sink = Sink(
    label="electricity consumer",
    inputs={el_bus: Flow(nominal_value=400, fix=1)},
)
es.add(el_sink)






script_name = os.path.splitext(os.path.basename(__file__))[0]
# create_res_scheme(es, f"{os.path.dirname(os.path.abspath(__file__))}/{script_name}" )

model = Model(energysystem=es)






 
for i in range(24):
    solph.constraints.equate_variables(
        model,
        model.NonConvexFlowBlock.status[cpp, el_bus, i],
        model.NonConvexFlowBlock.status[control_bus_npp, control_sink_npp, i],
    )



 
# for i in range(24):
solph.constraints.equate_flows_by_keyword(
        model,
        npp_key_word_1,
        npp_key_word_2
    )







model.solve(solver="cplex")
results = solph.processing.results(model)


el_results = solph.views.node(results, el_bus.label)["sequences"].dropna()

cb_results = solph.views.node(results, control_bus_npp.label)["sequences"].dropna()
# heat_results = solph.views.node(results, heat_bus.label)["sequences"].dropna()
# gas_results = solph.views.node(results, gas_bus.label)["sequences"].dropna()


# el_blocks = [el_block, el_expense_block]
el_blocks = [npp, cpp, cpp_cheap]
# el_blocks = [expense_block]
el_df = pd.DataFrame()
for el_block in el_blocks:
    el_df[el_block.label] = el_results[((el_block.label, el_bus.label), "flow")]

cb_blocks = [excess_sink_npp, control_sink_npp]
cb_df = pd.DataFrame()
for cb_block in cb_blocks:
    cb_df[cb_block.label] = cb_results[((control_bus_npp.label, cb_block.label), "flow")]


# cb_expense_blocks = [npp]
# cb_expense_blocks_df = pd.DataFrame()
# for cb_block in cb_expense_blocks:
#     cb_expense_blocks_df[cb_block.label] = cb_results[
#         ((cb_block.label, control_bus_npp.label), "flow")
#     ]


el_df = el_df.drop(el_df.index[-1])

ax_el = el_df.plot(kind="area", ylim=(0, 1000))

ax_cb_df = cb_df.plot(kind="area", ylim=(0, 1000))


# ax_cb_expense_df = cb_expense_blocks_df.plot(kind="area", ylim=(0, 1000))


# heat_blocks = [heat_block, heat_expense_block]
# heat_blocks = [heat_block]
# heat_df = pd.DataFrame()
# for heat_block in heat_blocks:
#     heat_df[heat_block.label] = heat_results[
#         ((heat_block.label, heat_bus.label), "flow")
#     ]


# gas_blocks = [gas_tr]
# gas_df = pd.DataFrame()
# for gas_block in gas_blocks:
#     gas_df[gas_block.label] = gas_results[((gas_block.label, gas_bus.label), "flow")]


# fig, (ax1, ax2, ax3) = plt.subplots(1, 3)


# ax_heat = heat_df.plot(kind="line", ylim=(0, 1000), color="orange", ax=ax2)
# ax_gas = gas_df.plot(kind="line", ylim=(0, 1000), color="green", ax=ax3)

plt.show(block=True)


# 1-источник полезный поток (мощность-1, bus-1) контролирующий поток(мощность-2 = мощность-1, bus-2)


# источник-2 с потоком-2 (с статусом) (вход - bus-2 с мощность-1)


# 3-источник полезный поток (статус выходного потока равен статусу потока-2)
