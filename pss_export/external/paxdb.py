''' Use paxdb to get protein abundances
'''
import os
import requests
import pandas as pd

PAXDB_BASE_URL = 'https://pax-db.org/downloads/'
PAXDB_VERSION = '6.0'

def download_abundances_file(taxon, tissue):
    '''
    '''

    # check if the file is already downloaded
    file_name = f'paxdb_{taxon}_{tissue}.tsv'
    if os.path.exists(file_name):
        return f'paxdb_{tissue}.tsv'

    url = f'{PAXDB_BASE_URL}/{PAXDB_VERSION}/datasets/{taxon}/{taxon}-{tissue}-integrated.txt'
    response = requests.get(url)
    with open(file_name, 'wb') as f:
        f.write(response.content)
    return file_name

def parse_abundances_file(file_path):
    '''
    '''
    df = pd.read_csv(file_path, sep='\t', comment='#', names=['protein_id', 'abundance'])

    # protein_id (3702.AT5G09660.4) to gene id (e.g. AT5G09660)
    df["gene_id"] = df["protein_id"].apply(lambda x: x.split('.')[1] if pd.notnull(x) else x)

    # TODO: handle multiple proteins for the same gene (e.g. average, max, sum)

    abundances = pd.Series(df.abundance.values, index=df.gene_id).to_dict()
    return abundances

def get_gene_abundance(gene_id, taxon='3702', tissue='leaf'):
    '''
    '''
    file_path = download_abundances_file(taxon, tissue)
    abundances = parse_abundances_file(file_path)
    return abundances.get(protein_id, None)

if __name__ == '__main__':
    # Example usage
    gene_id = 'ATCG00490'
    taxon = '3702'  # Arabidopsis thaliana
    tissue = 'leaf'

    abundances = get_gene_abundance(gene_id, taxon, tissue)
    if abundances is not None:
        print(f'Protein {gene_id} has abundances of {', '.join(abundances)} in {tissue}.')
    else:
        print(f'Protein {gene_id} not found in {tissue} data.')
