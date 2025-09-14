from datetime import datetime as dt

from src.npp_load_factor_calculator import Block_grouper, Oemof_model, Result_viewer
from src.npp_load_factor_calculator.result_viewer import Control_block_viewer
from src.npp_load_factor_calculator.solution_processor import Solution_processor
from src.npp_load_factor_calculator.utilites import all_months, days_to_hours, get_r

repair_options = {
    "maintence-1": {
        "id": 0,
        "status": True,
        "cost": 1e6,
        "duration": days_to_hours(1),
        "min_downtime": days_to_hours(30),
        "risk_reset": (),
        "risk_reducing": {"r2": get_r(0.3)},
        "npp_stop": False,
    },
    "maintence-2": {
        "id": 1,
        "status": True,
        "cost": 1e6,
        "duration": days_to_hours(1),
        "min_downtime": days_to_hours(30),
        "risk_reset": (),
        "risk_reducing": {"r1": get_r(0.3)},
        "npp_stop": False,
    },
    
    "light": {
        "id": 2,
        "status": True,
        "cost": 5e6,
        "duration": days_to_hours(5),
        "min_downtime": days_to_hours(30),
        "risk_reset": ("r1",),
        "risk_reducing": {"r2": 0.3},
        "npp_stop": True,
    },
    "medium-1": {
        "id": 3,
        "status": False,
        "cost": 15e6,
        "duration": days_to_hours(15),
        "min_downtime": days_to_hours(30),
        "risk_reset": ("r1","r2"),
        "risk_reducing": {},
        "npp_stop": True,
    },
    "medium-2": {
        "id": 4,
        "status": False,
        "cost": 15e6,
        "duration": days_to_hours(15),
        "min_downtime": days_to_hours(30),
        "risk_reset": ("r1", "r2", "r3"),
        "risk_reducing": {},
        "npp_stop": True,
    },
    "capital": {
        "id": 5,
        "status": False,
        "cost": 50e6,
        "duration": days_to_hours(25),
        "min_downtime": days_to_hours(30),
        "risk_reset": ("r1", "r2", "r3"),
        "risk_reducing": {},
        "npp_stop": True,
        "forced_freq_year": 1,
    },
}


scen = {
        "№": 1,
        "name": "test",
        "years": [2025],
        "bel_npp_block_1": {
            "status": True,
            "nominal_power": 1170,
            "var_cost": -56.5,
            "outage_options": {
                "start_of_month": False,
                "allow_months": all_months - set("jan"),
                "planning_outage_duration": days_to_hours(30),
                "fixed_outage_months":  set("june"),
            },
            "risk_options": {
                "r1": {"value": get_r(0.1), "max": 1},
                "r2": {"value": get_r(0.1), "max": 1},
                "r3": {"value": get_r(0.1), "max": 1},
                },
            "repair_options": repair_options,
        },
        "bel_npp_block_2": {
            "status": False,
        },
        "new_npp_block_1": {
            "status": False,
        },
}







oemof_model = Oemof_model(
    scenario = scen,
    solver_settings = {
        "solver": "cplex",
        "solver_verbose": True,
        "mip_gap": 0.01
    } 
)


solution_processor = Solution_processor(oemof_model)
solution_processor.set_calc_mode(save_results=False)
# solution_processor.set_calc_mode(save_results=True)
solution_processor.set_dumps_folder("./dumps")
solution_processor.set_excel_folder("./excel_results")

# solution_processor.set_restore_mode(file_number="00") 
# solution_processor.set_restore_mode(file_number="01") 
# solution_processor.set_restore_mode(file_number="02") 
# solution_processor.set_restore_mode(file_number="03") 
# solution_processor.set_restore_mode(file_number="06") 

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

control_block_viewer.plot_storage_profiles(mode = "storage_main_risk", flow_mode = "content")
control_block_viewer.plot_storage_profiles(mode = "storage_main_risk", flow_mode = "input")
control_block_viewer.plot_storage_profiles(mode = "storage_main_risk", flow_mode = "output")

print("done")


# Применение методов линейно-целочисленного программирования - 40 стр

# введение в oemof в контексте риск-мониаторинга, возможности и ограничения
# используемые компоненты
# общий принцип работы и расчетная схема (акцент на условности расчета)
# таблица настроек сценария
# исходные данные
# используемое ПО
# серия примеров расчета (графики: работа АЭС, события риска, выполенные ремонты, изменения раска во времени, деньги за ремонты)

# серия типовых расчетов от простого к сложному
# 1 блок - 1 риск - 1 год - 1 ремонт - ОТЧЕТ  
# 1 блока - 3 риска - 3 года - 3 ремонт - ОТЧЕТ
# 2 блока - 3 риска - 3 года - 3 ремонт - ОТЧЕТ
# 4 блока в каждом по 3 типа риска, в каждом блоке 3 типа ремонтов на 4 года - ОТЧЕТ 


# 3 блока в каждом по 3 типа риска, в каждом блоке 3 типа ремонтов на 1 год
# 1 блок - 1 риск - 1 год - 1 ремонт
# 1 блок - 2 риск - 1 год - 2 ремонт
# 1 блок - 3 риск - 1 год - 3 ремонт





# почасовой вклад в риск (сразу все риски)
# возможность изменение кпд переключателей топлива для учета разного вклада в понижение рисков
# для ремонтов требущих отключение блока добавить промежуточный блок со связья блоком (upper 1)
# запрет на одновременность работы промежуточных блоков
# для учета требования 30 дневной остановки добавить storage c mindowntime и фикс. source
# учесть паузу между ремонтами (расширить период и занулить доступности)






# фиксировать ремонты для показа большей целевой функции
# зеркальные non-convex source для нейтр. событий на которые попали ремонты от 1 до 3 на каждый вид ремонта в каждом блоке аэс
# отмечать какие ремонты могут нейтр. аварий событие 
# переделать расчет фикс ав. событий
# переключатель нейтролизуемого риска (от 1 до 3) в качестве input через сonverter_repair
# динам изменением maxY
# objective value extract
# solution_processor.write_excel_file("test.xlsx")
# result_plotter.plot_electricity_generation_profile()
# result_plotter.plot_risk_events_profile()
# result_plotter.plot_cumulative_risk_profile()
# result_plotter.plot_repair_cost_profile()
# параметры для записи и чтения у компонентов
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
# запись в эксель - числа - графика- сценарий - настройки решателя