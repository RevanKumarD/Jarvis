# 🏁 Future Roadmap to Approach D: Jarvis Evolution

This document outlines the planned evolution of Jarvis from the current "big IGA + parallel agents" approach (Approach A) to the fully parallel, consolidated clarification, and voice-integrated approach (Approach D).

## Goals

* Achieve full parallel agent execution for maximum efficiency.
* Consolidate user clarification prompts for a streamlined experience.
* Integrate voice input and output for a seamless, hands-free interaction.

## Roadmap

### 1\. Refactor Specialized Agents to Return "Missing Fields"

* **Task:** Modify each sub-agent (email, calendar, etc.) to return a structured result indicating missing data instead of simply failing.
    * **Example Output:**

    ``` json
    {
  "needs_more_info": true,
  "missing_fields": { "subject": "Email subject is missing" }
}
    ```

* **Why:** Enables agents to partially complete tasks and specify required additional information.

### 2\. Create a "Parallel Coordinator" Node

* **Task:** Develop a node (`parallel_aggregator`) to:
    * Launch all relevant agents in parallel.
    * Collect agent results.
    * Separate successful agents from those requiring more data.
* **Implementation:** Utilize LangGraph's asynchronous invocation and result aggregation capabilities.

### 3\. Implement a "Consolidated Clarification" Node

* **Task:** If any agent requests more information, compile all missing fields into a single user-facing prompt.
    * **Example Prompt:** "We need a subject for your email and a time for your meeting. Please provide them."
* **Implementation:**
    * Convert each agent's `missing_fields` into a unified message.
    * Use an interrupt node (`interrupt(...)`) or a specialized "voice prompt" to gather consolidated clarifications.

### 4\. Add a Loop to Re\-run Only the Agents that Needed More Data

* **Task:** After receiving user clarifications, update `JarvisState` and re-run only the agents with `needs_more_info: true`.
* **Implementation:**
    * Implement logic in the coordinator node or a subsequent pass to re-invoke incomplete agents with updated data.
    * Handle scenarios where agents still require further clarification.

### 5\. Ensure the Aggregator Node is Idempotent

* **Task:** Prevent re-running successfully completed agents. Re-run only those that required additional data.
* **Implementation:** Maintain a list of completed vs. incomplete agents in `JarvisState`.

### 6\. Combine Parallel Results into `aggregate_results`

* **Task:** After all agents succeed, merge partial results into a final response (e.g., "Email sent, meeting scheduled.").
* **Implementation:** Modify the aggregator node to consolidate results from all sub-agents.

### 7\. Incorporate Voice I/O

* **Task:** Integrate speech-to-text (STT) for user input and text-to-speech (TTS) for responses.
* **Implementation:**
    * STT: Use STT to transcribe voice input during clarification prompts.
    * TTS: Generate voice output from system messages using TTS engines like ElevenLabs or Azure.
* **Goal:** Create a fully voice-driven conversation experience.

### 8\. Build UI/UX for Multi\-Agent Clarifications

* **Task:** Design user interfaces (voice or web) to display or convey multiple missing fields.
* **Implementation:**
    * Voice: Enumerate missing fields (e.g., "Email agent needs subject, calendar agent needs time.").
    * Web UI: Display a form with fields for each missing piece of information.

### 9\. Extensive Testing

* **Task:** Thoroughly test scenarios involving:
    * Single agent needing data.
    * Multiple agents needing data.
    * Partial answers to missing fields.
    * Voice-based interactions.

## Quick Summary

* Enhance agents to return partial successes with a `needs_more_info` structure.
* Use a coordinator node to merge parallel results and generate consolidated clarification prompts.
* Re-run only incomplete agents, repeating if necessary.
* Integrate voice for consolidated prompts and user input.
* Design intuitive UI/UX for multi-agent clarifications.

This roadmap outlines the steps to evolve Jarvis into a fully parallel, efficient, and user-friendly voice-driven AI assistant.