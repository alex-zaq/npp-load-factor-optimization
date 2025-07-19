import os
import pprint

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


def get_valid_profile_by_day_numbers(start_year, end_year, day_numbers):
    t_delta = pd.to_datetime(f"{end_year}-01-01") - pd.to_datetime(f"{start_year}-01-01")
    num_hours = t_delta.days * 24
    profile = np.zeros(num_hours)
    date_range = pd.date_range(start=f"{start_year}-01-01", end=f"{end_year}-01-01", freq="H", inclusive="left"
    )
    for day_number in day_numbers:
            profile[(date_range.day == day_number) & (date_range.hour == 1)] = 1
            # profile[(date_range.day == day_number)] = 1
            
      
            
            
    count = np.count_nonzero(profile)
    print(f"count = {count}")
            
    return profile

l = get_valid_profile_by_day_numbers(2025,2026, (15,1))
print(l)
plot_array(l)