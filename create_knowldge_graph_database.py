import asyncio
import os
from datetime import datetime, timezone
import json
from graphiti_core  import Graphiti
from graphiti_core.nodes import EpisodeType
import os
from dotenv import load_dotenv

load_dotenv()
    
neo4j_uri = os.environ.get('NEO4J_URI')
neo4j_user = os.environ.get('NEO4J_USER')
neo4j_password = os.environ.get('NEO4J_PASSWORD')
        
graphiti = Graphiti(neo4j_uri,
                    neo4j_user,
                    neo4j_password)

async def main():
    try:
        
        await graphiti.build_indices_and_constraints()
        
        with open("epsiodes.json", "r") as f:
            epsiodes = json.load(f)

        for epsiode in epsiodes:
            epsiode["type"] = EpisodeType(epsiode["type"])


        for epsiode in epsiodes:
            await graphiti.add_episode(
                name = epsiode["name"],
                episode_body = epsiode['content']
                if isinstance(epsiode["content"], str) 
                else json.dumps(epsiode['content']),
                source=epsiode["type"],
                source_description=epsiode["description"],
                reference_time=datetime.now(timezone.utc)
            )

    finally:
        await graphiti.close()
        print('\nConnection closed')


if __name__ == "__main__":
    
    asyncio.run(main())