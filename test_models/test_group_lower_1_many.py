import pandas as pd
import pyomo.environ as po
from matplotlib import pyplot as plt
from oemof import solph


date_time_index = pd.date_range(start='1/1/2020', periods=5, freq='H')
es = solph.EnergySystem(timeindex=date_time_index)


el_bus = solph.Bus(label='electricity')
es.add(el_bus)

cheap_cost = 99
expense_cost = -99
cheap_power = 100

expense_block_1 = solph.components.Source(
    label='expense_block_1',
    outputs={el_bus: solph.Flow(
        nominal_value=cheap_power,  
        min=1,            
        max=1,            
        nonconvex=solph.NonConvex(),     
        variable_costs=expense_cost,  
    )}
)
es.add(expense_block_1)

expense_block_2 = solph.components.Source(
    label='expense_block_2',
    outputs={el_bus: solph.Flow(
        nominal_value=cheap_power,  
        min=1,            
        max=1,            
        nonconvex=solph.NonConvex(),     
        variable_costs=expense_cost,  
    )}
)
es.add(expense_block_2)


expense_block_3 = solph.components.Source(
    label='expense_block_3',
    outputs={el_bus: solph.Flow(
        nominal_value=cheap_power,  
        min=1,            
        max=1,            
        nonconvex=solph.NonConvex(),     
        variable_costs=expense_cost,  
    )}
)
es.add(expense_block_3)

expense_block_4 = solph.components.Source(
    label='expense_block_4',
    outputs={el_bus: solph.Flow(
        nominal_value=cheap_power,  
        min=1,            
        max=1,            
        nonconvex=solph.NonConvex(),     
        variable_costs=expense_cost,  
    )}
)
es.add(expense_block_4)


cheap_block_1 = solph.components.Source(
    label='cheap_block_1',
    outputs={el_bus: solph.Flow(
        nominal_value=1000,   
        min=0,            
        max=1.0,           
        nonconvex=solph.NonConvex(),    
        variable_costs=cheap_cost,   
    )}
)
es.add(cheap_block_1)

cheap_block_2 = solph.components.Source(
    label='cheap_block_2',
    outputs={el_bus: solph.Flow(
        nominal_value=1000,   
        min=0,            
        max=1.0,           
        nonconvex=solph.NonConvex(),    
        variable_costs=cheap_cost,   
    )}
)
es.add(cheap_block_2)




demand_el = solph.components.Sink(
    label='demand_el',
    inputs={el_bus: solph.Flow(
        nominal_value=2000,
        fix=1 #  спрос по времени
    )}
)
es.add(demand_el)


model = solph.Model(es)


block_associations = [
    (cheap_block_1, [expense_block_1, expense_block_2]),
    (cheap_block_2, [expense_block_3, expense_block_4]),
]




def dependency_rule_generalized(model, t, cheap_block, expense_group, bus):
    """
    Ограничение: cheap_block может работать только если работает хотя бы один из блоков в expense_group.
    """
    sum_of_group_statuses = sum(
        model.NonConvexFlowBlock.status[block, bus, t]
        for block in expense_group
    )
    return model.NonConvexFlowBlock.status[cheap_block, bus, t] <= sum_of_group_statuses

def mutual_exclusion_rule_generalized(model, t, expense_group, el_bus):
    """
    Ограничение: Только один блок из expense_group может работать в каждый момент времени.
    """
    sum_of_group_statuses = sum(
        model.NonConvexFlowBlock.status[block, el_bus, t]
        for block in expense_group
    )
    return sum_of_group_statuses <= 1


for i, (cheap_block, expense_group) in enumerate(block_associations):
    # Ограничение зависимости (cheap_block -> expense_group)
    setattr(
        model,
        f'dependency_constraint_{i}',
        po.Constraint(
            model.TIMESTEPS,
            rule=lambda model, t, cheap_block=cheap_block, expense_group=expense_group, bus=el_bus:
                   dependency_rule_generalized(model, t, cheap_block, expense_group, bus)
        )
    )

    # Ограничение взаимоисключения внутри expense_group
    setattr(
        model,
        f'mutual_exclusion_constraint_{i}',
        po.Constraint(
            model.TIMESTEPS,
            rule=lambda model, t, expense_group=expense_group, bus=el_bus:
                   mutual_exclusion_rule_generalized(model, t, expense_group, bus)
        )
    )







model.solve(solver="cplex")
results = solph.processing.results(model)


el_results = solph.views.node(results, el_bus.label)["sequences"].dropna()


el_blocks = [
    expense_block_1,
    expense_block_2,
    expense_block_3,
    expense_block_4,
    cheap_block_1,
    cheap_block_2
    ]
el_df = pd.DataFrame()
for el_block in el_blocks:
    el_df[el_block.label] = el_results[((el_block.label, el_bus.label), "flow")]



el_df = el_df.drop(el_df.index[-1])

ax_el = el_df.plot(kind="area", ylim=(0, 2500))


plt.show(block=True)