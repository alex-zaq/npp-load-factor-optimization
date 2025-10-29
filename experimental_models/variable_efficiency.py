import oemof.solph as solph
from pyomo.environ import Piecewise, Constraint

def add_piecewise_efficiency(model, generator, bus, efficiency_curve):
    """
    Добавляет кусочно-линейную зависимость КПД (efficiency) от мощности для генератора.

    Параметры:
    ----------
    model : oemof.solph.Model
        Оптимизационная модель.
    generator : oemof.solph.Source
        Генератор, для которого задаётся зависимость КПД.
    bus : oemof.solph.Bus
        Шина, к которой подключён генератор.
    efficiency_curve : dict
        Кусочно-линейная зависимость мощности (MW) от КПД (0-1).
        Пример: {0: 0.3, 50: 0.4, 100: 0.5}.
    """
    # Извлекаем временные шаги
    timesteps = model.TIMESTEPS

    # Преобразуем данные КПД в точки для кусочно-линейной аппроксимации
    power_levels = list(efficiency_curve.keys())
    efficiencies = list(efficiency_curve.values())

    # Добавляем кусочно-линейное ограничение для каждого временного шага
    def piecewise_efficiency_rule(m, t):
        # Связываем поток мощности с КПД через линейную интерполяцию
        return Piecewise(
            points=power_levels,
            values=efficiencies,
            input_expr=m.flow[generator, bus, t],
            output_var=m.flow[generator, bus, t],
            pw_constr_type="EQ"
        )

    # Применяем кусочно-линейную аппроксимацию к каждому временному шагу
    model.piecewise_efficiency = Constraint(timesteps, rule=piecewise_efficiency_rule)

    return model


import pandas as pd
import oemof.solph as solph
from oemof.solph import EnergySystem, Bus, Source, Sink, Model, Flow

# === 1. Инициализация энергосистемы ===
datetime_index = pd.date_range("2025-01-01", "2025-01-02", freq="H")
energysystem = EnergySystem(timeindex=datetime_index)

# === 2. Создание компонентов ===
# Создаём шину электричества
electricity_bus = Bus(label="electricity_bus")
energysystem.add(electricity_bus)

# Создаём генератор с переменным КПД
generator = Source(
    label="variable_efficiency_generator",
    outputs={electricity_bus: Flow(variable_costs=20)}
)
energysystem.add(generator)

# Создаём потребитель с фиксированным спросом
demand = Sink(
    label="electricity_demand",
    inputs={electricity_bus: Flow(fix=[30] * len(datetime_index), nominal_value=1)}
)
energysystem.add(demand)

# === 3. Создание модели ===
model = Model(energysystem)

# === 4. Задаём кусочно-линейную зависимость КПД ===
efficiency_curve = {
    0: 0.3,   # КПД 30% при мощности 0 MW
    50: 0.4,  # КПД 40% при мощности 50 MW
    100: 0.5  # КПД 50% при мощности 100 MW
}
model = add_piecewise_efficiency(model, generator, electricity_bus, efficiency_curve)

# === 5. Решение модели ===
model.solve(solver="cbc", solve_kwargs={"tee": True})

# === 6. Анализ результатов ===
results = solph.processing.results(model)
flows = solph.processing.convert_keys_to_strings(results["main"])
print("Flow from generator to bus:")
print(flows["('variable_efficiency_generator', 'electricity_bus')"])
