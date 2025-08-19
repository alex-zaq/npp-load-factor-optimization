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


el_grid = solph.Bus(label = "электроэнергия (grid)", balanced = False, inputs={el_bus: solph.Flow(variable_costs=15)})
energysystem.add(el_grid)


# Что это значит: Эта шина является безграничным поглотителем энергии для вашей системы. Она может принимать любое количество энергии от других шин, не требуя никакого "выхода" для себя.
# Когда полезно:
# Моделирование внешней электросети, которой вы ТОЛЬКО продаете электроэнергию (не покупаете). Это позволяет вашей системе сбрасывать излишки энергии в сеть без ограничений по спросу со стороны сети.
# "Сброс" излишков энергии или побочных продуктов: Например, если у вас есть избыточное тепло, которое не используется, и вы хотите просто "выбросить" его в окружающую среду, не моделируя его дальнейшую судьбу.
# Моделирование "идеального" потребителя: Если вы хотите, чтобы система всегда могла избавиться от излишков производства.

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
