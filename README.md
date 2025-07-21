# skm-pss-adapters
Export adapters from PSS neo4j db to other (flatfile) formats


## PSS database

For testing, a snapshot of the PSS database is available at:
https://github.com/NIB-SI/skm-neo4j

### Connection to Neo4j settings

You can pass the connection settings (uri, username, password) to the CLI using command-line arguments: 

```bash
  --neo4j-uri TEXT       Neo4j connection URI.
  --neo4j-user TEXT      Neo4j username.
  --neo4j-password TEXT  Neo4j password.
```

Alternatively, you can set these  in an `.env` file in the current directory. The file should contain the following variables:
```bash
MY_NEO4J_URI=bolt://localhost:7687
MY_NEO4J_USER=neo4j
MY_NEO4J_PASSWORD=password
```

If you used the defaults in the skm-neo4j repo, you can use the `.env.example` file as provided. 
```bash
mv .env.example .env
```

## Usage

Create environemnt with dependencies:

```bash
mamba create -n pss-sbml conda-forge::neo4j-python-driver conda-forge::python-libsbml conda-forge::pyyaml conda-forge::click
```


### SBML:

Create the SBML file using the CLI:
```bash
python pss_adapter_cli.py to-sbml output.sbml --access public
```
