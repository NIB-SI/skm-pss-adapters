'''
Graph class for Neo4j database interaction.
This class provides methods to connect to a Neo4j database
and execute queries.
'''

from neo4j import GraphDatabase

class Graph:

    def __init__(self, uri='bolt://neo4j:7687', user='neo4j', pwd='password'):
        # wait 30s for db to startup TODO
        self.driver = GraphDatabase.driver(uri, auth=(user, pwd))

    def close(self):
        self.driver.close()

    def run_query(self, query_function, *args):

        results = []
        with self.driver.session() as session:
            query_result = session.read_transaction(query_function, *args)
            # current_app.logger.info(query_result)

            for r in query_result:
                results.append(r)

        return results
