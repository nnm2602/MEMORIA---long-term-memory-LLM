# MEMORIA---long-term-memory-LLM

## HOW TO USE:
note: if you're only here to test it out, I recommend starting with steps 2. The book "Psychology of Persuasion" has already been preloaded, you can
use that as the default document to test out the program. 

### 1. Parse in the document
IN PROGRESS... NOT STABLE ENOUGH TO BE IMPLEMENTED

### 2. Interact with the expert system 

#### SETTING UP

set up your virtual environment and install all of the necessary requirements by typing the following in the terminal. 

```
pip install -r requirements.txt 

```

Since this program uses the chatgpt python wrapper, you have to do log into your openai account to start. Click [here](https://link-url-here.org) for more information
on how to set it up.

First, open up your terminal and type in the following 

```
chatgpt install
```
The browser will open up and from then you can log into your openai account. 

To make sure that everything is working fine you can type in 
```
chatgpt 
```
And ask it a few question to make sure everything is up and running. 

After logging in, you can exit the website and interact with the program in a 
main.py file like below.


```python
import knowledge_tree_parsing as bot

question = "replace this with your question" 
print(bot.get_answer(question))

```

The answer to the question will be logged in the folder "answers". It will takes a little while, around 5 minutes for the program to find the answer, this
is due to the fact that there's a bottle neck on the LLM output, making search excruciatingly slow. 

[^1]: DUE TO UNFORSEEN CIRCUMSTANCES, THE PROJECT IS NOW ONLY LIMITED TO INTERACTING WITH THE ALREADY BUILT IN "PSYCHOLOGY" BOT. DOCUMENT PARSING FEATURE WILL BE
ADDED SOON FOR CUSTOMIZABLE EXPERT SYSTEM. 
