import datetime as dt
from pathlib import Path

import pandas as pd
from matplotlib import pyplot as plt
from oemof import solph
from oemof.visio import ESGraphRenderer


class Res_scheme_builder:

    def __init__(self, oemof_es, folder):
        self.oemof_es = oemof_es
        self.folder = folder
        
    def create(self):
        folder = Path(self.folder)
        if not folder.exists():
            folder.mkdir(parents=True)
        
        file_name = "simpler_res"
        self.path = folder / file_name
        
        gr = ESGraphRenderer(
            energy_system=self.oemof_es,
            filepath=self.path.resolve(),
            img_format="png",
            txt_fontsize=14,
            txt_width=40,
            legend=False,
        )
        gr.view()

        
    def delete_file(self):
        path_sheme = Path(self.path)
        # path_diagram = Path(self.path.resolve().parent / path_sheme.stem)
        if path_sheme.exists():
            path_sheme.unlink()
        # if path_diagram.exists():
        #     path_diagram.unlink()


date_time_index = pd.date_range(dt.datetime(2025, 1, 1), periods=120, freq="H")
energysystem = solph.EnergySystem(timeindex=date_time_index, infer_last_interval=True)
el_blocks = []


el_bus = solph.Bus(label="электроэнергия")
energysystem.add(el_bus)
risk_bus = solph.Bus(label="повышение риска")
energysystem.add(risk_bus)
risk_out_bus = solph.Bus(label="снижение риска")
energysystem.add(risk_out_bus)


power_val = 1200


npp_source = solph.components.Source(
    label="Белорусская АЭС",
    outputs={
        el_bus: solph.Flow(
            nominal_value=power_val,
            variable_costs=-57.5,
        ),
        risk_bus: solph.Flow(nominal_value=power_val, variable_costs=0),
    },
)
energysystem.add(npp_source)

event_source = solph.components.Source(
        label="аварийные события",
        outputs={risk_bus: solph.Flow(nominal_value=power_val, variable_costs=0)},
)
energysystem.add(event_source)

storage = solph.components.GenericStorage(
        label="аккумулятор риска",
        inputs={risk_bus: solph.Flow()},
        outputs={risk_out_bus: solph.Flow()},
        nominal_capacity=200,
)
energysystem.add(storage)

repair_sink_1 = solph.components.Sink(
        label="ремонт (тип 1)",
        inputs={risk_out_bus: solph.Flow()},
)
energysystem.add(repair_sink_1)


# repair_sink_2 = solph.components.Sink(
#         label="ремонт (тип 2)",
#         inputs={risk_out_bus: solph.Flow()},
# )
# energysystem.add(repair_sink_2)

repair_sink_n = solph.components.Sink(
        label="ремонт (тип n)",
        inputs={risk_out_bus: solph.Flow()},
)
energysystem.add(repair_sink_n)


sink_demand=solph.components.Sink(
        label="потребитель",
        inputs={el_bus: solph.Flow(nominal_value = power_val, fix = 1)},
)
energysystem.add(sink_demand)


Res_scheme_builder(energysystem, "./").create()



model = solph.Model(energysystem)

model.solve(
    solver="cplex",
    solve_kwargs={
        'tee': True,  
    })




results = solph.processing.results(model)

el_results = solph.views.node(results, el_bus.label)["sequences"].dropna()


el_df = pd.DataFrame()
el_statuses_df = pd.DataFrame()

for block in el_blocks:
    el_df[block.label] = el_results[((block.label, el_bus.label), "flow")]


# ax_el = el_df.plot(kind="area", ylim=(0, 2000))

# plt.show(block=True)
