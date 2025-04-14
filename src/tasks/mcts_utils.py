import os
import json
import random
from typing import List, Dict
from MCTS.Node import Node
from termcolor import colored

def create_round_directory(graph_path: str, round_number: int) -> str:
    directory = os.path.join(graph_path, f"round_{round_number}")
    os.makedirs(directory, exist_ok=True)
    return directory



def load_graph(directory: str):
    # workflow
    with open(f"{directory}/workflow.txt", "r") as f:
        workflow = f.read()
    
    # action knowledge
    with open(f"{directory}/action_knowledge.txt", "r") as f:
        action_knowledge = f.read()

    return workflow, action_knowledge

import xml.etree.ElementTree as ET
import json

# def save_modification(modification,root_path,father_node,son_node):
#     action_knowledge = modification["action_knowledge"]
#     workflow = modification["workflow"]
#     analysis = modification["analysis"]
#     son_directory = create_round_directory(root_path, son_node.round_id)
#     father_directory = create_round_directory(root_path, father_node.round_id)
#     with open(f"{son_directory}/action_knowledge.txt", "w") as f:
#         f.write(action_knowledge)
#     with open(f"{son_directory}/workflow.txt", "w") as f:
#         f.write(workflow)
#     with open(f"{father_directory}/experience.json", "r") as f:
#         father_experience = json.load(f)

#     with open(f"{son_directory}/experience.json", "w") as f:
#         data = {
#             "father": father_node.round_id,
#             "father_score": father_experience["score"],
#             "modification": analysis
#         }
#         json.dump(data, f,indent=4,ensure_ascii=False)
#     return None


def save_modification(modification,root_path,father_node,son_node):
    tool_doc = modification["tool_doc"]
    workflow = modification["workflow"]
    son_directory = create_round_directory(root_path, son_node.round_id)
    father_directory = create_round_directory(root_path, father_node.round_id)
    tool_doc_set = {}
    for index,tool in enumerate(tool_doc):
        tool_doc_set[f"{index}"] = tool

    
    with open(f"{son_directory}/tool_doc.json", "w") as f:
        json.dump(tool_doc_set, f,indent=4,ensure_ascii=False)
    with open(f"{son_directory}/workflow.txt", "w") as f:
        f.write(workflow)
    with open(f"{father_directory}/experience.json", "r") as f:
        father_experience = json.load(f)


    with open(f"{father_directory}/workflow.txt", "r") as f:
        father_workflow = f.read()


    with open(f"{son_directory}/experience.json", "w") as f:
        data = {
            "father": father_node.round_id,
            "father_score": father_experience["score"],
            "modification": {
                "origin_workflow": father_workflow,
                "now_workflow": workflow,
            }
        }
        json.dump(data, f,indent=4,ensure_ascii=False)
    return None


# def save_son_information(child_round,directory):
#     with open(f"{directory}/experience.json", "w") as f:
#         data = json.load(f)
#     if "children" in data:
#         data["children"].append(child_round)
#     else:
#         data["children"] = [child_round]
#     with open(f"{directory}/experience.json", "w") as f:
#         json.dump(data, f,indent=4,ensure_ascii=False)


def xml_to_dict(element):
    """
    Recursively converts an XML element and its children to a dictionary.
    """
    result = {}
    
    for child in element:
        child_result = xml_to_dict(child)
        
        if child.tag in result:
            if not isinstance(result[child.tag], list):
                result[child.tag] = [result[child.tag]]
            result[child.tag].append(child_result)
        else:
            result[child.tag] = child_result
    
    if element.text and element.text.strip():
        result['text'] = element.text.strip()
    
    return result

def xml_string_to_json(xml_string) -> Dict:
    """
    Converts an XML string to a Dict .
    """
    root = ET.fromstring(xml_string)
    root_dict = {root.tag: xml_to_dict(root)}
    return root_dict

def load_sample_trajectory(directory,llm):
    if os.path.exists(os.path.join(directory,"validate_results.jsonl")):
        with open(os.path.join(directory,"validate_results.jsonl"), "r") as f:
            data = [json.loads(line) for line in f]
            # print(data[0])
        failure_trajectory = []
        success_trajectory = []
        threshold = 0.5
        for d in data:
            if d["result"] <= threshold:
                failure_trajectory.append(d)
            elif d["result"] > threshold:
                success_trajectory.append(d)
        sample_success = random.sample(success_trajectory, min(2,len(success_trajectory)))
        sample_failure = random.sample(failure_trajectory, min(2,len(failure_trajectory)))
        return sample_success,sample_failure
    else:
        toolbench_result_path = os.path.join(directory,"pass_rate_results",f"G3_instruction_{llm}_DFS_woFilter_w2.json")
        with open(toolbench_result_path, "r") as f:
            data = json.load(f)



def update_experience(directory,score=None,father=None,modification=None,father_score=None):

    with open(f"{directory}/experience.json", "r") as f:
        data = json.load(f)
    if score is not None:
        data["score"] = score
    if father is not None:
        data["father"] = father
    if father_score is not None:
        data["father_score"] = father_score
    if modification is not None:
        data["modification"] = modification

    with open(f"{directory}/experience.json", "w") as f:
        json.dump(data, f,indent=4,ensure_ascii=False)



# get the experience of parent and sibling nodes for the current node
def load_experience(node,root_path) -> List[Dict]:
    round_id = node.round_id
    experience = []
    #get sibling experience
    if node.children is not None:
        siblings = node.children
        for sibling in siblings:
            directory = create_round_directory(root_path, sibling.round_id)
            with open(os.path.join(directory,"experience.json"), "r") as f:
                data = json.load(f)
                experience.append({"score_before_modification":data["father_score"],"score_after_modification":data["score"],"modification":data["modification"]})
                f.close()
    #get ancestor experience
    while node is not None:
        print(colored(f"From Node {node.round_id}", "green"))
        directory = create_round_directory(root_path, round_id)
        with open(os.path.join(directory,"experience.json"), "r") as f:
            data = json.load(f)
            if data["father"] is not None:
                experience.append({"score_before_modification":data["father_score"],"score_after_modification":data["score"],"modification":data["modification"]})
            round_id = data.get("father",None)
            f.close()
        node = node.parent
        #random color

    if len(experience) == 0:
        return ["No experience"]
    else:
        return experience

        
