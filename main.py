from src.npp_load_factor_calculator import Block_grouper, Oemof_model, Result_plotter
from src.npp_load_factor_calculator.utilites import all_months

bel_npp_block_1_events = {
    "accident_1": {
        "start_datetime": "2025-01-01 00:00:00",
        "risk_increase": 0.1,
        "duration_hours": 1,
    },
    "melting_core": {
        "start_datetime": "2025-04-01 00:00:00",
        "risk_increase": 0.3,
        "duration_hours": 6,
    },
}

events = {
    "event_1": {
        "start_datetime": "2025-02-01 00:00:00",
        "risk_increase": 0.1,
        "duration_hours": 1,
    },
    "event_3": {
        "start_datetime": "2025-03-15 06:00:00",
        "risk_increase": 0.2,
        "duration_hours": 1,
    },
    "event_4": {
        "start_datetime": "2025-04-22 18:00:00",
        "risk_increase": 0.4,
        "duration_hours": 1,
    },
    "event_2": {
        "start_datetime": "2025-05-01 12:00:00",
        "risk_increase": 0.3,
        "duration_hours": 1,
    },
    "event_5": {
        "start_datetime": "2025-06-11 09:00:00",
        "risk_increase": 0.2,
        "duration_hours": 1,
    },
}


bel_npp_block_2_events = {}
new_npp_block_1_events = {}



repair_options = {
    "npp_light_repair": {"cost": 0.1, "duration": 7, "risk_reducing": 0.1, "start_day": [1, 15], "avail_months": all_months, "npp_stop": False},
    "npp_avg_repair": {"cost": 0.2, "duration": 14, "risk_reducing": 0.2, "start_day": [1, 15], "avail_months": all_months, "npp_stop": True},
    "npp_capital_repair": {"cost": 0.3, "duration": 21, "risk_reducing": 0.3, "start_day": [1, 15], "avail_months": all_months, "npp_stop": True},
}


scen_1 = {
    "№": 1,
    "name": "experimental",
    "years": [2025],
    "bel_npp": {
        "block_1": {
            "status": True,
            "nominal_power": 1170,
            "var_cost": -56.5,
            "risk_per_hour": 0.01,
            "upper_bound_risk": 0.5,
            "events": bel_npp_block_1_events,
            "repair_options": repair_options,
        },
        "block_2": {
            "status": False,
            "nominal_power": 1170,
            "var_cost": -56.5,
            "risk_per_hour": 0.01,
            "upper_bound_risk": 0.5,
            "events": bel_npp_block_2_events,
            "repair_options": repair_options,
        },
    },
    "new_npp": {
        "block_1": {
            "status": False,
            "nominal_power": 1170,
            "var_cost": -56.5,
            "risk_per_hour": 0.01,
            "upper_bound_risk": 0.5,
            "events": new_npp_block_1_events,
            "repair_options": repair_options,
        },
    },
}



scenario = scen_1


model = Oemof_model(
    scenario = scenario,
    solver_settings = {
        "solver": "cplex",
        "solver_verbose": True,
        "mip_gap": 0.01
    } 
)

model.calculate()

custom_es = model.get_custom_es()
results = model.get_results()


bel_npp_block_1 = custom_es.block_db.get_bel_npp_block_1()
bel_npp_block_2 = custom_es.block_db.get_bel_npp_block_2()
new_npp_block_1 = custom_es.block_db.get_new_npp_block_1()

bel_npp_block_1_risk_storage = bel_npp_block_1.risk_storage
bel_npp_block_2_risk_storage = bel_npp_block_2.risk_storage
new_npp_block_1_risk_storage = new_npp_block_1.risk_storage



block_grouper = Block_grouper(results, custom_es)


block_grouper.set_block_groups(
    electricity_gen={
        "БелАЭС (блок 1)": {"order": [bel_npp_block_1], "color": "#2ca02c"},
        "БелАЭС (блок 2)": {"order": [bel_npp_block_2], "color": "#ff7f0e"},
        "Новая АЭС (блок 1)": {"order": [new_npp_block_1], "color": "#1f77b4"},
    },
    risk_gen={
        "БелАЭС (блок 1) - риск": {"order": [bel_npp_block_1_risk_storage], "color": "#1ae0ff"},
        "БелАЭС (блок 2) - риск": {"order": [bel_npp_block_2_risk_storage], "color": "#e8ff1a"},
        "Новая АЭС (блок 1) - риск": {"order": [new_npp_block_1_risk_storage], "color": "#3d26a3"},
    },
)


result_plotter = Result_plotter(block_grouper)
result_plotter.plot_electricity_generation_profile()



print("done")



# result_plotter.plot_risk_events_profile()
# result_plotter.plot_cumulative_risk_profile()
# result_plotter.plot_repair_cost_profile()

# изменить начальный коенчный на [начальный, конечный]
# добавить структуру методов классов
# мин. фукц. класса oemof_model
# мин. фукц. класса custom_model_builder (добавить два блока аэс, риски)
# реализация фиксированного времени работы на ном. мощности
# стоимость включения для учета стоимости ремонта
# большой интервал времени 5 лет
# ввод модели накопителя для учета накопления рисков
# ограничения риска сверху
# снижение риска от ремонта 
# увеличение рисков по определенным во времени событием и штатной работы аэс
# добавить 3-4 сценария
# блок-схема
# 4 года, много событий, кокурирующие ремонты, 1 блок, 2 блока, 3 блока
# взять реальные значения из двух источников
# вывод в эксель
# sink ремонта c updown 17 дней и var_cost или start_up_cost и gradient для старта в опр. часы
# разные типы ремонтов не пересекаются в одной АЭС
# ремонты в разных аэс не совпадают во времени 
# через определенные интервалы времени (например длина ремонта) добавить sink и source который будет в данные интервалы
# заряжать storage, которая будет позволять работать sink для риска с учетом uptime равной длине ремента (можно произвольеные инетрвалы с выключения недопущения одновременной # # работы заряж. source и ремонтируюещего sink)
# проверить на малом примере: н и н+1 и два одновременных слова в custom_attributes и доп шаг для работы storage