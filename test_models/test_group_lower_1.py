import pandas as pd
import pyomo.environ as po
from matplotlib import pyplot as plt
from oemof import solph

# 1. Создание энергетической системы
date_time_index = pd.date_range(start='1/1/2020', periods=5, freq='H')
es = solph.EnergySystem(timeindex=date_time_index)

# 2. Создание шины (Bus)
el_bus = solph.Bus(label='electricity')

# 3. Создание компонентов
# Источник A: Этот блок должен быть ВКЛЮЧЕН, если Источник B ВКЛЮЧЕН.
# Мы используем NonConvex flow, чтобы получить бинарную переменную состояния.
# Установите min/max для потока, чтобы определить его рабочий диапазон, когда он включен.
expense_block = solph.components.Source(
    label='expense_block',
    outputs={el_bus: solph.Flow(
        nominal_value=50,  # Номинальная мощность
        min=1,            # Минимальная часть номинальной мощности, если включен (50%)
        max=1,            # Максимальная часть номинальной мощности, если включен (100%)
        nonconvex=solph.NonConvex(),     # Это создает бинарную переменную состояния (status)
        variable_costs=999,  # Пример переменных затрат
    )}
)

# Источник B: Этот блок зависит от Источника A.
cheap_block = solph.components.Source(
    label='cheap_block',
    outputs={el_bus: solph.Flow(
        nominal_value=1000,   # Номинальная мощность
        min=0,            # Минимальная часть номинальной мощности, если включен (60%)
        max=1.0,            # Максимальная часть номинальной мощности, если включен (100%)
        nonconvex=solph.NonConvex(),     # Это создает бинарную переменную состояния (status)
        variable_costs=-99,   # Пример переменных затрат
    )}
)

# Потребность для потребления электроэнергии
demand_el = solph.components.Sink(
    label='demand_el',
    inputs={el_bus: solph.Flow(
        nominal_value=150,
        fix=1 #  спрос по времени
    )}
)

# Добавляем компоненты в энергетическую систему
es.add(el_bus, expense_block, cheap_block, demand_el)

model = solph.Model(es)

def sequential_loading_rule(model, t):
    return model.NonConvexFlowBlock.status[cheap_block,el_bus, t] <= model.NonConvexFlowBlock.status[expense_block, el_bus, t]

model.sequential_loading_constraint = po.Constraint(
    model.TIMESTEPS,
    rule=sequential_loading_rule
)

model.solve(solver="cplex")
results = solph.processing.results(model)


el_results = solph.views.node(results, el_bus.label)["sequences"].dropna()


el_blocks = [expense_block, cheap_block]
el_df = pd.DataFrame()
for el_block in el_blocks:
    el_df[el_block.label] = el_results[((el_block.label, el_bus.label), "flow")]



el_df = el_df.drop(el_df.index[-1])

ax_el = el_df.plot(kind="area", ylim=(0, 1000))


plt.show(block=True)