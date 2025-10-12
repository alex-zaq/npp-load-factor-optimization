

import numpy as np
import pandas as pd

from src.npp_load_factor_calculator.utilites import zero_inner_ones


class Resolution_strategy:
    
    def __init__(self, timeindex):
        self.timeindex = timeindex
        
    @classmethod
    def create_strategy(cls, strategy_name, timeindex):
        match strategy_name:
            case "H":
                return Hourly_resolution_strategy(timeindex)
            case "D":
                return Daily_resolution_strategy(timeindex)
            case _:
                raise NotImplementedError
        
    def convert_time(self, timeintervals):
        raise NotImplementedError

    def convert_risk(self, risk_month_val):
        raise NotImplementedError
    
    def convert_power(self, power):
        raise NotImplementedError
    
    def get_profile_by_events(self):
        raise NotImplementedError
    
    def get_first_step_every_year_mask(self):
        raise NotImplementedError
    
    def get_mask_from_first_day_of_month(self, month, duration):
        raise NotImplementedError
            
    def get_fix_months_profile(self, selected_months):
        res = np.ones(len(self.timeindex))
        for month in selected_months:
            res[self.timeindex.month == pd.to_datetime(month, format='%b').month] = 0
        return res
    
    def get_avail_months_profile(self, selected_months):
        res = np.zeros(len(self.timeindex))
        for month in selected_months:
            res[self.timeindex.month == pd.to_datetime(month, format='%b').month] = 1
        return res
    
    def get_every_year_first_step_mask(self):
        raise NotImplementedError
    
    def get_start_points(self):
        raise NotImplementedError
    
    def get_last_step_mask(self):
        res = np.zeros(len(self.timeindex))
        res[-1] = 1
        return res
    
    def get_months_start_points(self):
        raise NotImplementedError
    
    
class Hourly_resolution_strategy(Resolution_strategy):
    
    def __init__(self, timeindex):
        super().__init__(timeindex)
        self.coeff = 1
        
    def convert_time(self, timeintervals):
        return timeintervals * 24

    def convert_risk(self, risk_month_val):
        return risk_month_val/30/24
    
    def convert_power(self, power):
        return power
    
    def get_first_step_every_year_mask(self):
        res = np.zeros(len(self.timeindex))
        res[(self.timeindex.day == 1) & (self.timeindex.hour == 0)] = 1
        res[0] = 0
        return res
    
    def get_profile_by_events(self, events):
        num_hours = len(self.timeindex)
        profile = np.zeros(num_hours)
        for event in events:
            start_idx = int((pd.to_datetime(event) - self.timeindex[0]).total_seconds() // (3600))
            risk_per_hour = events[event]
            profile[start_idx] += risk_per_hour
        return profile

    def get_every_year_first_step_mask(self):
        res = np.zeros(len(self.timeindex))
        res[(self.timeindex.hour == 0) & (self.timeindex.day == 1) & (self.timeindex.month == 1)] = 1
        res[0] = 0
        return res
    
    def get_mask_from_first_day_of_month(self, duration):
        raise NotImplementedError
    
    def get_start_points(self, start_days_of_month_lst):
        res = np.zeros(len(self.timeindex))
        for day in start_days_of_month_lst:
            res[(self.timeindex.day == day) & (self.timeindex.hour == 0)] = 1
        return res
    
    def get_months_start_points(self):
        res = np.zeros(len(self.timeindex))
        res[(self.timeindex.day == 1) & (self.timeindex.hour == 0)] = 1
        return res
    

class Daily_resolution_strategy(Resolution_strategy):
    
    def __init__(self, timeindex):
        super().__init__(timeindex)
        self.coeff = 24
        
    def convert_time(self, timeintervals):
        return timeintervals
    
    def convert_risk(self, risk_month_val):
        return risk_month_val/30/24
    
    def convert_power(self, power):
        return power * 24
        
    
    def get_first_step_every_year_mask(self):
        res = np.zeros(len(self.timeindex))
        res[(self.timeindex.day == 1) & (self.timeindex.hour == 0) & (self.timeindex.month == 1)] = 1
        res[0] = 0
        return res
        
    def get_last_step_every_year_mask(self):
        res = np.zeros(len(self.timeindex))
        res[(self.timeindex.day == 31)  & (self.timeindex.month == 12)] = 1
        res[0] = 0
        return res
    
        
    def get_profile_by_events(self, events):
        num_hours = len(self.timeindex)
        profile = np.zeros(num_hours)
        for event in events:
            start_idx = int((pd.to_datetime(event) - self.timeindex[0]).total_seconds() // (3600*24))
            risk_per_hour = events[event]
            profile[start_idx] += risk_per_hour
        return profile
    
    def get_every_year_first_step_mask(self):
        res = np.zeros(len(self.timeindex))
        res[(self.timeindex.day == 1) & (self.timeindex.month == 1)] = 1
        res[0] = 0
        return res
    
    def get_mask_from_first_day_of_month(self, month, duration):
        month_num = pd.to_datetime(month, format='%b').month
        res = np.zeros(len(self.timeindex))
        mask = (self.timeindex.day == 1) & (self.timeindex.month == month_num)
        res[mask] = 1
        indexes = np.where(res == 1)[0]
        for index in indexes:
            res[index:index + duration] = 1
        return res
    
        
    def get_grad_mask(self, month, duration):
        res = self.get_mask_from_first_day_of_month(month, duration)
        res = zero_inner_ones(res)
        return res
    
    def get_start_points(self, start_days_of_month_lst):
        res = np.zeros(len(self.timeindex))
        for day in start_days_of_month_lst:
            res[(self.timeindex.day == day)] = 1
        return res
    
    def get_months_start_points(self):
        res = np.zeros(len(self.timeindex))
        res[(self.timeindex.day == 1)] = 1
        return res