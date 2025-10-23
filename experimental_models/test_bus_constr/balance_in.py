import datetime as dt

import pandas as pd
from matplotlib import pyplot as plt
from oemof import solph

date_time_index = pd.date_range(dt.datetime(2021, 1, 1), periods=10, freq="H")
energysystem = solph.EnergySystem(timeindex=date_time_index, infer_last_interval=True)
# ######################### create energysystem components ################



process_bus_1 = solph.Bus(label="process_1_output_bus", balanced=True)
energysystem.add(process_bus_1)
process_bus_2 = solph.Bus(label="process_2_output_bus", balanced=True)
energysystem.add(process_bus_2)

# Шина для сбора отработанного тепла
waste_heat_bus = solph.Bus(
    label="waste_heat_bus",
    balanced=True,  # Должна быть сбалансирована
    inputs={
        # Определяем, откуда waste_heat_bus ПОЛУЧАЕТ энергию
        process_bus_1: solph.Flow(nominal_capacity=20),
        process_bus_2: solph.Flow(nominal_capacity=15),
    },
)
energysystem.add(waste_heat_bus)

# Что это значит: Эта шина явно определяет, откуда она получает энергию. Однако, поскольку balanced=True, она обязательно должна куда-то отдавать эту энергию.
# Когда полезно:
# Как и в предыдущем случае, такая конфигурация сама по себе неполна и приведет к неразрешимости модели, если вы не предоставите этой шине outputs для других компонентов.
# Это полезно, когда вы моделируете шину-коллектор, которая должна собирать энергию из нескольких источников, но затем эта энергия должна быть использована или передана дальше.
# Пример: Шина сбора отработанного тепла, куда поступает тепло от разных промышленных процессов. Вы определяете inputs от этих процессов. Но чтобы шина была сбалансирована, она должна отдавать это тепло, например, в систему централизованного теплоснабжения или на тепловой насос (т.е., input потребителя/трансформатора идет output от этой шины).


# !!! ВАЖНО: Для того чтобы waste_heat_bus был сбалансирован,
# !!! ему НУЖЕН ПОТРЕБИТЕЛЬ энергии (output)!
# Например, система централизованного теплоснабжения, которая потребляет тепло от waste_heat_bus:
# district_heating_sink = solph.Sink(
#     label="district_heating_sink",
#     inputs={waste_heat_bus: solph.Flow(nominal_capacity=50)} # Энергия идет ИЗ waste_heat_bus
# )
# Без такого потребителя, модель будет неразрешимой, так как waste_heat_bus
# получает энергию, но не может от нее избавиться.



process_source_1 = solph.components.Source(
    label="process_source_1",
    outputs={process_bus_1: solph.Flow()},
)
energysystem.add(process_source_1)
process_source_2 = solph.components.Source(
    label="process_source_2",
    outputs={process_bus_2: solph.Flow()},
)
energysystem.add(process_source_2)


el_sink_1 = solph.components.Sink(
    label="el_sink_1",
    inputs={process_bus_1: solph.Flow(nominal_value=20, fix=1)},
)
energysystem.add(el_sink_1)


el_sink_2 = solph.components.Sink(
    label="el_sink_2",
    inputs={process_bus_2: solph.Flow(nominal_value=15, fix=1)},
)
energysystem.add(el_sink_2)


model = solph.Model(energysystem)



model.solve(
    solver="cplex",
    solve_kwargs={"tee": True},
)
results = solph.processing.results(model)

substation_bus_1_results = solph.views.node(results, process_bus_1.label)["sequences"].dropna()
substation_bus_2_results = solph.views.node(results, process_bus_2.label)["sequences"].dropna()

res_df = pd.DataFrame()
res_df[process_bus_1.label] = substation_bus_1_results[((process_bus_1.label, el_sink_1.label), "flow")]
res_df[process_bus_2.label] = substation_bus_2_results[((process_bus_2.label, el_sink_2.label), "flow")]


ax_el = res_df.plot(kind="area", ylim=(0, 200))

plt.show(block=True)
