from oemof import solph

from src.npp_load_factor_calculator.wrappers.wrapper_base import Wrapper_base


class Wrapper_converter(Wrapper_base):
    
    def __init__(self, es, label):
        super().__init__(es, label)
        
        
    def create_wrapper_source_builder(self, es, label):
        import src.npp_load_factor_calculator.wrappers.wrapper_source as wrapper_source
        return wrapper_source.Wrapper_source(es, label)
    
    
    def create_wrapper_converter_builder(self, es, label):
        return self.__class__(es, label) 
        
        
    def get_pair_after_building(self):
        output_bus = self.options["output_bus"]
        converter = self.build()
        return converter, output_bus


    def add_keyword_to_flow(self, keyword):
        if hasattr(self, "flow"):
            setattr(self.flow, keyword, True)
        else:
            self.keywords[keyword] = True


    def get_main_flow(self):
        if hasattr(self, "_output_flow"):
            return self.flow
        else:
            return None

            
    def build(self):
        if self.block:
            return self.block
        
        self._input_flow = solph.Flow()
        self._output_flow = self.get_nonconvex_flow()

        
        input_bus = self.options["input_bus"]
        output_bus = self.options["output_bus"]

        self.block = solph.components.Converter(
            label=self.label,
            inputs={input_bus: self._input_flow},
            outputs={output_bus: self._output_flow},
        )
        
        self.block.inputs_pair = [(input_bus, self.block)]
        self.block.outputs_pair = [(self.block, output_bus)]        

        self.es.add(self.block)
        self._set_info_to_block()
        self._apply_constraints()

        return self.block
        
        
        