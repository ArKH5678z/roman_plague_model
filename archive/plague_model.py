import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np

# Load data
sites = pd.read_csv('data/gorbit-sites.csv')
edges = pd.read_csv('data/gorbit-edges.csv')

# Build network
G = nx.Graph()
pos = {row['id']: (row['longitude'], row['latitude']) for _, row in sites.iterrows()}
valid_nodes = set(pos.keys())

for _, row in sites.iterrows():
    G.add_node(row['id'], label=row['title'], lat=row['latitude'], lon=row['longitude'])

for _, row in edges.iterrows():
    if row['source'] in valid_nodes and row['target'] in valid_nodes:
        G.add_edge(row['source'], row['target'], weight=row['days'])

# SIR parameters
beta = 0.3   # infection rate
gamma = 0.05 # recovery rate

# Find Rome's node ID
rome = sites[sites['title'] == 'Roma']['id'].values[0]

# Initialise states - everyone susceptible except Rome
states = {node: 'S' for node in G.nodes()}
infected_level = {node: 0.0 for node in G.nodes()}
infected_level[rome] = 1.0
states[rome] = 'I'

# Track history
history = {node: [] for node in G.nodes()}
day = 0
days = 120

print(f"Starting plague in Roma (node {rome})")
print(f"Simulating {days} days...\n")

for d in range(days):
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
        infected_level[node] = 1.0

    # Recovery
    for node in G.nodes():
        if states[node] == 'I':
            if np.random.random() < gamma:
                states[node] = 'R'

    for node in G.nodes():
        history[node].append(states[node])

    total_i = sum(1 for s in states.values() if s == 'I')
    total_r = sum(1 for s in states.values() if s == 'R')
    total_s = sum(1 for s in states.values() if s == 'S')

    if d % 10 == 0:
        print(f"Day {d}: Susceptible={total_s}, Infected={total_i}, Recovered={total_r}")

# Plot final state
color_map = []
for node in G.nodes():
    if states[node] == 'I':
        color_map.append('red')
    elif states[node] == 'R':
        color_map.append('grey')
    else:
        color_map.append('green')

plt.figure(figsize=(14, 8))
nx.draw(G, pos, node_color=color_map, node_size=20, edge_color='blue', alpha=0.4, width=0.5)
plt.title(f'Plague Spread After {days} Days - Red=Infected, Grey=Recovered, Green=Susceptible')
plt.savefig('plague_result.png', dpi=150)
plt.show()
print("\nDone. plague_result.png saved.")