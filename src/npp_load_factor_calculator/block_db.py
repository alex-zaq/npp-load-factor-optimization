



class Block_db:
    def __init__(self):
        self.db = {"аэс": [], "потребитель ээ": []}
                
    def add_block(self, block_type, block):
        
        if block_type not in self.db:
            raise ValueError(f"Invalid block type: {block_type}")
        
        self.db[block_type].append(block)
        
        
    def _get_block_by_label(self, block_type, label):
        for block in self.db[block_type]:
            if block.label == label:
                return block
        raise ValueError(f"Block with label {label} not found in {block_type}")
    
    
    def get_bel_npp_block_1(self):
        return self._get_block_by_label("аэс", "БелАЭС (блок 1)")
    
    
    def get_bel_npp_block_2(self):
        return self._get_block_by_label("аэс", "БелАЭС (блок 2)")
    
    
    def get_new_npp_block_1(self):
        return self._get_block_by_label("аэс", "Новая АЭС (блок 1)")
    
 