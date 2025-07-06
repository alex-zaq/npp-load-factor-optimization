from src.npp_load_factor_calculator import Oemof_model, Result_grouper, Result_plotter

base_settings = {
    
}


scen_1 = {
    "№": 1,
    "name": "experimental",
    "bel_npp": {
        "block_1": {"pow": 1170, "allow_outage_months": ["june","dec"], "risk_per_hour": 0.01},
        "block_2": {"pow": 1170, "allow_outage_months": ["june","dec"], "risk_per_hour": 0.01},
    },
    "npp_light_repair": {"cost": 0.1, "duration_days": 7},
    "nnp_heavy_repair": {"cost": 0.2, "duration_days": 14},
    "npp_capital_repair": {"cost": 0.3, "duration_days": 21},
    "date_events": {
        "ligt_outage": {"date": "2025-01-01", "risk_increase": 0.1, "duration_hours": 1},
        "melting_core": {"date": "2025-04-01", "risk_increase": 0.3, "duration_hours": 6},
    },
    "max_risk": 0.5,
}



scen_settings = scen_1 | base_settings

all_year = slice(0, 8759)

model = Oemof_model(
    scen_settings = scen_settings,
    model_settings = {
        "custom_slice": all_year,
        "solver": "cplex",
        "solver_verbose": True,
        "mip_gap": 0.01
    } 
)




model.calculate()


custom_es = model.get_custom_es()
results = model.get_results()


npp_blocks = custom_es.get_npp_blocks()


block_grouper = Result_grouper(results, custom_es)


block_grouper.set_block_groups(
    electricity = {},
    risk_events = {},
)


result_grouper = Result_grouper(results)
result_plotter = Result_plotter(result_grouper)

# result_plotter.plot_npp_loading_profile()
# result_plotter.plot_risk_events_profile()
# result_plotter.plot_cumulative_risk_profile()
# result_plotter.plot_repair_cost_profile()


# добавить структуру методов классов
# мин. фукц. класса oemof_model
# мин. фукц. класса custom_model_builder (добавить два блока аэс, риски)
# реализация фиксированного времени работы на ном. мощности
# стоимость включения для учета стоиомсти ремонта
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
