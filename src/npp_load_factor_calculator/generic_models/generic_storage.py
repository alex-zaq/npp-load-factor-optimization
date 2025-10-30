from oemof import solph


class Generic_storage:

    def __init__(self, oemof_es):
        self.es = oemof_es
    
    def create_storage(
        self,
        label,
        input_bus,
        output_bus,
        capacity,
        initial_storage_level,
        max_storage_level
    ):
              
        # initial_storage_level = initial_storage_level if initial_storage_level else None
        
           
        storage = solph.components.GenericStorage(
            label=label,
            nominal_storage_capacity=capacity,
            initial_storage_level=initial_storage_level,
            inputs={input_bus: solph.Flow()},
            outputs={output_bus: solph.Flow()},
            balanced=False,
            max_storage_level=max_storage_level
        )
        
        storage.inputs_pair = [(input_bus, storage)]
        storage.outputs_pair = [(storage, output_bus)]

        self.es.add(storage)
        return storage