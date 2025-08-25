from src.npp_load_factor_calculator import Block_grouper, Oemof_model, Result_viewer
from src.npp_load_factor_calculator.result_viewer import Control_block_viewer
from src.npp_load_factor_calculator.solution_processor import Solution_processor
from src.npp_load_factor_calculator.utilites import all_months

bel_npp_block_1_events = {
    "accident_1": {
        "start_datetime": "2025-02-01 00:00:00",
        "risk_increase": 0.1,
        "duration_hours": 1,
    },
    "accident_2": {
        "start_datetime": "2025-04-01 00:00:00",
        "risk_increase": 0.3,
        "duration_hours": 1,
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
    "light_repair": {
        "id": 0,
        "status": False,
        "cost": 0.1,
        "duration": 7,
        "risk_reducing": 0.1,
        "start_day": {"status": True, "days": [1, 15]},
        "max_count_in_year": {"status": True, "count": 1},
        "avail_months": all_months,
        "npp_stop": False,
    },
    "avg_repair": {
        "id": 1,
        "status": False,
        "cost": 0.2,
        "duration": 14,
        "risk_reducing": 0.2,
        "start_day": {"status": True, "days": [1, 15]},
        "max_count_in_year": {"status": True, "count": 1},
        "avail_months": all_months,
        "npp_stop": True,
    },
    "capital_repair": {
        "id": 2,
        "status": False,
        "cost": 0.3,
        "duration": 21,
        "risk_reducing": 0.3,
        "start_day": {"status": True, "days": [1, 15]},
        "max_count_in_year": {"status": True, "count": 1},
        "avail_months": all_months,
        "npp_stop": True,
    },
}


scen_1 = {
        "№": 1,
        "name": "test",
        "years": [2025],
        "bel_npp_block_1": {
            "status": True,
            "nominal_power": 1170,
            "var_cost": -56.5,
            "risk_per_hour": 0.01,
            "upper_bound_risk": 5000 * 0.01,
            "events": bel_npp_block_1_events,
            "repair_options": repair_options,
        },
        "bel_npp_block_2": {
            "status": False,
            "nominal_power": 1170,
            "var_cost": -56.5,
            "risk_per_hour": 0.01,
            "upper_bound_risk": 0.5,
            "events": bel_npp_block_2_events,
            "repair_options": repair_options,
        },
       "new_npp_block_1": {
            "status": False,
            "nominal_power": 1170,
            "var_cost": -56.5,
            "risk_per_hour": 0.01,
            "upper_bound_risk": 0.5,
            "events": new_npp_block_1_events,
            "repair_options": repair_options,
        },
}



scenario = scen_1


oemof_model = Oemof_model(
    scenario = scenario,
    solver_settings = {
        "solver": "cplex",
        "solver_verbose": True,
        "mip_gap": 0.01
    } 
)


solution_processor = Solution_processor(oemof_model)
# solution_processor.set_calc_mode(save_results=False)
solution_processor.set_calc_mode(save_results=True)
solution_processor.set_dumps_folder("./dumps")
solution_processor.set_excel_folder("./excel_results")

# solution_processor.set_restore_mode(file_number="00") 
# solution_processor.set_restore_mode(file_number="01") 
# solution_processor.set_restore_mode(file_number="02") 
# solution_processor.set_restore_mode(file_number="03") 

solution_processor.apply()



custom_es = solution_processor.get_custom_model()
oemof_es = solution_processor.get_oemof_es()
results = solution_processor.get_results()



bel_npp_block_1 = custom_es.block_db.get_bel_npp_block_1()
bel_npp_block_2 = custom_es.block_db.get_bel_npp_block_2()
new_npp_block_1 = custom_es.block_db.get_new_npp_block_1()


block_grouper = Block_grouper(results, custom_es)


block_grouper.set_block_groups(
    electricity_gen={
        "БелАЭС (блок 1)": {"order": [bel_npp_block_1], "color": "#2ca02c"},
        "БелАЭС (блок 2)": {"order": [bel_npp_block_2], "color": "#ff7f0e"},
        "Новая АЭС (блок 1)": {"order": [new_npp_block_1], "color": "#1f77b4"},
    },
    main_risk_gen={
        "БелАЭС (блок 1) - риск": {"order": [bel_npp_block_1], "color": "#1ae0ff"},
        "БелАЭС (блок 2) - риск": {"order": [bel_npp_block_2], "color": "#e8ff1a"},
        "Новая АЭС (блок 1) - риск": {"order": [new_npp_block_1], "color": "#3d26a3"},
    },
    risk_events={
        "БелАЭС (блок 1) - аварии": {"order": [bel_npp_block_1], "color": "#7b235a"},
        "БелАЭС (блок 2) - аварии": {"order": [bel_npp_block_2], "color": "#968091"},
        "Новая АЭС (блок 1) - аварии": {"order": [new_npp_block_1], "color": "#412d9b"},
    },
    repair_cost={
        "БелАЭС (блок 1) - затраты": {"order": [bel_npp_block_1], "color": "#18be2f"},
        "БелАЭС (блок 2) - затраты": {"order": [bel_npp_block_2], "color": "#F07706"},
        "Новая АЭС (блок 1) - затраты": {"order": [new_npp_block_1],"color": "#4a3550"},
    }
)

block_grouper.set_repair_plot_options(
    repair_events={
        "БелАЭС (блок 1) - ремонт": {
            "order": [bel_npp_block_1],
            "options": {"легкий": (0, "#14e729"), "средний": (1, "#f9f10b"), "тяжелый": (2, "#f11111")},
        },
        "БелАЭС (блок 2) - ремонт": {
            "order": [bel_npp_block_2],
            "options": {"легкий": (0, "#14e729"), "средний": (1, "#f9f10b"), "тяжелый": (2, "#f11111")},
        },
        "Новая АЭС (блок 1) - ремонт": {
            "order": [new_npp_block_1],
            "options": {"легкий": (0, "#14e729"), "средний": (1, "#f9f10b"), "тяжелый": (2, "#f11111")},
        },
    }
)


solution_processor.set_block_grouper(block_grouper)
result_viewer = Result_viewer(block_grouper)
control_block_viewer = Control_block_viewer(block_grouper)
control_block_viewer.select_block(bel_npp_block_1)

result_viewer.set_image_flag(False)
# result_viewer.set_image_flag(True)
result_viewer.set_image_options(folder="./images", image_format="jpg", dpi=600)

result_viewer.plot_electricity_generation_profile()
# result_viewer.plot_main_risk_events_profile()
# result_viewer.plot_cost_profile()
# result_viewer.plot_repair_profile()
# result_viewer.plot_general_graph()


control_block_viewer.plot_default_risk_profile()



print("done")







# solution_processor.write_excel_file("test.xlsx")
# учитываемые ремонты в названии результатов и default
# result_plotter.plot_electricity_generation_profile()
# result_plotter.plot_risk_events_profile()
# result_plotter.plot_cumulative_risk_profile()
# result_plotter.plot_repair_cost_profile()
# параметры для записи и чтения у компонентов
# сделать минимальный расчет рабочий
# записать и восстановить решение
# проверить df.cumsum c многими столбцами
# solph.views на большом примере полезные методц
# как работает втроенный обзор результатов
# как работает results(block)
# +-сделать block_grouper
# +-сделать result_viewer
# мин. фукц. класса oemof_model
# реализация фиксированного времени работы на ном. мощности
# большой интервал времени 5 лет
# увеличение рисков по определенным во времени событием и штатной работы аэс
# добавить 3-4 сценария
# блок-схема
# 4 года, много событий, кокурирующие ремонты, 1 блок, 2 блока, 3 блока
# взять реальные значения из двух источников
# вывод в эксель
# через определенные интервалы времени (например длина ремонта) добавить sink и source который будет в данные интервалы
# заряжать storage, которая будет позволять работать sink для риска с учетом uptime равной длине ремента (можно произвольеные инетрвалы с выключения недопущения одновременной # # работы заряж. source и ремонтируюещего sink)
# проверить на малом примере: н и н+1 и два одновременных слова в custom_attributes и доп шаг для работы storage
# запись в эксель - числа - графика- сценарий - настройки решателя
# сохранение картинки через код plt.savefig('kartinka.png', dpi=300)