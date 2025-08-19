import datetime as dt

import pandas as pd
from matplotlib import pyplot as plt
from oemof import solph

date_time_index = pd.date_range(dt.datetime(2021, 1, 1), periods=10, freq="H")
# date_time_index = get_dt_range(self.year, self.selected_months)
energysystem = solph.EnergySystem(timeindex=date_time_index, infer_last_interval=True)
# ######################### create energysystem components ################

el_bus = solph.Bus(label="электроэнергия")
energysystem.add(el_bus)


el_grid = solph.Bus(label = "электроэнергия (grid)", balanced = False,  outputs={el_bus: solph.Flow()})
energysystem.add(el_grid)

# Что это значит: Эта шина является безграничным источником энергии для вашей системы. Она может поставлять любое количество энергии на другие шины, не требуя никакого "входа" для себя.
# Когда полезно:
# Моделирование внешней электросети, от которой вы ТОЛЬКО покупаете электроэнергию (не продаете). Это позволяет вашей системе брать столько энергии, сколько ей нужно, без ограничений по доступности или необходимости балансировать саму "сеть".
# "Виртуальный" источник неограниченного топлива/ресурса: Например, если вы моделируете завод, который потребляет природный газ, и вы считаете, что поставки газа неограничены.
# Моделирование идеализированного источника возобновляемой энергии: Если вы хотите посмотреть, как система будет работать с "бесконечным" ветром или солнцем, не моделируя реальные ограничения ресурса.


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


blocks = [el_source, el_grid]

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
