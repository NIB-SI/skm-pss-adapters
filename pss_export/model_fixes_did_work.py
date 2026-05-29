'''
The models auto-generated from PSS have two major issues that leave parts of it disconnected. This occurs in the SBML, SBGN, and BoolNet models.

The issues are:
1) Genes and gene products occur in multiple forms, e.g.
      - "protein" form (e.g. unphosphorylated) as output from a translation reaction
      - "protein_active" form (e.g. phosphorylated) acting as a modifier in a downstream reaction.
   However, some are missing conversion reactions to connect the different forms
   (e.g. a protein activation reaction).
2) A number of nodes occur in multiple compartments as different species,
   but are missing transport reactions to connect them.


The following solutions are implemented:
1) We assume the unmodified protein form is the active form (i.e. no protein activation is required for the protein to be in the "active" form). To connect the model, we therefore change the output of translation reactions from "protein" to "protein_active", thus directly connecting them to downstream reactions where they act as the modifier. This is done by:
    a) Identify all nodes that occur as both "protein" and "protein_active" forms, and are not connected.
    b) For each of these nodes, identify all translation reactions that produce the "protein" form.
    c) Change the output of these translation reactions to the "protein_active" form.

2) For each species that occurs in multiple compartments, add transport reactions, from where the node is produced to where it is consumed. This is done by:
    a) Identify all nodes that occur in multiple compartments as different species, and are not connected.
    b) For each of these nodes, identify all compartments where it is produced (output from a reaction) and where it is consumed (input to a reaction).
    c) For each pair of compartments (from production to consumption), add a transport reaction if it does not already exist.

'''

from collections import defaultdict
# use networkx to find the problematic nodes
import networkx as nx

from rich.console import Console

import matplotlib.pyplot as plt
# from .pss_adapter import PSSAdapter
from .entity_classes import IDTracker
from .reaction_definitions import reaction_types, reaction_classes

console = Console()

# function to create networkx DiGraph from PSSAdapter
def pss_to_digraph(pss_adapter, location=True) -> nx.DiGraph:
    idtracker = IDTracker(location=location)
    G = nx.DiGraph()
    for reaction in pss_adapter.reactions.values():
        G.add_node(reaction.id, label=f"{reaction.id}\n{reaction.reaction_type}", type='reaction', form='reaction', reaction_type=reaction.reaction_type)
        for substrate in reaction.substrates:
            substrate_id, status = idtracker.get_species_id(substrate)
            if status == 0:
                G.add_node(substrate_id, label=substrate.id, type='species', name=substrate.name, form=substrate.form, compartment=substrate.compartment)
                idtracker.set_species_id(substrate, substrate_id)
            G.add_edge(substrate_id, reaction.id, type='substrate')

        for product in reaction.products:
            product_id, status = idtracker.get_species_id(product)
            if status == 0:
                G.add_node(product.id, label=product.id, type='species', name=product.name, form=product.form, compartment=product.compartment)
                idtracker.set_species_id(product, product_id)
            G.add_edge(reaction.reaction_id, product_id, type='product')

        for modifier in reaction.modifiers:
            modifier_id, status = idtracker.get_species_id(modifier)
            if status == 0:
                G.add_node(modifier.id, label=modifier.id, type='species', name=modifier.name, form=modifier.form, compartment=modifier.compartment)
                idtracker.set_species_id(modifier, modifier_id)
            G.add_edge(modifier_id, reaction.id, type='modifier')

    return G

def neighbourhood(nodes, G):
    neighbors = set()
    for n in nodes:
        neighbors.update(G.to_undirected(as_view=True).neighbors(n))
    return list(neighbors)

def get_species_per_node(G):
    species_dict = defaultdict(list)
    for node, data in G.nodes(data=True):
        if data.get('type') == 'species':
            name = data.get('name')
            species_dict[name].append(node)
    return species_dict

def is_node_connected(node, species, G):

    # find the first neighbours (reactions) of the species in G
    reactions = neighbourhood(species, G)

    # find the second neighbours (species) of the reactions
    all_reactions_species = reactions + neighbourhood(reactions, G) # second neighbours are species

    # if the node-induced subgraph of all the species for one node is not connected, it's problematic
    subgraph = G.subgraph(all_reactions_species)
    if not nx.is_weakly_connected(subgraph):
        return False, subgraph

    return True, subgraph

def find_problematic_nodes(G):

    # first, ALL the PSS nodes that have multiple species in G (either form or location)
    species_dict = get_species_per_node(G)
    multi_species_nodes = {k: v for k, v in species_dict.items() if len(v) > 1}
    print(f"Model fixing: Found {len(multi_species_nodes)} nodes with multiple species.")

    # next, find the problematic (unconnected) nodes
    problematic_nodes = {}
    for node, species in multi_species_nodes.items():
        connected, subgraph = is_node_connected(node, species, G)
        if not connected:
            problematic_nodes[node] = {"subgraph": subgraph, "species": species}

    return problematic_nodes

