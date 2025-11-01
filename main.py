from src.npp_load_factor_calculator import Block_grouper, Oemof_model, Result_viewer
from src.npp_load_factor_calculator.excel_writer import Excel_writer
from src.npp_load_factor_calculator.result_viewer import Control_block_viewer
from src.npp_load_factor_calculator.scen_builder import Scenario_builder
from src.npp_load_factor_calculator.solution_processor import Solution_processor
from src.npp_load_factor_calculator.utilites import (
    get_repair_costs_by_capital,
)

capital_cost = 50e6

maintence_cost, current_cost ,medium_cost, capital_cost = get_repair_costs_by_capital(capital_cost)



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
        "min": 1,
        "start_day": {"status": True, "days": [1,15]},
        "npp_stop": False,
        "no_parallel_tag_for_npp": False,
        "no_parallel_tag_for_model": False,
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
        "start_day": {"status": True, "days": [1,15]},
        "npp_stop": False,
        "no_parallel_tag_for_npp": False,
        "no_parallel_tag_for_model": False,
        "forced_in_period": False,
    },
    
    "current-1": {
        "id": 2,
        "status": False,
        "startup_cost": current_cost,
        "duration": 30,
        "min_downtime": 0,
        "max_startup": 3,
        "risk_reset": {},
        "risk_reducing": {"r1": 0.5},
        "min": 0,
        "start_day": {"status": True, "days": [1,]},
        "npp_stop": True,
        "no_parallel_tag_for_npp": False,
        "no_parallel_tag_for_model": False,
        "forced_in_period": False,
    },
    "current-2": {
        "id": 3,
        "status": False,
        "startup_cost": current_cost,
        "duration": 30,
        "min_downtime": 0,
        "max_startup": 3,
        "risk_reset": {},
        "risk_reducing": {"r1": 0.5},
        "min": 0,
        "start_day": {"status": True, "days": [1,]},
        "npp_stop": True,
        "no_parallel_tag_for_npp": False,
        "no_parallel_tag_for_model": False,
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
        "start_day": {"status": True, "days": [1,]},
        "npp_stop": True,
        "no_parallel_tag_for_npp": False,
        "no_parallel_tag_for_model": False,
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
        "start_day": {"status": True, "days": [1,]},
        "npp_stop": True,
        "no_parallel_tag_for_npp": False,
        "no_parallel_tag_for_model": False,
        "forced_in_period": False,
    },
    "capital-1": {
        "id": 6,
        "status": False,
        "startup_cost": capital_cost,
        "duration": 30,
        "max_startup": 1,
        "min_downtime": 0,
        "risk_reset": {},
        "risk_reducing": {"r1": 0.9},
        "min": 0,
        "start_day": {"status": True, "days": [1,]},
        "npp_stop": True,
        "no_parallel_tag_for_npp": False,
        "no_parallel_tag_for_model": False,
        "forced_in_period": False,
    },
    
    "repair-1": {
        "id": 7,
        "status": False,
        "startup_cost": maintence_cost,
        "duration": 10,
        "min_downtime": 0,
        "max_startup": 36,
        "risk_reset": {},
        "risk_reducing": {"r1": 0.2},
        "min": 0,
        "start_day": {"status": False, "days": [1,15]},
        "npp_stop": True,
        "no_parallel_tag_for_npp": False,
        "no_parallel_tag_for_model": False,
        "forced_in_period": False,
    },
    
    "repair-2": {
        "id": 8,
        "status": False,
        "startup_cost": maintence_cost,
        "duration": 10,
        "min_downtime": 0,
        "max_startup": 36,
        "risk_reset": {},
        "risk_reducing": {"r1": 0.2},
        "min": 0,
        "start_day": {"status": False, "days": [1,15]},
        "npp_stop": True,
        "no_parallel_tag_for_npp": False,
        "no_parallel_tag_for_model": False,
        "forced_in_period": False,
    },
    
    "repair-3": {
        "id": 9,
        "status": False,
        "startup_cost": maintence_cost,
        "duration": 10,
        "min_downtime": 0,
        "max_startup": 36,
        "risk_reset": {},
        "risk_reducing": {"r1": 0.2},
        "min": 0,
        "start_day": {"status": False, "days": [1,15]},
        "npp_stop": True,
        "no_parallel_tag_for_npp": False,
        "no_parallel_tag_for_model": False,
        "forced_in_period": False,
    },
    
    "repair-4": {
        "id": 10,
        "status": False,
        "startup_cost": maintence_cost,
        "duration": 10,
        "min_downtime": 0,
        "max_startup": 36,
        "risk_reset": {},
        "risk_reducing": {"r1": 0.2},
        "min": 0,
        "start_day": {"status": False, "days": [1,15]},
        "npp_stop": True,
        "no_parallel_tag_for_npp": False,
        "no_parallel_tag_for_model": False,
        "forced_in_period": False,
    },
            
    "repair-5": {
        "id": 11,
        "status": False,
        "startup_cost": maintence_cost,
        "duration": 10,
        "min_downtime": 0,
        "max_startup": 36,
        "risk_reset": {},
        "risk_reducing": {"r1": 0.2},
        "min": 0,
        "start_day": {"status": False, "days": [1,15]},
        "npp_stop": True,
        "no_parallel_tag_for_npp": False,
        "no_parallel_tag_for_model": False,
        "forced_in_period": False,
    },
    
    "repair-6": {
        "id": 12,
        "status": False,
        "startup_cost": maintence_cost,
        "duration": 10,
        "min_downtime": 0,
        "max_startup": 36,
        "risk_reset": {},
        "risk_reducing": {"r1": 0.2},
        "min": 0,
        "start_day": {"status": False, "days": [1,15]},
        "npp_stop": True,
        "no_parallel_tag_for_npp": False,
        "no_parallel_tag_for_model": False,
        "forced_in_period": False,
    },    
    
    "repair-7": {
        "id": 13,
        "status": False,
        "startup_cost": maintence_cost,
        "duration": 10,
        "min_downtime": 0,
        "max_startup": 36,
        "risk_reset": {},
        "risk_reducing": {"r1": 0.2},
        "min": 0,
        "start_day": {"status": False, "days": [1,15]},
        "npp_stop": True,
        "no_parallel_tag_for_npp": False,
        "no_parallel_tag_for_model": False,
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




outage_base = Scenario_builder({
    "outage_options": {
        "status": False,
    }
})

one_risk_base = Scenario_builder(
    {
        "risk_options": {
            "status": False,
            "risks": {},
        }
    }
)

repair_base = Scenario_builder({
    "repair_options": {
        "status": False,
        "options": base_repair_options,
        }})


events_base_1 = {
    "2025-01-20": 0.10,
    "2025-10-15": 0.1,

    "2026-01-01": 0.15,
    "2026-03-01": 0.08,
    "2026-07-20": 0.11,
    "2026-11-20": 0.2,


    "2027-08-15": 0.09,
    "2027-10-01": 0.10,
    "2027-11-20": 0.12,
}

events_base_2 = {
    "2025-02-01": 0.15,
    "2025-05-01": 0.2,
    "2025-09-01": 0.10,
    "2025-11-01": 0.1,
    "2025-11-15": 0.05,

    "2026-02-10": 0.1,
    "2026-09-10": 0.07,


    "2027-02-15": 0.12,
    "2027-09-15": 0.10,
}


events_base_3 = {
    "2025-01-15": 0.11,
    "2025-02-28": 0.10,
    "2025-04-15": 0.12,
    "2026-05-28": 0.09,
    "2027-07-28": 0.10,
    "2027-09-28": 0.11,
}






one_year = {"years": [2025]}
two_years = {"years": [2025, 2026]}
three_years = {"years": [2025, 2026, 2027]}


# max_duration = 30

outage_jul = outage_base.update_outage({"start_of_month": True, "allow_months": {"Jul"}, "min_duration": 30, "max_duration": 30, "min_work_after_stop": 20})
outage_nov = outage_base.update_outage({"start_of_month": True, "allow_months": {"Nov"}, "min_duration": 30, "max_duration": 30,"min_work_after_stop": 20})

outage_jun_jul_aug = outage_base.update_outage({"start_of_month": True, "allow_months": {"Jun", "Jul", "Aug"}, "min_duration": 30, "max_duration": 30, "min_work_after_stop": 20})

outage_oct_nov_dec = outage_base.update_outage({"start_of_month": True, "allow_months": { "Oct", "Nov", "Dec"}, "min_duration": 30, "max_duration": 30, "min_work_after_stop": 20})

risk_b1 = one_risk_base.update_risk({"r1": {"id": 0, "events": events_base_1, "max": 1, "value": 0.06, "start_risk_rel": 0.3, "max_last_step": 0.8}})
risk_b2 = one_risk_base.update_risk({"r1": {"id": 0, "events": events_base_2, "max": 1, "value": 0.06, "start_risk_rel": 0.4, "max_last_step": 0.8}})


outage_jul_3 = outage_jul.update_outage({"max_duration": 40})
outage_nov_3 = outage_nov.update_outage({"max_duration": 40})

outage_jun_jul_aug_3 = outage_jun_jul_aug.update_outage({"max_duration": 40})
outage_oct_nov_dec_3 = outage_oct_nov_dec.update_outage({"max_duration": 40})

# repair_b1_two_risk = repair_base.update_repair({
#     "maintence-1": {"no_parallel_tag_for_model": 1, "no_parallel_tag_for_npp": 1,  "risk_reducing": {"r1": 0.15, "r2": 0.1}, "min_downtime": 0},
#     "maintence-2": {"no_parallel_tag_for_model": 1, "no_parallel_tag_for_npp": 1,  "risk_reducing": {"r1": 0.1, "r2": 0.15}, "min_downtime": 0},
#     "current-1":   {"no_parallel_tag_for_model": 1, "no_parallel_tag_for_npp": 1,  "risk_reducing": {"r1": 0.60, "r2": 0.50}},
# })

print(f"{maintence_cost=}")
print(f"{current_cost=}")
print(f"{medium_cost=}")
print(f"{capital_cost=}")

def get_r_for_repair(r_maintence, capital_cost):
    maintence_cost, current_cost, medium_cost, capital_cost = get_repair_costs_by_capital(capital_cost)
    r_maintence = r_maintence
    r_current = current_cost / maintence_cost * r_maintence * 1.1
    r_medium = medium_cost / maintence_cost * r_maintence * 1.2
    r_capital = capital_cost / maintence_cost * r_maintence * 1.3
    return r_maintence, r_current, r_medium, r_capital


r_maintence, r_current, r_medium, r_capital = get_r_for_repair(r_maintence=0.1, capital_cost = capital_cost)

print(f"{r_maintence=}")
print(f"{r_current=}")
print(f"{r_medium=}")
print(f"{r_capital=}")

repair_one_risk_1 = repair_base.update_repair({
    "maintence-1": {"no_parallel_tag_for_model": 1, "no_parallel_tag_for_npp": 1,  "risk_reducing": {"r1": r_maintence}, "min_downtime": 30},
    # "maintence-2": {"no_parallel_tag_for_model": 1, "no_parallel_tag_for_npp": 0,  "risk_reducing": {"r1": 0.2}, "duration": 15},
    "current-1":   {"no_parallel_tag_for_model": 1, "no_parallel_tag_for_npp": 1,  "risk_reducing": {"r1": r_current}, "startup_cost": current_cost, "min":0},
    "medium-1":   {"no_parallel_tag_for_model": 1, "no_parallel_tag_for_npp": 1,  "risk_reducing": {"r1": r_medium}, "startup_cost": medium_cost, "min":0},
    })

repair_one_risk_1_ver2 = repair_base.update_repair({
    "maintence-1": {"no_parallel_tag_for_model": 1, "no_parallel_tag_for_npp": 1,  "risk_reducing": {"r1": 0.1}, "min_downtime": 40},
    # "maintence-2": {"no_parallel_tag_for_model": 1, "no_parallel_tag_for_npp": 0,  "risk_reducing": {"r1": 0.2}, "duration": 15},
    "current-1":   {"no_parallel_tag_for_model": 1, "no_parallel_tag_for_npp": 1,  "risk_reducing": {"r1": 0.4}},
})

repair_one_risk_1_ver3 = repair_base.update_repair({
    "maintence-1": {"no_parallel_tag_for_model": 1, "no_parallel_tag_for_npp": 1,  "risk_reducing": {"r1": 0.1}, "min_downtime": 40},
    "current-1":   {"no_parallel_tag_for_model": 1, "no_parallel_tag_for_npp": 1,  "risk_reducing": {"r1": 0.4}},
    "capital-1": {"no_parallel_tag_for_model": 1, "no_parallel_tag_for_npp": 1, "risk_reducing": {"r1": 0.70}, "duration": 40, "forced_in_period": True},
})

repair_one_risk_1_forced_capital = repair_base.update_repair({
    "maintence-1": {"no_parallel_tag_for_model": 1, "no_parallel_tag_for_npp": 1,  "risk_reducing": {"r1": r_maintence}, "min_downtime": 30},
    # "maintence-2": {"no_parallel_tag_for_model": 1, "no_parallel_tag_for_npp": 0,  "risk_reducing": {"r1": 0.2}, "duration": 15},
    "current-1":   {"no_parallel_tag_for_model": 1, "no_parallel_tag_for_npp": 1,  "risk_reducing": {"r1": r_current}, "startup_cost": current_cost, "min":0},
    "capital-1": {"no_parallel_tag_for_model": 1, "no_parallel_tag_for_npp": 1, "risk_reducing": {"r1": r_capital}, "duration": 40, "forced_in_period": True},
})


repair_one_risk_2 = repair_base.update_repair({
    "maintence-1": {"no_parallel_tag_for_model": 1, "no_parallel_tag_for_npp": 1,  "risk_reducing": {"r1": 0.09}, "min_downtime": 30, "startup_cost": maintence_cost  - 2e6},
    "maintence-2": {"no_parallel_tag_for_model": 1, "no_parallel_tag_for_npp": 1,  "risk_reducing": {"r1": 0.16}, "min_downtime": 30},
    "current-1":   {"no_parallel_tag_for_model": 1, "no_parallel_tag_for_npp": 1,  "risk_reducing": {"r1": 0.50}},
    })


risk_b1_2 = one_risk_base.update_risk({"r1": {"id": 0, "events": events_base_2, "max": 1, "value": 0.12, "start_risk_rel": 0.2, "max_last_step": 0.9}})



d1, d2, d3, d4, d5 = 5, 10, 15, 5, 5

def get_separate_r(d1, d2, d3, d4, d5):
    multiplier = 0.5
    r1 = (d1/30)*(multiplier-0.1)
    r2 = (d2/30)*multiplier
    r3 = (d3/30)*multiplier
    r4 = (d4/30)*(multiplier-0.2)
    r5 = (d5/30)*(multiplier-0.3)
    return r1, r2, r3, r4, r5

r1, r2, r3, r4, r5 = get_separate_r(d1, d2, d3, d4, d5)

def get_separate_cost(r1, r2, r3, r4, r5):

    max_r = max(r1, r2, r3, r4, r5)

    c1 = current_cost * (r1/max_r) 
    c2 = current_cost * (r2/max_r)
    c3 = current_cost * (r3/max_r)
    c4 = current_cost * (r4/max_r)
    c5 = current_cost * (r5/max_r)
    return c1, c2, c3, c4, c5

c1, c2, c3, c4, c5 = get_separate_cost(r1, r2, r3, r4, r5)

min_val = 1

repair_one_risk_2 = repair_base.update_repair(
    {
        "maintence-1": {
            "no_parallel_tag_for_model": 1,
            "no_parallel_tag_for_npp": 1,
            "risk_reducing": {"r1": r_maintence},
            "duration": 10,
            "min_downtime": 10,
            "startup_cost": maintence_cost,
        },
        "repair-1": {
            "no_parallel_tag_for_model": 1,
            "no_parallel_tag_for_npp": 1,
            "risk_reducing": {"r1": r1},
            "duration": d1,
            "startup_cost": c1,
            "min": min_val,
        },
        "repair-2": {
            "no_parallel_tag_for_model": 1,
            "no_parallel_tag_for_npp": 1,
            "risk_reducing": {"r1": r2},
            "duration": d2,
            "startup_cost": c2,
            "min": min_val,
        },
        "repair-3": {
            "no_parallel_tag_for_model": 1,
            "no_parallel_tag_for_npp": 1,
            "risk_reducing": {"r1": r3},
            "duration": d3,
            "startup_cost": c3,
            "min": min_val,
        },
        "repair-4": {
            "no_parallel_tag_for_model": 1,
            "no_parallel_tag_for_npp": 1,
            "risk_reducing": {"r1": r4},
            "duration": d4,
            "startup_cost": c4,
            "min": min_val,
        },
        "repair-5": {
            "no_parallel_tag_for_model": 1,
            "no_parallel_tag_for_npp": 1,
            "risk_reducing": {"r1": r5},
            "duration": d5,
            "startup_cost": c5,
            "min": min_val,
        },
    }
)


repair_one_risk_2_forced_capital = repair_one_risk_2.update_repair({
        "capital-1":   {"no_parallel_tag_for_model": 1, "no_parallel_tag_for_npp": 1,  "risk_reducing": {"r1": r_capital}, "duration": 40, "startup_cost": capital_cost, "forced_in_period": True},
})


# scenarios
###############################################################################
# дать представление о возможностях модели


# тест
# 1 - год - 1 блок - 1 риск ++ c событиями
# 1 - год - 1 блок - 1 риск ++ c событиями с разным составом работ во время остановки


# запрет на одновременные ремонты и min_downtime
# 2 - года - 2 блока - 1 риск с событиями   цельные ремонты 
# 2 - года - 2 блока - 1 риск с событиями   цельные ремонты - выбор месяца года + алт maintence
# 2 - года - 2 блока - 1 риск с событиями   последовательный ремонт
# 2 - года - 2 блока - 1 риск с событиями   последовательный ремонт - выбор месяца ремонта + алт maintence


# запрет на одновременные ремонты и min_downtime + обязательный капитальный ремонт
# 3 - года - 2 блока - 1 риск с событиями цельные ремонты
# 3 - года - 2 блока - 1 риск с событиями цельный ремонты + выбора месяца + альт maintence
# 3 - года - 2 блока - 1 риск с событиями последовательный ремонт
# 3 - года - 2 блока - 1 риск с событиями последовательный ремонт + выбор месяца + альт maintence


mip_gap = 0.01

# scen = base | {"№": 1} | one_year | (b_1.update(risk_b1 | repair_one_risk_1_ver2 | outage_jul))
# scen = base | {"№": 2} | one_year | (b_1.update(risk_b1_2 | repair_one_risk_2 | outage_jul))




scen = base | {"№": 3} | two_years | (b_1.update(risk_b1 | repair_one_risk_1 | outage_jul)) | (b_2.update(risk_b2 | repair_one_risk_1 | outage_nov)) 
# scen = base | {"№": 4} | two_years | (b_1.update(risk_b1 | repair_one_risk_1 | outage_jun_jul_aug)) | (b_2.update(risk_b2 | repair_one_risk_1 | outage_oct_nov_dec)) 
# scen = base | {"№": 5} | two_years | (b_1.update(risk_b1 | repair_one_risk_2 | outage_jul)) | (b_2.update(risk_b2 | repair_one_risk_2 | outage_nov)) 
# scen = base | {"№": 6} | two_years | (b_1.update(risk_b1 | repair_one_risk_2 | outage_jun_jul_aug)) | (b_2.update(risk_b2 | repair_one_risk_2 | outage_oct_nov_dec)) 



# scen = base | {"№": 7} | three_years | (b_1.update(risk_b1 | repair_one_risk_1_forced_capital | outage_jul_3)) | (b_2.update(risk_b2 | repair_one_risk_1_forced_capital | outage_nov_3)) 
# scen = base | {"№": 8} | three_years | (b_1.update(risk_b1 | repair_one_risk_1_forced_capital | outage_jun_jul_aug_3)) | (b_2.update(risk_b2 | repair_one_risk_1_forced_capital | outage_oct_nov_dec_3)) 
# scen = base | {"№": 9} | three_years | (b_1.update(risk_b1 | repair_one_risk_2_forced_capital | outage_jul_3)) | (b_2.update(risk_b2 | repair_one_risk_2_forced_capital | outage_nov_3)) 
scen = base | {"№": 10} | three_years | (b_1.update(risk_b1 | repair_one_risk_2_forced_capital | outage_jun_jul_aug_3)) | (b_2.update(risk_b2 | repair_one_risk_2_forced_capital | outage_oct_nov_dec_3)) 









###############################################################################

oemof_model = Oemof_model(
    scenario = scen,
    solver_settings = {
        "solver": "cplex",
        "solver_verbose": True,
        "mip_gap": mip_gap
    } 
)



solution_processor = Solution_processor(oemof_model)
# solution_processor.set_calc_mode(save_results=False)
solution_processor.set_calc_mode(save_results=True)
solution_processor.set_dumps_folder("./dumps")

# solution_processor.set_restore_mode(file_number="100") 
# solution_processor.set_restore_mode(file_number="101") 
# solution_processor.set_restore_mode(file_number="102") 
# solution_processor.set_restore_mode(file_number="103") 

# solution_processor.set_restore_mode(file_number="104") 
# solution_processor.set_restore_mode(file_number="105") 
# solution_processor.set_restore_mode(file_number="106") 
# solution_processor.set_restore_mode(file_number="107") 
solution_processor.set_restore_mode(file_number="108") 



solution_processor.apply()



custom_es = solution_processor.get_custom_model()
oemof_es = solution_processor.get_oemof_es()
results = solution_processor.get_results()



b_1 = custom_es.block_db.get_bel_npp_block_1()
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
        "легкий ремонт-1": {"id": 0, "color": "#fdec02"},
        "легкий ремонт-2": {"id": 1, "color": "#02e0fd"},
        "текущий ремонт-1": {"id": 2, "color": "#0b07f3"},
        "текущий ремонт-2": {"id": 3, "color": "#ff00ff"},
        "средний ремонт-1": {"id": 4, "color": "#ffa600"},
        "средний ремонт-2": {"id": 5, "color": "#0c2450"},
        "капитальный ремонт-1": {"id": 6, "color": "#ff4000"},

        "тип ремонта-1": {"id": 7, "color": "#0b07fc"},
        "тип ремонта-2": {"id": 8, "color": "#ff00b3"},
        "тип ремонта-3": {"id": 9, "color": "#ffa600"},
        "тип ремонта-4": {"id": 10, "color": "#0c2450"},
        # "тип ремонта-4": {"id": 10, "color": "#FBFF00"},
        "тип ремонта-5": {"id": 11, "color": "#ff4000"},
        "тип ремонта-6": {"id": 12, "color": "#12741a"},
        "тип ремонта-7": {"id": 13, "color": "#275f66"},
    },
    repairs_cost_options={
        "БелАЭС (блок 1)-затраты": {"block": b_1, "style":"-", "color": "#18be2f"},
        "БелАЭС (блок 2)-затраты": {"block": b_2, "style":"-", "color": "#1f77b4"},
        "Новая АЭС (блок 1)-затраты": {"block": b_3, "style":"-", "color": "#b4671f"},
    }  
)


