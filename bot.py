import os
from langchain_openai import ChatOpenAI
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from tools import agent_tools

def create_agent():
    # Initialize the OpenAI model
    llm = ChatOpenAI(model="gpt-4o", temperature=0)

    # Simple prompt template for the AI Agent
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful production support AI assistant."
                   "You can query the application database, fetch CloudWatch logs, and search the ServiceNow knowledge base for historical incident resolutions.\n"
                   "When investigating an issue, ALWAYS search the ServiceNow knowledge base using the exact exception name if you find specific error messages in the logs."),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ])

    # Construct the tool calling agent
    agent = create_tool_calling_agent(llm, agent_tools, prompt)
    
    # Create the agent executor
    agent_executor = AgentExecutor(agent=agent, tools=agent_tools, verbose=True)
    return agent_executor


if __name__ == "__main__":
    
    if "OPENAI_API_KEY" not in os.environ:
        print("Error: OPENAI_API_KEY environment variable is not set.")
        print("Please set it in your environment: 'export OPENAI_API_KEY=your_key'")
        exit(1)

    print("==================================================")
    print("Welcome to the Production Support Bot (CLI Test).")
    print("Available tools: Text-to-SQL DB, CloudWatch Logs Mock, ServiceNow RAG Mock")
    print("Type 'exit' to quit.")
    print("==================================================\n")

    executor = create_agent()

    while True:
        user_input = input("Support Rep: ")
        if user_input.lower() in ["exit", "quit"]:
            break
        
        try:
            response = executor.invoke({"input": user_input})
            print(f"\nAI Agent: {response['output']}\n")
        except Exception as e:
            print(f"\n[Error during agent execution: {e}]\n")
