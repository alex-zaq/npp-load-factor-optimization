from src.npp_load_factor_calculator import Block_grouper, Oemof_model, Result_viewer
from src.npp_load_factor_calculator.excel_writer import Excel_writer
from src.npp_load_factor_calculator.result_viewer import Control_block_viewer
from src.npp_load_factor_calculator.scen_builder import Scenario_builder
from src.npp_load_factor_calculator.solution_processor import Solution_processor
from src.npp_load_factor_calculator.utilites import (
    all_months,
    get_repair_costs_by_capital,
)

maintence_cost, current_cost ,medium_cost, capital_cost = get_repair_costs_by_capital(50e6)

# maintence_duration = 10
# medium_duration = 40
# current_duration = 30
# capital_duration = 45


base_repair_options = {
    "maintence-1": {
        "id": 0,
        "status": False,
        "startup_cost": maintence_cost,
        "duration": 10,
        "min_downtime": 0,
        "max_startup": 36,
        "risk_reset": {},
        "risk_reducing": {"r1": 0.2},
        "min": 0,
        "npp_stop": False,
        "forced_in_period": False,
    },
    "maintence-2": {
        "id": 1,
        "status": False,
        "startup_cost": maintence_cost,
        "duration": 10,
        "min_downtime": 0,
        "max_startup": 36,
        "risk_reset": {},
        "risk_reducing": {"r1": 0.2},
        "min": 1,
        "start_day": {"status": True, "days": [1,]},
        "npp_stop": False,
        "forced_in_period": False,
    },
    
    "current-1": {
        "id": 2,
        "status": False,
        "startup_cost": current_cost,
        "duration": 30,
        "min_downtime": 0,
        "max_startup": 3,
        # "risk_reset": {"r1"},
        "risk_reset": {},
        # "risk_reducing": {},
        "risk_reducing": {"r1": 0.5},
        "min": 0,
        "start_day": {"status": True, "days": [1,]},
        "npp_stop": True,
        "forced_in_period": False,
    },
    "current-2": {
        "id": 3,
        "status": False,
        "startup_cost": current_cost,
        "duration": 10,
        "min_downtime": 0,
        "max_startup": 3,
        "risk_reset": {},
        "risk_reducing": {"r1": 0.6},
        "min": 0,
        "start_day": {"status": True, "days": [1,]},
        "npp_stop": True,
        "forced_in_period": False,
    },
    "medium-1": {
        "id": 4,
        "status": False,
        "startup_cost": medium_cost,
        "duration": 30,
        "max_startup": 3,
        "min_downtime": 0,
        "risk_reset": {},
        "risk_reducing": {"r1": 0.9},
        "min": 0,
        "npp_stop": True,
        "forced_in_period": False,
    },
    "medium-2": {
        "id": 5,
        "status": False,
        "startup_cost": medium_cost,
        "duration": 30,
        "max_startup": 3,
        "min_downtime": 0,
        "risk_reset": {},
        "risk_reducing": {},
        "min": 0,
        "npp_stop": True,
        "forced_in_period": False,
    },
    "capital": {
        "id": 6,
        "status": False,
        "startup_cost": capital_cost,
        "duration": 30,
        "max_startup": 3,
        "min_downtime": 0,
        "risk_reset": {},
        "risk_reducing": {"r1": 0.9},
        "min": 0,
        "npp_stop": True,
        "forced_in_period": False,
    },
    
}



block_base =   {   
            "status": True,
            "nominal_power": 1170,
            "var_cost": -56.5 * 10,
            "min_uptime": 10,
            # "min_uptime": 0,
            "outage_options": {
                "status": False,
            },
            "risk_options": {
                "status": False,
             },
            "repair_options": {
                "status": False,
                },
        }
   

b_1 = Scenario_builder({"bel_npp_block_1": block_base.copy()})
b_2 = Scenario_builder({"bel_npp_block_2": block_base.copy()})
b_3 = Scenario_builder({"new_npp_block_1": block_base.copy()})

