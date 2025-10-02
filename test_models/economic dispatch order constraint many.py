import pandas as pd
import pyomo.environ as po
from matplotlib import pyplot as plt
from oemof import solph

# 1. Создание энергетической системы
date_time_index = pd.date_range(start='1/1/2020', periods=5, freq='H')
es = solph.EnergySystem(timeindex=date_time_index)

# 2. Создание шины (Bus)
el_bus = solph.Bus(label='electricity')
es.add(el_bus)

# 3. Создание компонентов
# Источник A: Этот блок должен быть ВКЛЮЧЕН, если Источник B ВКЛЮЧЕН.
# Мы используем NonConvex flow, чтобы получить бинарную переменную состояния.
# Установите min/max для потока, чтобы определить его рабочий диапазон, когда он включен.
expense_block_1 = solph.components.Source(
    label='expense_block_1',
    outputs={el_bus: solph.Flow(
        nominal_value=50,  # Номинальная мощность
        min=1,            # Минимальная часть номинальной мощности, если включен (50%)
        max=1,            # Максимальная часть номинальной мощности, если включен (100%)
        nonconvex=solph.NonConvex(),     # Это создает бинарную переменную состояния (status)
        variable_costs=999,  # Пример переменных затрат
    )}
)
es.add(expense_block_1)

# Источник B: Этот блок зависит от Источника A.
cheap_block_1 = solph.components.Source(
    label='cheap_block_1',
    outputs={el_bus: solph.Flow(
        nominal_value=1000,   # Номинальная мощность
        min=0.1,            # Минимальная часть номинальной мощности, если включен (60%)
        max=1.0,            # Максимальная часть номинальной мощности, если включен (100%)
        nonconvex=solph.NonConvex(),     # Это создает бинарную переменную состояния (status)
        variable_costs=-99,   # Пример переменных затрат
        custom_attributes={"cheap": True}
    )}
)
es.add(cheap_block_1)

expense_block_2 = solph.components.Source(
    label='expense_block_2',
    outputs={el_bus: solph.Flow(
        nominal_value=50,  # Номинальная мощность
        min=1,            # Минимальная часть номинальной мощности, если включен (50%)
        max=1,            # Максимальная часть номинальной мощности, если включен (100%)
        nonconvex=solph.NonConvex(),     # Это создает бинарную переменную состояния (status)
        variable_costs=999,  # Пример переменных затрат
    )}
)
es.add(expense_block_2)

# Источник B: Этот блок зависит от Источника A.
cheap_block_2 = solph.components.Source(
    label='cheap_block_2',
    outputs={el_bus: solph.Flow(
        nominal_value=1000,   # Номинальная мощность
        min=0.1,            # Минимальная часть номинальной мощности, если включен (60%)
        max=1.0,            # Максимальная часть номинальной мощности, если включен (100%)
        nonconvex=solph.NonConvex(),     # Это создает бинарную переменную состояния (status)
        variable_costs=-99,   # Пример переменных затрат
        custom_attributes={"cheap": True}
    )}
)
es.add(cheap_block_2)


# Потребность для потребления электроэнергии
demand_el = solph.components.Sink(
    label='demand_el',
    inputs={el_bus: solph.Flow(
        nominal_value=1500,
        fix=1 #  спрос по времени
    )}
)
es.add(demand_el)



model = solph.Model(es)


solph.constraints.limit_active_flow_count_by_keyword(model, "cheap", lower_limit=2, upper_limit=2)


item_1 = (cheap_block_1, el_bus), (expense_block_1, el_bus)
item_2 = (cheap_block_2, el_bus), (expense_block_2, el_bus)



items = [item_1, item_2]



def sequential_loading_rule(model, t, item_1, item_2, item_3, item_4):
    return model.NonConvexFlowBlock.status[item_1, item_2, t] <= model.NonConvexFlowBlock.status[item_3, item_4, t]

model.sequential_loading_constraint = po.Constraint(
    model.TIMESTEPS,
    [item for item in items],
    rule=sequential_loading_rule
)

model.solve(solver="cplex")
results = solph.processing.results(model)


el_results = solph.views.node(results, el_bus.label)["sequences"].dropna()


el_blocks = [
    cheap_block_1,
    cheap_block_2,
    expense_block_1,
    expense_block_2,
    ]
el_df = pd.DataFrame()
for el_block in el_blocks:
    el_df[el_block.label] = el_results[((el_block.label, el_bus.label), "flow")]



el_df = el_df.drop(el_df.index[-1])

ax_el = el_df.plot(kind="area", ylim=(0, 2000))


plt.show(block=True)