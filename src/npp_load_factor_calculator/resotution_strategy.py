

class Base_resotution_strategy():
    def __init__(self, timeindex):
        self.time_index = timeindex
        
    def get_fix_months_profile(self):
        raise NotImplementedError
    
    def get_avail_months_profile(self):
        raise NotImplementedError
    
    def get_every_year_first_step_mask(self):
        raise NotImplementedError
    
    def get_start_points(self):
        raise NotImplementedError
    
    def get_last_step_mask(self):
        raise NotImplementedError
    
    def get_months_start_points(self):
        raise NotImplementedError
    
    def check_sequential_years(self):
        raise NotImplementedError
    
    
class Hourly_resotution_strategy(Base_resotution_strategy):
    pass

class Daily_resotution_strategy(Base_resotution_strategy):
    pass
    