from PyPDF2 import PdfReader
import os
import json
from Node import Node


max_pages = 60
# ultility


def equal_part_split(block_size, text):
    return [text[i:i+block_size] for i in range(0, len(text), block_size)]


def get_default_nodes(contents):
    Node_list = list()
    for content in contents:
        Node_list.append(Node(content))
    return Node_list

# main functions


def book_to_txt(book_path, folder_path):
    reader = PdfReader(book_path)
    for i, page in enumerate(reader.pages):
        file_text = page.extract_text()
        if file_text:
            with open(os.path.join(folder_path, f'page_{i}.txt'), "w") as file:
                file.write(file_text)
        if i == max_pages: 
            break 


def text_files_to_nodes(folder_path, max_block):
    Nodes = list()
    small_remainder = ""  # store cut-off stuff that is too small to process
    for filename in os.listdir(folder_path):
        # loop through the list of file names
        file_path = os.path.join(folder_path, filename)  # get each file path
        if os.path.isfile(file_path):
            # only run if it's a file
            with open(file_path, 'r') as file:
                file_text = file.read()
                parts = equal_part_split(max_block, file_text)
                # include the left over part
                if len(parts) == 0:
                    print(f'the text:{file_text}')
                    print(f'file name:{filename}')
                    print("\n\n\n\n")
                parts[0] = parts[0] + small_remainder
                # if the last piece is < 10% of the entire block -> pass it down
                if len(parts[-1]) < 0.1 * max_block:
                    small_remainder = parts[-1]
                    parts = parts[:-1]  # remove the last one

                # turn this into the node
                Nodes = Nodes + get_default_nodes(parts)

    return Nodes


def book_to_nodes(book_path, max_block, folder_path="./pages"):
    book_to_txt(book_path, folder_path)  # conver to books into txt
    Nodes = text_files_to_nodes(folder_path, max_block)
    return Nodes


def save_nodes(nodes,file_name="file_nodes.json"):
    node_list = [node.to_dict() for node in nodes]
    with open(file_name, 'w') as file:
        file.write(json.dumps(node_list))

# save_nodes(book_to_nodes(path,max_block))


