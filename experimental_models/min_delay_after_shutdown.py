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



expense_source_1 = solph.components.Source(
    label="expense_source_1000",
    outputs={el_bus: solph.Flow(
        nominal_value = power_val,
        min=1,
        variable_costs=1000,
        nonconvex=solph.NonConvex(),
    )},
)
energysystem.add(expense_source_1)


expense_source_2 = solph.components.Source(
    label="expense_source_2000",
    outputs={el_bus: solph.Flow(
        nominal_value = power_val,
        min=1,
        variable_costs=2000,
        nonconvex=solph.NonConvex(
            minimum_uptime=10,
            ),
    )},
)
energysystem.add(expense_source_2)



cheap_source = solph.components.Converter(
    label="cheap_converter",
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


items_startup = [(expense_source_2, el_bus, 10)] 
 
         
def rule_forced_startup(m, block, bus, tt):
    return m.NonConvexFlowBlock.status[block, bus, tt] == 1


model.constraint_forced_startup = po.Constraint(
    [item for item in items_startup],
    rule = lambda m, block, bus, tt: m.NonConvexFlowBlock.status[block, bus, tt] == 1
)


# item = (cheap_converter, el_bus, cheap_min_uptime)

items = [{
           "triggered_pair": (expense_source_2, el_bus),
           "delayed_pair": (cheap_source, el_bus),
            "delay": 40,
        }] 
         
def add_delayed_startup_efficient(m, items):
    """
    Эффективная версия: создает отдельное ограничение для каждой пары (t_shutdown, t_startup)
    """
    timesteps_list = list(m.TIMESTEPS)
    
    for idx, item in enumerate(items):
        triggered_block_a, bus_a = item["triggered_pair"]
        delayed_block_b, bus_b = item["delayed_pair"]
        delay = item["delay"]
        
        print(f"\n{'='*70}")
        print(f"Constraint #{idx}: {delayed_block_b.label} blocked for {delay} periods")
        print(f"                  after {triggered_block_a.label} shutdown")
        print(f"{'='*70}\n")
        
        # Создаем набор пар (t_shutdown, t_potential_startup)
        constraint_pairs = []
        
        for t_shutdown_idx in range(1, len(timesteps_list)):
            # Окно блокировки после shutdown в момент t_shutdown_idx
            for t_startup_idx in range(t_shutdown_idx, min(len(timesteps_list), t_shutdown_idx + delay + 1)):
                if t_startup_idx > 0:  # Нужен предыдущий момент для определения startup
                    constraint_pairs.append((t_shutdown_idx, t_startup_idx))
        
        def delayed_startup_rule(model, t_shutdown_idx, t_startup_idx):
            t_shutdown = timesteps_list[t_shutdown_idx]
            t_shutdown_prev = timesteps_list[t_shutdown_idx - 1]
            
            t_startup = timesteps_list[t_startup_idx]
            t_startup_prev = timesteps_list[t_startup_idx - 1]
            
            # Определяем shutdown triggered source в момент t_shutdown
            status_a_curr = model.NonConvexFlowBlock.status[triggered_block_a, bus_a, t_shutdown]
            status_a_prev = model.NonConvexFlowBlock.status[triggered_block_a, bus_a, t_shutdown_prev]
            shutdown_indicator = status_a_prev - status_a_curr
            
            # Определяем startup delayed source в момент t_startup
            status_b_curr = model.NonConvexFlowBlock.status[delayed_block_b, bus_b, t_startup]
            status_b_prev = model.NonConvexFlowBlock.status[delayed_block_b, bus_b, t_startup_prev]
            startup_indicator = status_b_curr - status_b_prev
            
            # Ограничение: если был shutdown, то startup запрещен
            # startup_indicator + shutdown_indicator <= 1
            # Это означает: не могут быть оба равны 1 одновременно
            
            return startup_indicator + shutdown_indicator <= 1
        
        constraint_name = f'delayed_startup_{idx}_{delayed_block_b.label}_after_{triggered_block_a.label}'
        setattr(m, constraint_name, po.Constraint(constraint_pairs, rule=delayed_startup_rule))


add_delayed_startup_efficient(model, items)

model.solve(
    solver="cplex",
    solve_kwargs={
        'tee': True,  
    }
    )



blocks = [expense_source_1, expense_source_2, cheap_source]

results = solph.processing.results(model)

el_results = solph.views.node(results, el_bus.label)["sequences"].dropna()


el_df = pd.DataFrame()
el_statuses_df = pd.DataFrame()

for block in blocks:
    el_df[block.label] = el_results[((block.label, el_bus.label), "flow")]
    
    el_statuses_df[block.label] = el_results[((block.label, el_bus.label), "status")]

ax_el = el_df.plot(kind="area", ylim=(0, 2000))

ax_el_statuses = el_statuses_df.plot(kind="line", ylim=(0, 2))

plt.show(block=True)
