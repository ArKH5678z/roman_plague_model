import sys
import os
import json
import numpy as np
import matplotlib.pyplot as plt

sys.path.append('scenarios')
from scenarios.antonine import run_antonine, G as G_A, beta_base as beta_A, gamma_base as gamma_A
from scenarios.cyprian import run_cyprian, G as G_C
from scenarios.justinianic import run_justinianic, G as G_J

# Historical lag estimates based on documented response capacity
HISTORICAL_LAGS = {
    'Antonine': 45,    # Marcus Aurelius relatively responsive
    'Cyprian': 90,     # Political chaos, Emperor Decius died
    'Justinianic': 150 # Byzantine dysfunction, Justinian caught plague
}

# Modelled lags for comparison
MODELLED_LAGS = {
    'Antonine': 30,
    'Cyprian': 30,
    'Justinianic': 45
}

N_RUNS = 100

def run_with_lag(run_func, lag, n_runs=N_RUNS):
    pid_affected = []
    nopid_affected = []
    pid_peaks = []
    nopid_peaks = []
    I_pid_all = []
    I_nopid_all = []

    for _ in range(n_runs):
        S, I, R, _, states = run_func(use_pid=True)
        pid_affected.append(sum(1 for s in states.values() if s in ['I','R']))
        pid_peaks.append(max(I))
        I_pid_all.append(I)

        S, I, R, _, states = run_func(use_pid=False)
        nopid_affected.append(sum(1 for s in states.values() if s in ['I','R']))
        nopid_peaks.append(max(I))
        I_nopid_all.append(I)

    return {
        'pid': int(np.mean(pid_affected)),
        'no_pid': int(np.mean(nopid_affected)),
        'peak_pid': int(np.mean(pid_peaks)),
        'peak_no_pid': int(np.mean(nopid_peaks)),
        'pid_std': int(np.std(pid_affected)),
        'I_pid': np.mean(I_pid_all, axis=0).tolist(),
        'I_no_pid': np.mean(I_nopid_all, axis=0).tolist()
    }

print("Running historical lag scenarios...")
print("This compares optimistic modelled lags vs historically realistic lags\n")

scenarios = [
    ('Antonine', run_antonine, HISTORICAL_LAGS['Antonine'], MODELLED_LAGS['Antonine']),
    ('Cyprian', run_cyprian, HISTORICAL_LAGS['Cyprian'], MODELLED_LAGS['Cyprian']),
    ('Justinianic', run_justinianic, HISTORICAL_LAGS['Justinianic'], MODELLED_LAGS['Justinianic'])
]

results_modelled = {}
results_historical = {}

for name, run_func, hist_lag, mod_lag in scenarios:
    print(f"[Modelled lag {mod_lag} days] {name}...")
    
    # Temporarily patch controller lag in scenario
    import scenarios.antonine as ant
    import scenarios.cyprian as cyp
    import scenarios.justinianic as jus
    
    if name == 'Antonine':
        original = ant.controller_lag
        ant.controller_lag = mod_lag
        results_modelled[name] = run_with_lag(run_antonine, mod_lag)
        ant.controller_lag = hist_lag
        print(f"[Historical lag {hist_lag} days] {name}...")
        results_historical[name] = run_with_lag(run_antonine, hist_lag)
        ant.controller_lag = original
        
    elif name == 'Cyprian':
        original = cyp.controller_lag
        cyp.controller_lag = mod_lag
        results_modelled[name] = run_with_lag(run_cyprian, mod_lag)
        cyp.controller_lag = hist_lag
        print(f"[Historical lag {hist_lag} days] {name}...")
        results_historical[name] = run_with_lag(run_cyprian, hist_lag)
        cyp.controller_lag = original
        
    elif name == 'Justinianic':
        original = jus.controller_lag
        jus.controller_lag = mod_lag
        results_modelled[name] = run_with_lag(run_justinianic, mod_lag)
        jus.controller_lag = hist_lag
        print(f"[Historical lag {hist_lag} days] {name}...")
        results_historical[name] = run_with_lag(run_justinianic, hist_lag)
        jus.controller_lag = original

# Print comparison table
print("\n" + "="*75)
print("MODELLED vs HISTORICAL LAG COMPARISON (averaged over 20 runs)")
print("="*75)
print(f"{'Scenario':<15} {'Mod Lag':<10} {'Hist Lag':<10} {'Mod PID':<12} {'Hist PID':<12} {'Difference'}")
print("-"*75)

for name, run_func, hist_lag, mod_lag in scenarios:
    mod = results_modelled[name]['pid']
    hist = results_historical[name]['pid']
    diff = hist - mod
    effect = f"+{diff} worse" if diff > 0 else f"{abs(diff)} better"
    print(f"{name:<15} {mod_lag:<10} {hist_lag:<10} {mod:<12} {hist:<12} {effect}")

# Plot comparison
fig, axes = plt.subplots(1, 3, figsize=(18, 6))
fig.suptitle('Modelled vs Historical Response Lag\nImpact on Plague Spread (PID Control Only)', 
             fontsize=13)

colors = ['steelblue', 'darkorange', 'crimson']
names = ['Antonine', 'Cyprian', 'Justinianic']

for i, name in enumerate(names):
    days = range(len(results_modelled[name]['I_pid']))
    axes[i].plot(days, results_modelled[name]['I_pid'], 
                 color=colors[i], linewidth=2, 
                 label=f"Modelled lag ({MODELLED_LAGS[name]}d)")
    axes[i].plot(days, results_historical[name]['I_pid'], 
                 color=colors[i], linewidth=2, linestyle='--',
                 label=f"Historical lag ({HISTORICAL_LAGS[name]}d)")
    axes[i].plot(days, results_modelled[name]['I_no_pid'],
                 color='grey', linewidth=1, linestyle=':',
                 label='No control')
    axes[i].set_title(f'{name}')
    axes[i].set_xlabel('Days')
    axes[i].set_ylabel('Infected Settlements')
    axes[i].legend(fontsize=8)
    axes[i].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('outputs/historical_lag_comparison.png', dpi=150)
plt.show()

# Save results
with open('outputs/historical_lag_results.json', 'w') as f:
    json.dump({
        'modelled': {k: {k2: v2 for k2, v2 in v.items() if not isinstance(v2, list)} 
                     for k, v in results_modelled.items()},
        'historical': {k: {k2: v2 for k2, v2 in v.items() if not isinstance(v2, list)} 
                       for k, v in results_historical.items()}
    }, f, indent=4)

print("\nSaved outputs/historical_lag_comparison.png")
print("Saved outputs/historical_lag_results.json")