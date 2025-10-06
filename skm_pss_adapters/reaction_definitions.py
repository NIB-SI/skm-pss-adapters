'''
This module defines constants for different types of reactions in PSS.
'''


class reaction_types:
    """
    Class to hold constants for different types of reactions.
    """

    BINDING_OLIGOMERISATION = 'binding/oligomerisation'
    DISSOCIATION = 'dissociation'
    CATALYSIS = 'catalysis'
    DEGRADATION_SECRETION = 'degradation/secretion'
    PROTEIN_DEACTIVATION = 'protein deactivation'
    PROTEIN_ACTIVATION = 'protein activation'
    TRANSCRIPTIONAL_TRANSLATIONAL_ACTIVATION = 'transcriptional/translational activation'
    TRANSCRIPTIONAL_TRANSLATIONAL_REPRESSION = 'transcriptional/translational repression'
    TRANSLOCATION = 'translocation'
    UNKNOWN = 'unknown'


class reaction_classes:
    """Class to hold constants for different classes of reaction types.
    These classes are used to categorize reactions based on their biological function.
    """

    TRANSCRIPTIONAL_TRANSLATIONAL = [
        reaction_types.TRANSCRIPTIONAL_TRANSLATIONAL_ACTIVATION,
        reaction_types.TRANSCRIPTIONAL_TRANSLATIONAL_REPRESSION
    ]

class participant_roles:
    """
    Class to hold constants for different roles of participants in reactions.
    """
    SUBSTRATE = 'substrate'
    PRODUCT = 'product'
    MODIFIER = 'modifier'
    INTERACTOR = 'interactor'
    TEMPLATE = 'template'
    STIMULATOR = 'stimulator'
    INHIBITOR = 'inhibitor'
    CATALYST = 'catalyst'
    TRANSPORTER = 'transporter'

    @staticmethod
    def assign_roles(reaction):
        """
        Assign roles to reaction participants based on the reaction type.
        This method sets the roles of substrates, products, and modifiers
        according to predefined rules for each reaction type.
        """

        # reactant roles
        if reaction.reaction_type == reaction_types.BINDING_OLIGOMERISATION:
            reaction.substrate_role = participant_roles.INTERACTOR
        elif reaction.reaction_type in reaction_classes.TRANSCRIPTIONAL_TRANSLATIONAL:
            reaction.substrate_role = participant_roles.TEMPLATE
        else:
            reaction.substrate_role = participant_roles.SUBSTRATE

        # modifier roles
        if reaction.reaction_type == reaction_types.TRANSCRIPTIONAL_TRANSLATIONAL_ACTIVATION:
            reaction.modifier_role = participant_roles.STIMULATOR
        elif reaction.reaction_type == reaction_types.TRANSCRIPTIONAL_TRANSLATIONAL_REPRESSION:
            reaction.modifier_role = participant_roles.INHIBITOR
        elif reaction.reaction_type == reaction_types.CATALYSIS:
            reaction.modifier_role = participant_roles.CATALYST
        elif reaction.reaction_type == reaction_types.TRANSLOCATION:
            reaction.modifier_role = participant_roles.TRANSPORTER
        else:
            reaction.modifier_role = participant_roles.MODIFIER

        # product roles
        reaction.product_role = participant_roles.PRODUCT
