def add_spinning_reserve_constraint_fast_only(om, sources, output_bus, min_reserve, fast_start_time=1):
    """
    Учитывает только блоки, которые могут быстро запуститься.
    
    Параметры:
    ----------
    fast_start_time : int
        Максимальное время запуска для "быстрых" блоков (в часах)
    """
    from pyomo.environ import Constraint
    
    def spinning_reserve_rule(m, t):
        total_available_capacity = 0
        total_used_capacity = 0
        
        for source in sources:
            flow = source.outputs[output_bus]
            
            # Проверяем, является ли блок "быстрым"
            # (можно добавить атрибут startup_time к блоку)
            is_fast = getattr(source, 'startup_time', 0) <= fast_start_time
            
            if not is_fast:
                continue  # Пропускаем медленные блоки
            
            nominal_power = flow.nominal_value
            actual_power = m.flow[source, output_bus, t]
            
            if hasattr(flow, 'nonconvex') and flow.nonconvex:
                status = m.NonConvexFlowBlock.status[source, output_bus, t]
                available_power = nominal_power * status
            else:
                available_power = nominal_power
            
            total_available_capacity += available_power
            total_used_capacity += actual_power
        
        reserve = total_available_capacity - total_used_capacity
        
        if isinstance(min_reserve, dict):
            min_res = min_reserve[t]
        else:
            min_res = min_reserve
        
        return reserve >= min_res
    
    setattr(om, 'spinning_reserve_constraint', 
            Constraint(om.TIMESTEPS, rule=spinning_reserve_rule))
    
    return om

# # Пример: помечаем блоки как быстрые/медленные
# generators[0].startup_time = 0.5  # Быстрый (30 минут)
# generators[1].startup_time = 0.5  # Быстрый
# generators[2].startup_time = 2    # Медленный (2 часа)
# generators[3].startup_time = 1    # Средний
# generators[4].startup_time = 3    # Медленный

# model = add_spinning_reserve_constraint_fast_only(
#     model, 
#     generators, 
#     el_bus, 
#     MIN_RESERVE,
#     fast_start_time=1  # Только блоки с запуском ≤ 1 час
# )