def plot_subgraph(subgraph, species):
    nx.draw(subgraph, with_labels=True, font_weight='bold',
        # use "label" attribute for labels
        labels=nx.get_node_attributes(subgraph, 'label'),
        # make the reaction nodes smaller
        node_size=[300 if subgraph.nodes[n].get('type') == 'reaction' else 800 for n in subgraph.nodes()],
        # make the species of interest a different color
        node_color=[1 if n in species else 2 for n in subgraph.nodes()],
        # larger arrow heads
        arrowsize=20,
        # layout
        # pos=nx.spring_layout(subgraph, iterations=1000, k=20, seed=42) #kamada_kawai_layout
        pos=nx.nx_agraph.graphviz_layout(subgraph, prog="dot")
    )
    plt.show()

def identify_model_fixes(pss_adapter, interactive=False, apply_fixes=True):
    ''' Identify and optionally apply model fixes to the collected reactions.
    Parameters
    ----------
    pss_adapter: PSSAdapter
    interactive: bool
        If True, show plots and ask user to confirm fixes.
    apply_fixes: bool
        If True, apply the fixes to the pss_adapter (only relevant if interactive is False).
    '''

    console.rule("[bold red]Applying model fixes")

    # 1) Fix protein activation issues, ignoring location for now
    console.print("Step 1: Fixing node 'form' issues, ignoring location for now.")
    identify_model_fixes_forms(pss_adapter, interactive=interactive, apply_fixes=apply_fixes)


    identify_model_fixes_forms(pss_adapter, interactive=True, apply_fixes=apply_fixes)


def identify_model_fixes_forms(pss_adapter, interactive=True, apply_fixes=True):
    ''' Identify and optionally apply model fixes to the collected reactions.
    '''

    # Create a directed graph to represent the reactions and species
    G = pss_to_digraph(pss_adapter, location=False)

    # Identify problematic nodes
    problematic_nodes = find_problematic_nodes(G)
    console.print(f"Model fixing: Ignoring location, found {len(problematic_nodes)} problematic nodes.")
    console.print()

    if interactive:
        # interactive mode to show plots
        plt.ion()

    num_fixes_applied = 0

    for node_name in problematic_nodes:

        console.print()
        console.rule(f"[bold red]Node {node_name}")

        species = problematic_nodes[node_name]['species']
        subgraph = problematic_nodes[node_name]['subgraph']