base = {
        "№": 1,
        "name": "test",
        "years": [2025],
        "freq": "D",
        "bel_npp_block_1": {"status": False},
        "bel_npp_block_2": {"status": False},
        "new_npp_block_1": {"status": False},
}


one_year = {"years": [2025]}
two_years = {"years": [2025, 2026]}
three_years = {"years": [2025, 2026, 2027]}

outage_base = Scenario_builder({
    "outage_options": {
        "status": True,
        "start_of_month": True,
        "allow_months": all_months,
        "min_duration": 30,
        "max_duration": 40,
    }
})

one_risk_base = Scenario_builder(
    {
        "risk_options": {
            "status": True,
            "risks": {
                "r1": {
                    "id": 0,
                    "value": 0.12,
                    # "value": 0.3,
                    "max": 1.0,
                    "start_risk_rel": 0.3,
                    "events": None,
                },
            },
        }
    }
)

repair_base = Scenario_builder({
    "repair_options": {
        "status": True,
        "options": base_repair_options,
        "allow_parallel_repairs": False,
        }})

events_base_1 = {
    "2025-02-01": 0.15,
    "2025-09-01": 0.10,
    "2026-02-10": 0.15,
    "2026-09-10": 0.07,
    "2027-02-15": 0.12,
    "2027-09-15": 0.10,
}

events_base_2 = {
    "2025-01-20": 0.10,
    "2025-10-15": 0.12,
    "2026-03-01": 0.08,
    "2026-07-20": 0.11,
    "2027-08-15": 0.09,
    "2027-10-01": 0.10,
    "2027-11-20": 0.12,
}

events_base_3 = {
    "2025-01-15": 0.11,
    "2025-02-28": 0.10,
    "2025-04-15": 0.12,
    "2026-05-28": 0.09,
    "2027-07-28": 0.10,
    "2027-09-28": 0.11,
}




one_risk = one_risk_base.update_risk({"r1": {"events": None}})
one_risk_events = one_risk_base.update_risk({"r1": {"events": events_base_1}})
outage_jul = outage_base.update_outage({"allow_months": {"Jul"}})
outage_nov = outage_base.update_outage({"allow_months": {"Nov"}})
# outage_multiply_all = outage_base.update_outage({"allow_months": {"Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"}})

# repair_reset = repair_base.update_repair({"maintence-2": {}, "current-1": {}, "current-2": {}, "medium-1": {}})
repair_base = repair_base.update_repair({"maintence-2": {}, "current-1": {}})
repair_base = repair_base.update_repair({"capital": {"forced_in_period": True, "duration": 40}})


# risk = one_risk
risk_b1 = one_risk_base.update_risk({"r1": {"events": events_base_1, "start_risk_rel": 0.2}})
risk_b2 = one_risk_base.update_risk({"r1": {"events": events_base_2, "start_risk_rel": 0.4}})
# outage = outage_jul 
# outage = outage_multiply
# outage = outage_multiply_all
# 
# one_risk = one_risk_base.update_risk({"r1": {"events": None}})

# one_risk_events_1 = one_risk_base.update_risk({"r1": {"events": events_1}})
# one_risk_events_2 = one_risk_base.update_risk({"r1": {"events": events_2}})
# one_risk_events_3 = one_risk_base.update_risk({"r1": {"events": events_3}})
# one_risk_events_4 = one_risk_base.update_risk({"r1": {"events": events_3}})
# one_risk_events_5 = one_risk_base.update_risk({"r1": {"events": events_3}})

# two_risk = one_risk_base.update_risk({"r1": {"events": None}, "r2": {"events": None}})
# two_risk_events_4 = one_risk_base.update_risk({"r1": {"events": events_4}, "r2": {"events": events_4}})
# two_risk_events_5 = one_risk_base.update_risk({"r1": {"events": events_5}, "r2": {"events": events_5}})


