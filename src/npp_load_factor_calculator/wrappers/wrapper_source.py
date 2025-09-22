from oemof import solph

from src.npp_load_factor_calculator.wrappers.wrapper_base import Wrapper_base


class Wrapper_source(Wrapper_base):
    
    def __init__(self, es, label):
        super().__init__(es, label)
        
        
    def create_wrapper_source_builder(self, es, label):
        return self.__class__(es, label)
    
    
    def create_wrapper_converter_builder(self, es, label):
        import src.npp_load_factor_calculator.wrappers.wrapper_converter as wrapper_converter
        return wrapper_converter.Wrapper_converter(es, label)
        
        
    def get_pair_after_building(self):
        output_bus = self.options["output_bus"]
        source = self.build()
        return source, output_bus
    
    def add_keyword_to_flow(self, keyword):
        if hasattr(self, "_output_flow"):
            setattr(self._output_flow, keyword, True)
        else:
            self.keywords[keyword] = True
        
        
    def get_main_flow(self):
        if hasattr(self, "_output_flow"):
            return self._output_flow
        else:
            return None

       
    def build(self):
        if self.block:
            return self.block
        
        self._output_flow = self.get_nonconvex_flow()
        
        self.block = solph.components.Source(
            label=self.label,
            outputs={self.options["output_bus"]: self._output_flow},
        )
        
        self.block.outputs_pair = [(self.block, self.options["output_bus"])]

        self.es.add(self.block)
        self._set_info_to_block()
        self._apply_constraints()

        return self.block