# is japan 2020 fixed?

year_for_plot = '2013'
df_jpn_2020 = dfE[(dfE['country'] == 'JPN') & (dfE['year'] == year_for_plot)]

# Plot
plt.figure(figsize=(8,5))
plt.bar(df_jpn_2020['sector'], df_jpn_2020['Employment'], color='skyblue')
plt.xlabel('Sector')
plt.ylabel('Employment')
plt.title(f'Employment by Sector in Japan, {year_for_plot}')
plt.xticks(rotation=45)  # rotate sector labels for readability
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.show()