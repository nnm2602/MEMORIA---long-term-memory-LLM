import math
import concurrent.futures
import functools
import openai
import os
import parsing
import json
import time 
from Node import Node
from dotenv import load_dotenv

path = "input_files/RobertCaldini_InfluencePsychologyofPersuasion.pdf"
max_block = 1000
max_token = 2458 

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")


def error_print(error):
    import sys
    exc_type, exc_value, exc_traceback = sys.exc_info()
    traceback_details = {
        'filename': exc_traceback.tb_frame.f_code.co_filename,
        'lineno': exc_traceback.tb_lineno,
        'name': exc_traceback.tb_frame.f_code.co_name,
        'type': exc_type.__name__,
        'message': error
    }
    print("Error type: {}".format(traceback_details['type']))
    print("Error message: {}".format(traceback_details['message']))
    print("Error location: {}:{} in {}".format(traceback_details['filename'],
                                               traceback_details['lineno'],
                                               traceback_details['name']))


def get_answer(prompt, model="text-davinci-003", max_tokens=1000, temperature=0, top_p=1, n=1, stream=False, logprobs=None, stop=None):
    # need to catch exception... (or do we?)
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=prompt,
        max_tokens=max_tokens,
        temperature=temperature,
        top_p=top_p,
        n=n,
        stream=stream,
        logprobs=None,
        stop=None
    )
    response_text = response["choices"][0]['text']
    return response_text


def divide_batch(count_per_batch, batch):
    divided_list = [batch[count_per_batch*i:count_per_batch *
                          (i+1)] for i in range(int(len(batch)/count_per_batch)+1)]
    if not divided_list[-1]:
        return divided_list[:-1]
    return divided_list

def first_layer(default_nodes):
    summary_nodes = list()
    for node in default_nodes:
        with open("./prompts/summarize2.txt", "r") as file:
            skeleton = file.read()
            prompt = skeleton + "\n" + node.content + "\nSUMMARY: "
            summary = get_answer(prompt)
            summary_node = Node(summary, [node])
            summary_nodes.append(summary_node)
    return summary_nodes


def first_layer_helper(skeleton, node):
    # this will return the tuples containg the final content and id
    summary = get_answer(skeleton + "\n" + node.content + "\nSUMMARY: ")
    return (summary, node)


def concurrent_execution(function, inputs, max_workers=100, batch_size=50,wait_time=30):
    batches = divide_batch(batch_size, inputs)
    output = list()
    for batch in batches:
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # send the server all of the prompt at the same time
            output = output + list(executor.map(function, batch))
        print("pausing to not crash the server...")
        time.sleep(wait_time)
    return output 

def first_layer_concurrent(default_nodes):
    summary_nodes = list()
    with open("./prompts/summarize2.txt", "r") as file:
        skeleton = file.read()
        helper = functools.partial(first_layer_helper, skeleton)
        #get the summaries concurrently and wait 30 seconds every 30 requests
        summaries_node_pairs = concurrent_execution(helper,default_nodes)
        # received a list of tuples (summary, node) and sort it according to the node's id
        sorted_tuples = sorted(summaries_node_pairs, key=lambda x: x[1].id)
        for t in sorted_tuples:
            # create the node and append it in the right order
            summary_nodes.append(Node(t[0], [t[1]]))
    return summary_nodes


# location varies
def layer_to_string_json(file_path):
    with open(file_path, "r") as file:
        output = ""
        nodes_dict = json.loads(file.read())
        for node_dict in nodes_dict:
            output = output + \
                f"{node_dict['id']}. {node_dict['content'][1:]}\n\n"
        with open("./miscellaneous/layer_to_string.txt", "w") as file:
            file.write(output)
        return output

# location varies


def layer_to_string(nodes):
    output = ""
    for node in nodes:
        output = output + f"{node.id}. {node.content[1:]}\n\n"
    with open("./miscellaneous/layer_to_string.txt", "w") as file:
        file.write(output)
    return output

# location varies


def json_to_nodes(file_path, previous_layer=list()):
    nodes = list()
    with open(file_path, "r") as file:
        #remove the limit later [:5]
        nodes_dict = json.loads(file.read())
        for node_dict in nodes_dict:
            pre_pointer = list()  # empty list as default
            # go through each dict_node, turning them into actual node
            if node_dict['nextNodes']:
                # if it actuall points to something
                for pre_node in previous_layer:
                    # search through the previous_layer
                    # if match then stop
                    # print(f"PREVIOUS NODES ID: {pre_node.id}")
                    # print(f'NODE LIST: {node_dict["nextNodes"]}')
                    if pre_node.id in node_dict['nextNodes']:
                        # print("MATCH!")
                        pre_pointer.append(pre_node)

            nodes.append(Node(node_dict["content"],pre_pointer, id=node_dict['id']))
    return nodes
