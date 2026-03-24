import pandas as pd
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scenarios.antonine import run_antonine, pos as pos_A
from scenarios.cyprian import run_cyprian, pos as pos_C
from scenarios.justinianic import run_justinianic, pos as pos_J

sites = pd.read_csv('data/gorbit-sites.csv')
edges = pd.read_csv('data/gorbit-edges.csv')

def plot_plague_maps():
    fig = plt.figure(figsize=(20, 8))
    fig.suptitle('Roman Plague Spread - Plague Footprint After 365 Days\nCrimson=Affected, Light Green=Unaffected Major Cities',
                 fontsize=13)

    scenarios = [
        ('Antonine 165 AD', run_antonine, pos_A),
        ('Cyprian 249 AD', run_cyprian, pos_C),
        ('Justinianic 541 AD', run_justinianic, pos_J)
    ]

    for i, (title, run_func, pos) in enumerate(scenarios):
        ax = fig.add_subplot(1, 3, i+1, projection=ccrs.PlateCarree())
        ax.set_extent([-10, 50, 25, 60], crs=ccrs.PlateCarree())

        # Map features
        ax.add_feature(cfeature.OCEAN, color='lightblue')
        ax.add_feature(cfeature.LAND, color='wheat')
        ax.add_feature(cfeature.COASTLINE, linewidth=0.8)
        ax.add_feature(cfeature.BORDERS, linewidth=0.5, linestyle='--', alpha=0.3)

        # Run simulation
        _, _, _, _, final_states = run_func(use_pid=True)

        # Draw edges
        valid_nodes = set(pos.keys())
        for _, row in edges.iterrows():
            if row['source'] in valid_nodes and row['target'] in valid_nodes:
                src = pos[row['source']]
                tgt = pos[row['target']]
                ax.plot([src[0], tgt[0]], [src[1], tgt[1]],
                        color='brown', alpha=0.2, linewidth=0.3,
                        transform=ccrs.PlateCarree())

        # Draw nodes
        for node_id, state in final_states.items():
            if node_id in pos:
                lon, lat = pos[node_id]
                if state == 'R':
                    ax.plot(lon, lat, 'o', color='crimson', markersize=6,
                            transform=ccrs.PlateCarree(), zorder=5, alpha=0.7)
                elif state == 'S':
                    row = sites[sites['id'] == node_id]
                    if not row.empty and row['rank'].values[0] >= 8:
                        ax.plot(lon, lat, 'o', color='green', markersize=3,
                                transform=ccrs.PlateCarree(), zorder=4, alpha=0.5)

        # Label major cities
        for _, row in sites.iterrows():
            if row['rank'] >= 10:
                ax.text(row['longitude'] + 0.3, row['latitude'] + 0.3,
                        row['title'], fontsize=5,
                        transform=ccrs.PlateCarree(),
                        color='black', fontweight='bold')

        ax.set_title(title, fontsize=11)

    plt.tight_layout()
    plt.savefig('outputs/plague_maps.png', dpi=150, bbox_inches='tight')
    plt.show()
    print("Saved outputs/plague_maps.png")

if __name__ == "__main__":
    plot_plague_maps()