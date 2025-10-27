import datetime as dt

import pandas as pd
import pyomo.environ as po
from matplotlib import pyplot as plt
from oemof import solph

date_time_index = pd.date_range(dt.datetime(2021, 1, 1), periods=100, freq="H")
energysystem = solph.EnergySystem(timeindex=date_time_index, infer_last_interval=True)


el_bus = solph.Bus(label="el_bus")
energysystem.add(el_bus)


power_val = 1000



expense_source = solph.components.Source(
    label="expense_source",
    outputs={el_bus: solph.Flow(
        nominal_value = power_val,
        min = 1,
        variable_costs=1000,
        nonconvex=solph.NonConvex(),
    )},
)
energysystem.add(expense_source)


cheap_source = solph.components.Source(
    label="cheap_source",
    outputs={el_bus: solph.Flow(
        nominal_value = power_val,
        variable_costs=1,
        min = 1,
        nonconvex=solph.NonConvex(), 
        )},
)
energysystem.add(cheap_source)

sink_demand=solph.components.Sink(
        label="sink_demand",
        inputs={el_bus: solph.Flow(nominal_value = power_val, fix = 1)},
)
energysystem.add(sink_demand)


model = solph.Model(energysystem)



periods_data = {((10,50), (60,90)) : [(expense_source, el_bus), 10]}
   
        

def mandatory_single_run_simple(m, periods_data):
    """
    Максимально простая версия: только 2 ограничения на период
    1. Общее время работы = required_uptime
    2. Максимум один старт
    """
    
    timesteps_list = list(m.TIMESTEPS)
    
    for i, (start_finish_pairs_lst, data) in enumerate(periods_data.items()):
        if len(data) == 3:
            source_obj, bus_obj, required_uptime = data
            flow_tuple = (source_obj, bus_obj)
        elif len(data) == 2:
            flow_tuple, required_uptime = data
        else:
            raise ValueError(f"Invalid data format: {data}")
        
        for j, (start_t, end_t) in enumerate(start_finish_pairs_lst):
            period_length = end_t - start_t
            
            if period_length < required_uptime:
                print(f"Warning: Period {i}_{j} too short")
                continue
            
            period_timesteps = timesteps_list[start_t:end_t]
            
            # Ограничение 1: Общее время работы
            setattr(m, f'total_uptime_{i}_{j}',
                   po.Constraint(
                       expr=sum(m.NonConvexFlowBlock.status[flow_tuple, t] 
                               for t in period_timesteps) == required_uptime
                   ))
            
            # Ограничение 2: Максимум один старт (переход 0->1)
            def max_one_startup_rule(model):
                startups = []
                
                for idx in range(len(period_timesteps)):
                    t = period_timesteps[idx]
                    
                    if idx == 0:
                        if start_t > 0:
                            prev_t = timesteps_list[start_t - 1]
                            startup = (model.NonConvexFlowBlock.status[flow_tuple, t] - 
                                     model.NonConvexFlowBlock.status[flow_tuple, prev_t])
                        else:
                            startup = model.NonConvexFlowBlock.status[flow_tuple, t]
                    else:
                        prev_t = period_timesteps[idx - 1]
                        startup = (model.NonConvexFlowBlock.status[flow_tuple, t] - 
                                 model.NonConvexFlowBlock.status[flow_tuple, prev_t])
                    
                    startups.append(startup)
                
                # Сумма всех стартов <= 1 (но с учетом первого ограничения будет = 1)
                return sum(startups) <= 1
            
            setattr(m, f'max_one_startup_{i}_{j}',
                   po.Constraint(rule=max_one_startup_rule))

# Использование
mandatory_single_run_simple(model, periods_data)
# timesteps_list = list(model.TIMESTEPS)
# period_timesteps = timesteps_list[10:50]
# setattr(model, f'total_uptime_{1}_{2}',
#         po.Constraint(
#             expr=sum(model.NonConvexFlowBlock.status[expense_source, el_bus, t] 
#                     for t in period_timesteps) == 10
#         ))

model.solve(
    solver="cplex",
    solve_kwargs={
        'tee': True,  
    })



blocks = [expense_source, cheap_source]

results = solph.processing.results(model)

el_results = solph.views.node(results, el_bus.label)["sequences"].dropna()


el_df = pd.DataFrame()

for block in blocks:
    el_df[block.label] = el_results[((block.label, el_bus.label), "flow")]


ax_el = el_df.plot(kind="area", ylim=(0, 2000))

plt.show(block=True)
