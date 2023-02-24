import matplotlib.pyplot as plt
import networkx as nx
from chatgpt_wrapper import ChatGPT
import parsing 
import os
import json 
import app

bot = ChatGPT()
#use bot.ask() 


def files_to_knowledge_tree(folder_path='./persuation_kb'):
    #create the tree (will be represent as a list)
    tree = list() 

    #parse the file into the tree with each node pointing to the next one
    file_list = sorted(os.listdir(folder_path))
    for index, filename in enumerate(file_list):
        file_path = os.path.join(folder_path, filename)
        if os.path.isfile(file_path):
            if(index == 0):
                first_layer = app.json_to_nodes(file_path)
                tree.append(first_layer)
            else: 
                current_layer = app.json_to_nodes(file_path,tree[index-1])
                tree.append(current_layer)
    return tree 

def visualize(tree,visited=[],visited_only=False):
    #counter for debugging -delete this after
    counter = 0 
    #pos store the position of each node 
    pos = dict()
    # Create a graph object
    G = nx.Graph()
    # Add nodes for each element in the linked list
    layer_num = 0
    node_num = 0
    for layer in tree:
        for node in layer:
            #will add the node if it's not visited_only mode or if it is then the node has to be visited
            if not visited_only or node.id in visited:
                counter = counter + 1 #delete this after 
                G.add_node(node.id,color="yellow")
                layer_offset = (len(tree[0])-len(layer))/2
                pos[node.id]=(node_num + layer_offset,layer_num)
                node_num = node_num + 1

            #check if the node has been visited
            if node.id in visited:
                G.nodes[node.id]['color'] = 'purple'

        layer_num = layer_num + 1
        node_num = 0 

    # Connect the nodes in the linked list
    for layer in tree[1:]:
        for node in layer:
                for next_node in node.next_nodes:
                    if not visited_only or (node.id in visited and next_node.id in visited):
                        G.add_edge(node.id,next_node.id)

    #get the color of all the nodes:
    print(counter)
    print(G.nodes)
    node_colors = [G.nodes[node]['color'] for node in G.nodes]  

    # Visualize the graph
    nx.draw(G, pos, with_labels=True, node_color=node_colors, node_size=1000, alpha=0.8)

    # Display the graph
    plt.show()

#decision making

def options_to_string(options):
    output = ""
    for i,option in enumerate(options): 
        output = output + f'{i+1}. {option.content}\n'
    return output 

def evaluate(response):
    output = list()
    # top five things that are 50% true 
    for pair in response: 
        if pair[1] >= 30 and len(output) < 6:
            output.append(pair[0])
    return output 

def get_answer_json(prompt):
    text_answer = retry_until_success(bot.ask,5,prompt)  #save point 
    print(text_answer)
    answer = json.loads(text_answer)
    print('\n----------------------------\n')
    return answer

def get_certainties(options, question, qid):
    global cache
    visited_nodes = [option.id for option in options] 

    #cache the visited node (add on) and the current layer
    cache[qid]["current_layer"] = visited_nodes
    cache[qid]["visited"] = cache[qid]['visited'] | set(visited_nodes) #this is a set to avoid duplication

    if options:
        with open('./prompts/file_search.txt') as file:
            #format the question 
            prompt = file.read() 
            prompt = prompt.replace("<<TOC>>",options_to_string(options)).replace("<<QUESTION>>", question)
            print(options_to_string(options))
            #get the answer 
            answer = retry_until_success(get_answer_json,10,prompt)
            #get the approriate path after evaluations
            valid_path = evaluate(answer)
            #get the actual selected nodes 
            valid_nodes = [options[i-1] for i in valid_path]
            #check if this is the second to last layer or not 
            if not valid_nodes or valid_nodes[0].next_nodes[0].next_nodes[0].next_nodes: #this looks way too ugly
                #getting the next nodes from the selected nodes and continue with the search 
                next_options = list()
                for valid_node in valid_nodes:
                    next_options = next_options + valid_node.next_nodes
                #get the list of all visited nodes/recursively continuing 
                visited_nodes = visited_nodes + get_certainties(next_options,question,qid)
            else:
                print("This is the last layer, proceed to judging mode")
                #cache valid path 
                cache[qid]["current_layer"] = [options[i-1].id for i in valid_path]
                # set search_complete
                cache[qid]['search_completed'] = True
                return [valid_nodes]
    else:
        print("No options fit")
        #set search_complete
        cache[qid]["search_completed"] = True 
        return [[]]
    return visited_nodes 

