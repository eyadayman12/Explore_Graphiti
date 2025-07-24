from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from connect_to_knowldge_db import KnowldgeGraphDB
from datetime import datetime, timezone
from neo4j import GraphDatabase
from graphiti_core.nodes import EpisodeType
from contextlib import asynccontextmanager

# Initialize Graphiti and Neo4j driver
db = KnowldgeGraphDB()

@asynccontextmanager
async def lifespan(app: FastAPI):
    global driver, graphiti
    driver = GraphDatabase.driver(db.neo4j_uri, auth=(db.neo4j_user, db.neo4j_password))
    graphiti = db.graphiti_client()
    yield
    driver.close()
    graphiti.close()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.post("/add_node/")
async def add_node(request: dict):
    data = request.get("data")
    if not data or "properties" not in data:
        raise HTTPException(status_code=400, detail="Invalid request: data and properties required")

    try:
        name = data["properties"]["name"]
        episode_body=data["properties"]["content"]
        source=data["properties"]["source"]
        source_description=data["properties"]["source_description"]
        reference_time=datetime.now(timezone.utc)
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error missing parameters: {str(e)}")
    try:
        await graphiti.add_episode(
            name=name,
            episode_body=episode_body,
            source=EpisodeType(source),
            source_description=source_description,
            reference_time=reference_time
        )
        return {"status": "success", "data": {"uuid": "generated-uuid"}, "message": "Node added successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error adding node: {str(e)}")

@app.post("/delete_node/")
def delete_node(request: dict):
    uuid = request.get("uuid")
    if not uuid:
        raise HTTPException(status_code=400, detail="Invalid request: id required")

    with driver.session() as session:
        delete_rels_query = """
        MATCH (n {uuid: $uuid})-[r]->()
        DELETE r
        """
        result =  session.run(delete_rels_query, {"uuid": uuid})
        result.consume()
        
        delete_node_query = "MATCH (n {uuid: $uuid}) DELETE n"
        result = session.run(delete_node_query, {"uuid": uuid})
        summary = result.consume()
        
        if summary.counters.nodes_deleted == 0:
            raise HTTPException(status_code=404, detail=f"Node with uuid {uuid} not found")
    return {"status": "success", "data": None, "message": f"Node {uuid} deleted"}

@app.post("/update_edge/")
def update_edge(request: dict):
    source_uuid = request.get("source_id")
    target_uuid = request.get("target_id")
    rel_type = request.get("rel_type")
    properties = request.get("properties", {})

    if not all([source_uuid, target_uuid, rel_type]):
        raise HTTPException(status_code=400, detail="Invalid request: source_id, target_id, and rel_type required")

    with driver.session() as session:
        query = "MATCH (s)-[r:%s]->(t) WHERE s.uuid = $source_uuid AND t.uuid = $target_uuid SET r += $props"
        result = session.run(query % rel_type, {"source_uuid": source_uuid, "target_uuid": target_uuid, "props": properties})
        summary = result.consume()
        if summary.counters.properties_set == 0:
            raise HTTPException(status_code=404, detail="Edge not found or no properties updated")
    return {"status": "success", "data": None, "message": "Edge updated"}

@app.post("/execute_cypher/")
def execute_cypher(request: dict):
    query = request.get("query")
    params = request.get("params", {})

    if not query:
        raise HTTPException(status_code=400, detail="Invalid request: query required")

    with driver.session() as session:
        result = session.run(query, params)
        return {"status": "success", "data": [record.data() for record in result], "message": "Query executed"}