from tasks.toolbench import Toolbench
from typing import Dict


class Toolbenchconfig:
    tool_root_dir = "../../StableToolBench/data/toolenv/tools"
    backbone_model = "chatgpt_function"
    chatgpt_model = "qwen-long"
    base_url = "OPENAI_API_BASE_URL"
    openai_key = "OPENAI_API_KEY"
    max_observation_length = 1024
    # method = "DFS_woFilter_w2" #DFS_woFilter_w2 for DFS
    method = "CoT@1"
    test_query_file = "....//StableToolBench/data/test_instruction/G3_instruction.json"
    dev_query_file = "./data/qwen-toolbench_vaild.json"
    toolbench_key = "your_toolbench_key"
    num_thread = 16
    rapidapi_key = None
    use_rapidapi_key = False
    api_customization = False
    observ_compress_method = "truncate"
    single_chain_max_step = 50
    max_source_sequence_length = 4096
    max_sequence_length = 8192
    max_query_count = 200
    overwrite = False

toolbench_args = Toolbenchconfig


dataset_config = {
    "Toolbench": {
        "benchmark": Toolbench,
        "args": toolbench_args,
    }
}