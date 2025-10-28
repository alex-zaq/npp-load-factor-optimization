
import oemof.solph as solph
import pandas as pd
from matplotlib import pyplot as plt
from pyomo.environ import Binary, Constraint, NonNegativeReals, Var


def add_startup_fuel_consumption(om, items, sink_by_fuel_dict):
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

        startup_sink = sink_by_fuel_dict[fuel_bus]
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
            return m.flow[fuel_bus, startup_sink, t] == total_startup_consumption
        
        constraint_name_flow = f'total_startup_fuel_flow_{fuel_bus.label}'
        setattr(om, constraint_name_flow, Constraint(om.TIMESTEPS, rule=total_startup_fuel_flow_rule))
    
    return om



timeindex = pd.date_range('2024-01-01', periods=10, freq='h')
es = solph.EnergySystem(timeindex=timeindex)

# Шины
el_bus = solph.Bus(label='electricity')
es.add(el_bus)
fuel_bus = solph.Bus(label='fuel')
es.add(fuel_bus)
gas_bus = solph.Bus(label='gas')
es.add(gas_bus)

fuel_types = [fuel_bus, gas_bus]

sink_by_fuel_dict = {}
for fuel_bus_type in fuel_types:
    sink_fuel = solph.components.Sink(
        label=f'sink_fuel_{fuel_bus_type.label}',
        inputs={fuel_bus_type: solph.Flow()}
    )
    es.add(sink_fuel)
    sink_by_fuel_dict[fuel_bus_type] = sink_fuel



fuel_source = solph.components.Source(
    label='fuel_source',
    outputs={fuel_bus: solph.Flow(variable_costs=10)}
)
es.add(fuel_source)

gas_source = solph.components.Source(
    label='gas_source',
    outputs={gas_bus: solph.Flow(variable_costs=15)}
)
es.add(gas_source)

blocks = []


el_fuel_converter = solph.components.Converter(
        label="el_fuel_converter",
        inputs={fuel_bus: solph.Flow()},
        outputs={el_bus: solph.Flow(
            nominal_value=100,
            min=0.2,
            nonconvex=solph.NonConvex()
        )},
        conversion_factors={el_bus: 0.4}
    )
es.add(el_fuel_converter)


el_gas_block = solph.components.Converter(
        label="el_gas_block",
        inputs={gas_bus: solph.Flow()},
        outputs={el_bus: solph.Flow(
            nominal_value=100,
            min=0.2,
            nonconvex=solph.NonConvex()
        )},
        conversion_factors={el_bus: 0.5}
    )
es.add(el_gas_block)

el_demand_sink = solph.components.Sink(
    label='el_demand_sink',
    inputs={el_bus: solph.Flow(
        fix=1,
        nominal_value=200
    )}
)
es.add(el_demand_sink)

model = solph.Model(es)

items = []

items.append({
        "block_pair": (el_fuel_converter, el_bus),
        "fuel_bus": fuel_bus,
        "startup_fuel_consumption": 400,  
    })

items.append({
        "block_pair": (el_gas_block, el_bus),
        "fuel_bus": gas_bus,
        "startup_fuel_consumption": 300,
    })


model = add_startup_fuel_consumption(model, items, sink_by_fuel_dict)

# Решаем
model.solve(solver='cplex', solve_kwargs={'tee': True})

# Результаты
results = solph.processing.results(model)
blocks = [el_fuel_converter, el_gas_block]

el_results = solph.views.node(results, el_bus.label)["sequences"].dropna()
fuel_results = solph.views.node(results, fuel_bus.label)["sequences"].dropna()
gas_results = solph.views.node(results, gas_bus.label)["sequences"].dropna()

el_df = pd.DataFrame()
for block in blocks:
    el_df[block.label] = el_results[((block.label, el_bus.label), "flow")]

fuel_df = pd.DataFrame()
fuel_df[el_fuel_converter.label] = fuel_results[((fuel_bus.label, el_fuel_converter.label), "flow")]
fuel_df["extra_fuel"] = fuel_results[((fuel_bus.label, sink_by_fuel_dict[fuel_bus].label), "flow")]


gas_df = pd.DataFrame()
gas_df[el_gas_block.label] = gas_results[((gas_bus.label, el_gas_block.label), "flow")]
gas_df["extra_gas"] = gas_results[((gas_bus.label, sink_by_fuel_dict[gas_bus].label), "flow")]

ax_el = el_df.plot(kind="area", ylim=(0, 2000))
ax_fuel = fuel_df.plot(kind="area", ylim=(0, 2000))
ax_gas = gas_df.plot(kind="area", ylim=(0, 2000))

plt.show(block=True)
