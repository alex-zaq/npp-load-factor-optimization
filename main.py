from src.npp_load_factor_calculator import Block_grouper, Oemof_model, Result_viewer
from src.npp_load_factor_calculator.result_viewer import Control_block_viewer
from src.npp_load_factor_calculator.solution_processor import Solution_processor
from src.npp_load_factor_calculator.utilites import all_months

repair_options = {
    "maintence-1": {
        "id": 0,
        "status": False,
        "startup_cost": 1e3,
        "duration": 10,
        "min_downtime": 0,
        "max_startup": 12,
        "risk_reset": set(),
        "risk_reducing": {"r1": 0.15},
        "min": 0,
        "npp_stop": False,
        "forced_in_period": False,
    },
    "maintence-2": {
        "id": 1,
        "status": True,
        "startup_cost": 1e3,
        "duration": 10,
        "min_downtime": 0,
        "max_startup": 36,
        "risk_reset": set(),
        "risk_reducing": {"r1": 0.1},
        "min": 1,
        "start_day": {"status": True, "days": [1,]},
        "npp_stop": False,
        "forced_in_period": False,
    },
    
    "light": {
        "id": 2,
        "status": True,
        "startup_cost": 15e3,
        "duration": 30,
        "min_downtime": 0,
        "max_startup": 3,
        "risk_reset": {"r1"},
        # "risk_reset": {},
        "risk_reducing": {},
        # "risk_reducing": {"r1": 0.9},
        "min": 0,
        "start_day": {"status": True, "days": [1,]},
        "npp_stop": True,
        "forced_in_period": False,
    },
    "medium-1": {
        "id": 3,
        "status": True,
        "startup_cost": 1e3,
        "duration": 30,
        "min_downtime": 0,
        "max_startup": 3,
        "risk_reset": {"r1"},
        "risk_reducing": {},
        "min": 0,
        "start_day": {"status": True, "days": [1,]},
        "npp_stop": True,
        "forced_in_period": False,
    },
    "medium-2": {
        "id": 4,
        "status": False,
        "startup_cost": 15e6,
        "duration": 15,
        "min_downtime": 30,
        "risk_reset": {"r1"},
        "risk_reducing": {},
        "min": 0,
        "npp_stop": True,
        "forced_in_period": False,
    },
    "capital": {
        "id": 5,
        "status": False,
        "startup_cost": 50e6,
        "duration": 25,
        "min_downtime": 30,
        "risk_reset": {"r1"},
        "risk_reducing": {},
        "min": 0,
        "npp_stop": True,
        "forced_in_period": False,
    },
}

events = {
    "2025-02-01": 0.05,
    "2025-04-15": 0.15,
    "2025-09-01": 0.05,
}

base_scen = {
        "№": 1,
        "name": "test",
        "years": [2025],
        # "years": [2025, 2026],
        # "years": [2025, 2026, 2027],
        "freq": "D",
        "bel_npp_block_1": (bel_npp_block_2 := {
            "status": True,
            "nominal_power": 1170,
            "var_cost": -56.5,
            "min_uptime": 10,
            # "min_uptime": 0,
            "outage_options": {
                "status": True,
                "start_of_month": True,
                # "allow_months": all_months - {"Jan"},
                "allow_months": {"Jul"},
                # "allow_months": {"Feb", "Oct"},
                "planning_outage_duration": 30,
                # "fixed_mode": True,
                # "fixed_mode": False,
                # "fixed_outage_month":  {"Sep"},
                # "fixed_outage_month":  {"Oct"},
            },
            "risk_options": {
                "status": True,
                "risks": {
                    "r1": {"id": 0, "value": 0.1, "max": 0.5, "start_risk_rel": 0.3, "events": events},
                    # "r2": {"id": 1, "value": 0.1, "max": 0.7, "start_risk_rel": 0.2, "events": None},
                    # "r3": {"id": 2, "value": 0.1, "max": 1, "start_risk_rel": 0, "events": None},
                }},
            "repair_options": {
                "status": True,
                "options": repair_options
                },
        }),
        # "bel_npp_block_2": bel_npp_block_2,
        "bel_npp_block_2": {"status": False},
        "new_npp_block_1": {"status": False},
        # "new_npp_block_1": bel_npp_block_2,
}

