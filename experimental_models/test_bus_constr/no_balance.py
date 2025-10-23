import datetime as dt

import pandas as pd
from matplotlib import pyplot as plt
from oemof import solph

date_time_index = pd.date_range(dt.datetime(2021, 1, 1), periods=10, freq="H")
energysystem = solph.EnergySystem(timeindex=date_time_index, infer_last_interval=True)
# ######################### create energysystem components ################


# бесполезный вариант использования
el_bus = solph.Bus(label="электроэнергия", balanced = False)
energysystem.add(el_bus)


# Что это значит: Это шина, которая существует в модели, но не связана ни с какими другими компонентами.
# Когда полезно: Практически никогда. Такая шина будет изолирована и не будет влиять на оптимизацию или потоки энергии в вашей системе. Это как создать переменную в коде, но никогда ее не использовать.


el_source = solph.components.Source(
    label="электроэнергия (source) cheap",
    outputs={
        el_bus: solph.Flow(
            nominal_value=2000,
            variable_costs=10,
            min = 1,
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

model.solve(solver="cplex",  solve_kwargs={"tee": True},)
results = solph.processing.results(model)

el_results = solph.views.node(results, el_bus.label)["sequences"].dropna()

el_df = pd.DataFrame()
for block in blocks:
    el_df[block.label] = el_results[((block.label, el_bus.label), "flow")]


ax_el = el_df.plot(kind="area", ylim=(0, 2000))

plt.show(block=True)