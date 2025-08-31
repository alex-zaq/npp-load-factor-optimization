
import pandas as pd
from matplotlib import pyplot as plt
from oemof import solph

# from .shared_limit import shared_limit




date_time_index = pd.date_range("1/1/2012", periods=10, freq="h")
energysystem = solph.EnergySystem(
    timeindex=date_time_index,
    infer_last_interval=False,
)


b1 = solph.Bus(label="Party1Bus")
energysystem.add(b1)
# b2 = solph.buses.Bus(label="Party2Bus")



source = solph.components.Source(
    label="source",
    outputs={b1: solph.Flow(
        nominal_capacity=20,
        variable_costs= 5 * [0] + 5 * [100]
        )},
)
energysystem.add(source)



# source = solph.components.Source(
#     label="source",
#     outputs={b1: solph.Flow(
#         nominal_capacity=20

#         )},
# )
# energysystem.add(source)






sink = solph.components.Sink(
    label="sink",
    inputs={b1: solph.Flow(nominal_value=10, fix=1)},
)
energysystem.add(sink)


storage1 = solph.components.GenericStorage(
    label="storage1",
    # nominal_capacity=500,
    nominal_storage_capacity=500,
    inputs={b1: solph.Flow(variable_costs=0, nominal_value=10)},
    outputs={b1: solph.Flow()},
)
storage2 = solph.components.GenericStorage(
    label="storage2",
    nominal_storage_capacity=500,
    # nominal_capacity=500,
    inputs={b1: solph.Flow(variable_costs=0, nominal_value=10)},
    outputs={b1: solph.Flow()},
)
energysystem.add(storage1, storage2)
model = solph.Model(energysystem)
solph.constraints.shared_limit(
    model,
    model.GenericStorageBlock.storage_content,
    "limit_storage",
    [storage1, storage2],
    [1, 1],
    upper_limit=25,
)

model.solve(solver="cplex")


results = solph.processing.results(model)


storage_1_results = solph.views.node(results, storage1.label)["sequences"].dropna()
storage_2_results = solph.views.node(results, storage2.label)["sequences"].dropna()

storage_1_content_df = pd.DataFrame()
storage_2_content_df = pd.DataFrame()

storage_content_df = pd.DataFrame()
storage_content_df["storage1 content"] = storage_1_results[(storage1.label, "None"), "storage_content"]
storage_content_df["storage2 content"] = storage_2_results[(storage2.label, "None"), "storage_content"]


ax_storage_content = storage_content_df.plot(kind="area")

plt.show(block=True)