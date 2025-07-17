from src.npp_load_factor_calculator import Block_grouper, Oemof_model, Result_plotter

base_settings = {}

bel_npp_block_1_events = {}
bel_npp_block_2_events = {}
new_npp_block_1_events = {}


repair_cost = {
    "npp_light_repair": {"cost": 0.1, "duration_days": 7},
    "nnp_heavy_repair": {"cost": 0.2, "duration_days": 14},
    "npp_capital_repair": {"cost": 0.3, "duration_days": 21},
}



scen_1 = {
    "№": 1,
    "name": "experimental",
    "bel_npp": {
        "block_1": {
            "status": True,
            "pow": 1170,
            "allow_outage_months": ["june", "dec"],
            "risk_per_hour": 0.01,
            "events": bel_npp_block_1_events,
        },
        "block_2": {
            "status": False,
            "pow": 1170,
            "allow_outage_months": ["june", "dec"],
            "risk_per_hour": 0.01,
            "events": bel_npp_block_2_events,
        },
    },
    "new_npp": {
        "block_1": {
            "status": False,
            "pow": 1200,
            "allow_outage_months": ["june", "dec"],
            "risk_per_hour": 0.01,
            "events": new_npp_block_1_events,
        },
    },
        "list_outage": {
            "start_datetime": "2025-01-01 00:00:00",
            "risk_increase": 0.1,
            "duration_hours": 1,
        },
        "melting_core": {
            "start_datetime": "2025-04-01 00:00:00",
            "risk_increase": 0.3,
            "duration_hours": 6,
        },
    "upper_bound_risk": 0.5,
}



scenario = scen_1 | base_settings | repair_cost


model = Oemof_model(
    scenario = scenario,
    model_settings = {
        "start_year": 2025,
        "end_year": 2026,
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
# заряжать storage, которая будет позволять работать sink для риска с учетом uptime равной длине ремента (можно произвольеные инетрвалы с выключения недопущения одновременной работы заряж. source и ремонтируюещего sink)
