import json
class Node:
    def __init__(self,round_id,breadth,parent=None):
        self.children = []
        self.round_id = round_id
        self.parent = parent
        self.workflow_score = 0
        self.total_score = 0
        self.visits = 0
        self.expansion_count = 0
        self.is_terminal = False
        self.breadth = breadth
    

    def update_workflow_score(self,score):
        self.workflow_score = score
        if self.parent is not None and self.workflow_score < (self.parent.workflow_score ):
            self.is_terminal = True

    def update_score(self, score,):
        self.total_score += score
        self.visits += 1
        # check if all child is terminal
        all_child_terminal = True
        for child in self.children:
            if not child.is_terminal:
                all_child_terminal = False
                break
        if all_child_terminal and self.expansion_count == self.breadth:
            self.is_terminal = True

            
        
    def add_child(self, node):
        self.children.append(node)
        self.expansion_count += 1
        
