# skm-pss-adapters
Export adapters from PSS neo4j db to other (flatfile) formats


## SBML:

Create environemnt with dependencies:

```bash
mamba create -n pss-sbml conda-forge::neo4j-python-driver conda-forge::python-libsbml conda-forge::pyyaml conda-forge::click
```


Create the SBML file using the CLI:
```bash
python pss_adapter_cli.py to-sbml output.sbml --access public --neo4j-uri bolt://heron:7687
```