###
        forms = {}
        for s in species:
            form = subgraph.nodes[s].get('form')
            if form:
                forms[s] = form

        console.print(f"All node forms: {forms}\n")

        # what are the separate components of the subgraph?
        components = list(nx.weakly_connected_components(subgraph))
        console.print(f"{len(components)} components found:")

        # which forms are in each component?
        comp_forms = []
        for i, comp in enumerate(components):
            forms_in_comp = {subgraph.nodes[n].get('form') for n in comp if n in species}
            console.print(f" - Component {i} has forms: {forms_in_comp}")
            comp_forms.append(forms_in_comp)
        console.print()


        # suggest fixes by case...
        fixes = []
        fix_identified = False

        with console.status("Identifying fixes:"):

            # if there are more than two components, too complex to fix automatically
            if len(components) > 2:
                console.print("More than two components, too complex to fix automatically.")
                continue

            # Multiple components, some with "protein" and some with "protein_active"
            # and the components with "protein" has one or more translation reactions,
            # suggest changing the output of those translation reactions to "protein_active"
            if ( {'protein'} in comp_forms ) and ( {'protein_active'} in comp_forms ):
                # find the component with "protein"
                protein_comp = components[comp_forms.index({'protein'})]

                # option 1 - we can change translation/transcription to output protein active
                # find all translation reactions in this component
                console.print("Looking for translation reactions in the 'protein' component...")
                translation_reactions = [
                    r for r in protein_comp if subgraph.nodes[r].get('type') == 'reaction' \
                    # reaction is translation/transcription
                    and subgraph.nodes[r].get('reaction_type') in reaction_classes.TRANSCRIPTIONAL_TRANSLATIONAL \
                    # node (node_name) has a 'product' edge from the reaction
                    and any(data.get('type') == 'product' and v in species for u, v, data in subgraph.out_edges(r, data=True))
                ]
                if translation_reactions:
                    for reaction_id in translation_reactions:
                        console.print(f"- Found translation reaction {reaction_id} producing 'protein' form.")
                        fix = ModelFix(
                            reaction_id=reaction_id,
                            species_role='product',
                            species_name=node_name,
                            new_form='protein_active'
                        )
                        fixes.append(fix)
                    fix_identified = True
                    console.print(f"Suggest changing output of these transcription/translation reactions to 'protein_active' form.")
                else:
                    console.print("- No translation reactions found in the 'protein' component.")

                if not fix_identified:

                    # option 2 - we can change binding/oligomerisation to use protein_active as substrate
                    # find all binding/oligomerisation reactions in these components
                    console.print("Looking for binding/oligomerisation reactions in the 'protein' component...")
                    binding_reactions = [
                        r for r in protein_comp if subgraph.nodes[r].get('type') == 'reaction' \
                        # reaction is binding/oligomerisation
                        and subgraph.nodes[r].get('reaction_type') == reaction_types.BINDING_OLIGOMERISATION \
                        # node (node_name) has a 'substrate' edge to the reaction
                        and any(data.get('type') == 'substrate' and u in species for u, v, data in subgraph.in_edges(r, data=True))
                    ]
                    if binding_reactions:
                        for reaction_id in binding_reactions:
                            console.print(f"Found binding/oligomerisation reaction {reaction_id} using 'protein' form as substrate.")
                            fix = ModelFix(
                                reaction_id=reaction_id,
                                species_role='substrate',
                                species_name=node_name,
                                new_form='protein_active'
                            )
                            fixes.append(fix)
                        fix_identified = True
                        console.print(f"Suggest changing substrate of these binding/oligomerisation reactions to 'protein_active' form.")
                    else:
                        console.print("- No binding/oligomerisation reactions found in the 'protein' component.")


            # similarly if we have complex and complex_active (with no link between), then suggest to make all 'complex' to 'complex_active'
            elif {'complex'} in comp_forms and {'complex_active'} in comp_forms:
                console.print("Found components with expected forms ('complex' and 'complex_active').")
                # find the components with "complex"
                complex_comps = [components[i] for i, forms in enumerate(comp_forms) if forms == {'complex'}]
                for complex_comp in complex_comps:
                    # find binding/oligomerisation reactions in this component
                    binding_reactions = [n for n in complex_comp if subgraph.nodes[n].get('type') == 'reaction' and subgraph.nodes[n].get('reaction_type') == reaction_types.BINDING_OLIGOMERISATION]
                    if binding_reactions:
                        for reaction_id in binding_reactions:
                            console.print(f"Found binding/oligomerisation reaction {reaction_id} producing 'complex' form.")
                            fix = ModelFix(
                                reaction_id=reaction_id,
                                species_role='product',
                                species_name=node_name,
                                new_form='complex_active'
                            )
                            fixes.append(fix)
                        fix_identified = True
                        console.print(f"Suggest changing output of these binding/oligomerisation reactions to 'complex_active' form.")
                if not fix_identified:
                    console.print("- No binding/oligomerisation reactions found in the 'complex' component, cannot suggest fix.")

        if not fix_identified:
            console.print("\nNo automatic fix identified for this node.")
        else:
            console.print(f"Suggested fixes:")

            # print the suggested fixes
            for fix in fixes:
                console.print(f"   - {fix}")

        console.print()

        if interactive:
            # plot the subgraph
            plot_subgraph(subgraph, species)

            # if no fixes, wait for the user to skip to the next one or quit
            if not fixes:
                action = console.input("Enter 's' to skip to the next node, or 'q' to quit: ").strip().lower()
                if action == 's':
                    console.print(f"   - Skipping node {node_name}")
                    # close the plot
                    plt.clf()
                    continue
                elif action == 'q':
                    console.print("Exiting model fixing.")
                    break
                else:
                    console.print("Invalid input, skipping.")
                    continue

            # ask the user what to do if we found a fix
            action = console.input("Enter 'a' to apply the fix(es)', 's' to skip, or 'q' to quit: ").strip().lower()
            plt.clf()
            if action == 'a':
                apply_model_fixes(pss_adapter, fixes)
            elif action == 's':
                console.print(f"   - Skipping node {node_name}")
                continue
            elif action == 'q':
                console.print("Exiting model fixing.")
                break
            else:
                console.print("Invalid input, skipping.")
                continue

        else:
            # non-interactive mode, just apply the fixes
            if fixes and apply_fixes:
                apply_model_fixes(pss_adapter, fixes)

        console.print()

    return 0


def apply_model_fixes(pss_adapter, fixes):

    for fix in fixes:
        # implement the fix, find the reaction and species
        reaction = pss_adapter.reactions.get(fix.reaction_id)
        if not reaction:
            console.print(f"Warning: Reaction {fix.reaction_id} not found, cannot apply fix.")
            continue
        if fix.species_role == 'substrate':
            species_list = reaction.substrates
        elif fix.species_role == 'product':
            species_list = reaction.products
        elif fix.species_role == 'modifier':
            species_list = reaction.modifiers
        else:
            console.print(f"Warning: Invalid species role {fix.species_role}, cannot apply fix.")
            continue

        species_found = False
        for species in species_list:
            if species.name == fix.species_name:
                species_found = True
                break

        if not species_found:
            console.print(f"Warning: Species {fix.species_name} not found in reaction {reaction.id}, cannot apply fix.")
            continue

        if fix.new_form:
            console.print(f"Applying fix: Changing form of {species.name} in reaction {reaction.id} from {species.form} to {fix.new_form}.")
            species.form = fix.new_form
        elif fix.new_location:
            console.print(f"Applying fix: Changing location of {species.name} in reaction {reaction.id} from {species.compartment} to {fix.new_location}.")
            species.compartment = fix.new_location
        else:
            console.print(f"Warning: No new form or location specified in fix, cannot apply.")

    console.print()
    console.print("[bold green]Model fixes applied!")
    return
