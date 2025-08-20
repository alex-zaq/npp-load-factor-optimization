import datetime as dt

import pandas as pd
from matplotlib import pyplot as plt
from oemof import solph

date_time_index = pd.date_range(dt.datetime(2021, 1, 1), periods=10, freq="H")
energysystem = solph.EnergySystem(timeindex=date_time_index, infer_last_interval=True)
# ######################### create energysystem components ################



main_grid_bus = solph.Bus(label="main_grid_bus", balanced=True)
energysystem.add(main_grid_bus)
solar_pv_bus = solph.Bus(label="solar_pv_bus", balanced=True)
energysystem.add(solar_pv_bus)

production_line_1_bus = solph.Bus(label="production_line_1_bus", balanced=True)
energysystem.add(production_line_1_bus)
production_line_2_bus = solph.Bus(label="production_line_2_bus", balanced=True)
energysystem.add(production_line_2_bus)



# Пример: Электрическая шина на промышленном объекте
# Получает энергию от главной сети и собственной солнечной установки,
# а затем распределяет ее по производственным линиям.

# Предполагаем, что main_grid_bus и solar_pv_bus уже определены
# и имеют outputs, идущие в industrial_el_bus.
# А production_line_1_sink и production_line_2_sink будут потреблять
# энергию от industrial_el_bus.

# Главная электрическая шина на промышленном объекте
industrial_el_bus = solph.Bus(
    label="industrial_el_bus",
    balanced=True,  # Должна быть сбалансирована
    inputs={
        # Определяем, откуда industrial_el_bus ПОЛУЧАЕТ энергию
        # (Эти потоки должны быть определены как outputs на main_grid_bus и solar_pv_bus)
        main_grid_bus: solph.Flow(nominal_capacity=1000),
        solar_pv_bus: solph.Flow(nominal_capacity=200),
    },
    outputs={
        # Определяем, куда industrial_el_bus ОТДАЕТ энергию
        # (Эти потоки будут inputs для production_line_1_sink и production_line_2_sink)
        production_line_1_bus: solph.Flow(nominal_capacity=500),
        production_line_2_bus: solph.Flow(nominal_capacity=300),
    },
)
energysystem.add(industrial_el_bus)

# Оптимизатор будет искать решение, при котором сумма потоков
# от main_grid_bus и solar_pv_bus будет равна сумме потоков
# в production_line_1_sink и production_line_2_sink в каждый момент времени.


# Что это значит: Эта шина явно определяет как входящие, так и исходящие потоки. Поскольку balanced=True, оптимизатор будет строго следить за тем, чтобы сумма входящих потоков равнялась сумме исходящих потоков.
# Когда полезно:
# Это самый распространенный и логичный способ использования Bus с balanced=True для моделирования внутренних узлов вашей системы.
# Моделирование точек соединения или перераспределения энергии. Например, электрическая шина на заводе, которая получает энергию от собственной генерации и внешней сети, а затем распределяет ее по различным цехам.
# Моделирование промежуточных энергетических носителей. Например, шина для водорода, которая получает водород от электролизера и отдает его в топливные элементы или хранилище.


solar_source = solph.components.Source(
    label="solar_source",
    outputs={solar_pv_bus: solph.Flow(nominal_value=200)},
)
energysystem.add(solar_source)



main_grid_source = solph.components.Source(
    label="main_grid_source",
    outputs={main_grid_bus: solph.Flow(nominal_value=1000)},
)
energysystem.add(main_grid_source)


# !!! взаимозаменямые варианты два сверху вместо одного снизу


# el_source = solph.components.Source(
#     label="электроэнергия (source) cheap",
#     outputs={industrial_el_bus: solph.Flow()},
# )
# energysystem.add(el_source)



production_line_1_sink = solph.components.Sink(
    label="production_line_1_sink",
    inputs={production_line_1_bus: solph.Flow(nominal_value=500, fix=1)},
)
energysystem.add(production_line_1_sink)

production_line_2_sink = solph.components.Sink(
    label="production_line_2_sink",
    inputs={production_line_2_bus: solph.Flow(nominal_value=300, fix=1)},
)
energysystem.add(production_line_2_sink)


model = solph.Model(energysystem)



model.solve(
    solver="cplex",
    solve_kwargs={"tee": True},
)
results = solph.processing.results(model)

production_line_1_bus_results = solph.views.node(results, production_line_1_bus.label)["sequences"].dropna()
production_line_2_bus_results = solph.views.node(results, production_line_2_bus.label)["sequences"].dropna()

res_df = pd.DataFrame()
res_df[industrial_el_bus.label + "1"] = production_line_1_bus_results[((industrial_el_bus.label, production_line_1_bus.label), "flow")]
res_df[industrial_el_bus.label + "2"] = production_line_2_bus_results[((industrial_el_bus.label, production_line_2_bus.label), "flow")]


ax_el = res_df.plot(kind="area", ylim=(0, 2000))

plt.show(block=True)


# https://oemof-solph.readthedocs.io/en/latest/introductory_tutorials/home_pv_battery_system.html