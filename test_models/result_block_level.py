import datetime as dt

import pandas as pd
from matplotlib import pyplot as plt
from oemof import solph

date_time_index = pd.date_range(dt.datetime(2021, 1, 1), periods=24, freq="H")
energysystem = solph.EnergySystem(timeindex=date_time_index, infer_last_interval=True)


gas_bus = solph.Bus(label="gas_bus")
energysystem.add(gas_bus)

el_bus = solph.Bus(label="el_bus")
energysystem.add(el_bus)

heat_bus = solph.Bus(label="heat_bus")
energysystem.add(heat_bus)


grid_el_bus = solph.Bus(label="grid_el", balanced=False,
            inputs={el_bus: solph.Flow(nominal_value=100, variable_costs=-3)},
            outputs={el_bus: solph.Flow(nominal_value=100, variable_costs=3)}
            )
energysystem.add(grid_el_bus)


gas_source = solph.components.Source(
    label="gas_source",
    outputs={gas_bus: solph.Flow(variable_costs=10)},
)
energysystem.add(gas_source)


el_cpp_cheap_converter = solph.components.Converter(
    label="el_cpp_cheap_converter",
    inputs={gas_bus: solph.Flow()},
    outputs={el_bus: solph.Flow(nominal_value=150, variable_costs=3)},
    conversion_factors={gas_bus: 1/0.5, el_bus: 1},
)
energysystem.add(el_cpp_cheap_converter)

el_cpp_expensive_converter = solph.components.Converter(
    label="el_cpp_expensive_converter",
    inputs={gas_bus: solph.Flow()},
    outputs={el_bus: solph.Flow(nominal_value=200, variable_costs=4)},
    conversion_factors={gas_bus: 1/0.3, el_bus: 1},
)
energysystem.add(el_cpp_expensive_converter)


heat_boiler_converter = solph.components.Converter(
    label="heat_boiler_converter",
    inputs={gas_bus: solph.Flow()},
    outputs={heat_bus: solph.Flow(nominal_value=400, variable_costs=3)},
    conversion_factors={gas_bus: 1/0.9, heat_bus: 1},
)
energysystem.add(heat_boiler_converter)


el_heat_chp_converter = solph.components.Converter(
    label="heat_chp_converter",
    inputs={gas_bus: solph.Flow()},
    outputs={heat_bus: solph.Flow(), el_bus: solph.Flow(nominal_value=550, variable_costs=3)},
    conversion_factors={gas_bus: 1/0.8, heat_bus: 2, el_bus: 1},
)
energysystem.add(el_heat_chp_converter
)


el_sink = solph.components.Sink(
    label="el_sink",
    inputs={el_bus: solph.Flow(nominal_value=800, fix=1)},
)
energysystem.add(el_sink)

heat_sink = solph.components.Sink(
    label="heat_sink",
    inputs={heat_bus: solph.Flow(nominal_value=1200, fix=1)},
)
energysystem.add(heat_sink)

model = solph.Model(energysystem)


# el_storage = solph.components.GenericStorage(
#     label="el_storage",
#     initial_storage_level=1,
#     nominal_capacity=800 * 24,
#     inputs={el_bus: solph.Flow(variable_costs=-10)},
#     outputs={el_bus: solph.Flow(variable_costs=-10)},
#     balanced=False
# )
# energysystem.add(el_storage)



model.solve(
    solver="cplex",
    solve_kwargs={"tee": True},
)

res = model.results()
model.receive_duals()

# results = solph.processing.results(model)
results = res


el_blocks = [el_cpp_cheap_converter, el_cpp_expensive_converter, el_heat_chp_converter, grid_el_bus]
heat_blocks = [heat_boiler_converter, el_heat_chp_converter]

el_results = solph.views.node(results, el_bus.label)["sequences"].dropna()
heat_results = solph.views.node(results, heat_bus.label)["sequences"].dropna()


el_df = pd.DataFrame()
for block in el_blocks:
    el_df[block.label] = el_results[((block.label, el_bus.label), "flow")]

heat_df = pd.DataFrame()
for block in heat_blocks:
    heat_df[block.label] = heat_results[((block.label, heat_bus.label), "flow")]

ax_el = el_df.plot(kind="area", ylim=(0, 2000), title="Electricity")
ax_heat = heat_df.plot(kind="area", ylim=(0, 2000), title="Heat")


# All = "all"
# HasInputs = "has_inputs"
# HasOnlyInputs = "has_only_inputs"
# HasOnlyOutputs = "has_only_outputs"
# HasOutputs = "has_outputs"

# only_inputs  = solph.views.NodeOption.HasOnlyInputs
# filtered_nodes = solph.views.filter_nodes(results, only_inputs) # множество экземпляров класса
# el_cpp_cheap_converter = solph.views.get_node_by_name(results, "el_cpp_cheap_converter") # экземпляр класса
# converters = solph.views.node_input_by_type(results, solph.components.Converter)
# converters_output = solph.views.node_output_by_type(results, solph.components.Converter)

# model.receive_duals()
# print(model.dual)
# print(model.rc)


# Что такое receive_duals?
# Метод receive_duals — это как будто вы просите вашу оптимизационную модель не просто сказать вам "как" произвести энергию дешевле всего (сколько каждая станция должна работать), но и ответить на вопрос:

# "Сколько мне будет стоить или сколько я сэкономлю, если я немного изменю какое-либо из моих ограничений?"

plt.show(block=True)
