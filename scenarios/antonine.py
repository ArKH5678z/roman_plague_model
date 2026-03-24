import pandas as pd
import networkx as nx
import numpy as np
import sys
import os

# Add root to path so we can import climate_model
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from climate_model import ClimateModel

# Load data
sites = pd.read_csv('data/gorbit-sites.csv')
edges = pd.read_csv('data/gorbit-edges.csv')

# Build network
G = nx.Graph()
pos = {row['id']: (row['longitude'], row['latitude']) for _, row in sites.iterrows()}
valid_nodes = set(pos.keys())

for _, row in sites.iterrows():
    G.add_node(row['id'], label=row['title'])

for _, row in edges.iterrows():
    if row['source'] in valid_nodes and row['target'] in valid_nodes:
        G.add_edge(row['source'], row['target'], weight=row['days'])

# Antonine plague parameters
# Started in Seleucia (modern Iraq) 165 AD
# Likely smallpox - moderately infectious, moderate mortality
START_YEAR = 165
START_CITY = 'Roma'
DAYS = 365

# Base SIR parameters tuned for smallpox-like disease
beta_base = 0.45
gamma_base = 0.03

# PID controller parameters
Kp = 0.8
Ki = 0.01
Kd = 0.1
setpoint = 15
controller_lag = 30   # days before imperial response kicks in

# Initialise climate model
climate = ClimateModel()

# Find starting node - Seleucia or nearest available
start_node = None
for _, row in sites.iterrows():
    if 'Roma' in str(row['title']):
        start_node = row['id']
        print(f"Starting in: {row['title']} (node {start_node})")
        break

# Fallback to Antiochia if Seleucia not found
if start_node is None:
    for _, row in sites.iterrows():
        if 'Antiochia' in str(row['title']):
            start_node = row['id']
            print(f"Seleucia not found, starting in: {row['title']} (node {start_node})")
            break

def run_antonine(use_pid=True):
    states = {node: 'S' for node in G.nodes()}
    states[start_node] = 'I'

    S_counts, I_counts, R_counts, beta_history = [], [], [], []

    integral = 0.0
    prev_error = 0.0

    for d in range(DAYS):
        # Get climate modified parameters for this year
        current_year = START_YEAR + (d // 365)
        beta, gamma = climate.get_modified_params(current_year, beta_base, gamma_base)

        total_i = sum(1 for s in states.values() if s == 'I')

        # PID control with lag
        if use_pid and d >= controller_lag:
            error = total_i - setpoint
            integral += error
            derivative = error - prev_error
            correction = Kp * error + Ki * integral + Kd * derivative
            prev_error = error
            beta = max(0.01, beta - correction * 0.01)

        new_infected = {}
        for node in G.nodes():
            if states[node] == 'I':
                for neighbor in G.neighbors(node):
                    if states[neighbor] == 'S':
                        travel_time = G[node][neighbor]['weight']
                        spread_prob = beta / travel_time
                        if np.random.random() < spread_prob:
                            new_infected[neighbor] = 'I'

        for node, state in new_infected.items():
            states[node] = state

        for node in G.nodes():
            if states[node] == 'I':
                if np.random.random() < gamma:
                    states[node] = 'R'

        S_counts.append(sum(1 for s in states.values() if s == 'S'))
        I_counts.append(sum(1 for s in states.values() if s == 'I'))
        R_counts.append(sum(1 for s in states.values() if s == 'R'))
        beta_history.append(beta)

    return S_counts, I_counts, R_counts, beta_history, states

if __name__ == "__main__":
    print("\nRunning Antonine Plague simulation...")
    print(f"Start: {START_CITY}, {START_YEAR} AD")
    print(f"Duration: {DAYS} days")
    
if __name__ == "__main__":
    import json
    
    print("\nRunning Antonine Plague simulation...")
    print(f"Start: {START_CITY}, {START_YEAR} AD")
    print(f"Duration: {DAYS} days")
    
    for use_pid in [True, False]:
        S, I, R, beta_hist, final_states = run_antonine(use_pid=use_pid)
        
        total_affected = sum(1 for s in final_states.values() if s in ['I', 'R'])
        
        print(f"\n--- {'With PID' if use_pid else 'Without PID'} ---")
        print(f"Settlements affected: {total_affected} of {len(G.nodes())}")
        print(f"Peak infections: {max(I)} settlements")
        print(f"Day of peak: {I.index(max(I))}")
        print(f"Final recovered: {R[-1]}")
        print(f"Beta base: {beta_base}")
        print(f"Gamma base: {gamma_base}")
        
        results = {
            'scenario': 'Antonine',
            'start_city': START_CITY,
            'start_year': START_YEAR,
            'days': DAYS,
            'beta_base': beta_base,
            'gamma_base': gamma_base,
            'use_pid': use_pid,
            'settlements_affected': total_affected,
            'peak_infections': max(I),
            'day_of_peak': I.index(max(I)),
            'final_recovered': R[-1]
        }
        
        filename = f'outputs/antonine_{"pid" if use_pid else "nopid"}_results.json'
        with open(filename, 'w') as f:
            json.dump(results, f, indent=4)
        print(f"Saved to {filename}")