def get_relevant_nodes(options,question,qid):
    return get_certainties(options,question,qid)[-1]

def get_visited_nodes(options,question,qid):
    return get_certainties(options,question,qid)[:-1]

def brainstorm(question, book_title):
    with open("./prompts/brainstorm.txt",'r') as file:
        prompt = file.read().replace('<<QUESTION>>',question).replace('<<TITLE>>',book_title) 
        brainstorm_questions = retry_until_success(get_answer_json,5,prompt) #retries built in 
    return brainstorm_questions 
        
def note_taking(question, current_note, content,book_title):
    with open("./prompts/note_taking.txt",'r') as file:
        prompt = file.read().replace("<<QUESTION>>", question).replace("<<EXCERPTS>>",content).replace("<<NOTE>>",current_note).replace("<<TITLE>>",book_title)
        print(prompt)
        new_note = retry_until_success(bot.ask,5,prompt)
        print(new_note)
    return new_note 

def learning(question,valid_nodes,book_title,qid,note=""):
    global cache
    excerpt_chunks = list()
    text = ""
    counter = 0
    print(f"Taking notes from brainstorm question #{qid}...")

    #extract the final content from all of the valid nodes
    print(f"Extracting the content from all the valid nodes")
    final_content = list() 
    for node in valid_nodes: 
        for next_node in node.next_nodes: 
            final_content.append(next_node.content)
    print(f"There are in total {len(final_content)} summaries...")

    print(f"Merge all of the summaries and section them into chunks...")
    #we first go through every node and section the contents into chunk
    for content in final_content:
        if len(text) < 2500:
            counter = counter + 1 
            text = text + f"\n{counter}. {content.strip()}"
        else:
            excerpt_chunks.append(text)
            counter = 1
            text = f"\n{counter}. {content.strip()}"
    excerpt_chunks.append(text)
    print(f"There are in total {len(excerpt_chunks)} chunks")

    # excerpt_chunks = excerpt_chunks[:2] #limit for testing
    #cache the excerpt chunk to the question
    cache[qid]['remaining_chunks'] = excerpt_chunks[:]
    print(f"Caching: {excerpt_chunks}")

    #go through the content one by one and take notes: 
    for index,content_chunk in enumerate(excerpt_chunks): 
        note = note_taking(question,note,content_chunk,book_title) #retry built in 
        print(f"Successfully taken notes at chunk {index}")
        #log the note 
        print(f"Logging the notes at chunk {index}")
        with open(f"./note_logs/note_{qid}_#{index}.txt",'w') as file:
            file.write(note)
        print("Caching the notes and update the chunks")
        print(f"chunks from: {cache[qid]['remaining_chunks']}")
        #cache the note 
        cache[qid]['notes'] = note
        #removing the chunk from cache 
        cache[qid]['remaining_chunks'].pop(0)
        print(f"to chunks: {cache[qid]['remaining_chunks']}")
    #cache it as complete
    cache[qid]["completed"] = True
    return note

