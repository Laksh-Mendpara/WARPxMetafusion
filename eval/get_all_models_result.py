from get_result import calculate_model_result
from loguru import logger
from tqdm import tqdm
import subprocess
import time

Models = ["Qwen/Qwen2.5-3B-Instruct", "bigcode/starcoder2-3b", "Mxode/NanoLM-1B-Instruct-v2", "Qwen/Qwen2.5-0.5B-Instruct", "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B", "Qwen/Qwen2.5-Coder-1.5B", "Qwen/Qwen2.5-Coder-1.5B-Instruct", "Qwen/Qwen2.5-Coder-3B"]


# Models = ["seeklhy/codes-1b-bird-with-evidence"]

def run_single_model(model_id: str, grammar: str, data_path: str):
    #run_cmd = "python get_result.py --model_id {} --grammar {} --data_path {}".format(
     #   model_id, 
      #  grammar, 
       # data_pathz
    # )
    # subprocess.run(run_cmd, shell=True)
    calculate_model_result(model_id, grammar, data_path)
    logger.info("Model {model_id} result calculated")
    remove_cmd = "rm -rf models && mkdir models"
    subprocess.run(remove_cmd, shell=True)

def main():
    grammar = "./mongo_grammar_1.gbnf"
    data_path = "./subset.csv"

    subprocess.run("mkdir models", shell=True)

    logger.info("Calculating result for all models")
    for model_id in (pbar := tqdm(Models, total=len(Models), desc="Calc Model result")):
        logger.info("Calculating result for model: {model_id}")
        run_single_model(model_id, grammar, data_path)
        pbar.set_description(f"Model {model_id} done")
        time.sleep(10)

    logger.info("All models result calculated")

if __name__=="__main__":
    main()
