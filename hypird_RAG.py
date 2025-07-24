import asyncio
from connect_to_knowldge_db import KnowldgeGraphDB

graphiti = KnowldgeGraphDB().graphiti_client()
            
async def main():

    try:
        query = "لماذا اللغة العربية مهمة؟"
        results = await graphiti.search(query)
        for result in results:
            print(f'UUID: {result.uuid}')
            print(f'Fact: {result.fact}')
            if hasattr(result, 'valid_at') and result.valid_at:
                print(f'Valid from: {result.valid_at}')
            if hasattr(result, 'invalid_at') and result.invalid_at:
                print(f'Valid until: {result.invalid_at}')
            print('---')
        
        if results and len(results) > 0:
            center_node_uuid = results[0].source_node_uuid
            print('\nReranking search results based on graph distance:')
            print(f'Using center node UUID: {center_node_uuid}')
            reranked_results = await graphiti.search(
                query, center_node_uuid=center_node_uuid
            )
        # Print reranked search results
        print('\nReranked Search Results:')
        for result in reranked_results:
            print(f'UUID: {result.uuid}')
            print(f'Fact: {result.fact}')
            if hasattr(result, 'valid_at') and result.valid_at:
                print(f'Valid from: {result.valid_at}')
            if hasattr(result, 'invalid_at') and result.invalid_at:
                print(f'Valid until: {result.invalid_at}')
            print('---')
        else:
            print('No results found in the initial search to use as center node.')

    finally:
        await graphiti.close()
        print('\nConnection closed')


if __name__ == "__main__":
    
    asyncio.run(main())
