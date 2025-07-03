'''
Exports ..... formats ..... of PSS model
'''
# library imports
from .entity_classes import Reaction

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

    def __init__(self, graph):
        '''
        Constructor for PSSAdapter class.
        '''

        self.graph = graph

        # TODO Create list of reactions to be exported:
        #   if reactions is defined, limit to list of reactions
        #   OR if pathways is defined, limit to reactions in list of pathways

        self.collect()



    def collect(self):
        '''Collect reaction list and pathway annotations (all reusable stuff)
            Limit to reactions in the PATHWAYS attr
            Limit to reactions in REACTIONS attr
        '''

        invented_reason_allowlist = ["invented:harmonise-location"]

        ### Part 1: include restricted = no external_links filter
        def _list_reaction_ids(tx):
            cy = '''
                MATCH (r:Reaction)-[]-(n)
                RETURN DISTINCT r.reaction_id AS reaction_id
                '''
            result = tx.run(cy)
            return [r['reaction_id'] for r in result]

        self.all_reactions = self.graph.run_query(_list_reaction_ids)

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
            result = tx.run(
                cy, invented_reason_allowlist=invented_reason_allowlist)
            return [r['reaction_id'] for r in result]

        self.public_reactions = self.graph.run_query(
            _list_reaction_ids_filter, invented_reason_allowlist)

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

        def _get_reactions_and_paths(tx, reaction_ids):
            cy = '''
                UNWIND $reaction_ids as id
                WITH id
                MATCH p=(r:Reaction)-[]-()
                WHERE r.reaction_id=id
                RETURN  id AS reaction_id,
                        r AS reaction,
                        collect(p) AS path
                '''
            result = tx.run(cy, reaction_ids=reaction_ids)
            return [r for r in result]

        reaction_data = self.graph.run_query(_get_reactions_and_paths, self.all_reactions)

        self.reaction_paths = {
            d['reaction_id']: d['path']
            for d in reaction_data
        }
        self.reaction_properties = {
            d['reaction_id']: d['reaction']
            for d in reaction_data
        }

    def create_sbml(self, access='public', filename=None):
        '''  '''

        if access == 'public':
            reaction_list = self.public_reactions
        else:
            reaction_list = self.all_reactions

        sbml = SBML(self.graph)

        for reaction_id in reaction_list:
            print(reaction_id)
            reaction_properties = self.reaction_properties[reaction_id]
            # print('reaction_properties: ', reaction_properties)

            # create reaction object
            reaction = Reaction(
                reaction_id,
                reaction_properties['reaction_type'],
                reaction_properties
            )

            edge_list = self.reaction_paths[reaction_id]
            reaction.add_edges(edge_list)

            sbml.add_reaction(reaction)

        return sbml.write(filename)

