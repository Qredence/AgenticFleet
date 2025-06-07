import chainlit as cl
from src.agentic_fleet.core.workflows.research_graph_workflow import run_research_graph
import asyncio

@cl.on_chat_start
async def start_chat():
    cl.user_session.set("history", [])
    await cl.Message(content="Welcome to AgenticFleet! How can I help you with your research task today?").send()

@cl.on_message
async def main(message: cl.Message):
    task_description = message.content
    history = cl.user_session.get("history", []) # Ensure default is list
    history.append({"role": "user", "content": task_description})
    cl.user_session.set("history", history) # Save user message to history

    # Step 1: Acknowledge Input & Start Processing
    step_input = cl.Step(name="Processing Request", type="run")
    step_input.input = task_description
    await step_input.send()
    # Send a message associated with this step to confirm receipt
    await cl.Message(content=f"Received task: '{task_description}'. Beginning process...", parent_id=step_input.id).send()
    step_input.output = f"Processing task: {task_description}" # Set output for the step
    await step_input.update()

    # Step 2: Workflow Execution
    # Child of step_input
    step_workflow = cl.Step(name="Research and Writing Workflow", type="run", parent_id=step_input.id)
    await step_workflow.send()

    results = {} # Initialize results

    # Messages from run_research_graph will be nested here if they use cl.Message and set parent_id
    # For this to work seamlessly, run_research_graph messages should ideally accept a parent_id
    # or we set a global context for cl.Message if possible (Chainlit usually handles this with contextvars)
    # For now, messages from run_research_graph will appear as top-level within this step's duration
    # or if they are modified to take parent_id, they can be direct children.
    # The current run_research_graph sends messages without parent_id, so they will be nested by Chainlit automatically
    # within the current step_workflow context.

    try:
        if asyncio.iscoroutinefunction(run_research_graph):
            results = await run_research_graph(task_description)
        else:
            results = run_research_graph(task_description)

        step_workflow.output = "Workflow completed. Results are being displayed."
        await step_workflow.update()

    except Exception as e:
        error_message = f"An error occurred during workflow execution: {str(e)}"
        # Associate error message with the workflow step
        await cl.ErrorMessage(content=error_message, parent_id=step_workflow.id).send()
        step_workflow.output = error_message
        await step_workflow.update()

        # Update history with error and end
        history.append({"role": "assistant", "content": error_message})
        cl.user_session.set("history", history)
        return

    # Step 3: Display Results
    # Child of step_workflow
    step_results = cl.Step(name="Final Results", type="run", parent_id=step_workflow.id)
    await step_results.send()

    summary = results.get('summary')
    blog_post = results.get('blog_post')

    assistant_messages_for_history = []

    if summary:
        summary_message_content = f"**Research Summary:**\n{summary}"
        await cl.Message(content=summary_message_content, author="System", parent_id=step_results.id).send()
        assistant_messages_for_history.append(summary_message_content)
    else:
        no_summary_msg = "No summary was generated."
        await cl.Message(content=no_summary_msg, author="System", parent_id=step_results.id).send()
        assistant_messages_for_history.append(no_summary_msg)

    if blog_post:
        blog_post_message_content = f"**Blog Post:**\n{blog_post}"
        await cl.Message(content=blog_post_message_content, author="System", parent_id=step_results.id).send()
        assistant_messages_for_history.append(blog_post_message_content)
    else:
        no_blog_msg = "No blog post was generated."
        await cl.Message(content=no_blog_msg, author="System", parent_id=step_results.id).send()
        assistant_messages_for_history.append(no_blog_msg)

    step_results.output = "Summary and blog post displayed."
    await step_results.update()

    # Consolidate assistant response for history from this turn
    # This joins all messages sent by the assistant in this turn for the history
    consolidated_assistant_response = "\n".join(assistant_messages_for_history)

    history.append({"role": "assistant", "content": consolidated_assistant_response})
    cl.user_session.set("history", history)
