# LightLang AI Workflow Builder

An AI workflow builder using LightLang and Streamlit.

## Introduction

This project provides a user-friendly interface for building and executing AI workflows using [LightLang](https://github.com/reasonmethis/lightlang), a lightweight Python package for working with Large Language Models (LLMs). The app allows you to create sequential workflows by adding custom tasks (prompts) and execute them with your input text. It also includes a web search feature powered by SerpAPI.

## Features

- **Sequential Task Execution**: Build workflows where each task can utilize the output of the previous tasks.
- **LLM Integration**: Leverage OpenAI's GPT models through LightLang for language processing.
- **Web Search Capability**: Perform real-time web searches using SerpAPI.
- **Interactive UI**: Streamlit provides an intuitive interface for easy interaction.

## Requirements

- Python 3.11 or higher
- OpenAI API Key
- SerpAPI API Key (optional, for web search functionality)

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/reasonmethis/lightlang-showcase.git
cd lightlang-showcase
```

### 2. Create a Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows, run .venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables

Copy the `.env.example` file to `.env` and fill in the required values:

```bash
OPENAI_API_KEY=your_openai_api_key
SERPAPI_API_KEY=your_serpapi_api_key  # Optional, required for web search functionality
```

- **`OPENAI_API_KEY`**: Your OpenAI API key for accessing GPT models.
- **`SERPAPI_API_KEY`**: Your SerpAPI key for web search capabilities.

## Usage

Run the Streamlit app:

```bash
streamlit run streamlit_app.py
```

This will launch the app in your default web browser.

### How to Use the App

1. **Add Workflow Tasks**:
   - Use the sidebar to add tasks by entering prompts.
   - Click **"Add Task"** to include the task in your workflow.
   - Optionally, use **"Use Example"** to add a placeholder task.

2. **View and Edit Tasks**:
   - Existing tasks are displayed in the **"Workflow Tasks"** section.
   - Expand a task to view or edit its prompt.
   - Use **"Save Changes"** to update a task or **"Delete Task"** to remove it.

3. **Execute Workflow**:
   - Enter your input text in the **"Input Text"** area.
   - Click **"Run Workflow"** to execute the tasks sequentially.
   - The output of each task will be displayed as it runs.

4. **Web Search**:
   - Scroll down to the **"Web Search"** section.
   - Enter a search query and click **"Perform Web Search"**.
   - Search results will be displayed below the input.

5. **Clear Workflow**:
   - Use the **"Clear Workflow"** button to reset all tasks.

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request with your changes. Ensure your code is well-documented and follows the existing style guidelines.

