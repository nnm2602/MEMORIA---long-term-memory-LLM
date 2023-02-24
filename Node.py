class Node: 
    id = 0 #this should be global 
    def __init__(self, content, next_nodes=None,id=None):
        self.content = content 
        self.next_nodes = next_nodes
        self.next_ids = None 
        if not id:
            Node.id = Node.id + 1 
            self.id = Node.id
        else:
            self.id = id 
        if self.next_nodes:
            self.next_ids = [node.id for node in self.next_nodes]

    def to_dict(self):
        return {
            "content":self.content,
            "nextNodes":self.next_ids,
            "id":self.id
        }
    def to_string(self):
        return f"content: {self.content}\nnext_nodes: {self.next_nodes}\nnext_ids: {self.next_ids}\nid: {self.id}\n"
    def __eq__(self,other):
        if isinstance(other,Node):
            return self.content == other.content and self.next_nodes == other.next_nodes and self.next_ids == other.next_ids and self.id == other.id 
        return False 
    
            
