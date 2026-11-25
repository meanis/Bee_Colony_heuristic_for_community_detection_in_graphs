from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx

from .functions import node_labeling


def draw(snapshots, partitions, analysis_data, plot_dir=None):
    """Draw each snapshot's communities and convergence chart: shown, or saved in plot_dir."""

    for moment in range(len(snapshots)):
        g = snapshots[moment]
        fs = partitions[moment]
        snapshot_analysis_data = analysis_data[moment]

        pos = nx.spring_layout(g)
        labels = node_labeling(fs.solution)

        plt.figure('Résultat de la détection de communautés')
        plt.title('Les communautés du réseau social')

        nx.draw(g, pos=pos, with_labels=True, node_color=labels, node_size=80)
        show_or_save(plot_dir, f'snapshot-{moment + 1}-communities.png')

        global_optimals = snapshot_analysis_data['global_optimal']
        plt.figure('Résultat de la détection de communautés')
        plt.title('Evolution de la qualité de la solution à travers les cycles de recherche')
        plt.bar(range(len(global_optimals)), global_optimals, width=0.1, color='green')
        plt.xlabel('cycle de recherche')
        plt.ylabel('coût de la meilleure solution trouvée')

        x_max = len(global_optimals)
        y_min = global_optimals[0]
        y_max = global_optimals[-1]

        plt.text(
            5,
            y_max,
            'f: ' + str(y_max),
            style='oblique',
            bbox={'facecolor': 'orange', 'alpha': 0.5, 'pad': 10},
        )
        plt.axis([0, x_max + 1, y_min - 0.01, y_max + 0.01])
        plt.grid(True, which='both', axis='y')
        show_or_save(plot_dir, f'snapshot-{moment + 1}-convergence.png')


def show_or_save(plot_dir, name):
    if plot_dir is None:
        plt.show()
    else:
        plt.savefig(Path(plot_dir) / name)
        plt.close()
