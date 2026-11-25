from .bcsa import BCSA
from .population_initializer import PopulationInitializer


class BCSADCD:
    def __init__(self, params, snapshots):

        ######################################################

        self.params = params
        self.snapshots = snapshots

        ######################################################

    def execute(self):

        pop_init_ = PopulationInitializer(float(self.params['sigma']), int(self.params['nb_s']))
        initial_population = pop_init_.init_snapshot_pop(self.snapshots[0])

        mobcsa_ = BCSA(self.params)

        community_structures = []

        analysis_data = []

        for snapshot in self.snapshots:
            community_structure, initial_population, snapshot_analysis_data = mobcsa_.execute(
                snapshot, initial_population
            )
            community_structures.append(community_structure)
            analysis_data.append(snapshot_analysis_data)

        return community_structures, analysis_data
