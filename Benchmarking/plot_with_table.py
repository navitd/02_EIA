import matplotlib.pyplot as plt
import pandas as pd

# Example data
data = {
    'Country': ['CAN', 'USA', 'FRA', 'GBR'],
    'Backward': [0.39, 0.58, 0.53, 0.56],
    'Forward': [0.31, 0.42, 0.36, 0.40]
}
df = pd.DataFrame(data)
df['Total'] = df['Backward'] + df['Forward']

# Plot
fig, (ax_bar, ax_table) = plt.subplots(1, 2, figsize=(12, 5), gridspec_kw={'width_ratios': [2, 1]})

# Stacked bar chart
x = range(len(df))
ax_bar.bar(x, df['Backward'], color='indigo', label='Backward')
ax_bar.bar(x, df['Forward'], bottom=df['Backward'], color='orchid', label='Forward')

ax_bar.set_xticks(x)
ax_bar.set_xticklabels(df['Country'], rotation=45)
ax_bar.set_ylabel('GDP Impact')
ax_bar.set_title('ICT GDP Impact')
ax_bar.legend()

# Table
table_data = df[['Country', 'Backward', 'Forward', 'Total']].round(3)
ax_table.axis('off')
tbl = ax_table.table(
    cellText=table_data.values,
    colLabels=table_data.columns,
    cellLoc='center',
    loc='center'
)
tbl.auto_set_font_size(False)
tbl.set_fontsize(10)
tbl.scale(1.2, 1.5)

plt.tight_layout()
plt.show()
