from libsbml import (SBMLDocument, writeSBMLToFile, writeSBMLToString,
                    LIBSBML_OPERATION_SUCCESS, OperationReturnValue_toString,
                    CVTerm, BIOLOGICAL_QUALIFIER, BQB_IS_DESCRIBED_BY)

from ..entity_classes import IDTracker, Species

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
        status = self.sbml_model.setId('PSS TODO!!!')
        if status != LIBSBML_OPERATION_SUCCESS:
            # Do something to handle the error here.
            print('SBML: Unable to set identifier on the Model object')


    def write(self, filename, replace_markup=True):
        if filename is None:
            return writeSBMLToString(self)
        return writeSBMLToFile(self, filename)


    def get_species_type(self, species_type):

        id_, status =  self.get_species_type_id(species_type)

        if status == 1:
            pass

        else:
            typ = self.sbml_model.createSpeciesType()

            check(typ, f'create species type {id_}')

            typ.setId(id_)
            typ.setName(f'{species_type.name} {species_type.form}')
            typ.setConstant(False)

            if species_type.sbo_term:
                typ.setSBOTerm(species_type.sbo_term)

            self.set_species_type_id(species_type, id_)

        return id_

    def get_species(self, species):
        ''' Get a species node in SBML model. Create if it does not exist.


        Returns
        -------
            id: str
        '''

        id_, status =  self.get_species_id(species)

        if status == 1:
            pass

        else:
            sp = self.sbml_model.createSpecies()
            sp.setId(id_)
            sp.setName(species.name)

            # if SBML_VERSION == 2:
            # TODO -- Error: Error: sbml: LibSBML returned a null value trying to create species type VPg_p.
            #     species_type = SpeciesType(name=species.name, form=species.form)
            #     specie_type_identifier = self.get_species_type(species_type)
            #     sp.setSpeciesType(specie_type_identifier)

            if species.sbo_term:
                sp.setSBOTerm(species.sbo_term)

            compartment_id = self.get_compartment(species.compartment)
            sp.setCompartment(compartment_id)

            sp.setHasOnlySubstanceUnits(False)
            sp.setBoundaryCondition(False)
            sp.setConstant(False)

            self.set_species_id(species, id_)

        return id_

    def get_compartment(self, compartment):

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
                cyto_identifier = self.get_compartment('cytoplasm')
                print(compartment, cyto_identifier)
                m = comp.setOutside(cyto_identifier)
                check(m, "Set 'outside' of compartment")

            self.set_compartment_id(compartment, id_)

        # print(f"SBML: compartment id: {compartment} --> {id_}")
        return id_

    def create_reaction(self, reaction):
        ''' Create SBML "Reaction" in the model
        Returns the reaction itself, not the identifier '''

        rxn = self.sbml_model.createReaction()
        rxn.setId(reaction.reaction_id)

        rxn.setMetaId(f"metaid_skm_{reaction.reaction_id}")

        if reaction.sbo_term:
            rxn.setSBOTerm(reaction.sbo_term)

        rxn.setReversible(False)
        rxn.setFast(False)

        if reaction.external_links:
            for link in reaction.external_links:
                SBML.add_annotation(rxn, link)
                # print(f"SBML: {reaction.reaction_id}, annotation added: {link}")

        if reaction.evidence_sentence:
            SBML.add_note(rxn, reaction.evidence_sentence)
            # print(f"SBML: {reaction.reaction_id}, note added: {reaction.evidence_sentence}")

        return rxn

    @staticmethod
    def add_annotation(node, link):
        ''' Add an annotation to a node (reaction or species)  '''

        cv = CVTerm(BIOLOGICAL_QUALIFIER)
        cv.setBiologicalQualifierType(BQB_IS_DESCRIBED_BY)
        cv.addResource(f"http://identifiers.org/{link.strip()}")

        status = node.addCVTerm(cv)
        return check(status, "add annotation to node")

    @staticmethod
    def add_note(node, note):
        ''' Add a note to a node (reaction or species) '''

        if not note:
            return

        note = f"<body xmlns='http://www.w3.org/1999/xhtml'><p>{note}</p></body>"
        if node.isSetNotes():
            status = node.appendNotes(note)
        else:
            status = node.setNotes(note)

        return check(status, "add note to node")

    def add_reaction(self, reaction, edge_list):

        # each reaction has ~4 nodes and ~3 arcs
        # substrate 1/+, product 1/+, process 1, modifier 1/+ nodes

        if reaction.reaction_type == 'unknown':
            # current_app.logger.info(f"{reaction_id}, undefined reaction type")
            print(f"SBML: {reaction.reaction_id}, unknown reaction type")

        # (1) create reaction object
        rxn = self.create_reaction(reaction)


        for path in edge_list:

            edge = path.relationships[0]
            edge_type = edge.type # edges only have 1 type

            if edge_type in ['SUBSTRATE', 'TRANSLOCATE_FROM']:

                # (1) source is SUBSTRATE
                key = 'source'
                name = edge.start_node['name']
                location = edge[f'{key}_location']
                form = edge[f'{key}_form']
                reaction.add_substrate(Species(name, form, location))

            elif edge_type in ['PRODUCT', 'TRANSLOCATE_TO']:

                # (2) target is PRODUCT
                key = 'target'
                name = edge.end_node['name']
                location = edge[f'{key}_location']
                form = edge[f'{key}_form']
                reaction.add_product(Species(name, form, location))

            elif edge_type in  ['INHIBITS',  'ACTIVATES']:

                # (1) source is MODIFIER
                key = 'source'
                name = edge.start_node['name']
                location = edge[f'{key}_location']
                form = edge[f'{key}_form']
                if form == "condition":
                    continue
                reaction.add_modifier(Species(name, form, location))

            else:
                # current_app.logger.info(f"{edge_type}, {reaction_id}")
                print(f"SBML: {edge_type}, {reaction.reaction_id}")

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
            id_ = self.get_species(species)
            reactant = rxn.createReactant()
            reactant.setSpecies(id_)
            reactant.setStoichiometry(1)
            reactant.setConstant(False)

        # (3) product glyphs and arcs
        # (reaction)-[production]->(product)
        for species in reaction.products:
            id_ = self.get_species(species)
            product = rxn.createProduct()
            product.setSpecies(id_)
            product.setStoichiometry(1)
            product.setConstant(False)

        # (4) modifier glyphs and arcs
        # (modifier)-[modifies]->(reaction)
        for species in reaction.modifiers:
            id_ = self.get_species(species)
            modifier = rxn.createModifier()
            modifier.setSpecies(id_)

