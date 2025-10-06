from libsbml import (SBMLDocument, writeSBMLToFile, writeSBMLToString,
                    LIBSBML_OPERATION_SUCCESS, OperationReturnValue_toString,
                    CVTerm, BIOLOGICAL_QUALIFIER, BQB_IS_DESCRIBED_BY)

from ..entity_classes import IDTracker, Species, SpeciesType, SpeciesReference, Reaction

SBML_LEVEL = 3
SBML_VERSION = 2
OUTSIDE_COMPARTMENTS = ['cytoplasm', 'extracellular']

#-------------------------------------
# libSBML helper stuff
#-------------------------------------

def check(value, message):
    """If 'value' is None, prints an error message constructed using
    'message' and then exits with status code 1.  If 'value' is an integer,
    it assumes it is a libSBML return status code.  If the code value is
    LIBSBML_OPERATION_SUCCESS, returns without further action; if it is not,
    prints an error message constructed using 'message' along with text from
    libSBML explaining the meaning of the code, and exits with status code 1.
    """
    if value is None:
        raise Exception('sbml: LibSBML returned a null value trying to ' + message + '.')

    if type(value) is int:
        if value == LIBSBML_OPERATION_SUCCESS:
            return
        else:
            err_msg = 'sbml: Error encountered trying to ' + message + '.' \
            + 'LibSBML returned error code ' + str(value) + ': "' \
            + OperationReturnValue_toString(value).strip() + '"'
            raise Exception(err_msg)

    return

#-------------------------------------
# SBML
#-------------------------------------

class SBML(SBMLDocument, IDTracker):

    def __init__(self, graph):
        '''


        '''
        SBMLDocument.__init__(self, SBML_LEVEL, SBML_VERSION)
        IDTracker.__init__(self)

        self.graph = graph

        # start the SBML model
        self.sbml_model = self.createModel()
        check(self.sbml_model, 'create model')
        check(self.sbml_model.setId('PSSTODO'), 'set identifier on the Model object')

    def write(self, filename, replace_markup=True):
        if filename is None:
            return writeSBMLToString(self)
        return writeSBMLToFile(self, filename)

    def get_sbml_species_type(self, species_type):
        ''' Get a species type node in SBML model. Create if it does not exist.
        '''

        id_, status =  self.get_species_type_id(species_type)

        if status == 1:
            pass

        else:
            typ = self.sbml_model.createSpeciesType()
            check(typ, f'create species type {id_}\n')
            check(typ.setId(id_), f'set species type id {id_}\n')
            typ.setName(f'{species_type.name} {species_type.form}')
            # typ.setConstant(False)

            if species_type.sbo_term:
                typ.setSBOTerm(species_type.sbo_term)

            self.set_species_type_id(species_type, id_)
            species_type.set_id(id_)

        return id_

    def get_sbml_species(self, species):
        ''' Get a species node in SBML model. Create if it does not exist.

        Returns
        -------
            id: str
        '''

        id_, status =  self.get_species_id(species) # look up the id in the IDTracker

        if status == 1:
            pass

        else:
            sp = self.sbml_model.createSpecies()
            sp.setId(id_)
            sp.setName(species.name)

            if (SBML_VERSION >= 2) and (SBML_LEVEL == 2):
            # TODO -- Error: Error: sbml: LibSBML returned a null value trying to create species type VPg_p.
                species_type = SpeciesType(name=species.name, form=species.form)
                specie_type_identifier = self.get_sbml_species_type(species_type)
                sp.setSpeciesType(specie_type_identifier)

            if species.sbo_term:
                sp.setSBOTerm(species.sbo_term)

            compartment_id = self.get_sbml_compartment(species.compartment)
            sp.setCompartment(compartment_id)

            sp.setHasOnlySubstanceUnits(False)
            sp.setBoundaryCondition(False)
            sp.setConstant(False)

            self.set_species_id(species, id_)
            species.set_id(id_)
            # print(f"SBML: species id: {species.name} --> {id_}", species.compartment, species.form, species.sbo_term)

        return id_

    def get_sbml_compartment(self, compartment):

        id_, status =  self.get_compartment_id(compartment)

        if status == 1:
            pass

        else:
            comp = self.sbml_model.createCompartment()
            comp.setId(id_)
            comp.setName(compartment)
            comp.setSize(1)
            comp.setConstant(True)

            if not (compartment in OUTSIDE_COMPARTMENTS):
                cyto_identifier = self.get_sbml_compartment('cytoplasm')
                m = comp.setOutside(cyto_identifier)
                check(m, "Set 'outside' of compartment")

            self.set_compartment_id(compartment, id_)

        # print(f"SBML: compartment id: {compartment} --> {id_}")
        return id_

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

        if reaction.sbo_term:
            rxn.setSBOTerm(reaction.sbo_term)

        rxn.setReversible(False)
        rxn.setFast(False)

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
            print(f"SBML: {reaction.reaction_id}, unknown reaction type")

        # (1) create reaction object
        if reaction.reaction_id in self.reaction_ids:
            print(f"SBML: {reaction.reaction_id}, already exists")
            return -1

        rxn = self.create_sbml_reaction(reaction)

        '''
                      (modifier)
                          |
                          |
                          |
                          o
        (substrate)----[process]---->(product)
        '''

        # (2) substrate glyphs and arcs
        # (substrate)-[consumption]->(reaction)
        for species in reaction.substrates:
            self.create_reactant_reference(species, role=reaction.substrate_role, reaction=rxn)

        # (3) product glyphs and arcs
        # (reaction)-[production]->(product)
        for species in reaction.products:
            self.create_product_reference(species, role=reaction.product_role, reaction=rxn)

        # (4) modifier glyphs and arcs
        # (modifier)-[modifies]->(reaction)
        for species in reaction.modifiers:
            self.create_modifier_reference(species, role=reaction.modifier_role, reaction=rxn)

        # create the empty kinetic law XML node for the reaction, set the SBO term
        kinetic_law = rxn.createKineticLaw()
        check(kinetic_law, f'create kinetic law for reaction {reaction.reaction_id}\n')
        if reaction.kinetic_law_sbo:
            kinetic_law.setSBOTerm(reaction.kinetic_law_sbo)
