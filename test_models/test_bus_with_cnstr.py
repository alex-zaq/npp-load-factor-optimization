


import datetime as dt

import matplotlib.pyplot as plt
import pandas as pd
from oemof import solph

hours_count = 24 * 7

date_time_index = pd.date_range(dt.datetime(2025, 1, 1), periods=hours_count, freq="H")
es = solph.EnergySystem(timeindex=date_time_index, infer_last_interval=True)


el_bus = solph.Bus(label="el_bus")
es.add(el_bus)


el_source = solph.components.Source(
    label="el_source",
    outputs={el_bus: solph.Flow(
        nominal_value=100,
        )})
es.add(el_source)



el_sink = solph.components.Sink(label="el_sink", inputs={el_bus: solph.Flow(nominal_value=100, fix = 1)})
es.add(el_sink)


model = solph.Model(es)

model.solve(solver="cplex", mipgap=0.01)

results = solph.processing.results(model)


res = solph.Results(model)

res_df = res.to_df()
print(res_df)



# el_results = solph.views.node(results, el_bus.label)["sequences"].dropna()


# el_df = pd.DataFrame()
# el_df[el_source.label] = el_results[((el_source.label, el_bus.label), "flow")]




# ax_el = el_df.plot(kind="area", ylim=(0, 1000))



# plt.show(block=True)


# https://oemof-solph.readthedocs.io/en/latest/examples/result_object.html