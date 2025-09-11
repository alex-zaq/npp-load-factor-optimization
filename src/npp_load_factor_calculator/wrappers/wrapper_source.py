from collections import deque

from oemof import solph


class Wrapper_source:
    
    def __init__(self, es):
        self.es = es
        self.queue = deque()
        
    def set_options(self, options):
        pass
        
    def add_min_active_status(self, start, finish, length):
        pass
    
    def add_min_inactive_status(self, start, finish, length):
        pass
                
    def add_general_status(wrapper_block):
        pass
    
    def add_equal_status_constr(wrapper_block):
        pass
       
    def build():
        pass