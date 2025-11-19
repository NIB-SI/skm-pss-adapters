'''
Use https://github.com/sys-bio/TabularQual to export table

'''

from collections import defaultdict

from TabularQual_converter.types import QualModel, ModelInfo
from TabularQual_converter.types import Species as TabularQualSpecies
from TabularQual_converter.types import Transition as TabularQualTransition
from TabularQual_converter.types import InteractionEvidence as TabularQualInteractionEvidence
from TabularQual_converter.types import Person as TabularQualPerson

from TabularQual_converter.spreadsheet_writer import write_spreadsheet

from ..entity_classes import IDTracker, Species, SpeciesType, SpeciesReference, Reaction
from .boolean import reaction_rule_constructor, rule_composer


#-------------------------------------
# TabluarQqual
#-------------------------------------

class TabluarQqual(IDTracker):

    def __init__(self, pss_adapter):
        '''


        '''

        IDTracker.__init__(self)

        self.pss_adapter = pss_adapter

        self.rules = defaultdict(lambda: {"activation":[], "inhibition":[]})

        self.species_dict = {}
        self.transitions = []
        self.interactions = []

    def to_QualModel(self):
        return QualModel(
            model=self.create_model_info(),
            species=self.species_dict,
            transitions=self.transitions,
            interactions=self.interactions
        )

    def write(self, filename):
        ''' Write TabularQual spreadsheet to file '''

        qualmodel = self.to_QualModel()
        write_spreadsheet(qualmodel, filename)

    def create_model_info(self):

        """Prepare model-level information"""

        model_id = self.pss_adapter.model_id
        name = self.pss_adapter.model_name

        notes = []
        versions = []

        source_urls = []
        described_by = []
        derived_from = []
        biological_processes = []
        taxons = []
        created_iso = self.pss_adapter.export_datetime
        modified_iso = None
        creators = []
        contributors = []

        return ModelInfo(
            model_id=model_id,
            name=name,
            source_urls=source_urls,
            described_by=described_by,
            derived_from=derived_from,
            biological_processes=biological_processes,
            taxons=taxons,
            created_iso=created_iso,
            modified_iso=modified_iso,
            creators=creators,
            contributors=contributors,
            versions=versions,
            notes=notes
        )


    def get_tabularqual_species(self, species):
        """Prepare species-level information"""

        species_id, status =  self.get_species_id(species) # look up the id in the IDTracker

        if status == 1:
            species.set_id(species_id)
            pass

        else:

            tabqual_species = TabularQualSpecies(
                species_id=species_id,
                name=species.name,
                compartment=species.compartment,
                constant=species.constant,
                initial_level=None,
                max_level=None,
                annotations=[],
                notes=[]
            )

            self.set_species_id(species, species_id)
            species.set_id(species_id)

            self.species_dict[species_id] = tabqual_species

            print(f"TabluarQqual: species id: {species.name} --> {species_id}", species.compartment, species.form, species.sbo_term)


        return species_id


    def create_reactant_reference(self, species, role, reaction):
        ''' Create SBML "SpeciesReference" in the model
        Returns the SBML species reference object '''

        id_ = self.get_sbml_species(species)
        species_reference = SpeciesReference(species, stoichiometry=1, role=role)
        reactant = reaction.createReactant()
        reactant.setSpecies(id_)
        reactant.setStoichiometry(species_reference.stoichiometry)
        reactant.setConstant(species_reference.constant)
        if species_reference.sbo_term:
            reactant.setSBOTerm(species_reference.sbo_term)

        return reactant


    def create_product_reference(self, species, role, reaction):
        ''' Create SBML "SpeciesReference" in the model
        Returns the SBML species reference object '''

        id_ = self.get_sbml_species(species)
        species_reference = SpeciesReference(species, stoichiometry=1, role=role)
        product = reaction.createProduct()
        product.setSpecies(id_)
        product.setStoichiometry(species_reference.stoichiometry)
        product.setConstant(species_reference.constant)
        if species_reference.sbo_term:
            product.setSBOTerm(species_reference.sbo_term)

        return product

    def create_modifier_reference(self, species, role, reaction):
        ''' Create SBML "ModifierReference" in the model
        Returns the SBML modifier reference object '''

        id_ = self.get_sbml_species(species)
        species_reference = SpeciesReference(species, stoichiometry=None, role=role)
        modifier = reaction.createModifier()
        modifier.setSpecies(id_)
        if species_reference.sbo_term:
            modifier.setSBOTerm(species_reference.sbo_term)

        return modifier

    def create_sbml_reaction(self, reaction):
        ''' Create SBML "Reaction" in the model
        Returns the reaction itself, not the identifier '''

        rxn = self.sbml_model.createReaction()
        rxn.setId(reaction.reaction_id)

        self.set_reaction_id(reaction, reaction.reaction_id)

        rxn.setMetaId(f"metaid_skm_{reaction.reaction_id}")

        if reaction.reaction_type_sbo:
            rxn.setSBOTerm(reaction.reaction_type_sbo)

        rxn.setReversible(False)
        rxn.setFast(False)

        if self.kinetic_laws:
            kinetic_law = rxn.createKineticLaw()
            kinetic_law.setMath(None)
            check(kinetic_law, f'create kinetic law for reaction {reaction.reaction_id}\n')
            if reaction.kinetic_law_sbo:
                kinetic_law.setSBOTerm(reaction.kinetic_law_sbo)

        SBML.add_annotation(rxn, f"skm:{reaction.reaction_id}")
        if reaction.external_links:
            for link in reaction.external_links:
                SBML.add_annotation(rxn, link)
                # print(f"SBML: {reaction.reaction_id}, annotation added: {link}")

        if reaction.evidence_sentence:
            SBML.add_note(rxn, 'curator_notes', reaction.evidence_sentence)

        if reaction.reaction_mechanism:
            SBML.add_note(rxn, 'mechanism', reaction.reaction_mechanism)

        if reaction.export_notes:
            SBML.add_note(rxn, 'export_notes', reaction.export_notes)

        return rxn

    @staticmethod
    def add_annotation(node, link):
        ''' Add an annotation to a node (reaction or species)  '''

        cv = CVTerm(BIOLOGICAL_QUALIFIER)
        cv.setBiologicalQualifierType(BQB_IS_DESCRIBED_BY)
        cv.addResource(f"http://identifiers.org/{link.strip().replace(" ", "")}")

        status = node.addCVTerm(cv)
        return check(status, "add annotation to node")

    @staticmethod
    def add_note(node, prefix, note):
        ''' Add a note to a node (reaction or species) '''

        if not note:
            return

        note = f"<body xmlns='http://www.w3.org/1999/xhtml'><p>{prefix}:{note}</p></body>"
        if node.isSetNotes():
            status = node.appendNotes(note)
        else:
            status = node.setNotes(note)

        return check(status, "add note to node")

    def add_reaction(self, reaction):

        # each reaction has ~4 nodes and ~3 arcs
        # substrate 1/+, product 1/+, process 1, modifier 1/+ nodes

        if reaction.reaction_type == 'unknown':
            # current_app.logger.info(f"{reaction_id}, undefined reaction type")
            print(f"TabluarQqual: {reaction.reaction_id}, unknown reaction type")

        # (1) create reaction object
        if reaction.reaction_id in self.reaction_ids:
            print(f"TabluarQqual: {reaction.reaction_id}, already exists")
            return -1

        # (2) substrate glyphs and arcs
        # (substrate)-[consumption]->(reaction)
        for species in reaction.substrates:
            print("TabluarQqual: substrate species:", species.name)
            self.get_tabularqual_species(species)

        # (3) product glyphs and arcs
        # (reaction)-[production]->(product)
        for species in reaction.products:
            print("TabluarQqual: product species:", species.name)
            self.get_tabularqual_species(species)

        # (4) modifier glyphs and arcs
        # (modifier)-[modifies]->(reaction)
        for species in reaction.modifiers:
            print("TabluarQqual: modifier species:", species.name)
            self.get_tabularqual_species(species)

        rule_constructor = reaction_rule_constructor(reaction)
        if rule_constructor is None:
            print(f"TabluarQqual: {reaction.reaction_id}, could not construct reaction rule")
            return -1

        targets, reaction_rule = rule_constructor(reaction)

        print("TabluarQqual: reaction rule:", reaction.reaction_id, "targets:", targets, "rule:", reaction_rule)

        if reaction_rule is None:
            print(f"TabluarQqual: {reaction.reaction_id}, no reaction rule generated")
            return

        for target in targets:
            self.rules[target][reaction.reaction_effect].append(reaction_rule)
            # rules_rx[target][reaction_effect].append(reaction_id)

    def create_transitions(self):
        ''' Create TabularQual Transitions from the collected rules '''

        for species_id, rule_dict in self.rules.items():

            print("TabluarQqual: creating transition for species:", species_id)

            activation_rules = rule_dict["activation"]
            inhibition_rules = rule_dict["inhibition"]

            update_function = rule_composer(species_id, activation_rules, inhibition_rules)

            transition_id = f"tr_{species_id}"
            transition = TabularQualTransition(
                transition_id=transition_id,
                target=species_id,
                name=None,
                level=1,
                rule=update_function,
                annotations=[],
                notes=[]
            )

            self.transitions.append(transition)
