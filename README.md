# Social-to-Lead Agentic Workflow: AutoStream

This repository contains a Conversational AI Agent built for the fictional SaaS company "AutoStream." It features intent detection, RAG-powered knowledge retrieval, and tool execution for lead capture, built using LangGraph and Gemini 2.5 Flash.

## How to Run Locally

1. Clone this repository to your local machine.
2. Create a virtual environment: `python -m venv myenv`
3. Activate the virtual environment:
   - Windows: `myenv\Scripts\activate`
   - Mac/Linux: `source myenv/bin/activate`
4. Install the dependencies: `pip install -r requirements.txt`
5. Create a `.env` file in the root directory and add your Google Gemini API Key:
   `GOOGLE_API_KEY=your_key_here`
6. Run the agent: `python agent.py`

## Architecture Explanation

To build this agentic workflow, I chose **LangGraph** over AutoGen because LangGraph provides fine-grained, cyclical control over the agent's reasoning loop using a graph-based state machine. Rather than relying on autonomous agents talking to each other (which can sometimes drift off-topic), LangGraph allows me to explicitly define nodes (the LLM and the Tools) and the conditional edges between them. This ensures the agent reliably triggers the `mock_lead_capture` tool only when all required parameters (Name, Email, Platform) are gathered.

**State Management:**
State is managed using LangGraph's `StateGraph` and a `TypedDict`. The state acts as the "memory dictionary" for the graph, specifically storing a list of `messages`. As the conversation progresses, new `HumanMessage` and `SystemMessage` objects are appended to this list using the `add_messages` reducer. To fulfill the requirement of retaining memory across multiple turns, I implemented LangGraph's `MemorySaver()` checkpointer. By passing a `thread_id` into the configuration during the stream invocation, the checkpointer saves the entire message history locally, allowing the agent to remember context, answer follow-up questions, and maintain the user's intent across the required 5-6 conversational turns.

## WhatsApp Webhook Integration

To deploy this agent to WhatsApp, I would use the **WhatsApp Business API** integrated with a Python backend server (like **FastAPI** or **Flask**). 

1. **Webhook Setup:** I would configure a webhook endpoint on my FastAPI server and register that URL in the Meta Developer Portal. 
2. **Receiving Messages:** When a user sends a message on WhatsApp, Meta sends a `POST` request to my webhook containing the user's message text and phone number.
3. **Processing with LangGraph:** My server would parse the JSON payload, extract the text, and pass it into my compiled LangGraph `app.stream()`. I would use the user's WhatsApp phone number as the LangGraph `thread_id` to ensure their specific conversation history is retrieved from the `MemorySaver`.
4. **Responding:** Once the LangGraph agent generates its response, my server would take that output string and make a `POST` request back to the WhatsApp Cloud API (`/messages` endpoint), which instantly delivers the message to the user's phone.