# repair_reset = repair_base.update_repair({0: {"risk_reset": {"r1"}}})
# repair_two_risk = repair_base.update_repair({0: {"risk_reset": {"r1", "r2"}}})
# repair_stop_conc_1 = {}
# repair_no_stop_conc_1 = {}
# repair_npp_no_stop_concurent_reduced = {}
# repair_forced_capital = repair_base.update_repair({5: {"forced_in_period": True}})



# outage_july = outage_base.update_outage({"allow_months": {"Jul"}})
# outage_november = outage_base.update_outage({"allow_months": {"Nov"}})
# outage_april = outage_base.update_outage({"allow_months": {"Apr"}})

# outage_july_june = outage_base.update_outage({"allow_months": {"Jul", "Jun"}})
# outage_november_december = outage_base.update_outage({"allow_months": {"Nov", "Dec"}})
# outage_april_may = outage_base.update_outage({"allow_months": {"Apr", "May"}})


# scenarios
###############################################################################
# scen = base | {"№": 1} | one_year | (b_1.update(risk_b1 | repair_reset | outage)) 
# scen = base | {"№": 1} | two_years | (b_1.update(risk_b1 | repair_reset | outage)) 
# scen = base | {"№": 1} | three_years | (b_1.update(risk_b1 | repair_reset | outage)) 


# b1 = (b_1.update(risk_b1 | repair_base | outage_jul))
# b2 = (b_2.update(risk_b2 | repair_base | outage_nov))
# c = b1 | b2

scen = base | {"№": 1} | three_years | (b_1.update(risk_b1 | repair_base | outage_jul)) | (b_2.update(risk_b2 | repair_base | outage_nov)) 





# scen = base | {"№": 2} | one_year | (b_1.update(one_risk_events_1 | repair_reset | outage_july))
# scen = base | {"№": 3} | one_year | (b_1.update(two_risk_events_4 | repair_two_risk | outage_july))
# scen = base | {"№": 4} | one_year | (b_1.update(one_risk_events_1 | repair_stop_conc_1 | repair_no_stop_conc_1 | outage_july_june))

# scen = base | {"№": 5} | two_years | (b_1.update(one_risk_events_5 | repair_stop_conc_1 |repair_no_stop_conc_1 | outage_july_june)) 
# scen = base | {"№": 6} | two_years | (b_1.update(two_risk_events_4 | repair_stop_conc_1 |repair_no_stop_conc_1 | outage_july_june)) 
# scen = base | {"№": 7} | two_years | (b_1.update(one_risk_events_5 | repair_stop_conc_1 |repair_no_stop_conc_1 | outage_july_june)) 
# scen = base | {"№": 8} | two_years | (b_1.update(one_risk_events_5 | repair_stop_conc_1 |repair_no_stop_conc_1 | outage_july_june)) 

# scen = base | {"№": 9} | three_years | (b_1.update(one_risk_events_5 | repair_stop_conc_1 |repair_no_stop_conc_1 | outage_july_june)) 
# scen = base | {"№": 10} | three_years | (b_1.update(one_risk_events_5 | repair_stop_conc_1 |repair_no_stop_conc_1 | outage_july_june)) 
# scen = base | {"№": 11} | three_years | (b_1.update(one_risk_events_5 | repair_stop_conc_1 |repair_no_stop_conc_1 | outage_july_june)) 
# scen = base | {"№": 12} | three_years | (b_1.update(one_risk_events_5 | repair_stop_conc_1 | repair_no_stop_conc_1 | outage_july_june)) 
###############################################################################

