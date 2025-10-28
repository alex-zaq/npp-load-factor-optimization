def add_startup_fuel_consumption(om, items, energysystem):
    from pyomo.environ import Constraint, Var, Binary, NonNegativeReals
    import oemof.solph as solph
    
    
    
    # быстрая и медленная версия
    
    
    
    for idx, item in enumerate(items):
        source, bus = item["block_pair"]
        fuel_bus = item["fuel_bus"]
        startup_fuel_consumption = item["startup_fuel_consumption"]
        
        # Создаем виртуальный Sink для дополнительного расхода топлива
        startup_sink = solph.components.Sink(
            label=f'startup_fuel_sink_{source.label}_{idx}',
            inputs={fuel_bus: solph.Flow(
                variable_costs=0  # Стоимость уже учтена в топливе
            )}
        )
        
        energysystem.add(startup_sink)
        
        # Создаем переменную для фиксации момента включения
        switch_var_name = f'switch_on_{source.label}_{bus.label}_{idx}'
        setattr(om, switch_var_name, Var(om.TIMESTEPS, within=Binary))
        switch_on = getattr(om, switch_var_name)
        
        # Определяем включение как переход 0->1
        def switch_detection_rule(m, t):
            timesteps_list = list(m.TIMESTEPS)
            t_idx = timesteps_list.index(t)
            
            if t_idx == 0:
                return switch_on[t] >= m.NonConvexFlowBlock.status[source, bus, t]
            else:
                t_prev = timesteps_list[t_idx - 1]
                return switch_on[t] >= m.NonConvexFlowBlock.status[source, bus, t] - m.NonConvexFlowBlock.status[source, bus, t_prev]
        
        constraint_name_1 = f'switch_detection_{source.label}_{bus.label}_{idx}'
        setattr(om, constraint_name_1, Constraint(om.TIMESTEPS, rule=switch_detection_rule))
        
        # Связываем поток виртуального стока с моментом запуска
        def startup_fuel_flow_rule(m, t):
            return m.flow[fuel_bus, startup_sink, t] == switch_on[t] * startup_fuel_consumption
        
        constraint_name_flow = f'startup_fuel_flow_{source.label}_{idx}'
        setattr(om, constraint_name_flow, Constraint(om.TIMESTEPS, rule=startup_fuel_flow_rule))
    
    return om


# Использование
import pandas as pd
import oemof.solph as solph

timeindex = pd.date_range('2024-01-01', periods=100, freq='h')
energysystem = solph.EnergySystem(timeindex=timeindex)

el_bus = solph.Bus(label='electricity')
fuel_bus = solph.Bus(label='fuel')

fuel_source = solph.components.Source(
    label='fuel_source',
    outputs={fuel_bus: solph.Flow(variable_costs=10)}
)

el_block = solph.components.Converter(
    label='el_block',
    inputs={fuel_bus: solph.Flow()},
    outputs={el_bus: solph.Flow(
        nominal_value=100,
        nonconvex=solph.NonConvex()
    )},
    conversion_factors={el_bus: 0.4}
)

demand = solph.components.Sink(
    label='demand',
    inputs={el_bus: solph.Flow(
        fix=[50] * len(timeindex),
        nominal_value=1
    )}
)

energysystem.add(el_bus, fuel_bus, fuel_source, el_block, demand)

model = solph.Model(energysystem)

items = [
    {
        "block_pair": (el_block, el_bus),
        "fuel_bus": fuel_bus,
        "startup_fuel_consumption": 50,
    }
]

model = add_startup_fuel_consumption(model, items, energysystem)

model.solve(solver='cbc')
