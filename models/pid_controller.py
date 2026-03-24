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
    G.add_node(row['id'], label=row['title'])

for _, row in edges.iterrows():
    if row['source'] in valid_nodes and row['target'] in valid_nodes:
        G.add_edge(row['source'], row['target'], weight=row['days'])

# SIR base parameters
beta_base = 0.3
gamma = 0.05

# PID controller parameters
Kp = 2.0  # proportional gain
Ki = 0.1 # integral gain
Kd = 0.0   # derivative gain
setpoint = 30  # target max infected settlements

# Find Rome
rome = sites[sites['title'] == 'Roma']['id'].values[0]

def run_simulation(use_pid=True):
    states = {node: 'S' for node in G.nodes()}
    states[rome] = 'I'

    S_counts, I_counts, R_counts, beta_history = [], [], [], []

    # PID state
    integral = 0.0
    prev_error = 0.0
    beta = beta_base

    days = 150

    for d in range(days):
        total_i = sum(1 for s in states.values() if s == 'I')

        if use_pid:
            # PID control
            error = total_i - setpoint
            integral += error
            derivative = error - prev_error
            correction = Kp * error + Ki * integral + Kd * derivative
            prev_error = error

            # Apply correction - reduce beta when infections rise
            beta = max(0.01, beta_base - correction * 0.01)

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

    return S_counts, I_counts, R_counts, beta_history

print("Running without PID control...")
S1, I1, R1, beta1 = run_simulation(use_pid=False)

print("Running with PID control...")
S2, I2, R2, beta2 = run_simulation(use_pid=True)

# Plot comparison
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle('Roman Plague Model - PID Controller vs No Control', fontsize=14)

days_range = range(150)

axes[0, 0].plot(days_range, I1, color='red', linewidth=2)
axes[0, 0].set_title('Infected Settlements - No Control')
axes[0, 0].set_xlabel('Days')
axes[0, 0].set_ylabel('Settlements')
axes[0, 0].grid(True, alpha=0.3)

axes[0, 1].plot(days_range, I2, color='red', linewidth=2)
axes[0, 1].set_title('Infected Settlements - With PID Control')
axes[0, 1].set_xlabel('Days')
axes[0, 1].set_ylabel('Settlements')
axes[0, 1].grid(True, alpha=0.3)

axes[1, 0].plot(days_range, S1, color='green', label='S')
axes[1, 0].plot(days_range, I1, color='red', label='I')
axes[1, 0].plot(days_range, R1, color='grey', label='R')
axes[1, 0].set_title('SIR Curves - No Control')
axes[1, 0].legend()
axes[1, 0].grid(True, alpha=0.3)

axes[1, 1].plot(days_range, S2, color='green', label='S')
axes[1, 1].plot(days_range, I2, color='red', label='I')
axes[1, 1].plot(days_range, R2, color='grey', label='R')
axes[1, 1].set_title('SIR Curves - With PID Control')
axes[1, 1].legend()
axes[1, 1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('pid_comparison.png', dpi=150)
plt.show()

# Beta over time
plt.figure(figsize=(10, 4))
plt.plot(days_range, beta2, color='purple', linewidth=2)
plt.axhline(y=beta_base, color='red', linestyle='--', label='Base beta (no control)')
plt.title('PID Controller Response - Transmission Rate Over Time')
plt.xlabel('Days')
plt.ylabel('Beta (transmission rate)')
plt.legend()
plt.grid(True, alpha=0.3)
plt.savefig('pid_response.png', dpi=150)
plt.show()

print("\nDone. pid_comparison.png and pid_response.png saved.")