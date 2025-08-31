import pandas as pd
from matplotlib import pyplot as plt
from oemof import solph


# from .equate_flows import equate_flows_by_keyword
# from .integral_limit import emission_limit
# from .integral_limit import emission_limit_per_period
# from .integral_limit import generic_integral_limit
# from .integral_limit import generic_periodical_integral_limit
# from .investment_limit import additional_investment_flow_limit
# from .investment_limit import investment_limit
# from .investment_limit import investment_limit_per_period
# from .storage_level import storage_level_constraint


date_time_index = pd.date_range("1/1/2022", periods=3, freq="H")

energysystem = solph.EnergySystem(timeindex=date_time_index)

b_el = solph.Bus(label="electricity_bus")
energysystem.add(b_el)
b_heat = solph.Bus(label="heat_bus")
energysystem.add(b_heat)


source_a = solph.components.Source(
    label="source_a",
    outputs={b_el: solph.Flow(nominal_value=10, custom_attributes={"main_flow_1": True})},
)
energysystem.add(source_a)

source_b = solph.components.Source(
    label="source_b",
    outputs={b_heat: solph.Flow(custom_attributes={"main_flow_2": True})},
)
energysystem.add(source_b)

sink_a = solph.components.Sink(
    label="sink_a", inputs={b_el: solph.Flow(nominal_value=10, fix=1)}
)
energysystem.add(sink_a)

sink_b = solph.components.Sink(
    label="sink_b", inputs={b_heat: solph.Flow()}
)
energysystem.add(sink_b)



model = solph.Model(energysystem)


solph.constraints.equate_flows_by_keyword(model, "main_flow_1", "main_flow_2" , factor1=1, name="equate_flows")
# solph.constraints.equate_flows_by_keyword(model, "main_flow_1", "main_flow_2" , factor1=2, name="equate_flows")

model.solve(solver="cplex")
  
results = model.results()

el_results = solph.views.node(results, b_el.label)["sequences"].dropna()
heat_results = solph.views.node(results, b_heat.label)["sequences"].dropna()

el_df = pd.DataFrame()
el_df["source_a"] = el_results[((source_a.label, b_el.label), "flow")]

heat_df = pd.DataFrame()
heat_df["source_b"] = heat_results[((source_b.label, b_heat.label), "flow")]

ax_el = el_df.plot(kind="area")

ax_heat = heat_df.plot(kind="area")

plt.show(block=True)