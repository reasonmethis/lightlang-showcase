import os
import random
from datetime import datetime

import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv
from lightlang.abilities.web import get_content_from_urls, search_with_serp_api
from lightlang.llms.llm import LLM
from lightlang.prompts.chat_prompt_template import ChatPromptTemplate
from lightlang.tasks.task import LLMTask

# Load environment variables
load_dotenv()

# Unified TASK_TEMPLATE with dynamic chat_history_section
TASK_TEMPLATE = """<system>
You are an AI assistant in a sequential workflow.
Date: {current_date}
Time: {current_time}
System context: {system_context}
{chat_history_section}
</system>
<user>
{task_prompt}
</user>"""

# Page configuration
st.set_page_config(page_title="LightLang AI Workflow Builder", layout="wide")
st.title("LightLang AI Workflow Builder")

# Initialize OpenAI API key and check
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    st.error("Please set OPENAI_API_KEY in the .env file.")

# Initialize the LLM with OpenAI configuration
llm = LLM(provider="openai", model="gpt-4o-mini", temperature=0.7)

# Initialize session state to manage tasks and workflow data
if "tasks" not in (ss := st.session_state):
    ss.tasks = []
    ss.default_llm = llm
    ss.workflow_data = {}
    ss.saved_searches = []
    ss.saved_scrapes = []


# Function to update date and time in the workflow data
def update_workflow_data():
    now = datetime.now()
    ss.workflow_data["current_date"] = now.strftime("%Y-%m-%d")
    ss.workflow_data["current_time"] = now.strftime("%H:%M:%S")


# Generate chat history for displaying task interactions
def generate_chat_history(tasks, workflow_data):
    chat_history = ""
    for i, task in enumerate(tasks, start=1):
        user_prompt = extract_user_prompt(task.chat_prompt_template.to_string())
        assistant_response = workflow_data.get(f"task_{i}_output", "")
        chat_history += f"User: {user_prompt}\nAssistant: {assistant_response}\n\n"
    return chat_history.strip()


# Extracts the content inside <user> tags
def extract_user_prompt(prompt_template_string):
    start_tag = "<user>"
    end_tag = "</user>"
    start_index = prompt_template_string.find(start_tag) + len(start_tag)
    end_index = prompt_template_string.find(end_tag)
    return prompt_template_string[start_index:end_index].strip()


# Replace task outputs in the chat prompt dynamically
def replace_task_outputs(text, workflow_data):
    for key, value in workflow_data.items():
        if key.startswith("task_") and key.endswith("_output"):
            text = text.replace(f"{{{key}}}", str(value))
    return text


# Prepare or update a task with dynamically replaced content
def prepare_task(task_id, tasks, workflow_data):
    task = tasks[task_id - 1]
    new_template = replace_task_outputs(
        task.chat_prompt_template.to_string(), workflow_data
    )
    task.chat_prompt_template = ChatPromptTemplate.from_string(new_template)
    return task


# Add a new task with formatted prompts based on user input
def add_task(system_context, task_prompt):
    task_id = len(ss.tasks) + 1

    full_prompt = TASK_TEMPLATE.format(
        current_date="{current_date}",
        current_time="{current_time}",
        system_context=system_context,
        task_prompt=task_prompt,
        chat_history_section="{chat_history_section}",
    )

    ss.tasks.append(
        LLMTask(ChatPromptTemplate.from_string(full_prompt), llm=ss.default_llm)
    )

    # Store system context and task prompt immediately
    ss.workflow_data[f"task_{task_id}_system_context"] = system_context
    ss.workflow_data[f"task_{task_id}_task_prompt"] = task_prompt


# Define custom workflow to handle streaming and execution of tasks
class MyWorkflow:
    def __init__(self, tasks, default_llm, workflow_data):
        self.tasks = tasks
        self.default_llm = default_llm
        self.workflow_data = workflow_data
        self.curr_task_id = None

    def get_task_input(self, task_id):
        # Task 1: No chat history
        if task_id == 1:
            chat_history_section = ""
        else:
            chat_history = generate_chat_history(
                self.tasks[: task_id - 1], self.workflow_data
            )
            chat_history_section = f"Here's the chat history so far:\n{chat_history}"

        # Set up inputs for the task
        return self.workflow_data | {
            "system_context": self.workflow_data.get(
                f"task_{task_id}_system_context", ""
            ),
            "task_prompt": self.workflow_data.get(f"task_{task_id}_task_prompt", ""),
            "chat_history_section": chat_history_section,
        }

    def stream(self):
        for task_id, task in enumerate(self.tasks, start=1):
            # Get task inputs and populate the prompt template
            inputs = self.get_task_input(task_id)

            # Run the task
            task.set_task_id(task_id)
            self.curr_task_id = task_id
            task_res = yield from task.stream(inputs, self.default_llm)

            # Update the workflow data with the task output
            self.workflow_data[f"task_{task_id}_output"] = task_res.llm_output


