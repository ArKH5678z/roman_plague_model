import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sys
import os
import networkx as nx

base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(base_dir)
from climate_model import ClimateModel

# Page config
st.set_page_config(
    page_title="Roman Plague Model",
    page_icon="🏛️",
    layout="wide"
)

st.title("🏛️ Roman Plague Model")
st.subheader("Geospatial Network Analysis of Stochastic Disease Spread Under Environmental Stressors")

# Sidebar controls
st.sidebar.header("Simulation Parameters")

scenario = st.sidebar.selectbox(
    "Select Plague Scenario",
    ["Antonine (165 AD)", "Cyprian (249 AD)", "Justinianic (541 AD)"]
)

st.sidebar.markdown("---")

# Initialise session state defaults
defaults = {
    'Kp': 0.8, 'Ki': 0.01, 'Kd': 0.1,
    'setpoint': 15, 'controller_lag': 30,
    'beta_base': 0.45, 'gamma_base': 0.03, 'days': 365
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# Reset button
if st.sidebar.button("↺ Reset to Defaults"):
    for key, val in defaults.items():
        st.session_state[key] = val
    st.rerun()

st.sidebar.subheader("PID Controller")
Kp = st.sidebar.slider("Kp — Proportional (Present)", 0.0, 3.0, st.session_state.Kp, 0.1, key='Kp')
Ki = st.sidebar.slider("Ki — Integral (Past)", 0.0, 0.5, st.session_state.Ki, 0.01, key='Ki')
Kd = st.sidebar.slider("Kd — Derivative (Future)", 0.0, 1.0, st.session_state.Kd, 0.05, key='Kd')
setpoint = st.sidebar.slider("Setpoint (target max infected)", 5, 50, st.session_state.setpoint, 5, key='setpoint')
controller_lag = st.sidebar.slider("Controller Lag (days)", 0, 60, st.session_state.controller_lag, 5, key='controller_lag')

st.sidebar.markdown("---")
st.sidebar.subheader("Disease Parameters")
beta_base = st.sidebar.slider("Beta (transmission rate)", 0.1, 1.0, st.session_state.beta_base, 0.05, key='beta_base')
gamma_base = st.sidebar.slider("Gamma (recovery rate)", 0.01, 0.1, st.session_state.gamma_base, 0.005, key='gamma_base')
days = st.sidebar.slider("Simulation Duration (days)", 90, 365, st.session_state.days, 30, key='days')

run_button = st.sidebar.button("▶ Run Simulation", type="primary")

# Load data
sites = pd.read_csv(os.path.join(base_dir, 'data/gorbit-sites.csv'))
edges = pd.read_csv(os.path.join(base_dir, 'data/gorbit-edges.csv'))

# Build network
G = nx.Graph()
pos = {row['id']: (row['longitude'], row['latitude']) for _, row in sites.iterrows()}
valid_nodes = set(pos.keys())

for _, row in sites.iterrows():
    G.add_node(row['id'], label=row['title'])

for _, row in edges.iterrows():
    if row['source'] in valid_nodes and row['target'] in valid_nodes:
        G.add_edge(row['source'], row['target'], weight=row['days'])

# Apply network damage based on scenario
np.random.seed(42)
if scenario == "Cyprian (249 AD)":
    all_edges = list(G.edges())
    to_remove = np.random.choice(len(all_edges), size=int(len(all_edges) * 0.10), replace=False)
    for idx in to_remove:
        G.remove_edge(*all_edges[idx])
elif scenario == "Justinianic (541 AD)":
    all_edges = list(G.edges())
    to_remove = np.random.choice(len(all_edges), size=int(len(all_edges) * 0.25), replace=False)
    for idx in to_remove:
        G.remove_edge(*all_edges[idx])

# Find start node
scenario_config = {
    "Antonine (165 AD)": {"city": "Roma", "year": 165},
    "Cyprian (249 AD)": {"city": "Alexandria", "year": 249},
    "Justinianic (541 AD)": {"city": "Alexandria", "year": 541}
}

config = scenario_config[scenario]
start_node = None
for _, row in sites.iterrows():
    if config['city'] in str(row['title']):
        start_node = row['id']
        break

climate = ClimateModel(
    climate_data_path=os.path.join(base_dir, 'data/roman_climate.csv')
)

def run_simulation(use_pid):
    states = {node: 'S' for node in G.nodes()}
    states[start_node] = 'I'

    S_counts, I_counts, R_counts = [], [], []
    integral = 0.0
    prev_error = 0.0

    for d in range(days):
        current_year = config['year'] + (d // 365)
        beta, gamma = climate.get_modified_params(current_year, beta_base, gamma_base)

        total_i = sum(1 for s in states.values() if s == 'I')

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

    return S_counts, I_counts, R_counts, states

# Main content
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Scenario", scenario)
with col2:
    climate_mod = climate.get_beta_modifier(config['year'])
    st.metric("Climate Beta Modifier", f"{climate_mod:.3f}x")
with col3:
    st.metric("Network Edges", G.number_of_edges())

st.markdown("---")

if run_button:
    with st.spinner("Running simulation..."):
        S_pid, I_pid, R_pid, states_pid = run_simulation(use_pid=True)
        S_no, I_no, R_no, states_no = run_simulation(use_pid=False)

    total_pid = sum(1 for s in states_pid.values() if s in ['I', 'R'])
    total_no = sum(1 for s in states_no.values() if s in ['I', 'R'])

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Affected (No Control)", total_no)
    with col2:
        st.metric("Affected (With PID)", total_pid,
                  delta=f"{total_pid - total_no}",
                  delta_color="inverse")
    with col3:
        st.metric("Peak (No Control)", max(I_no))
    with col4:
        st.metric("Peak (With PID)", max(I_pid),
                  delta=f"{max(I_pid) - max(I_no)}",
                  delta_color="inverse")

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    days_range = range(days)

    axes[0].plot(days_range, I_no, color='red', linewidth=2, label='Infected')
    axes[0].plot(days_range, R_no, color='grey', linewidth=2, label='Recovered')
    axes[0].plot(days_range, S_no, color='green', linewidth=2, label='Susceptible')
    axes[0].set_title(f'{scenario} — No Control')
    axes[0].set_xlabel('Days')
    axes[0].set_ylabel('Settlements')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    axes[1].plot(days_range, I_pid, color='steelblue', linewidth=2, label='Infected')
    axes[1].plot(days_range, R_pid, color='grey', linewidth=2, label='Recovered')
    axes[1].plot(days_range, S_pid, color='green', linewidth=2, label='Susceptible')
    axes[1].set_title(f'{scenario} — With PID Control')
    axes[1].set_xlabel('Days')
    axes[1].set_ylabel('Settlements')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    plt.tight_layout()
    st.pyplot(fig)

    st.markdown("---")
    st.subheader("PID Parameters Used")
    st.write(f"Kp={Kp}, Ki={Ki}, Kd={Kd}, Setpoint={setpoint}, Lag={controller_lag} days")
    st.write(f"Beta={beta_base}, Gamma={gamma_base}, Days={days}")

else:
    st.info("Adjust parameters in the sidebar and click **Run Simulation** to begin.")
    st.markdown("""
    ### How to use this dashboard
    1. Select a plague scenario from the dropdown
    2. Adjust PID controller parameters using the sliders
    3. Adjust disease parameters
    4. Click Run Simulation
    5. Compare controlled vs uncontrolled outcomes
    
    ### Research Question
    *At what threshold of environmental stress does institutional intervention 
    lose the capacity to suppress epidemic spread in a complex network system?*
    """)