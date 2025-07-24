from connect_to_knowldge_db import KnowldgeGraphDB

def print_schema():
    db = KnowldgeGraphDB()
    schema = db.inspect_schema()
    print("Node Types:", schema["node_types"])
    print("Edge Types:", schema["edge_types"])
    print("Node Properties:", schema["node_properties"])
    print("Edge Properties:", schema["edge_properties"])

if __name__ == "__main__":
    print_schema()