# Sidebar for task management
with st.sidebar:
    st.header("Add Workflow Task")
    system_context = st.text_area("System Context", height=100)
    task_prompt = st.text_area("Task Prompt", height=200)
    col_add_task, col_sample_task = st.columns([1, 2])
    if col_add_task.button("Add Task", type="primary"):
        add_task(system_context, task_prompt)
        st.rerun()
    if col_sample_task.button("Add Example Task"):
        system_context = f"Respond to everything as {random.choice(['Donald Trump', 'Cleopatra', 'Napoleon', 'Sherlock Holmes', 'Shakespeare'])}"
        task_prompt = "What is the meaning of life?"
        add_task(system_context, task_prompt)
        st.rerun()

# Main content area for task management and execution
col1, col2 = st.columns([1, 1])

with col1:
    st.header("Workflow Tasks")
    if ss.tasks:
        for idx, task in enumerate(ss.tasks):
            # Show a snippet of the task
            task_snippet = task.chat_prompt_template.to_string()[:30]
            with st.expander(f"Task {idx + 1}: {task_snippet}..."):
                st.text_area(
                    "System Context",
                    value=ss.workflow_data.get(f"task_{idx + 1}_system_context", ""),
                    key=f"system_context_{idx}",
                    height=100,
                )
                st.text_area(
                    "Task Prompt",
                    value=ss.workflow_data.get(f"task_{idx + 1}_task_prompt", ""),
                    key=f"task_prompt_{idx}",
                    height=100,
                )
                if st.button(f"Delete Task {idx + 1}", key=f"delete_{idx}"):
                    ss.tasks.pop(idx)
                    st.rerun()
    else:
        st.info("No tasks added yet. Use the sidebar to add tasks.")

with col2:
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
            # Update workflow data with the input text
            ss.workflow_data["input_text"] = input_text
            update_workflow_data()  # Update date and time right before running

            # Initialize the workflow
            workflow = MyWorkflow(
                tasks=ss.tasks,
                default_llm=ss.default_llm,
                workflow_data=ss.workflow_data,
            )

            # Execute the workflow and display outputs
            result_placeholder = st.empty()
            result = ""

            for output in workflow.stream():
                if output.event_type == "BEGIN_TASK":
                    result += f"### Task {workflow.curr_task_id} Output:\n\n"
                elif output.event_type == "END_TASK":
                    result += "\n\n---\n\n"
                elif output.content is not None:
                    result += output.content
                    result_placeholder.markdown(result)

# Clear workflow button
if st.button("Clear Workflow"):
    ss.tasks = []
    ss.workflow_data = {}
    ss.saved_searches = []
    ss.saved_scrapes = []
    st.success("Workflow cleared.")

# Web-sourced Context with Tabs for Web Search and Web Scrape
st.header("Web-sourced Context")
tabs = st.tabs(["Web Search", "Web Scrape"])

with tabs[0]:
    st.subheader("Web Search")
    with st.form("web_search_form"):
        query = st.text_input("Enter search query")
        submit_button = st.form_submit_button("Perform Web Search")

    if submit_button and query:
        results = search_with_serp_api([query])
        ref_name = f"search_ref_{len(ss.saved_searches) + 1}"
        ss.saved_searches.append((ref_name, query, results))

        # Add the search results to the workflow data with the key ref_name
        ss.workflow_data[ref_name] = results

    # Popover for Saved Searches
    st.subheader("Saved Searches")
    for name, search, results in ss.saved_searches:
        with st.popover(f"ref: {name} - search: {search}"):
            st.write(f"Search Query: {search}")
            st.write("Results:")
            st.write(results)


with tabs[1]:
    st.subheader("Web Scrape")
    with st.form("web_scrape_form"):
        scrape_query = st.text_input("Enter domain to scrape")
        scrape_button = st.form_submit_button("Perform Web Scrape")

    if scrape_button and scrape_query:
        # Perform the web scrape and store it in saved_scrapes
        scraped_data = get_content_from_urls([scrape_query])
        raw_text = scraped_data.link_data_dict.get(scrape_query).text
        ref_name = f"scrape_ref_{len(ss.saved_scrapes) + 1}"
        ss.saved_scrapes.append((ref_name, scrape_query, raw_text))

        # Add the scraped data to the workflow data with the key ref_name
        ss.workflow_data[ref_name] = raw_text

    saved_scrape_options = [
        f"ref: {name} - domain: {scrape}" for name, scrape, _ in ss.saved_scrapes
    ]
    selected_scrape = st.selectbox(
        "Saved Scrapes", saved_scrape_options, index=0 if saved_scrape_options else None
    )

    # Show the raw text from the scrape
    if selected_scrape:
        selected_scrape_ref = selected_scrape.split()[1]
        for ref, domain, raw_text in ss.saved_scrapes:
            if ref == selected_scrape_ref:
                st.subheader(f"Raw Text for {domain}")
                st.text_area("Scraped Raw Text", value=raw_text, height=300)

                # Embed the domain in an iframe
                st.subheader(f"Domain Preview: {domain}")
                components.iframe(src=f"https://{domain}", height=500, scrolling=True)

# Sidebar with usage information
st.sidebar.markdown("""
---
### How to use:

1. Add tasks using the sidebar. You can use `{task_X_output}` to reference previous task outputs.
2. View your tasks in the left column.
3. Enter input text and run the workflow in the right column.
4. Clear the workflow anytime using the 'Clear Workflow' button.
5. Use the Web Search section to perform web searches.
6. Use the Web Scrape section to scrape data from a domain and save it.
""")
