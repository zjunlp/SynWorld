import inspect
import os
import json
import random
from tqdm import tqdm
from termcolor import colored
import concurrent.futures
from LLMs import *
from agents.workflow import Workflow
from typing import Dict
from mcts_utils import load_sample_trajectory,load_graph,xml_string_to_json
from prompts.workflow import WORKFLOW_OPTIMIZE_SYSTEM_PROMPT,WORKFLOW_INPUT
from prompts.tool_optimize import TOOL_OPTIMIZE_PROMPT,TOOL_INPUT_PROMPT,TOOL_WORKFLOW_OPTIMIZE_SYSTEM_PROMPT,TOOL_WORKFLOW_INPUT
def calculate_score(is_solved):
    score = 0
    for status in is_solved.values():
        if status == "AnswerStatus.Solved":
            score += 1  # 或者根据需要设置分数
        elif status == "AnswerStatus.Unsolved":
            score += 0  # 无需额外添加分数
        elif status == "AnswerStatus.Unsure":
            score += 0.5
    return score/3


def optimize_tool(tool,llm):
    messages = []
    messages.append({
        "role": "system",
        "content": TOOL_OPTIMIZE_PROMPT
    })

    sample_tra = random.sample(tool["trajectory"], 3)  # 随机选择3个轨迹
    input_tra = []
    for tra in sample_tra:
        now_tra = {key: value for key, value in tra.items() if key != "is_solved"}
        input_tra.append({"trajectory": now_tra, "is_solved": calculate_score(tra["is_solved"])})

    messages.append({
        "role": "user",
        "content": TOOL_INPUT_PROMPT.format(tool_name=tool["api_name"], original_description=tool["tool_description"], trajectory=input_tra)
    })

    modification = llm(messages)
    tool["new_description"] = modification.split("Optimized Description:")[-1].strip()
    return tool  # 返回更新后的工具

def format_tool_doc(tool_refine_base):
    format_tool_doc = []
    for api in tool_refine_base:
        if "new_description" not in api.keys():
            continue
        tool_name = api["tool_name"]
        tool_guideline = {
            "name": api["api_name"],
            "description": api["new_description"],
            "required_parameters": api["required_parameters"],
            "optional_parameters": api["optional_parameters"]
        }
        is_exist = False
        for tool in format_tool_doc:
            if tool["tool_name"] == tool_name:
                tool["tool_guidelines"][api["api_name"]] = tool_guideline
                is_exist = True
                break
        if not is_exist:
            format_tool_doc.append({
                        "tool_name": tool_name,
                        "category_name": api["category"],
                        "tool_guidelines": {
                            api["api_name"]: tool_guideline
                        }
            })
    return format_tool_doc

def format_tool_name(tool_name):

    format_name = tool_name
    format_name = format_name.replace("(FREE)", "free")
    format_name = format_name.replace(" & ", "_")
    format_name = format_name.replace("/", "_")
    format_name = format_name.replace(" ", "_").lower()
    return format_name