result_viewer = Result_viewer(block_grouper)
excel_writer = Excel_writer(block_grouper, solution_processor)
control_block_viewer = Control_block_viewer(block_grouper)


# image_simple = result_viewer.plot_single_block_graph(b_1, dpi=180)
# image_simple = result_viewer.plot_single_block_graph(b_2, dpi=180)
# image_simple = result_viewer.plot_single_block_graph(b_3, dpi=180)

# image_all_block_with_risks = result_viewer.plot_all_blocks_with_risks_graph(outages_graph=True, cost_balance_graph=False, dpi=180)
# image_all_block_with_risks = result_viewer.plot_all_blocks_with_risks_graph(outages_graph=True, cost_balance_graph=True, dpi=140)
# image_all_block_with_risks = result_viewer.plot_all_blocks_with_risks_graph(outages_graph=False, cost_balance_graph=True, dpi=180)


image_all_block_with_cost = result_viewer.plot_all_blocks_with_cost_graph(outages_graph=True, risk_graph=True, dpi=180)
# image_all_block_with_cost = result_viewer.plot_all_blocks_with_cost_graph(outages_graph=True, risk_graph=False, dpi=140)
# image_all_block_with_cost = result_viewer.plot_all_blocks_with_cost_graph(outages_graph=False, risk_graph=True, dpi=180)



