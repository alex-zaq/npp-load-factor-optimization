from oemof import solph
import pandas as pd


def set_equate_flow_by_keyword(model, keyword_1, keyword_2):
    solph.constraints.equate_flows_by_keyword(
        model, keyword_1, keyword_2
    )


def set_equate_statuses(model, block_pairs):
    count = len(model.timeincrement)
    for pair in block_pairs:
        (block_1, bus_1), (block_2, bus_2) = pair
        for i in range(count):
            solph.constraints.equate_variables(
                model,
                model.NonConvexFlowBlock.status[block_1, bus_1, i],
                model.NonConvexFlowBlock.status[block_2, bus_2, i],
            )


def set_single_active_flow(model, keyword):
    solph.constraints.limit_active_flow_count_by_keyword(
        model, keyword, lower_limit=0, upper_limit=1)


def get_df(results, bus, blocks):
    reuslt_for_bus = solph.views.node(results, bus.label)["sequences"].dropna()
    df = pd.DataFrame()
    for block in blocks:
        df[block.label] = reuslt_for_bus[((block.label, bus.label), "flow")]
    return df


def get_outage_df(results, outage_blocks):
    res = pd.DataFrame()
    for outage_block in outage_blocks:
        output_bus = outage_block.outputs[0]
        results_for_bus = solph.views.node(results, output_bus.label)["sequences"].dropna()
        res[outage_block.label] = results_for_bus[((outage_block.label, output_bus.label), "flow")]
    return res


def set_dispatch_order(es, block_1, block_2):
    
    
    # set_equate_statuses([])
    # set_equate_flow_by_keyword
    
    control_bus = solph.Bus(label="control bus")
    es.add(control_bus)
    control_sink_npp = solph.components.Sink(
    label="sink (npp)",
    inputs= {control_bus: solph.Flow(
        nominal_value = power * (1 - min_val),
        min = 1,
        nonconvex= solph.NonConvex(),
        )}
    )
    es.add(control_sink_npp)
    
    excess_sink_npp = solph.components.Sink(
    label="excess sink (npp)",
    inputs={control_bus: solph.Flow(
        nominal_value= power*(1-min_val),
        )},
    )
    es.add(excess_sink_npp)
    
