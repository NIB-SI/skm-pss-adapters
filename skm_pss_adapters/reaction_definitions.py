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

