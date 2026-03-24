import json
import matplotlib.pyplot as plt
import numpy as np
import sys
import os

# Import all three scenarios
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scenarios'))
from scenarios.antonine import run_antonine, G as G_antonine, climate, DAYS as DAYS_A, beta_base as beta_A, gamma_base as gamma_A, START_YEAR as YEAR_A
from scenarios.cyprian import run_cyprian, G as G_cyprian, DAYS as DAYS_C, beta_base as beta_C, gamma_base as gamma_C, START_YEAR as YEAR_C
from scenarios.justinianic import run_justinianic, G as G_justinianic, DAYS as DAYS_J, beta_base as beta_J, gamma_base as gamma_J, START_YEAR as YEAR_J

print("="*60)
print("ROMAN PLAGUE MODEL - THREE PLAGUE COMPARISON")
print("Geospatial Network Analysis of Stochastic Disease Spread")
print("Under Environmental Stressors")
print("="*60)

# Run all three scenarios
print("\nRunning all scenarios...")

results = {}

N_RUNS = 20  # number of Monte Carlo runs

def monte_carlo(run_func, n_runs=N_RUNS):
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

    # Average curves
    I_pid_avg = np.mean(I_pid_all, axis=0).tolist()
    I_nopid_avg = np.mean(I_nopid_all, axis=0).tolist()

    return {
        'pid': int(np.mean(pid_affected)),
        'no_pid': int(np.mean(nopid_affected)),
        'peak_pid': int(np.mean(pid_peaks)),
        'peak_no_pid': int(np.mean(nopid_peaks)),
        'pid_std': int(np.std(pid_affected)),
        'nopid_std': int(np.std(nopid_affected)),
        'I_pid': I_pid_avg,
        'I_no_pid': I_nopid_avg
    }

# Antonine
print("\n[1/3] Antonine Plague (165 AD) - 20 runs...")
results['antonine'] = monte_carlo(run_antonine)

# Cyprian
print("[2/3] Cyprian Plague (249 AD) - 20 runs...")
results['cyprian'] = monte_carlo(run_cyprian)

# Justinianic
print("[3/3] Justinianic Plague (541 AD) - 20 runs...")
results['justinianic'] = monte_carlo(run_justinianic)
# Print summary table
print("\n" + "="*65)
print("RESULTS SUMMARY (averaged over 20 runs)")
print("="*65)
print(f"{'Scenario':<20} {'No Control':<15} {'With Control':<15} {'Std Dev':<12} {'Effect'}")
print("-"*65)
for name, r in results.items():
    diff = r['no_pid'] - r['pid']
    effect = f"+{diff} reduced" if diff > 0 else f"{abs(diff)} worse"
    print(f"{name.capitalize():<20} {r['no_pid']:<15} {r['pid']:<15} ±{r['pid_std']:<10} {effect}")

# Plot comparison
fig, axes = plt.subplots(1, 3, figsize=(18, 6))
fig.suptitle('Three Roman Plagues - PID Controller vs No Control\nAveraged over 20 Monte Carlo Runs', fontsize=13)

plagues = [
    ('Antonine 165 AD', results['antonine'], 'steelblue'),
    ('Cyprian 249 AD', results['cyprian'], 'darkorange'),
    ('Justinianic 541 AD', results['justinianic'], 'crimson')
]

for ax, (title, r, color) in zip(axes, plagues):
    days = range(len(r['I_pid']))
    ax.plot(days, r['I_no_pid'], color='grey', linewidth=2, linestyle='--', label='No Control')
    ax.plot(days, r['I_pid'], color=color, linewidth=2, label='With PID')
    ax.set_title(title)
    ax.set_xlabel('Days')
    ax.set_ylabel('Infected Settlements')
    ax.legend()
    ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('outputs/three_plagues_comparison.png', dpi=150)
plt.show()

# Save combined results
with open('outputs/combined_results.json', 'w') as f:
    json_results = {k: {k2: v2 for k2, v2 in v.items()
                        if not isinstance(v2, list)}
                    for k, v in results.items()}
    json.dump(json_results, f, indent=4)
print("\nSaved outputs/three_plagues_comparison.png")
print("Saved outputs/combined_results.json")
