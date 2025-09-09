from src.npp_load_factor_calculator.utilites import all_months, check_unig_seq

events = {
    "event_1": {
        "start_datetime": "2025-01-01 00:00:00",
        "risk_increase": 0.1,
        "duration_hours": 1,
        "repair_types": ("light",),
    },
    "event_2": {
        "start_datetime": "2025-02-01 00:00:00",
        "risk_increase": 0.2,
        "duration_hours": 1,
        "repair_types": ("light",),

    },
    
    "event_3": {
        "start_datetime": "2025-03-15 06:00:00",
        "risk_increase": 0.3,
        "duration_hours": 1,
        "repair_types": ("light",),
    },
    "event_4": {
        "start_datetime": "2025-04-22 18:00:00",
        "risk_increase": 0.4,
        "duration_hours": 1,
        "repair_types": ("light",),
    },
    "event_5": {
        "start_datetime": "2025-05-01 12:00:00",
        "risk_increase": 0.5,
        "duration_hours": 1,
        "repair_types": ("light",),
    },
    "event_6": {
        "start_datetime": "2025-06-11 09:00:00",
        "risk_increase": 0.3,
        "duration_hours": 1,
        "repair_types": ("light",),
    },
    "event_7": {
        "start_datetime": "2025-07-01 00:00:00",
        "risk_increase": 0.2,
        "duration_hours": 1,
        "repair_types": ("light",),
    },
    "event_8": {
        "start_datetime": "2025-08-15 06:00:00",
        "risk_increase": 0.4,
        "duration_hours": 1,
        "repair_types": ("light",),
    },
    "event_9": {
        "start_datetime": "2025-09-22 18:00:00",
        "risk_increase": 0.5,
        "duration_hours": 1,
        "repair_types": ("light",),
    },
    "event_10": {
        "start_datetime": "2025-10-01 12:00:00",
        "risk_increase": 0.6,
        "duration_hours": 1,
        "repair_types": ("light",),
    },
    "event_11": {
        "start_datetime": "2025-11-11 09:00:00",
        "risk_increase": 0.4,
        "duration_hours": 1,
        "repair_types": ("light",),
    },
    "event_12": {
        "start_datetime": "2025-12-01 00:00:00",
        "risk_increase": 0.7,
        "duration_hours": 1,
        "repair_types": ("light",),
    },
}

assert check_unig_seq(events)


repair_options = {
    "light": {
        "id": 0,
        "status": True,
        "cost": 100,
        "duration": 14,
        "risk_reducing": 2,
        "start_day": {"status": True, "days": [1, 15]},
        "max_count_in_year": {"status": False, "count": 1},
        "avail_months": all_months,
        "npp_stop": False,
    },
    "medium": {
        "id": 1,
        "status": False,
    },
    "heavy": {
        "id": 2,
        "status": False,

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
            "min_up_time": 0,
            "min_down_time": 0,
            "upper_bound_risk": 2,
            "allow_no_cost_mode": True,
            "default_risk_options": {},
            "events": events,
            "repair_options": repair_options,
        },
        "bel_npp_block_2": {
            "status": False,
        },
        "new_npp_block_1": {
            "status": False,
        },
}


year_1_block_1_risk_1_repair_1 = {
    "scenario": scen,
    "events": events,
}