import pandas as pd

df = pd.read_csv('data/pages2k_temperature.txt', 
                 sep='\t',
                 comment='#',
                 header=0)

df.columns = ['year', 'instrumental', 'temp_anomaly', 'lower_95', 'upper_95', 
              'instrumental_filtered', 'temp_filtered', 'lower_filtered', 'upper_filtered']

df = df[['year', 'temp_anomaly']]
df = df.dropna()
df_filtered = df[df['year'].between(100, 600)]

df_filtered.to_csv('data/roman_climate.csv', index=False)
print("Saved to data/roman_climate.csv")
