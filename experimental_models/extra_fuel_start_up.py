def add_startup_fuel_consumption(om, items, energysystem):
    from pyomo.environ import Constraint, Var, Binary, NonNegativeReals
    import oemof.solph as solph
    
    # Группируем элементы по топливной шине для оптимизации
    items_by_fuel_bus = {}
    for item in items:
        fuel_bus = item["fuel_bus"]
        if fuel_bus not in items_by_fuel_bus:
            items_by_fuel_bus[fuel_bus] = []
        items_by_fuel_bus[fuel_bus].append(item)
    
    # Для каждой топливной шины создаем ОДИН общий виртуальный Sink
    for fuel_bus, bus_items in items_by_fuel_bus.items():
        # Создаем один Sink на всю топливную шину
        startup_sink = solph.components.Sink(
            label=f'startup_fuel_sink_{fuel_bus.label}',
            inputs={fuel_bus: solph.Flow(
                variable_costs=0  # Стоимость уже учтена в топливе
            )}
        )
        
        energysystem.add(startup_sink)
        
        # Создаем переменные switch_on для всех источников на этой шине
        switch_vars = []
        
        for idx, item in enumerate(bus_items):
            source, bus = item["block_pair"]
            startup_fuel_consumption = item["startup_fuel_consumption"]
            
            # Создаем переменную для фиксации момента включения
            switch_var_name = f'switch_on_{source.label}_{bus.label}'
            setattr(om, switch_var_name, Var(om.TIMESTEPS, within=Binary))
            switch_on = getattr(om, switch_var_name)
            
            switch_vars.append({
                'var': switch_on,
                'consumption': startup_fuel_consumption,
                'source': source,
                'bus': bus
            })
            
            # Определяем включение как переход 0->1
            def switch_detection_rule(m, t, src=source, b=bus):
                timesteps_list = list(m.TIMESTEPS)
                t_idx = timesteps_list.index(t)
                
                sw = getattr(m, f'switch_on_{src.label}_{b.label}')
                
                if t_idx == 0:
                    return sw[t] >= m.NonConvexFlowBlock.status[src, b, t]
                else:
                    t_prev = timesteps_list[t_idx - 1]
                    return sw[t] >= m.NonConvexFlowBlock.status[src, b, t] - \
                                    m.NonConvexFlowBlock.status[src, b, t_prev]
            
            constraint_name = f'switch_detection_{source.label}_{bus.label}'
            setattr(om, constraint_name, Constraint(om.TIMESTEPS, rule=switch_detection_rule))
        
        # Один constraint связывает поток виртуального стока с суммой всех запусков
        def total_startup_fuel_flow_rule(m, t):
            total_startup_consumption = sum(
                sw_info['var'][t] * sw_info['consumption']
                for sw_info in switch_vars
            )
            return m.SimpleFlowBlock[fuel_bus, startup_sink, t] == total_startup_consumption
        
        constraint_name_flow = f'total_startup_fuel_flow_{fuel_bus.label}'
        setattr(om, constraint_name_flow, Constraint(om.TIMESTEPS, rule=total_startup_fuel_flow_rule))
    
    return om


# Пример использования с МНОЖЕСТВОМ источников
import pandas as pd
import oemof.solph as solph

timeindex = pd.date_range('2024-01-01', periods=100, freq='h')
energysystem = solph.EnergySystem(timeindex=timeindex)

# Шины
el_bus = solph.Bus(label='electricity')
fuel_bus = solph.Bus(label='fuel')
gas_bus = solph.Bus(label='gas')

# Источники топлива
fuel_source = solph.components.Source(
    label='fuel_source',
    outputs={fuel_bus: solph.Flow(variable_costs=10)}
)

gas_source = solph.components.Source(
    label='gas_source',
    outputs={gas_bus: solph.Flow(variable_costs=15)}
)

# Множество энергоблоков на разных топливах
converters = []

# 5 блоков на жидком топливе
for i in range(5):
    conv = solph.components.Converter(
        label=f'fuel_block_{i}',
        inputs={fuel_bus: solph.Flow()},
        outputs={el_bus: solph.Flow(
            nominal_value=100,
            nonconvex=solph.NonConvex()
        )},
        conversion_factors={el_bus: 0.4}
    )
    converters.append(conv)
    energysystem.add(conv)

# 3 блока на газе
for i in range(3):
    conv = solph.components.Converter(
        label=f'gas_block_{i}',
        inputs={gas_bus: solph.Flow()},
        outputs={el_bus: solph.Flow(
            nominal_value=150,
            nonconvex=solph.NonConvex()
        )},
        conversion_factors={el_bus: 0.5}
    )
    converters.append(conv)
    energysystem.add(conv)

# Потребитель
demand = solph.components.Sink(
    label='demand',
    inputs={el_bus: solph.Flow(
        fix=[500] * len(timeindex),
        nominal_value=1
    )}
)

energysystem.add(el_bus, fuel_bus, gas_bus, fuel_source, gas_source, demand)

# Создаем модель
model = solph.Model(energysystem)

# Формируем список элементов с перерасходом топлива
items = []

# Для блоков на жидком топливе
for i in range(5):
    items.append({
        "block_pair": (converters[i], el_bus),
        "fuel_bus": fuel_bus,
        "startup_fuel_consumption": 50 + i * 10,  # Разный расход для каждого
    })

# Для блоков на газе
for i in range(3):
    items.append({
        "block_pair": (converters[5 + i], el_bus),
        "fuel_bus": gas_bus,
        "startup_fuel_consumption": 80 + i * 15,
    })

# Применяем функцию
model = add_startup_fuel_consumption(model, items, energysystem)

# Решаем
model.solve(solver='cbc', solve_kwargs={'tee': True})

# Результаты
results = solph.processing.results(model)

# Анализ запусков и расхода топлива
print("\n=== АНАЛИЗ ЗАПУСКОВ ===")
for i in range(5):
    conv = converters[i]
    switch_var = model.component(f'switch_on_{conv.label}_{el_bus.label}')
    if switch_var:
        startups = sum(switch_var[t].value for t in model.TIMESTEPS if switch_var[t].value > 0.5)
        print(f"{conv.label}: {int(startups)} запусков")

print("\n=== РАСХОД ТОПЛИВА ===")
fuel_flow = results[(fuel_source, fuel_bus)]['sequences']['flow']
print(f"Общий расход жидкого топлива: {fuel_flow.sum():.2f}")

gas_flow = results[(gas_source, gas_bus)]['sequences']['flow']
print(f"Общий расход газа: {gas_flow.sum():.2f}")

# Расход на запуск
startup_fuel_sink = [comp for comp in energysystem.nodes 
                     if comp.label == f'startup_fuel_sink_{fuel_bus.label}'][0]
startup_fuel_flow = results[(fuel_bus, startup_fuel_sink)]['sequences']['flow']
print(f"Расход топлива на запуски (жидкое): {startup_fuel_flow.sum():.2f}")

startup_gas_sink = [comp for comp in energysystem.nodes 
                    if comp.label == f'startup_fuel_sink_{gas_bus.label}'][0]
startup_gas_flow = results[(gas_bus, startup_gas_sink)]['sequences']['flow']
print(f"Расход топлива на запуски (газ): {startup_gas_flow.sum():.2f}")
