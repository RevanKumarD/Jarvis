# TODO - Jarvis Development Tasks

## PHASE 1: Project Bootstrapping

- [x] Initialize Git Repository
- [x] Create .gitignore, .env.example
- [x] Add README with project purpose
- [x] Setup Project Structure
- [x] Create folders: /agents, /core, /ui, /utils
- [x] Add empty __init__.py to each (for Python modules)
- [x] Environment and Dependencies
- [x] Setup requirements.txt with specified dependencies
- [x] Create virtual environment + install deps
- [x] Create Basic .env and Model Loader
- [x] .env.example and a get_model() helper in utils/model.py

## PHASE 2: Define Core Architecture

- [ ] **Define Jarvis State (core/state.py)**
    - [ ] Create `core/state.py` file.
    - [ ] Define `JarvisState` Pydantic model.
        - [ ] Add `user_input` field (string).
        - [ ] Add `intent` field (string or list of strings).
        - [ ] Add `entities` field (dictionary or Pydantic model).
        - [ ] Add `actions` field (list of strings).
        - [ ] Add sub-agent output fields (e.g., `email_result`, `calendar_result`, `contact_result`, `web_search_result`, `content_result`) as optional dictionaries or Pydantic models.
    - [ ] Document the `JarvisState` model with comments.

- [ ] **Define LangGraph Workflow (core/graph.py)**
    - [ ] Create `core/graph.py` file.
    - [ ] Import necessary LangGraph components.
    - [ ] Define nodes for:
        - [ ] `gather_info` (initial information gathering).
        - [ ] `route_user_intent` (determine which agents to run).
        - [ ] `run_agents_in_parallel` (execute agents concurrently).
        - [ ] `aggregate_results` (combine agent outputs).
    - [ ] Implement the LangGraph graph structure.
    - [ ] Define the graph edges connecting the nodes.
    - [ ] Define the starting node.

- [ ] **Implement dynamic interrupt (interrupt())**
    - [ ] Create an `interrupt()` function in `core/graph.py`.
    - [ ] Implement logic to detect interrupt conditions (e.g., missing information, user request to stop).
    - [ ] Add an interrupt node to the graph and connect it to the appropriate nodes.

- [ ] **Add conditional branching to determine agent execution**
    - [ ] Implement logic in `route_user_intent` node to determine which agents to run based on user intent and required fields.
    - [ ] Add conditional edges to the graph based on the output of `route_user_intent`.

## PHASE 3: Agent Development

- [ ] **Information Gathering Agent**
    - [ ] Create `agents/information_gathering.py` file.
    - [ ] Define a Pydantic model for input validation.
    - [ ] Implement logic to extract missing fields from user messages.
    - [ ] Implement logic to validate structured input.

- [ ] **Email Agent**
    - [ ] Create `agents/email.py` file.
    - [ ] Define Pydantic models for input (`to`, `subject`, `message`) and output.
    - [ ] Implement simulated email sending logic.
    - [ ] Create a prompt for the language model.
    - [ ] Add necessary dependencies.

- [ ] **Calendar Agent**
    - [ ] Create `agents/calendar.py` file.
    - [ ] Define Pydantic models for input (`participants`, `date`, `time`) and output.
    - [ ] Implement simulated calendar creation logic.
    - [ ] Create a prompt for the language model.
    - [ ] Add necessary dependencies.

- [ ] **Contact Agent**
    - [ ] Create `agents/contact.py` file.
    - [ ] Define Pydantic models for input (`name` or `email`) and output.
    - [ ] Implement logic to resolve names to email/contact info.
    - [ ] Create a prompt for the language model.
    - [ ] Add necessary dependencies.

- [ ] **Web Search Agent**
    - [ ] Create `agents/web_search.py` file.
    - [ ] Define Pydantic models for input (`query`) and output (search results).
    - [ ] Implement logic to perform web searches.
    - [ ] Create a prompt for the language model.
    - [ ] Add necessary dependencies.

- [ ] **Content Creator Agent**
    - [ ] Create `agents/content_creator.py` file.
    - [ ] Define Pydantic models for input (`topic`, `tone`, `format`) and output (structured content).
    - [ ] Implement logic to generate structured content.
    - [ ] Create a prompt for the language model.
    - [ ] Add necessary dependencies.

- [ ] **Synthesizer Agent**
    - [ ] Create `agents/synthesizer.py` file.
    - [ ] Define Pydantic models for input (all agent outputs) and output (final message).
    - [ ] Implement logic to merge sub-agent results into a coherent output.
    - [ ] Create a prompt for the language model.
    - [ ] Add necessary dependencies.

## PHASE 4: Build Frontend (Optional CLI/Streamlit)

- [ ] **CLI using rich**
    - [ ] Create a CLI application using the `rich` library.
    - [ ] Implement input handling for user queries.
    - [ ] Display agent responses in a formatted way.

- [ ] **Streamlit UI with input + streaming output**
    - [ ] Create a Streamlit application (`ui/app.py`).
    - [ ] Implement input handling for user queries.
    - [ ] Display agent responses using streaming output.
    - [ ] Design a user-friendly interface.

## PHASE 5: Testing & Debugging

- [ ] **Unit test agents and graph routing**
    - [ ] Write unit tests for each agent.
    - [ ] Write integration tests for the LangGraph workflow.
    - [ ] Test different scenarios and edge cases.

- [ ] **Test with different user scenarios**
    - [ ] Create a set of test cases with diverse user inputs.
    - [ ] Test the application with real-world scenarios.
    - [ ] Document test results and identify areas for improvement.

- [ ] **Add logs where needed (logfire or print)**
    - [ ] Add logging statements to critical parts of the code.
    - [ ] Use `logfire` or `print` for debugging.
    - [ ] Configure logging levels and formats.

## PHASE 6: Final Polish

- [ ] **Add instructions to README**
    - [ ] Update the `README.md` with detailed instructions on how to use the application.
    - [ ] Add examples and usage scenarios.

- [ ] **Create .env.example**
    - [ ] Ensure that the `.env.example` file is up-to-date.
    - [ ] Add comments to explain each environment variable.

- [ ] **Optional Docker setup**
    - [ ] Create a `Dockerfile` for containerizing the application.
    - [ ] Create a `docker-compose.yml` file for managing dependencies.

- [ ] **Deploy or keep local with Streamlit**
    - [ ] Decide on the deployment strategy (e.g., Streamlit sharing, cloud deployment).
    - [ ] Deploy the application to the chosen platform.

## Optional: Future Extensions

- [ ] **Add memory/persistence (Redis, DB)**
    - [ ] Integrate a database (e.g., Redis, PostgreSQL) for storing conversation history.
    - [ ] Implement logic to retrieve and use stored data.

- [ ] **Knowledge Blocks for RAG**
    - [ ] Implement retrieval-augmented generation (RAG) using knowledge blocks.
    - [ ] Integrate a vector database for storing and retrieving knowledge.

- [ ] **PDF/image parsing**
    - [ ] Integrate libraries for parsing PDF and image files.
    - [ ] Implement logic to extract text and data from these files.

- [ ] **User authentication**
    - [ ] Implement user authentication and authorization.
    - [ ] Secure the application and protect user data.

- [ ] **Elevan Labs Conversational Voice Agent integration**
    - [ ] Integrate the Eleven Labs API for voice input and output.
    - [ ] Implement logic to convert text to speech and vice versa.