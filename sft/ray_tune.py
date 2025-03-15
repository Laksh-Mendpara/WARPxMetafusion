from dataset_util import get_data
from trainer_utils import get_trainer
from ray.tune.search.optuna import OptunaSearch
import torch
import gc
from model_util import (
    load_model,
    get_param_details
)
from ray import(
    tune,
    train
)
import subprocess
import time
import os

def file_name(config):
    fname = "model_"
    for key, val in config.items():
        fname += "{}_{}_".format(key, val) 
    return fname

def train_model(config):
    
    train_data_path = "/home/raid3/MetaFusion/data_v2/data_v1.csv"
    eval_data_path = "/home/raid3/MetaFusion/data_v2/eval_data_v1.csv"
    root_dir_path = "/home/raid3/MetaFusion/outputs"
    output_dir_name = file_name(config)
    output_path = os.path.join(root_dir_path, output_dir_name)
    config["output_dir"] = output_path

    model, tokenizer = load_model(config=config)

    train_data = get_data(
        file_path=train_data_path,
        tokenizer=tokenizer
    )
    eval_data = get_data(
        file_path=eval_data_path,
        tokenizer=tokenizer
    )

    trainer = get_trainer(
        model=model,
        train_dataset=train_data,
        eval_dataset=eval_data,
        tokenizer=tokenizer,
        config=config
    )

    stats, test_metric = trainer.train()
    print(stats)
    print(test_metric)
    train.report({"loss": test_metric["eval_loss"]})

    remove_cmd = f"rm -rf {output_path}"
    subprocess.run(remove_cmd, shell=True)

    # Clear GPU cache
    del model
    del tokenizer
    del train_data
    del eval_data
    del trainer
    
    # Force garbage collection
    gc.collect()
    
    # Clear CUDA cache
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    time.sleep(10)
    print("Done training")


def main():

    config = {
        ## batch
        ## gradient step
        "num_train_epochs": tune.choice([1, 2]),
        "per_device_train_batch_size": tune.choice([2, 4, 8, 16]),
        "learning_rate": tune.loguniform(1e-6, 5e-4),
        "weight_decay": tune.loguniform(1e-5, 1e-1),
        "lr_scheduler_type": tune.choice(["cosine_with_restarts", "reduce_lr_on_plateau"]),
        "lora_alpha": tune.choice([16, 64, 256, 512]),
        "warmup_ratio": tune.uniform(0.03, 0.2),
        "lora_dropout": tune.uniform(0, 0.2),
    }
    
    # scheduler = ASHAScheduler(
    #     metric="loss",
    #     mode="min",
    #     max_t=10,
    #     grace_period=1,
    #     reduction_factor=2
    # )

    # result = tune.run(
    #     train_model,
    #     # resources_per_trial={"cpu": 2, "gpu": 1},
    #     config=config,
    #     num_samples=10,
    #     scheduler=scheduler
    # )

    algo = OptunaSearch()
    tuner = tune.Tuner(
        tune.with_resources(train_model, {'cpu': 64, 'gpu': 1}),
        tune_config=tune.TuneConfig(
            search_alg=algo,
            num_samples=20,
            metric="loss",
            mode="min"
        ),
        param_space=config
    )
    results = tuner.fit()
    print(results)
    print("Best config: ", results.get_best_result().config)

if __name__=="__main__":
    main()
