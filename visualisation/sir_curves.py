import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scenarios.antonine import run_antonine, G as G_A
from scenarios.cyprian import run_cyprian, G as G_C
from scenarios.justinianic import run_justinianic, G as G_J

def plot_sir_curves():
    fig, axes = plt.subplots(3, 2, figsize=(16, 14))
    fig.suptitle('SIR Curves - Three Roman Plagues\nWith and Without PID Control', 
                 fontsize=14)

    scenarios = [
        ('Antonine 165 AD', run_antonine, G_A, 'steelblue'),
        ('Cyprian 249 AD', run_cyprian, G_C, 'darkorange'),
        ('Justinianic 541 AD', run_justinianic, G_J, 'crimson')
    ]

    for i, (title, run_func, G, color) in enumerate(scenarios):
        # Run with and without PID
        S_pid, I_pid, R_pid, _, _ = run_func(use_pid=True)
        S_no, I_no, R_no, _, _ = run_func(use_pid=False)

        days = range(len(S_pid))

        # Without PID
        axes[i, 0].plot(days, S_no, color='green', linewidth=2, label='Susceptible')
        axes[i, 0].plot(days, I_no, color='red', linewidth=2, label='Infected')
        axes[i, 0].plot(days, R_no, color='grey', linewidth=2, label='Recovered')
        axes[i, 0].set_title(f'{title} — No Control')
        axes[i, 0].set_xlabel('Days')
        axes[i, 0].set_ylabel('Settlements')
        axes[i, 0].legend()
        axes[i, 0].grid(True, alpha=0.3)

        # With PID
        axes[i, 1].plot(days, S_pid, color='green', linewidth=2, label='Susceptible')
        axes[i, 1].plot(days, I_pid, color=color, linewidth=2, label='Infected')
        axes[i, 1].plot(days, R_pid, color='grey', linewidth=2, label='Recovered')
        axes[i, 1].set_title(f'{title} — With PID Control')
        axes[i, 1].set_xlabel('Days')
        axes[i, 1].set_ylabel('Settlements')
        axes[i, 1].legend()
        axes[i, 1].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('outputs/sir_curves_all.png', dpi=150)
    plt.show()
    print("Saved outputs/sir_curves_all.png")

if __name__ == "__main__":
    plot_sir_curves()