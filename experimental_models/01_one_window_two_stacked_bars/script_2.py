import os
from matplotlib import pyplot as plt
import pandas as pd


folder_path = os.path.dirname(os.path.abspath(__file__))
excel_file = "data_2.xlsx"


left_df = pd.read_excel(
    os.path.join(folder_path, excel_file), sheet_name="data-1", header=0, index_col=0
)
right_df = pd.read_excel(
    os.path.join(folder_path, excel_file), sheet_name="data-2", header=0, index_col=0
)
left_df = left_df.T
right_df = right_df.T

left_df = left_df.drop(left_df.columns[-1], axis=1)
right_df = right_df.drop(right_df.columns[-1], axis=1)



left_df.index = ["подсценарий-1"]
right_df.index = ["подсценарий-2"]


line_df = pd.DataFrame()
line_df.index = [left_df.index[0], right_df.index[0]]
line_df["Всего"] = [left_df.sum(axis=1)[0], right_df.sum(axis=1)[0]]


max_Y_left = left_df.sum().sum()
max_Y_right = right_df.sum().sum()
largest = max(max_Y_left, max_Y_right)

res_df = pd.concat([left_df, right_df])


fontsize = 7

ax = res_df.plot(
    kind="bar",
    stacked=True,
    legend="reverse",
    figsize=(7, 6),
    ylim=(0, largest * 1.2),
    width=0.4,
    fontsize=fontsize,
)
ax2 = line_df.plot(
    kind="line",
    legend=False,
    ylim=(0, largest * 1.2),
    color="red",
    fontsize=fontsize,
    ax=ax,
    marker='o',
    markersize=5,
    markerfacecolor='black'
)



y_res = 0
x_res = ax.patches[0].get_x() + ax.patches[0].get_width() / 2
for p in ax.patches:
    width = p.get_width()
    height = p.get_height()
    y_res += height
    x, y = p.get_x(), p.get_y()
    if y:
        ax.text(
            x + width / 2,
            y + height / 2,
            f"{height:.0f}",
            ha="center",
            va="center",
            fontsize=fontsize,
        )


plt.legend(
    fontsize=fontsize - 1,
    loc = "upper left",
    ncol=2,
    reverse=True,
)
    
    
    
total = max_Y_left
ax.text(
    0,
    total * 1.03,
    f"{total:.0f}",
    ha="center",
    va="center",
    fontsize=fontsize,
    fontweight="bold",
)

        
total = max_Y_right
ax.text(
    1,
    total * 1.03,
    f"{total:.0f}",
    ha="center",
    va="center",
    fontsize=fontsize,
    fontweight="bold",
)

    
    
    
    
    
    
    
    
    
    

plt.xticks(rotation=0)
plt.ylabel("Денежные затраты, млн долл. США ", labelpad=10, fontsize=fontsize)

fig = plt.gcf()
fig.set_dpi(100)
plt.show(block=True)