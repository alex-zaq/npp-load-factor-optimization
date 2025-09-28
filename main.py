from datetime import datetime as dt

from src.npp_load_factor_calculator import Block_grouper, Oemof_model, Result_viewer
from src.npp_load_factor_calculator.result_viewer import Control_block_viewer
from src.npp_load_factor_calculator.solution_processor import Solution_processor
from src.npp_load_factor_calculator.utilites import all_months, days_to_hours, get_r

repair_options = {
    "maintence-1": {
        "id": 0,
        "status": False,
        "startup_cost": 1e3,
        "duration": days_to_hours(1),
        # "min_downtime": days_to_hours(60),
        "min_downtime": 0,
        "max_startup": 5,
        "risk_reset": set(),
        "risk_reducing": {"r2": get_r(0.3)},
        "npp_stop": False,
    },
    "maintence-2": {
        "id": 1,
        "status": False,
        "startup_cost": 1e5,
        "duration": days_to_hours(5),
        # "min_downtime": days_to_hours(30),
        "min_downtime": 0,
        "max_startup": 12,
        "risk_reset": set(),
        "risk_reducing": {"r1": 0.15},
        "start_day": {"status": True, "days": [1,]},
        "npp_stop": False,
    },
    
    "light": {
        "id": 2,
        "status": True,
        "startup_cost": 15e6,
        "duration": days_to_hours(15),
        "min_downtime": 0,
        "max_startup": 1,
        "risk_reset": {"r1"},
        "risk_reducing": {},
        "start_day": {"status": True, "days": [1,]},
        "npp_stop": True,
    },
    "medium-1": {
        "id": 3,
        "status": False,
        "startup_cost": 5e6,
        "duration": days_to_hours(15),
        "min_downtime": 0,
        "risk_reset": {"r1","r2"},
        "max_startup": 1,
        "risk_reducing": {},
        "npp_stop": True,
    },
    "medium-2": {
        "id": 4,
        "status": False,
        "startup_cost": 15e6,
        "duration": days_to_hours(15),
        "min_downtime": days_to_hours(30),
        "risk_reset": {"r1", "r2", "r3"},
        "risk_reducing": {},
        "npp_stop": True,
    },
    "capital": {
        "id": 5,
        "status": False,
        "startup_cost": 50e6,
        "duration": days_to_hours(25),
        "min_downtime": days_to_hours(30),
        "risk_reset": {"r1", "r2", "r3"},
        "risk_reducing": {},
        "npp_stop": True,
        "forced_in_period": True,
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
            # "min_uptime": days_to_hours(30),
            "min_uptime": 0,
            "outage_options": {
                "status": True,
                "start_of_month": True,
                "allow_months": all_months - {"Jan"},
                "planning_outage_duration": days_to_hours(30),
                "fixed_mode": True,
                "fixed_outage_month":  set(["Jul"]),
            },
            "risk_options": {
                "status": True,
                "risks": {
                    "r1": {"id": 0, "value": get_r(0.1), "max": 7*0.1, "start_risk_rel": 0},
                    # "r2": {"id": 1," "value": get_r(0.1), "max": 1, "start_risk": 0},
                    # "r3": {"id": 2," "value": get_r(0.1), "max": 1, "start_risk": 0},
                }},
            "repair_options": {
                "status": True,
                "options": repair_options
                },
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
        "mip_gap": 0.05
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
# solution_processor.set_restore_mode(file_number="06") 
# solution_processor.set_restore_mode(file_number="09") 
# solution_processor.set_restore_mode(file_number="15") 

solution_processor.apply()



custom_es = solution_processor.get_custom_model()
oemof_es = solution_processor.get_oemof_es()
results = solution_processor.get_results()



bel_npp_block_1 = custom_es.block_db.get_bel_npp_block_1()
bel_npp_block_2 = custom_es.block_db.get_bel_npp_block_2()
new_npp_block_1 = custom_es.block_db.get_new_npp_block_1()


block_grouper = Block_grouper(results, custom_es)


block_grouper.set_options(
    electricity_options={
        "БелАЭС (блок 1)": {"block": bel_npp_block_1, "color": "#2ca02c"},
        "БелАЭС (блок 2)": {"block": bel_npp_block_2, "color": "#ff7f0e"},
        "Новая АЭС (блок 1)": {"block": new_npp_block_1, "color": "#1f77b4"},
    },
    risks_options={
        "R1": {"risk_name": "r1", "style":"-", "color": "#181008"},
        "R2": {"risk_name": "r2", "style":"-", "color": "#1417d1"},
        "R3": {"risk_name": "r3", "style":"-", "color": "#10c42e"},
    },
    repairs_options={
        "НО-1": {"id": 0, "color": "#00FFAA"},
        "НО-2": {"id": 1, "color": "#fdec02"},
        "ТР-1": {"id": 2, "color": "#0b07fc"},
        "ТР-2": {"id": 3, "color": "#0080ff"},
        "КР-1": {"id": 4, "color": "#ff4000"},
    },
    repairs_cost_options={
        "БелАЭС (блок 1)-затраты": {"block": bel_npp_block_1, "style":"-", "color": "#18be2f"},
        "БелАЭС (блок 2)-затраты": {"block": bel_npp_block_2, "style":"-", "color": "#ff7f0e"},
        "Новая АЭС (блок 1)-затраты": {"block": new_npp_block_1, "style":"-", "color": "#1f77b4"},
    }  
)


solution_processor.set_block_grouper(block_grouper)
result_viewer = Result_viewer(block_grouper)
control_block_viewer = Control_block_viewer(block_grouper)

result_viewer.set_image_flag(False)
# result_viewer.set_image_flag(True)
result_viewer.set_image_options(folder="./images", image_format="jpg", dpi=600)

result_viewer.plot_general_graph(bel_npp_block_1)

# control_block_viewer.plot_sinks_profile(bel_npp_block_1, repair_id=1, risk_name="r1")
control_block_viewer.plot_sinks_profile(bel_npp_block_1, repair_id=2, risk_name="r1")









# result_viewer.plot_electricity_generation_profile()
# result_viewer.plot_main_risk_events_profile()
# result_viewer.plot_cost_profile()
# result_viewer.plot_repair_profile()
# result_viewer.plot_general_graph()


# control_block_viewer.plot_default_risk_profile()

# control_block_viewer.plot_storage_profiles(mode = "storage_main_risk", flow_mode = "content")
# control_block_viewer.plot_storage_profiles(mode = "storage_main_risk", flow_mode = "input")
# control_block_viewer.plot_storage_profiles(mode = "storage_main_risk", flow_mode = "output")

print("done")


# учет штрафов за остановку
# почасовой вклад в риск (сразу все риски)
# для ремонтов требущих отключение блока добавить промежуточный блок со связья блоком (upper 1)
# запрет на одновременность работы промежуточных блоков
# для учета требования 30 дневной остановки добавить storage c mindowntime и фикс. source
# учесть паузу между ремонтами (расширить период и занулить доступности)
# фиксировать ремонты для показа большей целевой функции
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












