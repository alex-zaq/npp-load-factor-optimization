import datetime
import os

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt

all_months = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
]


start_day_by_month = {
    "Jan": [1, 15],
    "Feb": [1, 15],
    "Mar": [1, 15],
    "Apr": [1, 15],
    "May": [1, 15],
    "Jun": [1, 15],
    "Jul": [1, 15],
    "Aug": [1, 15],
    "Sep": [1, 15],
    "Oct": [1, 15],
    "Nov": [1, 15],
    "Dec": [1, 15],
}


def get_full_filename(folder, startswith):
    for file in os.listdir(folder):
        if file.startswith(startswith):
            return file
    return None


def get_number(number):
    if number < 10:
        return f"0{number}"
    else:
        return str(number)
    
    
def get_next_number_file_name(folder):
    files = os.listdir(folder)
    files = [file for file in files if file.endswith(".oemof")]
    if not files:
        return 0
    number_files = [int(file.split("_")[0]) for file in files]
    res = max(number_files) + 1
    return res

def get_dumps_file_name(self, scenario):
    scen_number = scenario["№"]
    scen_name = scenario["name"]
    start_year = scenario["years"][0]
    end_year = scenario["end_year"][-1]
    active_npp_count = get_npp_block_active_count_by_scen(scenario)
    file_name = "_".join(
        [scen_number, scen_name, start_year, end_year, active_npp_count]
    )
    return file_name

def get_file_name_with_auto_number(dumps_folder, scenario, ext):
    next_number = get_number(get_next_number_file_name(dumps_folder))
    file_name = f"{get_dumps_file_name(scenario)}.{ext}"
    res = [next_number, file_name]
    res = "_".join(res)
    return res

def set_label(*items, sep="_"):
    if not items:
        return ""
    else:
        items = list(filter(lambda x: x, items))

    return sep.join(items)

def plot_array(arr):
    plt.plot(arr, linewidth=1)
    plt.margins(x=0, y=0)
    plt.show(block=True)





def get_risk_events_profile(start_year, end_year, events):
    t_delta = pd.to_datetime(f"{end_year}-01-01") - pd.to_datetime(f"{start_year}-01-01")
    num_hours = t_delta.days * 24
    profile = np.zeros(num_hours)
    for event in events.values():
        start_idx = int((pd.to_datetime(event["start_datetime"]) - pd.to_datetime(f"{start_year}-01-01")).total_seconds() // 3600)
        risk_per_hour = event["risk_increase"] / event["duration_hours"]
        profile[start_idx:start_idx + event["duration_hours"]] += risk_per_hour
    return profile





def get_valid_profile_by_months(start_year, end_year, months):
    t_delta = pd.to_datetime(f"{end_year}-01-01") - pd.to_datetime(f"{start_year}-01-01")
    num_hours = t_delta.days * 24
    profile = np.zeros(num_hours)
    date_range = pd.date_range(start=f"{start_year}-01-01", end=f"{end_year}-01-01", freq="H", inclusive="left"
    )
    for month in months:
        profile[date_range.month == pd.to_datetime(month, format='%b').month] = 1
    return profile




def get_profile_with_first_day(start_year, end_year):
    t_delta = datetime.datetime(end_year, 1, 1) - datetime.datetime(start_year, 1, 1)
    num_hours = int(t_delta.total_seconds() // 3600)
    profile = np.zeros(num_hours)
    for year in range(start_year, end_year):
        start_of_year_idx = (datetime.datetime(year, 1, 1) - datetime.datetime(start_year, 1, 1)).days * 24
        profile[start_of_year_idx] = 1
    return profile


def get_profile_by_month_day_dict(start_year, end_year, month_days):
    
    # задаем порядковые дни для каждого месяца
    if list(month_days.keys()) != all_months:
        raise Exception("Months are not the same")    
    
    res = {}
    for month in month_days:
        for order in month_days[month]:
            date = pd.to_datetime(f"{start_year}-{month}-{order}")- pd.Timedelta(days=1)
            if date.month not in res:
                res[date.month] = []
            # if date.year == start_year:
            res[date.month].append(date.day)
                
                
    t_delta = pd.to_datetime(f"{end_year}-01-01") - pd.to_datetime(f"{start_year}-01-01")
    num_hours = t_delta.days * 24
    date_range = pd.date_range(start=f"{start_year}-01-01", end=f"{end_year}-01-01", freq="H", inclusive="left")
    profile = np.zeros(num_hours)
    for month_order, day_number_series in res.items():
        for day_number in day_number_series:
            profile[(date_range.month == month_order) & (date_range.hour == 23) & (date_range.day == day_number)] = 1

    return profile


def get_profile_by_month_day_dict_many_years(start_year, end_year, month_days):
    year_seq = list(range(start_year, end_year))
    if len(year_seq) < 2:
        raise Exception("Too few years")
    year_seq_res = {}
    for year in year_seq:
        year_seq_res[year] = get_profile_by_month_day_dict(year, year + 1, month_days)
    profile = np.concatenate(list(year_seq_res.values()))
    return profile 


def get_profile_by_day(start_year, end_year, day_numbers):
    day_numbers = {month: day_numbers for month in all_months}
    profile = get_profile_by_month_day_dict(start_year, end_year, day_numbers)
    return profile


def get_profile_by_period_for_charger(start_year, end_year, day_numbers):
    if isinstance(day_numbers, list):
        return get_profile_by_day(start_year, end_year, day_numbers)
    if isinstance(day_numbers, dict):
        return get_profile_by_month_day_dict(start_year, end_year, day_numbers)
    


def check_sequential_years(years):
    return all(years[i] - years[i - 1] == 1 for i in range(1, len(years)))
            
            
def hours_between_years(start_year, end_year):
    start_date = datetime.datetime(start_year, 1, 1)
    end_date = datetime.datetime(end_year + 1, 1, 1)
    delta = end_date - start_date
    hours = delta.total_seconds() / 3600
    return hours
 
 
def get_npp_block_active_count_by_scen(scen):
    return sum(1 for k, v in scen.items() if "block" in k and v["active"])
 
 
def get_time_pairs_lst(start_year, end_year, start_repair_days_lst):
    profile = get_profile_by_period_for_charger(start_year, end_year, start_repair_days_lst)
    converter_start_hours = np.nonzero(profile)[0].astype(int).flatten()
    res = []
    for i in converter_start_hours:
        res.append((i, i + 1))
    return res
