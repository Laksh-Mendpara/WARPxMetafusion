from dataset_util import get_data
from trainer_utils import get_trainer
from model_util import (
    load_model,
    get_param_details
)

def main():
    train_data_path = "data/data_v4.csv"
    eval_data_path = "data/eval_data_v4.csv"

    config = {
        "num_train_epochs": 1,
        "per_device_train_batch_size": 16,
        "learning_rate": 4.08222e-06,
        "weight_decay": 0.046407,
        "lr_scheduler_type": "reduce_lr_on_plateau",
        "lora_alpha": 64,
        "warmup_ratio": 0.164557,
        "lora_dropout": 0.160246,
        "output_dir": "outputs"
    }

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

    trainer.train()

if __name__=="__main__":
    main()