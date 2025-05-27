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
@click.option("--neo4j-uri", default="bolt://localhost:7687", help="Neo4j connection URI.")
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose output.")
def to_sbml(access, neo4j_uri, filename, verbose):
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

    # Your actual logic here
    try:

        # connect to pSS in neo4j:
        graph = Graph(neo4j_uri)
        adapter = PSSAdapter(graph)

        adapter.create_sbml(filename=filename, access=access)
        
        if verbose:
            click.secho("SBML export complete.", fg="green")

    except Exception as e:
        click.secho(f"Error: {e}", fg="red", err=True)
        raise click.Abort()

if __name__ == "__main__":
    cli()
