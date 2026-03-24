import pandas as pd
import networkx as nx
import numpy as np
import json
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from climate_model import ClimateModel

# Load data
sites = pd.read_csv('data/gorbit-sites.csv')
edges = pd.read_csv('data/gorbit-edges.csv')

# Build network - heavily damaged from two previous plagues
G = nx.Graph()
pos = {row['id']: (row['longitude'], row['latitude']) for _, row in sites.iterrows()}
valid_nodes = set(pos.keys())

for _, row in sites.iterrows():
    G.add_node(row['id'], label=row['title'])

for _, row in edges.iterrows():
    if row['source'] in valid_nodes and row['target'] in valid_nodes:
        G.add_edge(row['source'], row['target'], weight=row['days'])

# Simulate cumulative network damage from Antonine AND Cyprian
# Remove 25% of edges - significantly degraded empire
np.random.seed(42)
all_edges = list(G.edges())
edges_to_remove = np.random.choice(len(all_edges),
                                    size=int(len(all_edges) * 0.15),
                                    replace=False)
for idx in edges_to_remove:
    G.remove_edge(*all_edges[idx])

print(f"Network after cumulative plague damage: {G.number_of_edges()} edges (was 560)")

# Justinianic plague parameters
# Started in Egypt 541 AD during Late Antique Little Ice Age
# Confirmed bubonic plague - Yersinia pestis
# Most lethal of the three
START_YEAR = 541
START_CITY = 'Alexandria'
DAYS = 365

# Highest beta, lowest gamma - bubonic plague
beta_base = 0.75
gamma_base = 0.015

# PID parameters - same controller, overwhelmed conditions
# Controller lag longer - Byzantine bureaucracy slower than Roman
Kp = 0.5
Ki = 0.005
Kd = 0.05
setpoint = 15
controller_lag = 60

# Initialise climate model
climate = ClimateModel()

# Find Alexandria
start_node = None
for _, row in sites.iterrows():
    if 'Alexandria' in str(row['title']) or 'Alexandri' in str(row['title']):
        start_node = row['id']
        print(f"Starting in: {row['title']} (node {start_node})")
        break

if start_node is None:
    for _, row in sites.iterrows():
        if 'Carthago' in str(row['title']):
            start_node = row['id']
            print(f"Alexandria not found, starting in: {row['title']} (node {start_node})")
            break

def run_justinianic(use_pid=True):
    states = {node: 'S' for node in G.nodes()}
    states[start_node] = 'I'

    S_counts, I_counts, R_counts, beta_history = [], [], [], []

    integral = 0.0
    prev_error = 0.0

    for d in range(DAYS):
        # 541 AD - severe climate stress from 536 volcanic winter
        current_year = START_YEAR + (d // 365)
        beta, gamma = climate.get_modified_params(current_year, beta_base, gamma_base)

        total_i = sum(1 for s in states.values() if s == 'I')

        # PID control with longer lag
        if use_pid and d >= controller_lag:
            error = total_i - setpoint
            integral += error
            derivative = error - prev_error
            correction = Kp * error + Ki * integral + Kd * derivative
            prev_error = error

            # Controller struggles - climate stress keeps pushing beta back up
            # Apply correction but climate modifier partially overrides it
            climate_beta_mod = climate.get_beta_modifier(current_year)
            beta = max(0.01, (beta_base * climate_beta_mod) - correction * 0.01)

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
    print("\nRunning Justinianic Plague simulation...")
    print(f"Start: {START_CITY}, {START_YEAR} AD")
    print(f"Duration: {DAYS} days")

    # Print climate conditions for 541 AD
    beta_mod = climate.get_beta_modifier(541)
    gamma_mod = climate.get_gamma_modifier(541)
    print(f"\nClimate stress 541 AD:")
    print(f"Beta modifier: {beta_mod:.3f}x")
    print(f"Gamma modifier: {gamma_mod:.3f}x")
    print(f"Effective beta: {beta_base * beta_mod:.3f}")
    print(f"Effective gamma: {gamma_base * gamma_mod:.3f}")

    for use_pid in [True, False]:
        S, I, R, beta_hist, final_states = run_justinianic(use_pid=use_pid)

        total_affected = sum(1 for s in final_states.values() if s in ['I', 'R'])

        print(f"\n--- {'With PID' if use_pid else 'Without PID'} ---")
        print(f"Settlements affected: {total_affected} of {G.number_of_nodes()}")
        print(f"Peak infections: {max(I)} settlements")
        print(f"Day of peak: {I.index(max(I))}")
        print(f"Final recovered: {R[-1]}")
        print(f"Beta base: {beta_base}")
        print(f"Gamma base: {gamma_base}")

        results = {
            'scenario': 'Justinianic',
            'start_city': START_CITY,
            'start_year': START_YEAR,
            'days': DAYS,
            'beta_base': beta_base,
            'gamma_base': gamma_base,
            'use_pid': use_pid,
            'network_edges': G.number_of_edges(),
            'climate_beta_modifier': beta_mod,
            'climate_gamma_modifier': gamma_mod,
            'settlements_affected': total_affected,
            'peak_infections': max(I),
            'day_of_peak': I.index(max(I)),
            'final_recovered': R[-1]
        }

        filename = f'outputs/justinianic_{"pid" if use_pid else "nopid"}_results.json'
        with open(filename, 'w') as f:
            json.dump(results, f, indent=4)
        print(f"Saved to {filename}")