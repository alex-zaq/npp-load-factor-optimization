import datetime as dt
from datetime import datetime as dt

import pandas as pd
from matplotlib import pyplot as plt
from oemof import solph



# доступность электрокотлов на уровне тэц или на уровне энергссистемы

chp_options = {
    
    "block_1": {"duration_days": 15},    
    "block_2": {"duration_days": 10},
    # "whole_period": True, # внутри периода может быть один характерный день
    
    "typical_day_1": {
        "period": (dt(2025, 1, 1), dt(2025, 2, 1)),
        # fixed_day: True, # фиксированный характерный день
        # "min_time": 7 *24, # допускается смена характерного дня внутри периода но работа не меньше min_time
        "repair_avail": {
            "block_1": {
                "start_date": (dt(2025, 1, 10), dt(2025, 1, 15)), # разрешенные даты начала ремонта в периоде
                "any_day": True, # старт ремонта может быть любой день в периоде
                },
        },
        "var_cost": 10,
        # "fixed_cost": 0
        # chp_eff: (0.8, 0.83),
        # cond_eff: (0.2, 0.3),
        # cond_min_load: 50,
        # cond_max_load: 200,
        # "chp_min_load": 400,
        # "chp_max_load": 500,
        "el_boiler_options": {
          "power": 150,
          "el_boiler_load_chp_eff_losses": {
              30: 0.2,
              80: 0.3,
              150 : 0.4}, 
          # потери кпд тэц в зависимости загрузки электрокотла
        }
    },    
    
    "typical_day_2": {
        "period": (dt(2025, 1, 1), dt(2025, 2, 1)),
        "repair_avail": {
            "block_1": {
                "start_date": (dt(2025, 1, 10), dt(2025, 1, 15)),
                "any_day": True,
                },
            "block_2": {
                "start_date": (dt(2025, 5, 10), dt(2025, 10, 15)),
                "any_day": True,
                },
        },
        "var_cost": 9,
        "min_load": 350,
        "max_load": 400,
    },
    
    "typical_day_3": {
        "period": (dt(2025, 2, 1), dt(2025, 3, 1)),
        "repair_avail": {
            "block_2": {
                "start_date": (dt(2025, 2, 10), dt(2025, 1, 15))},
        },
        "var_cost": 8,
        "min_load": 300,
        "max_load": 390,
    },
    
}


start_year, end_year = 2025, 2025
t_delta = dt(end_year, 2, 1) - dt(start_year, 1, 1)
# t_delta = dt(end_year, 3, 1) - dt(start_year, 1, 1)
first_time_step = dt(start_year, 1, 1)
periods_count = t_delta.days * 24
date_time_index = pd.date_range(first_time_step, periods=periods_count, freq="h")
es = solph.EnergySystem(timeindex=date_time_index, infer_last_interval=True)


el_bus = solph.Bus(label="el_bus")
es.add(el_bus)

chp_inner_bus = solph.Bus(label="chp_inner_bus")
es.add(chp_inner_bus)




chp_source_var_1 = solph.components.Source(
    label="chp_source_var_1",
    outputs={chp_inner_bus: solph.Flow(
            nominal_capacity=chp_options["typical_day_1"]["max_load"],
            min = chp_options["typical_day_1"]["min_load"]/chp_options["typical_day_1"]["max_load"],
            nonconvex=solph.NonConvex(),
            variable_costs=chp_options["typical_day_1"]["var_cost"],
            custom_attributes={"chp_source_var": True},
        )},
)
es.add(chp_source_var_1)

chp_source_var_2 = solph.components.Source(
    label="chp_source_var_2",
    outputs={chp_inner_bus: solph.Flow(
            nominal_capacity=chp_options["typical_day_2"]["max_load"],
            min = chp_options["typical_day_2"]["min_load"]/chp_options["typical_day_2"]["max_load"],
            nonconvex=solph.NonConvex(),
            variable_costs=chp_options["typical_day_2"]["var_cost"],
            custom_attributes={"chp_source_var": True},
        )},
)
es.add(chp_source_var_2)


chp_source_var_3 = solph.components.Source(
    label="chp_source_var_3",
    outputs={chp_inner_bus: solph.Flow(
            nominal_capacity=chp_options["typical_day_3"]["max_load"],
            min = chp_options["typical_day_3"]["min_load"]/chp_options["typical_day_3"]["max_load"],
            nonconvex=solph.NonConvex(),
            variable_costs=chp_options["typical_day_3"]["var_cost"],
            custom_attributes={"chp_source_var": True},
        )},
)
es.add(chp_source_var_3)


chp_output = solph.components.Converter(
    label="chp_output",
    inputs={chp_inner_bus: solph.Flow()},
    outputs={el_bus: solph.Flow()},
)
es.add(chp_output)


expense_source = solph.components.Source(
    label="expense_source",
    outputs={el_bus: solph.Flow(variable_costs=999)},
)
es.add(expense_source)



block_1_outage_bus = solph.Bus(label="block_1_outage_bus")
block_1_outage = solph.components.Source(
    label="block_1_outage",
    outputs={el_bus: solph.Flow(
        nominal_value=1,
        min=0,
        nonconvex=solph.NonConvex(
            minimum_uptime=0,
            ),
        full_load_time_max=0,
        full_load_time_min=0,
        positive_gradient_limit=0,
        negative_gradient_limit=0,
        )},
)
es.add(block_1_outage)

block_2_outage_bus = solph.Bus(label="block_2_outage_bus")
block_2_outage = solph.components.Source(
    label="block_2_outage",
    outputs={el_bus: solph.Flow(
        nominal_value=1,
        min=0,
        nonconvex=solph.NonConvex(
            minimum_uptime=0,
            ),
        full_load_time_max=0,
        full_load_time_min=0,
        positive_gradient_limit=0,
        negative_gradient_limit=0,
        )},
)
es.add(block_2_outage)



el_sink = solph.components.Sink(
    label="el_sink",
    inputs={el_bus: solph.Flow(nominal_value=1000, fix=1)},
)
es.add(el_sink)


model = solph.Model(energysystem=es)

# set_equate_flow(model, [])
# set_single_active_flow(model, [])
# set_equate_statuses(model, [])

# set_block_order()

results = model.solve(solver="cplex")

results = model.results()

blocks = []

outage_blocks = [block_1_outage, block_2_outage]


el_df = get_df(results, el_bus, blocks)

outage_df = get_outage_df(results, outage_blocks)





ax_outage_df = outage_df.plot(kind="line", ylim=(0, 10))

ax_outage_df = ax_outage_df.twinx()

ax_el_df = el_df.plot(kind="area", ylim=(0, 1200), ax = ax_outage_df)


plt.show(block=True)