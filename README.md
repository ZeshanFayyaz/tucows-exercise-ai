# Tucows AI Interview Exercise: Knowledge Assistant for Support Team

## Overview

This project is a small Retrieval-Augmented Generation (RAG) system designed to help support teams handle customer tickets more quickly and consistently. It pulls from documentation and predefined policy FAQs, finds the most relevant context, and returns a JSON response with an answer, references, and a recommended action.

Everything runs in Docker Compose to ensure an easy setup:

- FastAPI serves the Knowledge Assistant API

- Ollama runs the language model locally (default: llama3.1:latest)

- A single docker compose up brings the whole system online

The result is that support agents get clear, structured answers without having to search through docs themselves.

---

## Tech Stack

- **FastAPI** - lightweight framework for serving the Knowledge Assistant API
- **SentenceTransformers + FAISS** - embedding documentation and retrieving document chunks
- **Ollama** - LLM backend for generating structured MCP-compliant answers
- **Pydantic** - schema validation for request and response models
- **Docker Compose** - setup for reproducible local deployment
- **Pytest** - unit testing framework to ensure quality and reliability

---

## Key Features 

- **Context-aware answers** – looks up the most relevant chunks from documentation and policies before replying.  
- **Helper script (`./ask.sh`)** – interactive CLI to test tickets without curl/Postman; type a ticket and get instant JSON back 
- **MCP-compliant output** – always returns JSON with `answer`, `references`, and `action_required`.  
- **Expandable action set** – includes common support workflows like WHOIS updates, abuse escalation, billing, and more.  
- **Containerized setup** – everything runs through Docker Compose with one command.   
- **Unit tested** – core pieces (models, RAG, LLM integration) covered with simple pytest tests.  
- **Controlled action space** – the assistant selects from a predefined set of support actions. This guarantees consistent and schema-compliant outputs. It makes the system more reliable and integration-ready, while still leaving room to expand the action set over time.

---

## Running Locally  

To run the Knowledge Assistant on your machine:

1. **Clone the repository**
   ```bash
   git clone https://github.com/ZeshanFayyaz/tucows-exercise-ai.git

   cd tucows-exercise-ai
   ```

2. **Build and start the containers**

    Make sure Docker is running, then run: 
    ```bash
    docker compose up --build
    ```

    This starts: 
    - FastAPI server (`listening on http://127.0.0.1:8000`)

    - Ollama LLM backend (`port 11434`)

3. **Pull the model (only needed for the first run)**

    In another terminal: 
    ```bash
    docker compose exec ollama ollama pull llama3.1:latest
    ```


4. **Ask a question**

   Make the provided helper script executable:  
   ```bash
   chmod +x ./ask.sh
   ```

    Using the provided helper script: 
    ```bash
    ./ask.sh
    ```

    Example: 
    ```text
    Enter ticket text: My domain was suspended and I didn’t get any notice. How do I reactivate it?
    ```

    The system will return a structured JSON response like: 
    ```json
    {
      "answer": "Update your WHOIS details and contact support to request reactivation.",
      "references": ["Policy: Domain Suspension Guidelines, Section 4.2"],
      "action_required": "escalate_to_abuse_team"
    }
    ```

---

## Architecture 

The following image depicts the system architecture: 

<div align="center">
  <img src="refs/architecture.svg" alt="Architecture Diagram" width="400"/>
</div>

The system has several main pieces that work together:

1. **Customer Ticket**  
   - The entry point to the system. A user (e.g. support agent) submits a raw ticket.  
   - Input can be provided via the included `./ask.sh` script (interactive CLI) or directly through the REST API.  

2. **FastAPI Server**  
   - Acts as the orchestrator of the pipeline.  
   - Exposes the `/resolve-ticket` endpoint, which accepts the raw ticket text.  
   - Handles request routing, input validation, and coordinates the downstream RAG process.  
   - Ensures the caller only ever sees clean JSON output (never raw LLM text). 

3. **KnowledgeBase**  
   - Holds the support and policy documents that the model will ground its answers in.  
   - Each document is split into overlapping chunks to preserve context.  
   - Chunks are embedded using a SentenceTransformer and stored in a FAISS vector index for efficient similarity search.  
   - This turns free-text knowledge into something the system can “search like a database.”  

4. **Retrieval**
   - When a new ticket is submitted, the text is vectorized and compared against the FAISS index.  
   - The top-k most relevant chunks are retrieved (the ones most likely to help answer the ticket).  
   - This ensures the system doesn’t hallucinate but instead grounds answers in the provided knowledge base. 

5. **MCP Prompt Builder**
   - Combines the original ticket text with the retrieved chunks from the knowledge base.  
   - Wraps everything into a structured JSON prompt that follows **MCP (Machine-Consumable Prompting) principles**:  
     - **Consistency** → every answer must follow the same JSON schema (`answer`, `references`, `action_required`).  
     - **Traceability** → references link back to exact document chunks, so agents know *why* an answer was given.  
     - **Actionability** → ensures the model doesn’t just “chat,” but clearly states what action (if any) is required.  
     - **Robustness** → schema validation ensures invalid outputs are caught and retried automatically.  
   - This step guarantees that even though the model is generative, the API response stays predictable, machine-parseable, and aligned with support workflows.

6. **LLM Wrapper**
   - Sends the structured prompt to the Ollama LLM backend (default: `llama3.1:latest`).  
   - The wrapper enforces JSON-only responses, validates them against a Pydantic schema, and retries if needed.  
   - I also experimented with smaller models, but found the answers to be noticeably less accurate and less useful.  
   - For this reason, the default is set to `llama3.1:latest`, which gave the best balance of speed and quality in testing.

7. **MCP JSON Response**
   - The final output returned to the client.  
   - Always follows the MCP JSON schema with three keys:  
     - `"answer"` → plain-language resolution for the support agent.  
     - `"references"` → source document chunks used to build the answer.  
     - `"action_required"` → explicit next step (if any).

---

## Configuration

The app reads environment variables for LLM backend:

- `OPENAI_BASE_URL` – defaults to `http://ollama:11434/v1`
- `OPENAI_API_KEY` – dummy key for Ollama, real key if using OpenAI
- `OPENAI_MODEL` – default: `llama3.1:latest`

These are set automatically in `docker-compose.yml`, but can be overridden.

---

## Future Improvements

- Add support for multi-turn conversations (not just single tickets)  
- Improve action classification with a larger set of workflows  
- Experiment with faster/smaller LLM models to reduce response latency (smaller models show to decrease response quality severely) 


