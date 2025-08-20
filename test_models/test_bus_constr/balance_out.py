import datetime as dt

import pandas as pd
from matplotlib import pyplot as plt
from oemof import solph

date_time_index = pd.date_range(dt.datetime(2021, 1, 1), periods=10, freq="H")
energysystem = solph.EnergySystem(timeindex=date_time_index, infer_last_interval=True)
# ######################### create energysystem components ################

substation_bus_1 = solph.Bus(label="substation_bus_1", balanced=True)
energysystem.add(substation_bus_1)
substation_bus_2 = solph.Bus(label="substation_bus_2", balanced=True)
energysystem.add(substation_bus_2)

main_bus = solph.Bus(
    label="main_bus",
    balanced=True,  # Должна быть сбалансирована
    outputs={
        # Определяем, куда main_bus ОТПРАВЛЯЕТ энергию
        substation_bus_1: solph.Flow(nominal_capacity=50),
        substation_bus_2: solph.Flow(nominal_capacity=30),
    },
)
energysystem.add(main_bus)

# Что это значит: Эта шина явно определяет, куда она отправляет энергию. Однако, поскольку balanced=True, она обязательно должна откуда-то получать эту энергию.
# Когда полезно:
# Такая конфигурация сама по себе неполна и приведет к неразрешимости модели, если вы не предоставите этой шине inputs от других компонентов.
# Это полезно, когда вы моделируете распределительную шину, которая должна обеспечивать энергией определенные потребители или другие шины, но источник этой энергии находится "выше" или "перед" ней в иерархии.
# Пример: Главная электрическая шина на подстанции, которая распределяет энергию по нескольким фидерам. Вы определяете outputs на эти фидеры. Но чтобы шина была сбалансирована, она должна получать энергию от трансформатора или генератора, который подключен к ней (т.е., output трансформатора/генератора идет input на эту шину).


# !!! ВАЖНО: Для того чтобы main_bus был сбалансирован,
# !!! ему НУЖЕН ИСТОЧНИК энергии (input)!
# Например, электростанция, которая подает энергию на main_bus:
# power_plant = solph.Source(
#     label="power_plant",
#     outputs={main_bus: solph.Flow(nominal_capacity=100)} # Энергия идет В main_bus
# )
# Без такого источника, модель будет неразрешимой, так как main_bus
# пытается отправить энергию, но не получает ее.



el_source = solph.components.Source(
    label="электроэнергия (source) cheap",
    outputs={
        main_bus: solph.Flow()
    },
)
energysystem.add(el_source)


el_sink_1 = solph.components.Sink(
    label="электроэнергия (sink)_1",
    inputs={substation_bus_1: solph.Flow(nominal_value=50, fix=1)},
)
energysystem.add(el_sink_1)

el_sink_2 = solph.components.Sink(
    label="электроэнергия (sink)_2",
    inputs={substation_bus_2: solph.Flow(nominal_value=30, fix=1)},
)
energysystem.add(el_sink_2)


model = solph.Model(energysystem)


blocks = [el_source]

model.solve(
    solver="cplex",
    solve_kwargs={"tee": True},
)
results = solph.processing.results(model)

substation_bus_1_results = solph.views.node(results, substation_bus_1.label)["sequences"].dropna()
substation_bus_2_results = solph.views.node(results, substation_bus_2.label)["sequences"].dropna()

res_df = pd.DataFrame()
res_df[substation_bus_1.label] = substation_bus_1_results[((main_bus.label, substation_bus_1.label), "flow")]
res_df[substation_bus_2.label] = substation_bus_2_results[((main_bus.label, substation_bus_2.label), "flow")]




ax_el = res_df.plot(kind="area", ylim=(0, 200))

plt.show(block=True)
