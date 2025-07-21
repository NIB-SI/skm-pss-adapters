#!/usr/bin/env python3

import click

from skm_pss_adapters.graph import Graph
from skm_pss_adapters.pss_adapter import PSSAdapter


@click.group()
def cli():
    """Top-level CLI entrypoint."""
    pass

@cli.command()
@click.argument("filename", type=click.Path())
@click.option("--access",  default='public', help="Use public access data.")
@click.option("--neo4j-uri", default=None, help="Neo4j connection URI.")
@click.option("--neo4j-user", default=None, help="Neo4j username.")
@click.option("--neo4j-password", default=None, help="Neo4j password.")
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose output.")
@click.option("--include_genes", is_flag=True, help="Include genes as species (transcription reactions).")
@click.option("--entities_table", default=None, type=click.Path(), help="Path to also export a table of entities in model.")
def to_sbml(access, neo4j_uri, neo4j_user, neo4j_password, filename, verbose, include_genes, entities_table):
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
        adapter = PSSAdapter(graph, include_genes=include_genes)

        adapter.create_sbml(filename=filename, access=access, entities_table=entities_table)

        if verbose:
            click.secho("SBML export complete.", fg="green")

    except Exception as e:
        click.secho(f"Error: {e}", fg="red", err=True)
        raise click.Abort()

if __name__ == "__main__":
    cli()