base_scen = base_scen

# scenarios
###############################################################################

# 
scen = base_scen | {"№": 1, "name": "one_block_one_risk_one_year", "years": [2025]}



# scen = base_scen | {"№": 2, "name": "two_block_one_risk_two_years", "years": [2025, 2026]}







# 3 блока - 3 года - 1 риск - 1 обяз.капремонт - 4 конкур. npp-stop reduce-20-10, 2 конкур. два non-stop reduce 10-15 дней, разн.ст. риски 


###############################################################################


oemof_model = Oemof_model(
    scenario = scen,
    solver_settings = {
        "solver": "cplex",
        "solver_verbose": True,
        "mip_gap": 0.0001
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
# solution_processor.set_restore_mode(file_number="09") 

# solution_processor.set_restore_mode(file_number="39") 
# solution_processor.set_restore_mode(file_number="41") 

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
        "показатель риска r1": {"risk_name": "r1", "style":"-", "color": "#181008"},
        "риск 2": {"risk_name": "r2", "style":"-", "color": "#1417d1"},
        "риск 3": {"risk_name": "r3", "style":"-", "color": "#10c42e"},
    },
    repairs_options={
        "легкий ремонт-1": {"id": 0, "color": "#00FFAA"},
        "легкий ремонт-2": {"id": 1, "color": "#fdec02"},
        "текущий ремонт-1": {"id": 2, "color": "#0b07fc"},
        "текущий ремонт-2": {"id": 3, "color": "#ff00b3"},
        "капитальный ремонт-1": {"id": 4, "color": "#ff4000"},
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


# image_simple = result_viewer.plot_general_graph(bel_npp_block_1)
image_main = result_viewer.plot_profile_all_blocks_graph(font_size=10, risk_graph=True, dpi=120)

# result_viewer.plot_general_graph(bel_npp_block_2)
# result_viewer.plot_general_graph(new_npp_block_1)

control_block_viewer.plot_control_stop_block(bel_npp_block_1)
control_block_viewer.plot_npp_status(bel_npp_block_1)

control_block_viewer.plot_npp_storage_data(bel_npp_block_1)
control_block_viewer.plot_repair_storage_max_uptime(bel_npp_block_1, repair_id=1)
control_block_viewer.plot_repair_storage_max_uptime(bel_npp_block_1, repair_id=2)
 

# result_viewer.create_scheme("./schemes")
# image_simple.save("./images","jpg", 600)
# image_main.save("./images","jpg", 600)




print("done")



# название блока верхней границе риска
# добавить скобки в легенде
# сделать расчет с ноутбука
# фото с ноутбука
# разные верхние границы максимумов
# добавить отображения событий повышающих риск (вертикальные черты)
# простое переключение сценариев
# параметры для записи и чтения у компонентов
# блок-схема
# взять реальные значения из двух источников
# вывод в эксель









# время расчета, точность, по в отчет
# ключевые формулировки актульности (моника)
# формализованная блок-схема расчет
# дальнейшенее развитие
# принцип реализации
# актуальность и полезность
# модель с тестовыми данными
# введение в лп
# введение в oemof
# введение в oemof в контексте риск-мониаторинга
# введение в oemof в контексте риск-мониаторинга, возможности и ограничения
# используемые компоненты OEMOF
# общий принцип работы и расчетная схема (акцент на условности расчета)
# таблица настроек сценария
# исходные данные
# используемое ПО
# серия примеров расчета (графики: работа АЭС, события риска, выполенные ремонты, изменения раска во времени, деньги за ремонты)

















