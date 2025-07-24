from graphiti_core  import Graphiti
import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

class KnowldgeGraphDB:

    def __init__(self):

        self.neo4j_uri = os.environ.get('NEO4J_URI')
        self.neo4j_user = os.environ.get('NEO4J_USER')
        self.neo4j_password = os.environ.get('NEO4J_PASSWORD')
    
    def get_neo4j_data(self):
        return self.neo4j_uri, self.neo4j_user, self.neo4j_password

    def graphiti_client(self): 

        graphiti = Graphiti(self.neo4j_uri,
                            self.neo4j_user,
                            self.neo4j_password)
        
        return graphiti
    
    def inspect_schema(self):
        driver = GraphDatabase.driver(self.neo4j_uri, auth=(self.neo4j_user, self.neo4j_password))
        try:
            with driver.session() as session:
                nodes = session.run("CALL db.labels() YIELD label RETURN label")
                node_types = [record["label"] for record in nodes]
                edges = session.run("CALL db.relationshipTypes() YIELD relationshipType RETURN relationshipType")
                edge_types = [record["relationshipType"] for record in edges]
                node_props = session.run(
                    "CALL db.schema.nodeTypeProperties() YIELD nodeLabels, propertyName "
                    "RETURN nodeLabels, collect(propertyName) AS properties"
                )
                node_properties = {}
                edge_properties = {}

                edge_props = session.run(
                    "CALL db.schema.relTypeProperties() YIELD relType, propertyName "
                    "RETURN relType, collect(propertyName) AS properties"
                )
                for node_record, edge_record in zip(node_props, edge_props):
                    #print(node_record['nodeLabels'][0], node_record["properties"])
                    print(type(edge_record['relType']), edge_record["properties"])
                    node_properties[node_record['nodeLabels'][0]] = node_record["properties"]
                    edge_properties[edge_record['relType']] = edge_record["properties"]

                return {
                    "node_types": node_types,
                    "edge_types": edge_types,
                    "node_properties": node_properties,
                    "edge_properties": edge_properties
                }
        finally:
            driver.close()