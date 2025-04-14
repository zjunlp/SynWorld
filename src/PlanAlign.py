import argparse
import os
from typing import Dict, List
from Evaluation import Evaluator
from Expansion import Modifier
from MCTS.Node import Node
from mcts_utils import *
import sys
from LLMs import call_qwen, call_gpt
import numpy as np
from functools import partial
from termcolor import colored

class ExperimentConfig:
    def __init__(self, dataset: str, question_type: str, tools: List[str] = []):
        self.dataset = dataset
        self.question_type = question_type
        self.tools = tools



    
EXPERIMENT_CONFIGS: Dict[str, ExperimentConfig] = {
    "HotpotQA": ExperimentConfig(
        dataset="HotpotQA",
        question_type="qa",
        tools=["Search"]
    ),
    "Toolbench": ExperimentConfig(
        dataset="Toolbench",
        question_type="API Calling",

    )
}


def get_model(model_name:str):
    if ("qwen" in model_name) or ("llama" in model_name):
        llm = partial(call_qwen, model=model_name)
    elif "gpt" in model_name:
        llm = partial(call_gpt, model=model_name)
    else:
        raise ValueError(f"Model { model_name } not found")
    return llm

class PlanAlignMCTS:
    def __init__(
        self,
        dataset: str,
        model_name: str,
        llm: object,
        workflow_path: str,
        method: str = "CoT@1",
        initial_round: int = 1,
        max_rounds: int = 50,
        validation_rounds: int = 1,
        validation_nums: int = 50,
        breadth: int = 3,
        max_workers: int = 8,
        mode: str = "test"
    ) -> None:
        self.model_name = model_name
        self.llm = llm
        self.dataset = dataset
        self.root_path = os.path.join(workflow_path,method)
        self.round = initial_round
        self.max_rounds = max_rounds
        self.validation_rounds = validation_rounds
        self.validation_nums = validation_nums
        self.breadth = breadth
        self.ucb_constant = 1.41
        self.max_workers = max_workers
        self.split = mode

    def run(self):
        root_node = Node(round_id=self.round,breadth=self.breadth)
        for index in range(self.max_rounds):
            #selection
            if index == 0:
                current_node = root_node
            else:
                current_node = self.selection(root_node)
            if current_node == None :
                print("No more nodes to select")
            print(colored(f"Round {current_node.round_id} - Selection", "green"))
            self.directory = create_round_directory(self.root_path, current_node.round_id)

            # Evaluation
            # workflow, action_knowledge = load_graph(self.directory)
            # Evaluate the workflow
            score = self.simulation(
                split="dev",
            )
            current_node.update_workflow_score(score)

            # Backpropagation
            self.backpropagation(current_node, score)
            update_experience(self.directory,score=score)
            self.round += 1

    def test(self,round_id):
        node = Node(round_id=round_id,breadth=self.breadth)
        self.directory = create_round_directory(self.root_path, node.round_id)
        # workflow, action_knowledge = load_graph(self.directory)
        score = self.simulation(
            split="test"
        )
        print(score)

    def selection(self, node):
        # Implement UCB selection
        # 如果不是终结节点
        while not node.is_terminal:
            if node.expansion_count < self.breadth:
                return self.expansion(node)
            else:
                max_score = -float('inf')
                for child in node.children:
                    if child.is_terminal:
                        continue
                    score = self.ucb_score(child)
                    if score > max_score and not child.is_terminal:
                        max_score = score
                        max_node = child
                if max_score == -float('inf'):
                    return None
                else:
                    node = max_node
        return None

    def expansion(self, node):
        
        experience = load_experience(node,self.root_path)
        directory = create_round_directory(self.root_path, node.round_id)
        print(directory)
        modifier = Modifier(
            experience=experience,
            llm=self.llm,
            directory=directory,
            split=self.split
        )
        modification = modifier.modify()
        
        print(colored(f"Round {self.round} - Expansion", "green"))
        # print(colored(f"experience: {experience}", "blue"))

        son_node = Node(round_id=self.round,parent=node,breadth=self.breadth)
        node.add_child(son_node)
        son_node_directory = create_round_directory(self.root_path, self.round)
        save_modification(
            modification=modification,
            root_path=self.root_path,
            father_node=node,
            son_node=son_node
        )
        return son_node

        

    def simulation(self,split): #

        evaluator = Evaluator(
            action_knowledge_path = self.directory,
            llm = self.llm,
            model_name = self.model_name,
            dataset_type = self.dataset,
            max_workers = self.max_workers
        )
        score = evaluator.eval(split=split,sample=self.validation_nums)
        return score

    def backpropagation(self, node, score):
        while node is not None:
            node.update_score(score)
            node = node.parent

    def ucb_score(self, node):
        if node.visits == 0:
            return float('inf')  # Explore unvisited nodes
        
        # Parent visits should at least be 1 to avoid division by zero
        parent_visits = node.parent.visits if node.parent else 1
        
        exploitation = node.total_score / node.visits
        exploration = self.ucb_constant * np.sqrt(np.log(parent_visits) / node.visits)
        
        return exploitation + exploration

    def sample_training_data(self):
        return random.sample(self.training_data, 20)

def main(args):
    # args 
    print(sys.path)
    call_llm = get_model(args.model)
    workflow_path = args.workflow_path
    config = EXPERIMENT_CONFIGS[args.dataset]
    validation_rounds = args.validation_rounds
    validation_nums = args.validate_nums
    workflow_path = args.workflow_path
    workflow_path = os.path.join(workflow_path,args.model,args.dataset)
    breadth = args.breadth
    max_workers = args.max_workers
    mode = args.mode

    # init MCTS
    Mcts = PlanAlignMCTS(
        model_name=args.model,
        dataset=config.dataset,
        llm=call_llm,
        initial_round=1,
        max_rounds=args.max_rounds,
        validation_rounds=validation_rounds,
        validation_nums=validation_nums,
        workflow_path=workflow_path,
        breadth=breadth,
        max_workers=max_workers,
        mode=mode
    )
    print("Task Begin!")
    if mode == "dev":
        Mcts.run()
    else:
        Mcts.test(round_id = args.test_round)



# Example Usage
if __name__ == "__main__":
    print("hellp")
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, default="qwen-long")
    parser.add_argument("--max_rounds", type=int, default=10)
    parser.add_argument("--dataset", type=str, default="Toolbench")
    parser.add_argument("--validation_rounds", type=int, default=1)
    parser.add_argument("--validate_nums", type=int, default=100)
    parser.add_argument("--workflow_path", type=str, default="workflow/")
    parser.add_argument("--breadth", type=int, default=3)
    parser.add_argument("--method", type=str, default="CoT@1")
    parser.add_argument("--max_workers", type=int, default=8)
    parser.add_argument("--mode", type=str, choices=["dev","test"], default="dev")
    parser.add_argument("--test_round", type=int, default=3)

    args = parser.parse_args()
    main(args)




