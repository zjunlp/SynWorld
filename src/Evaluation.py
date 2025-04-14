from tasks.hotpotqa import HotpotQABenchmark
from tasks.toolbench import Toolbench
from tasks.dataset_config import dataset_config
from typing import Dict
from LLM import *
from prompts.system_prompts import SYSTEM_PROMPTS, EXAMPLES
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import random
class Evaluator:
    def __init__(self,llm: object,model_name:str, dataset_type: str, action_knowledge_path: str, max_workers: int = 8):
    
        self.action_knowledge_path = action_knowledge_path
        self.llm = llm
        self.model_name = model_name
        self.dataset_type = dataset_type
        self.max_workers = max_workers
        print(action_knowledge_path)
    # def eval_one(self, d):
    #     question = d["question"]
    #     answer = d["answer"]
    #     trajectory, pred = self.benchmark.evaluate(
    #         prompt=SYSTEM_PROMPTS[self.dataset_type].format(workflow=self.workflow, action_knowledge=self.action_knowledge),
    #         examples=EXAMPLES[self.dataset_type],
    #         question=question,
    #         answer=answer,
    #         llm=self.llm
    #     )
    #     result = self.benchmark.calculate_score(answer, pred)[0]
    #     return {
    #         "result": result,
    #         "question": d["question"],
    #         "gold": answer,
    #         "pred": pred,
    #         "trajectory": trajectory,
    #         "level": d["level"]
    #     }

    def eval(self, split: str = "dev", sample: int = 100):
        # get benchmark
        dataset = dataset_config[self.dataset_type]["benchmark"]

        # get benchmark config
        config = dataset_config[self.dataset_type]["args"]

        self.benchmark = dataset(
            args=config,
            action_knowledge_path = self.action_knowledge_path,
            split=split,
            sample = sample
        )
        # inference
        self.benchmark.run()
        
        score = self.benchmark.evaluate()
        return score
        # evaluate




# Test Evaluation
if __name__ == "__main__":
    with open('./workflow/Hotpotqa/round_1/action_knowledge.txt', 'r') as f:
        action_knowledge = f.read()
    with open('./workflow/Hotpotqa/round_1/workflow.txt', 'r') as f:
        workflow = f.read()

    llm = call_qwen
    dataset_type = "HotpotQA"
    directory = "./workflow/Hotpotqa/round_1"
    evaluator = Evaluator(
        workflow=workflow,
        action_knowledge=action_knowledge,
        llm=llm,
        dataset_type=dataset_type,
        directory=directory
    )

    score, = evaluator.eval(split="validate")
    print(f"Score: {score}")
    print("Evaluation Passed")
    