# image_all_block_with_risks.save("./images","jpg", 1500)
# image_all_block_with_cost.save("./images","jpg", 1500)


# control_block_viewer.plot_control_stop_block(bel_npp_block_1)
# control_block_viewer.plot_npp_status(bel_npp_block_1)

# control_block_viewer.plot_npp_storage_data(bel_npp_block_1)
# control_block_viewer.plot_repair_storage_max_uptime(bel_npp_block_1, repair_id=1)
# control_block_viewer.plot_repair_storage_max_uptime(bel_npp_block_1, repair_id=2)
# control_block_viewer.plot_repair_storage_max_uptime(bel_npp_block_1, repair_id=3)
# control_block_viewer.plot_repair_storage_max_uptime(bel_npp_block_1, repair_id=5)
 

# result_viewer.create_scheme("./schemes")
# image_all_block_with_risks.save("./images","jpg", 600)
# image_all_block_with_cost.save("./images","jpg", 600)


excel_writer.write("./excel_results")

print("done")


# фото с ноутбука
# сделать расчет с ноутбука
# блок-схема











# список сценариев
# компактная таблица дя описания сценария
# моника - разработанная модель - структура отчета
# таблица для Трифонова плановые остановки затраты, время
# время расчета, точность, по в отчет
# ключевые формулировки актульности (моника)
# формализованная блок-схема расчет
# дальнейшенее развитие
# принцип реализации
# актуальность и полезность
# модель с тестовыми данными
# введение в лп
# неравенства через монику
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
















