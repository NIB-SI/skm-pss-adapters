#!/usr/bin/env python3

import click
import functools

from skm_pss_adapters.graph import Graph
from skm_pss_adapters.pss_adapter import PSSAdapter

def neo4j_common_params(func):
    @click.option("--access",  default='public', help="Use public access data.")
    @click.option("--neo4j-uri", default=None, help="Neo4j connection URI.")
    @click.option("--neo4j-user", default=None, help="Neo4j username.")
    @click.option("--neo4j-password", default=None, help="Neo4j password.")
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper

def modelfixing_common_params(func):
    @click.option("--model-fixes-identify", is_flag=True, help="Run the model fixing module to identify model inconsistencies and suggest automatic fixes.")
    @click.option("--model-fixes-apply", is_flag=True, help="If running the model fixing module, also apply all suggested model fixes")
    @click.option("--model-fixes-interactive", is_flag=True, help="If running the model fixing module, enter interactive mode to visualise and optionally apply fixes per node. Overrides `--model-fixes-apply`. ")
    @click.option("--nodes-to-ignore", default='default', help="Nodes to ignore during export. Default is 'default', which ignores nodes defined in the configuration.")
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper

@click.group()
def cli():
    """Top-level CLI entrypoint."""
    pass

@cli.command()
@neo4j_common_params
@modelfixing_common_params
@click.argument("filename", type=click.Path())
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose output.")
@click.option("--include-genes", is_flag=True, help="Include genes as species (transcription reactions).")
@click.option("--entities-table", default=None, type=click.Path(), help="Path to also export a table of entities in model.")
@click.option("--kinetic-laws", is_flag=True, help="Include kinetic laws (SBO term only) in SBML output.")
def to_sbml(access, neo4j_uri, neo4j_user, neo4j_password, model_fixes_identify, model_fixes_apply, model_fixes_interactive, nodes_to_ignore, filename, verbose, include_genes, entities_table, kinetic_laws):
    """
    Export model to SBML.

    ACCESS: Boolean flag (True or False) for public access.

    NEO4J_URI: Neo4j connection URI (e.g. bolt://localhost:7687).

    FILENAME: Output SBML file path.
    """
    if verbose:
        click.echo(f"Exporting to SBML...")
        click.echo(f"  Access: {access}")
        click.echo(f"  Neo4j URI: {neo4j_uri}")
        click.echo(f"  Output file: {filename}")

    try:

        # connect to pSS in neo4j:
        graph = Graph(uri=neo4j_uri, user=neo4j_user, pwd=neo4j_password)
        adapter = PSSAdapter(graph, include_genes=include_genes, nodes_to_ignore=nodes_to_ignore, model_fixes_identify=model_fixes_identify, model_fixes_apply=model_fixes_apply, model_fixes_interactive=model_fixes_interactive)

        adapter.create_sbml(filename=filename, access=access, entities_table=entities_table, kinetic_laws=kinetic_laws)

        if verbose:
            click.secho("SBML export complete.", fg="green")

    except Exception as e:
        click.secho(f"Error: {e}", fg="red", err=True)
        raise click.Abort()

if __name__ == "__main__":
    cli()
