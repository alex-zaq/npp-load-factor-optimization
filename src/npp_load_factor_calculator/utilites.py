import datetime
import itertools
import os
from collections import Counter

import matplotlib
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt

all_months = {
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
}


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

def get_dumps_file_name(scenario):
    scen_number = str(scenario["№"])
    scen_name = scenario["name"]
    start_year, end_year = scenario["years"][0], scenario["years"][-1]
    years = str(start_year) if start_year == end_year else f"{start_year}-{end_year}"
    active_npp_count = f"npp_count_{str(get_npp_block_active_count_by_scen(scenario))}"
    # default_str = get_default_str(scenario)
    # repair_conf_str = get_repair_conf_str(scenario)
    res = [scen_number, scen_name, years, active_npp_count]
    res = [item for item in res if item]
    file_name = "_".join(res)
    return file_name


def get_default_str(scenario):
    res = ''
    if  sum(scenario[key]["risk_per_hour"] for key in scenario if "block" in key and scenario[key]["status"]):
        res = "default"
    return res


def get_repair_conf_str(scenario):
    res = []
    for i in range(3):
        for key in scenario:
            if "block" in key and scenario[key]["status"]:
                for repair_type in scenario[key]["repair_options"]:
                    if scenario[key]["repair_options"][repair_type]["status"] and scenario[key]["repair_options"][repair_type]["id"] == i:
                        res.append(int(scenario[key]["repair_options"][repair_type]["status"]))
                        
        if repair_status_sum := sum(res):
            res[i] = bool(repair_status_sum)  
    res = sum(res.values()) * "l" if res else ""
    return res



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

def plot_array(arr, date_time_index=None):
    if date_time_index is not None:
        plt.plot(date_time_index, arr, linewidth=1)
    else:
        plt.plot(arr, linewidth=1)
    plt.margins(x=0, y=0)
    plt.show(block=True)


def plot_array_from_dict(dct):
    dct = {",".join(k): v for k, v in dct.items()}
    df = pd.DataFrame(dct)
    df.plot(kind="line", linewidth=1, legend=False)
    plt.margins(x=0, y=0)
    plt.ylim(0, df.max().max() * 1.2)
    plt.xlabel("Время, часы")
    plt.ylabel("Условные единицы повышения риска")
    plt.legend(loc='upper center', ncol=len(dct))
    plt.show(block=True)



def plot_array_from_dict_cumsum(dct):
    dct = {",".join(k): v for k, v in dct.items()}
    df = pd.DataFrame(dct)
    df = df.cumsum()
    df.plot(kind="line", linewidth=1, legend=False)
    plt.margins(x=0, y=0)
    plt.ylim(0, df.max().max() * 1.2)
    plt.xlabel("Время, часы")
    plt.ylabel("Условные единицы повышения риска")
    plt.legend(loc='upper center', ncol=len(dct))
    plt.show(block=True)



first_time_step = datetime.datetime(2025, 1, 1)
t_delta = datetime.datetime(2025 + 1, 1, 1) - first_time_step
date_timeindex = pd.date_range(first_time_step, periods=365, freq="D")