def answer_question(question, book_title): #the main operation 
    # answer = ""
    global cache 
    error_counter = 0
    #answer the question given a book title
    notes = [] #this will collect all of the notes for the brain storm question 

    #cache the main question
    cache[0] = {
        "question": question,
        "current_layer":[],
        "search_completed": True,
        "visited": set(), #duplicate through retries
        "notes": "",
        "remaining_chunks": [],
        "completed":False
    }

    tree = files_to_knowledge_tree()
    further_questions = retry_until_success(brainstorm,10,question,book_title) #save_point
    print(further_questions)
    #cache the brain storm question 
    for index,bquestion in enumerate(further_questions):
        cache[index+1] = {
            "question": bquestion,
            "current_layer":[],
            "search_completed": False,
            "visited": set(), #duplicate through retries
            "notes": "",
            "remaining_chunks": [],
            "completed":False
        }

    #answering all of the brain storm questions
    for index,bquestion in enumerate(further_questions):
        valid_nodes = get_relevant_nodes(tree[-1],bquestion,index+1) #get the nodes containing the information #save_point index + 1 is the qid 
        notes.append(learning(bquestion,valid_nodes,book_title,index+1)) #adding the finished notes from brainstorm question #save_point
        
    print("\n\n")
    print("ANSWERING THE QUESTION:")
    print(f"TOTAL NUMBER OF NOTES COLLECTED: {len(notes)}")
    #cache the notes into the main question
    cache[0]['remaining_chunks'] = notes[:]
    current_answer = ""
    #actuall answering the final question:
    with open("./prompts/answering.txt",'r') as file:
        skeleton = file.read() 
        for i,note in enumerate(notes):
            if note:
                print(f"Answering from the {i}-th note...")
                prompt = skeleton.replace("<<QUESTION>>",question).replace("<<TITLE>>",book_title).replace("<<NOTE>>",note).replace("<<PREVIOUS ANSWER>>",current_answer)
                answer = bot.ask(prompt) #save_point
                #update the current answer
                current_answer = answer
                #cache the notes 
                cache[0]['notes'] = answer
            #remove the chunk
            cache[0]['remaining_chunks'].pop(0)
            
    print(current_answer)
    #set as completed:
    cache[0]["completed"] = True
    with open(f"./answers/{question}.txt","w") as file:
        file.write(f"Question: {question}\n\n{current_answer}")
    return current_answer
    
def retry_until_success(func, max_tries, *args, **kwargs):
    for i in range(max_tries):
        try:
            # Call the passed function with the specified parameters
            output = func(*args, **kwargs)
            print("Code executed successfully")
            break
        except KeyboardInterrupt:
            #do not retry if it's the user shutting down the system 
            raise KeyboardInterrupt('System shutting down')
        except:
            # Code to be executed if there's an exception
            # Replace this with your own exception handling code
            if i == max_tries - 1:
                print("Maximum number of tries reached")
            else:
                print("Code execution failed. Retrying...")
    return output

def convert_visited_to_list(dictionary):
    for key, value in dictionary.items():
        if "visited" in value:
            value["visited"] = list(value["visited"])
    return dictionary

def resuming(): 
    with open("./cache/questions_cache.json","r") as file:
        cache = json.load(file)
        for qid,question_cache in cache.items(): 
            if not question_cache["completed"]:
                #if the current process has not yet been completed
                if qid == "0":
                    #if there is something in the remaning_chunks -> we'll finish it 
                    if question_cache["remaining_chunks"]:
                        print("Continue taking notes")
                        return #stop the process after completed, continue if not 
                else: 
                    if not question_cache["search_completed"]:
                        #continue the search if not completed 
                        print("Continuing the search")
                        #the remaning chunks will be updated in preparation to the next step 
                    #use the remaining chunks to take notes 
                    print("Taking notes")
            else:
                # if the current process has been completed 
                if qid == "0":
                    #halt completely if the main question has already been answered. 
                    print("The process has alread been completed!")
                    return 
        #after resuming every brainstorm questions -> we will continue with the main question 
        print("Continue with the main question")




cache = dict() 
def get_answer(question,book="INFLUENCE The Psychology of Persuasion"):
    try:
        answer_question(question,book)
        cache = convert_visited_to_list(cache)
        with open("./cache/questions_cache.json","w") as file:
            json.dump(cache,file)
    except:
        print("Something terrible happened... Please check the cache")
        cache = convert_visited_to_list(cache)
        with open("./cache/questions_cache.json","w") as file:
            json.dump(cache,file)