class Modifier:
    def __init__(self,experience:Dict,llm:object,directory:str,split:str):
        self.experience = experience
        self.llm = llm
        self.directory = directory
        self.split = split



    def modify(self):
        if "HotPotQA" in self.directory:
            success_trajectory,failure_trajectory = load_sample_trajectory(self.directory,self.llm)
            workflow,action_knowledge = load_graph(self.directory)
            prompt = WORKFLOW_INPUT.format(experience=self.experience,success_trajectory=success_trajectory,failure_trajectory=failure_trajectory,workflow=workflow,action_knowledge=action_knowledge)
            messages = []
            messages.append({
                "role":"system",
                "content":WORKFLOW_OPTIMIZE_SYSTEM_PROMPT
            })
            messages.append({
                "role":"user",
                "content":prompt
            })
            modification = self.llm(messages)
            modification = modification.split("<modification>")[-1].split("</modification>")[0]
            modification = "<modification>\n"+modification+"</modification>"
            modify_dict = xml_string_to_json(modification)
            result_dict = {
                "analysis":modify_dict["modification"]["analysis"]['text'],
                "action_knowledge":modify_dict["modification"]["action_knowledge"]['text'],
                "workflow":modify_dict["modification"]["workflow"]['text']
            }
            return result_dict
        elif "Toolbench" in self.directory:
            if "qwen-long" in self.directory:
                model_name = "qwen-long"
            elif "gpt-4-turbo" in self.directory:
                model_name = "gpt-4-turbo"
            with open(os.path.join(self.directory,f"pass_rate_results_{self.split}",f"G3_instruction_qwen-long_DFS_woFilter_w2.json"),"r") as f:
                trajectory = json.load(f)
            origin_tool_path = "./DRAFT/dataset/ToolBench/test_data/G3_instruction.json"
            with open(origin_tool_path,"r") as f:
                tool_origin = json.load(f)

            tool_set = []
            for t in tool_origin:
                for api in t["api_list"]:
                    if api not in tool_set:
                        tool_set.append(api)


            print(len(tool_set))
            tool_refine_base = []
            for t in tool_set:
                # print(t)
                tool_refine_base.append(
                    {
                        "category": t["category_name"],
                        "tool_name": t["tool_name"],
                        "api_name": t["api_name"],
                        "tool_description": t["api_description"],
                        "required_parameters": t["required_parameters"],
                        "optional_parameters": t["optional_parameters"],
                    }
                )

            for index,tra in trajectory.items():
                # print(tra)
                for tool_name in tra["tool_names"]:
                    if tool_name == "Finish":
                        continue
                    else:
                        for origin_tool in tool_refine_base:

                            format_name = format_tool_name(origin_tool["api_name"])
                            if format_name in tool_name:
                                if "trajectory" in origin_tool.keys(): 
                                    origin_tool["trajectory"].append(tra)
                                else:
                                    origin_tool["trajectory"] = [tra]


            with concurrent.futures.ThreadPoolExecutor(max_workers=32) as executor:
            # 提交任务
                futures = {executor.submit(optimize_tool, tool, self.llm): tool for tool in tool_refine_base}
                for future in tqdm(concurrent.futures.as_completed(futures), total=len(futures), desc="优化工具进度"):
                    tool = futures[future]  # 获取与未来关联的工具
                    try:
                        updated_tool = future.result()  # 获取每个线程的结果
                        print(f'{updated_tool["tool_name"]}____{updated_tool["api_name"]} 的描述已更新。')
                    except Exception as e:
                        print(f'优化工具时出错: {e}，出错工具: {tool["tool_name"]}_{tool["api_name"]}')
            for tool in tool_refine_base:
                if "trajectory" in tool:
                    del tool["trajectory"] 
            tool_refine_base = format_tool_doc(tool_refine_base)

            print(len(tool_refine_base))
            with open(os.path.join(self.directory,"tool_refine_base.json"),"w") as f:
                json.dump(tool_refine_base,f,indent=4,ensure_ascii=False)

            #modify the workflow
            
            sample_trajectory = random.sample([tra for index,tra in trajectory.items()],3)
            # print(sample_trajectory)
            messages = []
            messages.append({
                "role":"system",
                "content": TOOL_WORKFLOW_OPTIMIZE_SYSTEM_PROMPT
            })
            input_tra = []
            for tra in sample_trajectory:
                now_tra =  {key: value for key, value in tra.items() if key != "is_solved"}
                input_tra.append({"trajectory":now_tra,"is_solved":calculate_score(tra["is_solved"])})
            messages.append({
                "role":"user",
                "content":TOOL_WORKFLOW_INPUT.format(workflow=self.experience,trajectory=input_tra)
            })
            new_workflow = self.llm(messages)
            # print(colored(new_workflow,"blue"))
            new_workflow = new_workflow.split("Optimized Workflow:")[-1].strip()
            print(colored(new_workflow,"green"))
            return {
                "tool_doc":tool_refine_base,
                "workflow":new_workflow
            }

            

if __name__ ==  "__main__":
    experience =  [
        {
            "workflow": "To solve multi-hop reasoning questions, the system first decomposes the question into sub-questions. Then, it uses a tool to answer each sub-question. Finally, it combines the answers to generate the final answer.",
            "action_knowledge": "Goolge search: Use Google search to find information about the question.",
            "reward": 0.8
        },
        {
            #different workflow
            "workflow": "To solve multi-hop reasoning questions, the system indicates the sub-questions to the user. The user then uses a tool to answer each sub-question. Finally, the system combines the answers to generate the final answer.",
            "action_knowledge": "Goolge search: Use Google search to find information about the question.",
            "reward": 0.6
        }
    ]
    llm = call_qwen
    directory = "./workflow/qwen-long/Toolbench/CoT@1/round_1"
    modify = Modifier(
        experience=experience,
        llm=llm,
        directory=directory,
    )
    modify.modify()
    # print(modify.modify())

