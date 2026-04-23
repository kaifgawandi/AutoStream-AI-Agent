import os
from dotenv import load_dotenv

load_dotenv()
from langchain_core.tools import tool
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import MemorySaver # <-- NEW: Memory tool

@tool
def mock_lead_capture(name: str, email: str, platform: str) -> str:
    """Use this tool ONLY when you have collected the user's name, email, and creator platform."""
    print(f"\n✅ SUCCESS! Lead captured successfully: {name}, {email}, {platform}\n")
    return "Lead capture successful. Thank the user and end the workflow."

class State(TypedDict):
    messages: Annotated[list, add_messages]

# 1. Wake up the Gemini AI model
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

# 2. Give the AI its toolbelt
llm_with_tools = llm.bind_tools([mock_lead_capture])


# --- 1. THE INSTRUCTIONS (SYSTEM PROMPT) ---
system_prompt = """You are a helpful AI agent for a SaaS company named AutoStream.
Your jobs:
1. Greeting: Greet the user nicely ONLY at the beginning. Do not say hello in every message.
2. Pricing/Product: Answer using ONLY this knowledge base:
   - Basic Plan: $29/month. 10 videos/month, 720p.
   - Pro Plan: $79/month. Unlimited videos, 4K, AI captions.
   - Policies: No refunds after 7 days. 24/7 support only on Pro plan.
3. Lead Capture: If the user wants to buy or sign up, ask for their Name, Email, and Platform. Ask for them conversationally. Once you have all three, use the mock_lead_capture tool!
"""

# --- 2. THE ACTIONS (NODES) ---
def call_ai(state: State):
    # Combine the instructions with the chat history
    messages = [SystemMessage(content=system_prompt)] + state["messages"]
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}

# Create the node that actually runs the tool
tool_node = ToolNode(tools=[mock_lead_capture])

# --- 3. WIRING IT ALL TOGETHER (THE GRAPH) ---
workflow = StateGraph(State)

# Add our two actions to the graph
workflow.add_node("agent", call_ai)
workflow.add_node("tools", tool_node)

# Draw the lines connecting them
workflow.add_edge(START, "agent") 
workflow.add_conditional_edges("agent", tools_condition) 
workflow.add_edge("tools", "agent") 

# Compile the final application WITH MEMORY (Checkpointer)
memory = MemorySaver()
app = workflow.compile(checkpointer=memory)

# --- 4. RUNNING THE CHAT ---
# We give the chat a thread_id so the memory knows which conversation to remember
config = {"configurable": {"thread_id": "1"}} 

print("🤖 AutoStream Agent is awake! (Type 'quit' to stop)")
while True:
    user_text = input("\nYou: ")
    if user_text.lower() == "quit":
        break
        
    # Send user message to the AI, passing the memory config!
    for chunk in app.stream({"messages": [HumanMessage(content=user_text)]}, config=config, stream_mode="values"):
        last_message = chunk["messages"][-1]
        
        # Only print the AI's response
        if last_message.type == "ai":
            content = last_message.content
            
            # Clean the data package
            if isinstance(content, list) and len(content) > 0:
                content = content[0].get("text", "")
                
            if content:
                print(f"Agent: {content}")