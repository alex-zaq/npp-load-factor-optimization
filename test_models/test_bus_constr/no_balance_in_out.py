import datetime as dt

import pandas as pd
from matplotlib import pyplot as plt
from oemof import solph

date_time_index = pd.date_range(dt.datetime(2021, 1, 1), periods=10, freq="H")
energysystem = solph.EnergySystem(timeindex=date_time_index, infer_last_interval=True)
# ######################### create energysystem components ################

el_bus = solph.Bus(label="электроэнергия")
energysystem.add(el_bus)


el_grid = solph.Bus(
    label = "электроэнергия (grid)",
    balanced = False,
    inputs={el_bus: solph.Flow(variable_costs=-15)},   # доход от продажи
    outputs={el_bus: solph.Flow(variable_costs=15, nominal_value=200)},)  # расход от покупки
energysystem.add(el_grid)


# Что это значит: Эта шина является двунаправленным безграничным шлюзом для вашей системы. Она может как поставлять энергию в вашу систему, так и принимать энергию из вашей системы, при этом ее собственный баланс не имеет значения.
# Когда полезно:
# Моделирование основной внешней электросети (как в вашем исходном примере grid). Это самый распространенный и реалистичный сценарий. Ваша система может покупать электроэнергию из сети, когда ей не хватает, и продавать излишки в сеть, когда она производит больше, чем потребляет. Сеть выступает как бесконечный буфер.
# Моделирование крупного рынка энергии/ресурсов: Когда ваша система является лишь малым участником большого рынка и ее действия не влияют на общие цены или доступность.


el_source = solph.components.Source(
    label="электроэнергия (source) cheap",
    outputs={
        el_bus: solph.Flow(
            nominal_value=2000,
            variable_costs=10,
            min=1,
            nonconvex=solph.NonConvex(),
        )
    },
)
energysystem.add(el_source)


el_sink = solph.components.Sink(
    label="электроэнергия (sink)",
    inputs={el_bus: solph.Flow(nominal_value=1500, fix=1)},
)
energysystem.add(el_sink)


model = solph.Model(energysystem)


blocks = [el_source]

model.solve(
    solver="cplex",
    solve_kwargs={"tee": True},
)
results = solph.processing.results(model)

el_results = solph.views.node(results, el_bus.label)["sequences"].dropna()

el_df = pd.DataFrame()
for block in blocks:
    el_df[block.label] = el_results[((block.label, el_bus.label), "flow")]


ax_el = el_df.plot(kind="area", ylim=(0, 2000))

plt.show(block=True)
