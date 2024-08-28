# Gaby
This project is a chatbot designed to assist users of the Concordia University Library by providing helpful responses, answering questions, and offering guidance on library resources. The chatbot is built using `Streamlit` for the user interface and `LangChain` for the chatbot's logic and processing. This chatbot is built using Retrieval-Augmented Generation (RAG), which retrieves information from a database that was created using Swallow and manual scraping of the library's website.

## Installation and Setup
Install Dependencies:
Make sure you have Python installed. Then, install the required Python packages:
```
pip install -r requirements.txt
```
To set up the project locally, follow these steps:

1. **Clone the Repository**:
```
git clone https://github.com/yarastouhi/gaby.git
cd gaby
```
2. **Set Up OpenAI API Key**

Create a credentials.json file in the directory with your OpenAI API key:
```
   [
       {
           "service_provider": "openai",
           "key": "your-openai-api-key"
       }
   ]
```
3. **Prepare the CSV File**
Add your CSV file named titles_and_links.csv in the directory.
The `titles_and_links.csv` file should contain two columns:
  
  a. **Title**: This represents the name or topic that the chatbot might refer to in its responses.
  
  b. **Link**: This is the URL that corresponds to the title, which will be inserted into the chatbot's response when the title is mentioned.

Here is an example of the format:
```
Title,Link
how to find articles,https://library.concordia.ca/help/finding/articles/index.php
peer-reviewed articles,https://library.concordia.ca/help/finding/articles/peer-review.php
```
## Customization

You can customize the behavior and responses of the chatbot by adjusting the prompt templates or changing the temperature settings of the language model. These customizations allow you to fine-tune the chatbot's tone, formality, and creativity.

### 1. Prompt Customization

The chatbot's responses are influenced by the system prompts and user prompts defined in the code. You can modify these prompts to adjust how the chatbot behaves.

#### System Prompt

The system prompt defines the general behavior and constraints of the chatbot. It's set up to make the chatbot respond in the context of Concordia University Library. You can find and modify this prompt in the `system_prompt` variable within the code.

Example:
```
system_prompt = (
    """You are Gaby, a helpful AI library assistant at Concordia University Library. 
    Answer the questions from the perspective of Concordia University Library. 
    Ask follow-up questions for clarification if needed. If you don't know the answer, say that you don't know 
    and suggest speaking to a human librarian. Only provide links that are available in the context.
    If asked about recommendations for books or articles always provide the link to the Sofia Discovery Tool and never recommend books."""
    "\n\n"
    "{context}"
)
```
To Customize: You can adjust the text within the triple quotes to change how the chatbot interacts with users. For example, you can make the chatbot more formal or casual, or you can focus on different aspects of library services.

### 2. Temperature Setting

The temperature setting controls the creativity and variability of the chatbot's responses. A higher temperature will make the responses more creative and diverse, while a lower temperature will make them more deterministic and focused. 

To Customize: Change the temperature parameter to a value between 0 and 1:

  -Lower Temperature (e.g., 0.2): The chatbot will provide more precise and consistent answers, suitable for technical or formal contexts.
  
  -Higher Temperature (e.g., 0.9): The chatbot will generate more varied and creative responses, which can be useful in brainstorming sessions or less formal contexts.
  
There are two ways to set or change the temperature.

#### Method 1: Changing Temperature Through `ChatOpenAI` Object

You can set the temperature directly when initializing the `ChatOpenAI` object in your code.
```
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.7)
```

#### Method 2: Changing Temperature Through Credentials File
Alternatively, you can adjust the temperature setting in the credentials file used to authenticate and configure the language model. This method is particularly useful if you want to centralize your model configuration or if you're deploying the bot in different environments.

Example Credentials File:
```
[
    {
        "service_provider": "openai",
        "key": "your_key",
        "model": "gpt-3.5-turbo",
        "temperature": "0.7"
    },
    {
        "service_provider": "google",
        "key": "your_key",
        "model": "gemini-pro",
        "temperature": "0.6"
    }
]
```
## Running the Chatbot

After customizing the chatbot, whether by adjusting prompts, temperature settings, or other parameters, you need to generate the embeddings and set up the vector database to reflect these changes.

### Step 1: Generate Embeddings

Once you've made your customizations, run the `01_generate_embeddings.py` script to generate the necessary embeddings based on your updated settings. These embeddings are essential for creating a vector database that the chatbot will use to provide contextually relevant responses.

```
python 01_generate_embeddings.py
```
After running this script, a .chroma directory will be created in your project folder. This directory contains the vector database, which stores the embeddings generated from your documents or data sources.

### Step 2: Run the Application

With the embeddings generated and the vector database in place, you can now run the application using Streamlit.

```
streamlit run 02x_gaby_version.py
```

Running the App: This command will launch the Streamlit application, allowing you to interact with your customized chatbot. Make sure that the .chroma directory and the necessary configuration files are present in your working directory, as they are required for the chatbot to function correctly.
