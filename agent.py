from __future__ import annotations
from typing import Dict, List, Optional
from dataclasses import dataclass
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from rich.markdown import Markdown
from rich.console import Console
from rich.live import Live
import asyncio
import os

from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai import Agent, RunContext
from graphiti_core import Graphiti
from connect_to_knowldge_db import KnowldgeGraphDB
from graphiti_core.search.search_config_recipes import NODE_HYBRID_SEARCH_RRF



load_dotenv()

graphiti = KnowldgeGraphDB()
@dataclass
class GraphitiDependencies:
    graphiti_client: Graphiti

def get_model():
    """Configure and return the LLM model to use."""
    model_choice = "gpt-4.1-mini"
    api_key = os.getenv('OPENAI_API_KEY')

    return OpenAIModel(model_choice, provider=OpenAIProvider(api_key=api_key))

graphiti_agent = Agent(
    get_model(),
    
    system_prompt=""" an expert Arabic language teacher specializing in the official curriculum for the 2nd secondary year with access to a knowledge graph filled with temporal data about  Arabic Subject for secondary 2nd year.
    When the user asks you a question, use your search tool to query the knowledge graph and then answer honestly.
    Be willing to admit when you didn't find the information necessary to answer the question.
    Use the avaliable information to answer and dont repeat the same piece of information ever.
    """,
    deps_type=GraphitiDependencies
)

class GraphitiSearchResult(BaseModel):
    """Model representing a search result from Graphiti."""
    uuid: str = Field(description="The unique identifier for this fact")
    name: str = Field(description="The name of retrieved content the knowledge graph")
    summary:str = Field(description="The summary of the piece of information retrieved from the knowledge graph")

@graphiti_agent.tool
async def search_graphiti(ctx: RunContext[GraphitiDependencies], query: str) -> List[GraphitiSearchResult]:
    
    graphiti = ctx.deps.graphiti_client
    
    try:
        # Perform the search
        node_search_config = NODE_HYBRID_SEARCH_RRF.model_copy(deep=True)
        node_search_config.limit = 5 
        results = await graphiti._search(query=query, config=node_search_config)
        global formatted_results
        formatted_results = []
        for result in results.nodes:
            formatted_result = GraphitiSearchResult(
                uuid=result.uuid,
                name=result.name,
                summary = result.summary
            )
            
            formatted_results.append(formatted_result)
        
        return formatted_results
    except Exception as e:
        print(f"Error searching Graphiti: {str(e)}")
        raise

async def main():
    """Run the Graphiti agent with user queries."""
    print("Enter 'exit' to quit the program.")
    
    graphiti_client = graphiti.graphiti_client()
    
    try:
        await graphiti_client.build_indices_and_constraints()
        print("Graphiti indices built successfully.")
    except Exception as e:
        print(f"Note: {str(e)}")
        print("Continuing with existing indices...")

    console = Console()
    messages = []
    
    try:
        while True:
            user_input = input("\n[You] ")
            
            if user_input.lower() in ['exit', 'quit', 'bye', 'goodbye']:
                print("Goodbye!")
                break
            
            try:
                print("\n[Assistant]")
                with Live('', console=console, vertical_overflow='visible') as live:
                    # Pass the Graphiti client as a dependency
                    deps = GraphitiDependencies(graphiti_client=graphiti_client)
                    
                    async with graphiti_agent.run_stream(
                        user_input, message_history=messages, deps=deps
                    ) as result:
                        curr_message = ""
                        async for message in result.stream_text(delta=True):
                            curr_message += message
                            live.update(Markdown(curr_message))
                            print(formatted_results)
                    
                    messages.extend(result.all_messages())
                
            except Exception as e:
                print(f"\n[Error] An error occurred: {str(e)}")

    finally:
        # Close the Graphiti connection when done
        await graphiti_client.close()
        print("\nGraphiti connection closed.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nProgram terminated by user.")
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")
        raise