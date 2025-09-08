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

Create environment with dependencies:

```bash
mamba create -n pss-sbml conda-forge::neo4j-python-driver conda-forge::python-libsbml conda-forge::pyyaml conda-forge::click
```

If using the model fixes module, also install the following dependecies:
```bash 
pip install pandas networkx rich matplotlib
```

### SBML:

To view the CLI options:
```bash
python pss_adapter_cli.py to-sbml --help
```

Create the SBML file using the CLI:
```bash
python pss_adapter_cli.py to-sbml output.sbml --access public
```


Using the model-fixing functions:
```bash
python pss_adapter_cli.py to-sbml output-model-fixes.sbml --access public --model-fixes-identify  --model-fixes-apply
```

To add equations to the SBML file, you can use SBMLsqueezer from 
https://github.com/draeger-lab/SBMLsqueezer, e.g.
```bash
java -jar  /path..to..jar/SBMLsqueezer-2.2.jar --sbml-in-file output.sbml  --sbml-out-file output-squeezed
```

Known limitations and issues:
- The SBML file does not contain equations for the reactions.
	- You can add the equations using SBMLsqueezer as described above.
- Continuous updates to the PSS database means that the model may not be connected or completely consistent with modelling.
- Some molecules may be disconnected in the SBML file, for example if:
	- They occur in multiple compartments, but are not connected by a transport reaction.
	- A protein is formed by a translation reaction, but the protein is not "activated" by an "activation" reaction.
	- A complex is formed by a reaction, but the complex is not "activated" by an "activation" reaction.

## TODOs

- Make a TOML file for installing from pip and a requirements file with fixed dependency version for testing