def get_risk_events_profile(date_range, events):
    num_hours = len(date_range)
    profile = np.zeros(num_hours)

    for event in events:
        start_idx = int((pd.to_datetime(event) - date_range[0]).total_seconds() // (3600 * 24))
        risk_per_hour = events[event]
        profile[start_idx] += risk_per_hour
        
    return profile


def add_white_spaces_and_colors_el_gen(df, value):
    
    new_df = pd.DataFrame()
    new_colors = []
    colors = df.colors
    for i,col in enumerate(df.columns):
        new_df.insert(len(new_df.columns), f"{col}", df.iloc[:, i], True)
        new_colors.append(colors[i])
        if df.iloc[:, i].min() < value:
            new_df.insert(len(new_df.columns), f"{col}_white_spaces", value - df.iloc[:, i], True)
            new_colors.insert(len(new_colors) - 1 + 1, "white")
    
    new_df.colors = new_colors
    return new_df

def add_white_spaces_and_colors_repairs(dict_value, value):
    
    new_df = pd.DataFrame()
    new_colors = []

    for key, df_item in dict_value.items():

        new_colors.extend(df_item.colors)
        for col in df_item.columns:
            new_df.insert(len(new_df.columns), f"{col}", df_item[col], True)

        buf = df_item.sum(axis = 1).to_frame()
        # print(buf)

        if buf.iloc[:, 0].min() < value:
            df_insert = value - buf.iloc[:, 0]
            new_df.insert(len(new_df.columns), f"{key}_white_spaces", df_insert, True)
            # new_colors.insert(len(new_colors) - 1 + 1, (1,0,0,0)) 
            new_colors.insert(len(new_colors) - 1 + 1, df_item.block_color) 
    
    new_df.clip(lower=0)
    new_df[new_df < 0] = 0
    new_df.colors = new_colors
    return new_df
    



def get_profile_for_all_repair_types(start_year, end_year, events):
    res = {}
    check_set = set([event["repair_types"] for event in events.values()])
    for repair_type in check_set:
        filtered_events_dict = {key: value for key, value in events.items() if repair_type == value["repair_types"]}
        res[repair_type] = get_risk_events_profile(start_year, end_year, filtered_events_dict)
    return res



def check_unig_seq(seq):
    dates = [v["start_datetime"] for k,v in seq.items()]
    return len(dates) == len(set(dates))


def get_selected_month_profile(start_year, end_year, selected_months):
    t_delta = pd.to_datetime(f"{end_year}-01-01") - pd.to_datetime(f"{start_year}-01-01")
    num_hours = t_delta.days * 24
    profile = np.zeros(num_hours)
    date_range = pd.date_range(start=f"{start_year}-01-01", end=f"{end_year}-01-01", freq="H", inclusive="left"
    )
    for month in selected_months:
        profile[date_range.month == pd.to_datetime(month, format='%b').month] = 1
    return profile



def get_fix_months_profile(date_range, selected_months):
    res = np.ones(len(date_range))
    for month in selected_months:
        res[date_range.month == pd.to_datetime(month, format='%b').month] = 0
    return res

def get_avail_months_profile(date_range, selected_months):
    res = np.zeros(len(date_range))
    for month in selected_months:
        res[date_range.month == pd.to_datetime(month, format='%b').month] = 1
    return res

def get_months_start_points(date_range):
    res = np.zeros(len(date_range))
    res[(date_range.day == 1) & (date_range.hour == 0)] = 1
    return res

def get_start_points(date_range, start_days_of_month_lst):
    res = np.zeros(len(date_range))
    for day in start_days_of_month_lst:
        res[(date_range.day == day) & (date_range.hour == 0)] = 1
    return res

def get_every_year_first_step_mask(date_range):
    res = np.zeros(len(date_range))
    res[(date_range.hour == 0) & (date_range.day == 1) & (date_range.month == 1)] = 1
    res[0] = 0
    return res

def get_last_step_mask(date_range):
    res = np.zeros(len(date_range))
    res[-1] = 1
    return res



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
    

def get_main_risk_by_inner_types(events_lst):
    pass



def check_sequential_years(years):
    return all(years[i] - years[i - 1] == 1 for i in range(1, len(years)))
            
            
def hours_between_years(start_year, end_year):
    start_date = datetime.datetime(start_year, 1, 1)
    end_date = datetime.datetime(end_year + 1, 1, 1)
    delta = end_date - start_date
    hours = delta.total_seconds() / 3600
    return hours
 
 
def get_npp_block_active_count_by_scen(scen):
    return sum(1 for k, v in scen.items() if "block" in k and v["status"])
 
 
def get_time_pairs_lst(start_year, end_year, start_repair_days_lst):
    profile = get_profile_by_period_for_charger(start_year, end_year, start_repair_days_lst["start_day"]["days"])
    converter_start_hours = np.nonzero(profile)[0].astype(int).flatten()
    res = []
    for i in converter_start_hours:
        res.append((i, i + 1))
    return res


def get_repair_mode_for_block(block_options):
    return bool(sum(repair_type_val["status"] for repair_type_val in block_options["repair_options"].values()))


def center_matplotlib_figure(fig, extra_x=0, extra_y=0):
    
    manager = fig.canvas.manager
    # backend = matplotlib.get_backend()

    window = manager.window

    # Важно: Обновляем задачи окна, чтобы убедиться, что его размеры актуальны
    # перед получением размеров экрана и расчетом позиции.
    window.update_idletasks()

    # Получаем разрешение экрана с помощью методов Tkinter
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()

    # Получаем размеры графика в пикселях.
    # fig.get_size_inches() возвращает размеры фигуры в дюймах.
    # Умножаем на DPI (точек на дюйм) фигуры, чтобы получить пиксели.
    fig_width_px = int(fig.get_size_inches()[0] * fig.dpi)
    fig_height_px = int(fig.get_size_inches()[1] * fig.dpi)

    # Вычисляем координаты для центрирования окна
    x = (screen_width - fig_width_px) // 2 + extra_x
    y = (screen_height - fig_height_px) // 2 + extra_y

    # Устанавливаем геометрию окна. Формат строки: "ширинаxвысота+x+y"
    window.geometry(f"{fig_width_px}x{fig_height_px}+{x}+{y}")

def get_combinations(a):
    combinations = []
    for r in range(1, len(a) + 1):
        combinations.extend(itertools.combinations(a, r))
    return combinations


def get_r(val):
    return val/30/24
    
def days_to_hours(val):
    return val * 24

    
def months_to_hours(val):
    return val * 24

def zero_middle_ones(arr):
    result = arr.copy()
    in_segment = False
    start = 0
    for i in range(len(arr)):
        if arr[i] == 1 and not in_segment:
            in_segment = True
            start = i
        elif arr[i] == 0 and in_segment:
            in_segment = False
            if start < i-1:
                result[start+1:i-1] = 0
    # Если сегмент единиц длиной до конца массива
    if in_segment and start < len(arr)-1:
        result[start+1:] = 0
    return result



def zero_inner_ones(arr):

    n = len(arr)
    result = [0] * n  # Создаем новый массив, заполненный нулями, той же длины
    i = 0
    while i < n:
        if arr[i] == 1:
            # Найдено начало блока единиц
            result[i] = 1  # Первая единица в блоке остается единицей

            # Находим конец блока единиц
            end_of_block_index = i
            while end_of_block_index + 1 < n and arr[end_of_block_index + 1] == 1:
                end_of_block_index += 1

            # Если есть позиция сразу после блока единиц, ставим там единицу
            if end_of_block_index + 1 < n:
                result[end_of_block_index + 1] = 1

            # Перемещаем указатель 'i' за текущий блок, чтобы продолжить поиск
            i = end_of_block_index + 1
        else:
            # Если текущий элемент 0, он остается 0 (поскольку result уже инициализирован нулями)
            i += 1
    return result

my_array = [0,0,1,1,1,1,1,1,1,1,1,0,0,0,0]
transformed_array = zero_inner_ones(my_array)
print(transformed_array) # Выведет: [0, 0, 1, 0, 0, 1, 0]