def divide_batch(count_per_batch, batch):
    divided_list = [batch[count_per_batch*i:count_per_batch * (i+1)] for i in range(int(len(batch)/count_per_batch)+1)]
    if not divided_list[-1]:
        return divided_list[:-1]
    return divided_list
    

# grouping section


def grouping(previous_layer):
    # getting the prompt
    layer_string = layer_to_string(previous_layer)
    with open("./prompts/grouping.txt", "r") as file:
        skeleton = file.read()
    prompt = skeleton.replace("<<SUMMARIES>>", layer_string)

    # getting the answer
    # comment out when testing
    grouping_text = '[' + get_answer(prompt) + ']'
    # grouping_text ='['+'[1,2,3,4,"Overview of Persuasion"],[5,6,"Compliance Professionals"],[7,8,"Updates to the Study of Persuasion"],[9,10,"Six Principles of Compliance"],[11,12,"Automatic Influence"],[13,14,"Example of Compliance"]'+']'
    print(grouping_text)
    grouping_list = json.loads(grouping_text)

    # now that we have the grouping, we need to match things up
    final_nodes = list()
    for group in grouping_list:
        members_ids = group[:-1]
        title = group[-1]
        members = list()
        for node in previous_layer:
            if node.id in members_ids:
                members.append(node)
        final_nodes.append(Node(title, members))
    return final_nodes

def batch_dividing(previous_layer,max_token=1500):
    count = 0
    current_batch = list() 
    output = list()
    for node in previous_layer:
        if count < max_token:
            current_batch.append(node)
            count = count + token_count(node.content)
        else:
            output.append(current_batch)
            current_batch = list() 
            count = 0 
    output.append(current_batch)
    return output 

def grouping_helper(batch_index_pair):
    batch,index = batch_index_pair 
    return (grouping(batch),index) 

def index_attachment(batch):
    return [(batch,i) for i,batch in enumerate(batch)]

def grouping_concurrent(previous_layer,max_token=1500):
    #first divide the previous layer into sizable batches 
    batches = batch_dividing(previous_layer,max_token) 
    #pair them up with their current position in the list
    batch_index_pair = index_attachment(batches)
    #execute grouping for all of the pairs concurrently
    next_layer = concurrent_execution(grouping_helper,batch_index_pair)
    #sort the result according to their position again 
    sorted_tuples = sorted(next_layer,key=lambda x: x[1])
    next_layer_batches = [t[0] for t in sorted_tuples]
    next_layer = sum(next_layer_batches,[])
    return next_layer
    



def nodes_to_string(nodes):
    text = ""
    for node in nodes:
        text = text + node.to_string() + "\n"
    return text


def grouping_recursion(max_nodes, max_layer, previous_layer, layer_num):
    try:
        if len(previous_layer) > max_nodes and layer_num < max_layer:
            print(f"Creating the {layer_num + 1}-th layer...")
            new_layer = grouping_concurrent(previous_layer)
            grouping_recursion(max_nodes, max_layer, new_layer, layer_num + 1)
        print(f"Saving the {layer_num}-th layer...")
        parsing.save_nodes(
            previous_layer, f"./knowledge_tree_concurrent/layer_{layer_num}.json")
    except Exception as e:
        print(f"Error occured at level {layer_num + 1 } - unable to save. Start from layer {layer_num} next.")
        error_print(e)
        print(f"Saving the {layer_num}-th layer...")
        parsing.save_nodes(
            previous_layer, f"./knowledge_tree_concurrent/layer_{layer_num}.json")

def retry(max_nodes, max_layer, layer_num): 
    previous_layer = json_to_nodes(f"./knowledge_tree_concurrent/layer_{layer_num}.json")
    grouping_recursion(max_nodes,max_layer,previous_layer,layer_num) 

def token_count(text):
    # returns an estimate of #tokens corresponding to #characters nchars
    return len(text)/4


def create_knowledge_tree(max_nodes, max_layer):
    # max_nodes is that maximum nodes that the last layer should have 
    # max_layer is the maximum depth of the tree
    print("Parsing the book into nodes...")
    zeroth_layer = parsing.book_to_nodes(path, max_block)
    parsing.save_nodes(zeroth_layer, "./knowledge_tree_concurrent/layer_0.json")

    # creating the first layer: why don't you save here?...ircc it's because the grouping already saved the first layer 
    print("Summarize the zeroth layer into the first layer...")
    first_layer = first_layer_concurrent(zeroth_layer)

    # recursively create the tree structure
    print("starting the recurrent tree building process")
    grouping_recursion(max_nodes, max_layer, first_layer, 1)


