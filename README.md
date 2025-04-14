<h1 align="center"> SynWorld </h1>
<h3 align="center">Virtual Scenario Synthesis for Agentic Action Knowledge Refinement</h3>

<p align="center">
  <a href="https://arxiv.org/pdf/2504.03561" target="_blank">📄arXiv</a> •
  <a href="https://huggingface.co/papers/2504.03561" target="_blank">🤗HFPaper</a> 
</p>

<!-- [![Awesome](https://awesome.re/badge.svg)](https://github.com/zjunlp/WorFBench)  -->
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
![](https://img.shields.io/github/last-commit/zjunlp/SynWorld?color=green) 

## Table of Contents

- 🌻[Acknowledgement](#acknowledgement)
- 🌟[Overview](#overview)
- 🔧[Installation](#installation)
- ✏️[ToolBench-API-Deploy](#toolbench-api-deploy)
- 📝[MCTS-refine](#MCTS-refine)
- 🤔[ActionKnowledge-Evaluation](#ActionKnowledge-evaluation)
- 🚩[Citation](#citation)
<!-- - 🎉[Contributors](#🎉contributors) -->

---

## 🌻Acknowledgement

Our code of training module is referenced and adapted from [StableToolbench](https://github.com/THUNLP-MT/StableToolBench), [Aflow](https://github.com/FoundationAgents/AFlow), [Draft](https://github.com/quchangle1/DRAFT). And the Dataset is collected from [ToolBench](https://github.com/openbmb/toolbench?tab=readme-ov-file), [HotpotQA](). Our end-to-end evaluation module is based on [IPR](https://github.com/WeiminXiong/IPR), [Stable ToolBench](https://github.com/THUNLP-MT/StableToolBench), [HotpotQA](https://github.com/hotpotqa/hotpot). Thanks for their great contributions!



## 🌟Overview

In the interaction between agents and their environments, agents expand their capabilities by planning and executing actions. However, LLM-based agents face substantial challenges when deployed in novel environments or required to navigate unconventional action spaces. To empower agents to autonomously explore environments, optimize workflows, and enhance their understanding of actions, we propose SynWorld, a framework that allows agents to synthesize possible scenarios with multi-step action invocation within the action space and perform Monte Carlo Tree Search (MCTS) exploration to effectively refine their action knowledge in the current environment. Our experiments demonstrate that SynWorld is an effective and general approach to learning action knowledge in new environments

## 🔧Installation

```bash
git clone https://github.com/zjunlp/SynWorld
cd SynWorld
pip install -r requirements.txt

```



## ✏️ToolBench-API-Deploy
```bash
git clone https://github.com/THUNLP-MT/StableToolBench.git
cd StableToolBench
pip install requirements.txt
cd server
python main.py
```




## 📝MCTS—refine
Generate workflow with local llm api
```bash
cd SynWrold/src
python PlanAlign.py \
    --model qwen-max \
    --max_rounds 15 \
    --dataset Toolbench \
    --validate_nums 100 \
    --max_workers 16 \
    --mode dev \
    --overwrite
  
```



## 🤔ActionKnowledge-Evaluation

Evaluation the workflow of node n
```bash
cd SynWrold/src
python PlanAlign.py \
    --model qwen-max \
    --dataset Toolbench \
    --validate_nums 100 \
    --max_workers 16 \
    --mode test \
    --test_round the_round_num_you_select(eg. 3) \
    --overwrite
  
```



## 🚩Citation

If this work is helpful, please kindly cite as:

```bibtex
@article{fang2025synworld,
  title={SynWorld: Virtual Scenario Synthesis for Agentic Action Knowledge Refinement},
  author={Fang, Runnan and Wang, Xiaobin and Liang, Yuan and Qiao, Shuofei and Wu, Jialong and Xi, Zekun and Zhang, Ningyu and Jiang, Yong and Xie, Pengjun and Huang, Fei and others},
  journal={arXiv preprint arXiv:2504.03561},
  year={2025}
}
```