import os

import streamlit as st
from dotenv import load_dotenv
from lightlang.abilities.web import search_with_serp_api
from lightlang.llms.llm import LLM
from lightlang.tasks.task_streaming import TaskEvent
from lightlang.workflows.sequential_workflow import SequentialWorkflow

# Load environment variables
load_dotenv()

PLACEHOLDER_TASK_1_EXAMPLE = """<system>
You always echo what USER says in Shakespearean English.
</system>
<user>
{input_text}
</user>"""

PLACEHOLDER_OTHER_TASKS_EXAMPLE = """<system>
You are an amazing playwright.
</system>
<user>
Please write the first two paragraphs of a play inspired by:
{task_1_output}
</user>"""

# Page configuration
st.set_page_config(page_title="LightLang AI Workflow Builder", layout="wide")
st.title("LightLang AI Workflow Builder")

# Initialize OpenRouter API
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    st.error("Please set OPENAI_API_KEY in the .env file.")

# Initialize session state
if "tasks" not in (ss := st.session_state):
    ss.tasks = []
    ss.default_llm = LLM(provider="openai", model="gpt-4o-mini", temperature=0.7)


# Sidebar for adding tasks
with st.sidebar:
    st.header("Add Workflow Task")
    placeholder = (
        PLACEHOLDER_OTHER_TASKS_EXAMPLE if ss.tasks else PLACEHOLDER_TASK_1_EXAMPLE
    )
    task_prompt = st.text_area(
        "Task Prompt",
        help="Enter the prompt for your task here.",
        height=200,
        placeholder=placeholder,
    )
    col_add_task, col_use_example = st.columns([1, 1])
    if col_add_task.button("Add Task", type="primary", disabled=not task_prompt):
        ss.tasks.append(task_prompt)
        st.rerun()  # To update the placeholder
    if col_use_example.button("Use Example", type="secondary"):
        ss.tasks.append(placeholder)
        st.rerun()  # To update the placeholder

# Main content area
col1, col2 = st.columns([1, 1])

# Display current workflow tasks
with col1:
    with st.container():
        st.header("Workflow Tasks")
        if ss.tasks:
            for idx, task in enumerate(ss.tasks):
                with st.expander(f"Task {idx + 1}", expanded=True):
                    st.text_area("Prompt", value=task, key=f"task_{idx}", height=100)
                    col11, col12 = st.columns([1, 1])
                    if col11.button("Save Changes", key=f"save_{idx}"):
                        ss.tasks[idx] = ss[f"task_{idx}"]
                        st.success(f"Task {idx + 1} updated successfully!")
                    if col12.button(f"Delete Task {idx + 1}", key=f"delete_{idx}"):
                        ss.tasks.pop(idx)
                        st.rerun()
        else:
            st.info("No tasks added yet. Use the sidebar to add tasks.")

# Execute workflow
with col2:
    with st.container():
        st.header("Execute Workflow")
        input_text = st.text_area(
            "Input Text",
            help="Enter the text to be processed by the workflow.",
            height=150,
        )

        if st.button("Run Workflow", type="primary", use_container_width=True):
            if not ss.tasks:
                st.warning("Please add tasks to the workflow before running.")
            elif not input_text:
                st.warning("Please enter some input text before running the workflow.")
            else:
                workflow = SequentialWorkflow(
                    tasks=ss.tasks,
                    default_llm=ss.default_llm,
                    workflow_data={"input_text": input_text},
                )

                with st.container(border=True):
                    result_placeholder = st.empty()
                    result = ""

                    for output in workflow.stream():
                        if isinstance(output, TaskEvent):
                            print(f"Event '{output.event}' for task {workflow.task_id}")
                            if output.event == "BEGIN_TASK":
                                result += f"### Task {workflow.task_id} Output:\n\n"
                            elif output.event == "END_TASK":
                                result += "\n\n---\n\n"
                        elif output.content is not None:
                            result += output.content
                            result_placeholder.markdown(result)

st.markdown("---")

# Web Search section
st.header("Web Search")
with st.form("web_search_form"):
    query = st.text_input("Enter search query")
    submit_button = st.form_submit_button("Perform Web Search")

if submit_button and query:
    results = search_with_serp_api([query])
    st.subheader("Search Results")
    st.write(results)

# Clear workflow button
if st.button("Clear Workflow"):
    ss.tasks = []
    st.success("Workflow cleared.")

# Display helpful information
st.sidebar.markdown("""
---
### How to use:

1. Add tasks using the sidebar.
2. View your tasks in the left column.
3. Enter input text and run the workflow in the right column.
4. Clear the workflow anytime using the 'Clear Workflow' button.
5. Use the Web Search section to perform web searches.
""")
