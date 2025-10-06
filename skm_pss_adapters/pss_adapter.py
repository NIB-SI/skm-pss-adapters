'''
Exports ..... formats ..... of PSS model
'''
# library imports
from .entity_classes import Reaction
from .config import pss_export_config

# internal imports
from .entity_classes import IDTracker
from .model_fixes import ModelFixer

# # SBGN
# from .sbgn_api import SBGN

# SBML
from .sbml import SBML

# # projection for DiNAR
# from .pss_dinar_translation import pss_dinar_translation

################################################################################
# Handles all exports, and has paths for endpoints to use
################################################################################
class PSSAdapter():
    '''Exports for PSS model.s
    Exports (will) include:
        - SBML
        - *SBGN
        - *DiNAR projection
        - *JSON (for API)
    '''

    def __init__(self, graph, include_genes=False, nodes_to_ignore='default', model_fixes_identify=True, model_fixes_apply=True, model_fixes_interactive=False):
        '''
        Constructor for PSSAdapter class.

        Parameters
        ----------
        graph : Graph
            The graph database connection object.
        include_genes : bool, optional
            Whether to include gene information in the reactions. Default is False.
        nodes_to_ignore : list or str, optional
            Nodes to ignore during export. Can be a list of node names or a single string. Default is 'default', which ignores nodes defined in the configuration.
        implement_model_fixes : bool, optional
            Whether to apply model fixes after collecting data. Default is True.

        Returns
        -------
        None

        '''
        self.graph = graph
        self.include_genes = include_genes

        if nodes_to_ignore == 'default':
            # ignore nodes that are not reactions or families
            self.nodes_to_ignore = pss_export_config.nodes_to_ignore
        elif nodes_to_ignore is None:
            # no nodes to ignore
            self.nodes_to_ignore = []
        elif isinstance(nodes_to_ignore, str):
            # assume a single node
            self.nodes_to_ignore = [nodes_to_ignore.strip()]
        elif not isinstance(nodes_to_ignore, list):
            raise ValueError("nodes_to_ignore must be a list or a comma-separated string.")
        else:
            # assume a list of nodes
            self.nodes_to_ignore = [n.strip() for n in nodes_to_ignore]

        # TODO Create list of reactions to be exported:
        #   if reactions is defined, limit to list of reactions
        #   OR if pathways is defined, limit to reactions in list of pathways


        self.reactions = {}
        self.nodes = {}
        self.species = {}

        print("Collecting reactions and annotations from the database...")
        self.collect()
        print(f"Collected {len(self.reactions)} reactions.")

        self.additional_reactions = [] # any fixes go here

        if model_fixes_identify:
            self.identify_model_fixes(apply_fixes=model_fixes_apply, interactive=model_fixes_interactive)

    def collect(self):
        '''Collect reaction list and pathway annotations (all reusable between formats)
            Limit to reactions in the PATHWAYS attr
            Limit to reactions in REACTIONS attr
        '''

        invented_reason_allowlist = ["invented:harmonise-location"]

        def _get_reactions_and_paths(tx, nodes_to_ignore):

            cy = '''
                MATCH (r:Reaction)
                OPTIONAL MATCH p=(r)-[]-(n)
                WHERE NOT n.name IN $nodes_to_ignore
                RETURN  r.reaction_id AS reaction_id,
                        r AS reaction,
                        collect(p) AS path
                '''
            result = tx.run(cy, nodes_to_ignore=nodes_to_ignore)
            return [r for r in result]

        reaction_data = self.graph.run_query(_get_reactions_and_paths, self.nodes_to_ignore)

        for reaction_dict in reaction_data:

            reaction_id = reaction_dict['reaction_id']
            reaction_paths = reaction_dict['path']

            if len(reaction_paths) == 0:
                print(f"No edges on reaction {reaction_id}")
                continue

            reaction_properties = reaction_dict['reaction']

            reaction = Reaction(
                reaction_id,
                reaction_properties['reaction_type'],
                reaction_properties,
                include_genes=self.include_genes
            )
            reaction.add_edges(reaction_paths)
            self.reactions[reaction_id] = reaction

        ### Part 1: include restricted = no external_links filter
        self.all_reactions = list(self.reactions.keys())

        ### Part 2: public = filter external_links to reactions with at least
        #                    one source which is not 'other' or 'invented'
        #                    but can be from the allowlist
        def _list_reaction_ids_filter(tx, invented_reason_allowlist):
            cy = '''
                MATCH (r:Reaction)-[]-(n)
                WITH r,
                    size([link IN r.external_links WHERE link =~ 'other:.*' | 1]) AS a,
                    size([link IN r.external_links WHERE link =~ 'invented:.*' | 1]) AS b,
                    size([link IN r.external_links WHERE link IN $invented_reason_allowlist | 1]) AS c
                WHERE size(r.external_links) > a+b
                OR c>0
                RETURN DISTINCT r.reaction_id AS reaction_id
                '''
            result = tx.run(cy, invented_reason_allowlist=invented_reason_allowlist)
            return [r['reaction_id'] for r in result]

        self.public_reactions = [
            r for r in self.graph.run_query(_list_reaction_ids_filter,
                                            invented_reason_allowlist)
            if r in self.all_reactions
        ]

        # fetch annotations
        def _collect_node_annotations(tx):
            cy = '''
                MATCH (n)
                WHERE NOT ('Reaction' IN labels(n) OR 'Family' in labels(n) )
                RETURN n.name AS name, n.pathway AS pathway, labels(n) AS labels
                '''
            result = tx.run(cy)
            return [x for x in result]

        node_annotations = self.graph.run_query(_collect_node_annotations)
        self.node_annotations = {d["name"]: d for d in node_annotations}

        def _collect_reaction_pathways(tx):
            cy = '''
                MATCH (r:Reaction)--(n)
                RETURN r.name AS name, collect(DISTINCT n.pathway) AS pathway
                '''
            result = tx.run(cy)
            return [x for x in result]

        self.reaction_pathways = self.graph.run_query(
            _collect_reaction_pathways)

    def identify_model_fixes(self, interactive=False, apply_fixes=True):
        ''' Identify model fixes to the collected reactions.
            1) Fix node 'form' issues by changing input/outputs to active forms.
            2) Add transport reactions for species in multiple compartments.
        '''
        ModelFixer(self, apply_fixes=apply_fixes, interactive=interactive).identify_model_fixes()

    def create_sbml(self, access='public', filename=None, entities_table=None, kinetic_laws=True):
        '''  '''

        if access == 'public':
            reaction_list = self.public_reactions
        else:
            reaction_list = self.all_reactions

        sbml = SBML(self.graph, kinetic_laws=kinetic_laws)

        for reaction_id in reaction_list:
            sbml.add_reaction(self.reactions[reaction_id])

        for reaction_id in self.additional_reactions:
            print(reaction_id)
            sbml.add_reaction(self.reactions[reaction_id])

        print("-"*40)
        print("Ignored nodes: ", self.nodes_to_ignore)
        print("Number of species in SBML: ", len(sbml.species_ids))
        print("Number of species types in SBML: ", len(sbml.species_types_ids))
        print("Number of compartments in SBML: ", len(sbml.compartment_ids))
        print("Number of reactions in SBML: ", len(sbml.reaction_ids))
        print("-"*40)

        if entities_table:
            sbml.write_entities_table(entities_table)

        return sbml.write(filename)

