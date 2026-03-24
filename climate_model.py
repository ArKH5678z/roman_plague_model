import pandas as pd
import numpy as np

class ClimateModel:
    def __init__(self, climate_data_path='data/roman_climate.csv'):
        self.data = pd.read_csv(climate_data_path)
        self.data = self.data.set_index('year')
        
        # Baseline anomaly for normal conditions
        # Using Antonine period average as reference
        self.baseline = self.data.loc[100:180, 'temp_anomaly'].mean()
        print(f"Climate baseline (100-180 CE): {self.baseline:.4f}°C")
    
    def get_temp_anomaly(self, year):
        # Get temperature anomaly for a given year
        # If exact year not found interpolate nearest
        if year in self.data.index:
            return self.data.loc[year, 'temp_anomaly']
        else:
            # Interpolate between nearest years
            return self.data['temp_anomaly'].iloc[
                self.data.index.get_indexer([year], method='nearest')[0]
            ]
    
    def get_stress_level(self, year):
        # How much worse is this year compared to baseline
        # Positive stress = colder than baseline = more vulnerable population
        anomaly = self.get_temp_anomaly(year)
        stress = anomaly - self.baseline
        return stress
    
    def get_beta_modifier(self, year):
        # Colder years increase transmission rate
        # Each 0.1 degree below baseline increases beta by 10%
        stress = self.get_stress_level(year)
        if stress < 0:
            # Getting colder than baseline — increase transmission
            modifier = 1 + (abs(stress) * 1.0)
        else:
            # Warmer than baseline — slight decrease in transmission
            modifier = 1 - (stress * 0.3)
        # Clamp between 0.8 and 2.5
        return max(0.8, min(2.5, modifier))
    
    def get_gamma_modifier(self, year):
        # Colder/drier conditions reduce recovery capacity
        stress = self.get_stress_level(year)
        if stress < 0:
            # Getting colder — slower recovery
            modifier = 1 + (stress * 0.8)
        else:
            modifier = 1.0
        # Clamp between 0.4 and 1.0
        return max(0.4, min(1.0, modifier))
    
    def get_modified_params(self, year, beta_base, gamma_base):
        beta = beta_base * self.get_beta_modifier(year)
        gamma = gamma_base * self.get_gamma_modifier(year)
        return beta, gamma
    
    def print_plague_conditions(self):
        # Print climate conditions for each plague period
        plagues = {
            'Antonine (165 AD)': 165,
            'Cyprian (249 AD)': 249,
            'Justinianic (541 AD)': 541
        }
        print("\n=== Climate Conditions at Each Plague ===")
        for name, year in plagues.items():
            anomaly = self.get_temp_anomaly(year)
            beta_mod = self.get_beta_modifier(year)
            gamma_mod = self.get_gamma_modifier(year)
            print(f"\n{name}")
            print(f"  Temp anomaly: {anomaly:.4f}°C")
            print(f"  Beta modifier: {beta_mod:.3f}x")
            print(f"  Gamma modifier: {gamma_mod:.3f}x")

if __name__ == "__main__":
    climate = ClimateModel()
    climate.print_plague_conditions()