oemof_model = Oemof_model(
    scenario = scen,
    solver_settings = {
        "solver": "cplex",
        "solver_verbose": True,
        "mip_gap": 0.001
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

# solution_processor.set_restore_mode(file_number="39") 
solution_processor.set_restore_mode(file_number="184") 

solution_processor.apply()



custom_es = solution_processor.get_custom_model()
oemof_es = solution_processor.get_oemof_es()
results = solution_processor.get_results()



b_1 = custom_es.block_db.get_bel_npp_block_1()
# b_1.build()
b_2 = custom_es.block_db.get_bel_npp_block_2()
b_3 = custom_es.block_db.get_new_npp_block_1()


block_grouper = Block_grouper(results, custom_es)


block_grouper.set_options(
    electricity_options={
        "БелАЭС (блок 1)": {"block": b_1, "color": "#2ca02c"},
        "БелАЭС (блок 2)": {"block": b_2, "color": "#0a6470"},
        "Новая АЭС (блок 1)": {"block": b_3, "color": "#ff7f0e"},
    },
    risks_options={
        "накопленный риск r1": {"risk_name": "r1", "style":"-", "color": "#181008"},
        "накопленный риск r2": {"risk_name": "r2", "style":"-", "color": "#1417d1"},
        "накопленный риск r3": {"risk_name": "r3", "style":"-", "color": "#10c42e"},
    },
    repairs_options={
        "легкий ремонт-1": {"id": 0, "color": "#FF00DD"},
        "легкий ремонт-2": {"id": 1, "color": "#fdec02"},
        "текущий ремонт-1": {"id": 2, "color": "#0b07fc"},
        "текущий ремонт-2": {"id": 3, "color": "#ff00b3"},
        "средний ремонт-1": {"id": 4, "color": "#501d0c"},
        "средний ремонт-2": {"id": 5, "color": "#0c2450"},
        "капитальный ремонт-1": {"id": 6, "color": "#ff4000"},
    },
    repairs_cost_options={
        "БелАЭС (блок 1)-затраты": {"block": b_1, "style":"-", "color": "#18be2f"},
        "БелАЭС (блок 2)-затраты": {"block": b_2, "style":"-", "color": "#1f77b4"},
        "Новая АЭС (блок 1)-затраты": {"block": b_3, "style":"-", "color": "#b4671f"},
    }  
)


result_viewer = Result_viewer(block_grouper)
excel_writer = Excel_writer(block_grouper)
control_block_viewer = Control_block_viewer(block_grouper)


# image_simple = result_viewer.plot_general_graph(b_1)
image_main = result_viewer.plot_profile_all_blocks_graph(font_size=10, risk_graph=False, dpi=170)

# result_viewer.plot_general_graph(bel_npp_block_2)
# result_viewer.plot_general_graph(new_npp_block_1)

# control_block_viewer.plot_control_stop_block(bel_npp_block_1)
# control_block_viewer.plot_npp_status(bel_npp_block_1)

# control_block_viewer.plot_npp_storage_data(bel_npp_block_1)
# control_block_viewer.plot_repair_storage_max_uptime(bel_npp_block_1, repair_id=1)
# control_block_viewer.plot_repair_storage_max_uptime(bel_npp_block_1, repair_id=2)
# control_block_viewer.plot_repair_storage_max_uptime(bel_npp_block_1, repair_id=3)
# control_block_viewer.plot_repair_storage_max_uptime(bel_npp_block_1, repair_id=5)
 

# result_viewer.create_scheme("./schemes")
# image_simple.save("./images","jpg", 600)
# image_main.save("./images","jpg", 600)


excel_writer.write("./excel_results")

print("done")



# запрет на одновременные ремонты с вкл аэс
# события для второго и третьего блока
# разные цвета событий
# вывод в эксель по месяцам
# простое переключение сценариев
# проверить min_downtime
# график без риска
# график только с риском
# фото с ноутбука
# сделать расчет с ноутбука
# блок-схема









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
# формализованная схема
# ключевые неравенства (фрагменты кода?)
# общий принцип работы и расчетная схема (акцент на условности расчета)
# таблица настроек сценария
# исходные данные
# используемое ПО
# серия примеров расчета (графики: работа АЭС, события риска, выполенные ремонты, изменения раска во времени, деньги за ремонты)
# графики и таблицы
# источника oemof-solph статья
# сложные два примера для показа снижения целевой функции
















