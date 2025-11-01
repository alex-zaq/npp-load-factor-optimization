import datetime as dt

import pandas as pd
from matplotlib import pyplot as plt
from oemof import solph

date_time_index = pd.date_range(dt.datetime(2025, 1, 1), periods=20, freq="H")
energysystem = solph.EnergySystem(timeindex=date_time_index, infer_last_interval=True)


el_bus = solph.Bus(label="el_bus")
energysystem.add(el_bus)

power_val = 1500

expense_source = solph.components.Source(
    label="expense_source",
    outputs={el_bus: solph.Flow(
        nominal_value = power_val,
        variable_costs=1000)},
)
energysystem.add(expense_source)


cheap_converter = solph.components.Converter(
    label="cheap_converter",
    outputs={el_bus: solph.Flow(
        nominal_value = power_val,
        variable_costs=1,
        min = 1,
        nonconvex=solph.NonConvex(), 
        )},
)
energysystem.add(cheap_converter)

 


sink_demand=solph.components.Sink(
        label="sink_demand",
        inputs={el_bus: solph.Flow(nominal_value = power_val, fix = 1)},
)
energysystem.add(sink_demand)


model = solph.Model(energysystem)

model.solve(
    solver="cplex",
    solve_kwargs={
        'tee': True,  
        'logfile': 'cplex_solve.log',  
        'keepfiles': False, 
    }
    )

# Читаем весь лог
with open('cplex_solve.log', 'r', encoding='utf-8') as f:
    log_content = f.read()

# Разбиваем на строки для Excel
log_lines = log_content.split('\n')

# Простой DataFrame
log_df = pd.DataFrame({'CPLEX_Log': log_lines})

# Сохраняем всё в один файл
with pd.ExcelWriter('results.xlsx') as writer:
    # el_df.to_excel(writer, sheet_name='Results')
    log_df.to_excel(writer, sheet_name='Log', index=False)

print("✓ Сохранено в results.xlsx")

blocks = [expense_source, cheap_converter]

results = solph.processing.results(model)

el_results = solph.views.node(results, el_bus.label)["sequences"].dropna()




el_df = pd.DataFrame()

for block in blocks:
    el_df[block.label] = el_results[((block.label, el_bus.label), "flow")]


ax_el = el_df.plot(kind="area", ylim=(0, 5000))

plt.show(block=True)
