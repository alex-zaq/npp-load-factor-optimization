import pandas as pd
import pyomo.environ as po
from matplotlib import pyplot as plt
from oemof import solph


date_time_index = pd.date_range(start='1/1/2020', periods=5, freq='H')
es = solph.EnergySystem(timeindex=date_time_index)


el_bus = solph.Bus(label='electricity')
es.add(el_bus)


expense_block_1 = solph.components.Source(
    label='expense_block_1',
    outputs={el_bus: solph.Flow(
        nominal_value=200,  
        min=1,            
        max=1,            
        nonconvex=solph.NonConvex(),     
        variable_costs=-99,  
    )}
)
es.add(expense_block_1)

expense_block_2 = solph.components.Source(
    label='expense_block_2',
    outputs={el_bus: solph.Flow(
        nominal_value=200,  
        min=1,            
        max=1,            
        nonconvex=solph.NonConvex(),     
        variable_costs=-99,  
    )}
)
es.add(expense_block_2)


cheap_block = solph.components.Source(
    label='cheap_block',
    outputs={el_bus: solph.Flow(
        nominal_value=1000,   
        min=0,            
        max=1.0,           
        nonconvex=solph.NonConvex(),    
        variable_costs=99,   
    )}
)
es.add(cheap_block)


demand_el = solph.components.Sink(
    label='demand_el',
    inputs={el_bus: solph.Flow(
        nominal_value=1000,
        fix=1 #  спрос по времени
    )}
)
es.add(demand_el)


model = solph.Model(es)



def sequential_loading_rule_1(model, t):
    return model.NonConvexFlowBlock.status[cheap_block,el_bus, t] <= model.NonConvexFlowBlock.status[expense_block_1, el_bus, t] + model.NonConvexFlowBlock.status[expense_block_2, el_bus, t]




def sequential_loading_rule_2(model, t):
    return model.NonConvexFlowBlock.status[expense_block_1, el_bus, t] + model.NonConvexFlowBlock.status[expense_block_2, el_bus, t] <=1


model.sequential_loading_constraint = po.Constraint(
    model.TIMESTEPS,
    rule=sequential_loading_rule_1
)

model.sequential_loading_constraint_2 = po.Constraint(
    model.TIMESTEPS,
    rule=sequential_loading_rule_2
)







model.solve(solver="cplex")
results = solph.processing.results(model)


el_results = solph.views.node(results, el_bus.label)["sequences"].dropna()


el_blocks = [expense_block_1, expense_block_2, cheap_block]
el_df = pd.DataFrame()
for el_block in el_blocks:
    el_df[el_block.label] = el_results[((el_block.label, el_bus.label), "flow")]



el_df = el_df.drop(el_df.index[-1])

ax_el = el_df.plot(kind="area", ylim=(0, 1500))


plt.show(block=True)