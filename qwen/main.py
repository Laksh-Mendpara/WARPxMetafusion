from dataset_util import get_data
from trainer_utils import get_trainer
from model_util import (
    load_model,
    get_param_details
)

def main():
    train_data_path = "data/data_v4.csv"
    eval_data_path = "data/eval_data_v4.csv"

    model, tokenizer = load_model()

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
        train_data=train_data,
        eval_data=eval_data,
        tokenizer=tokenizer
    )

    trainer.train()

if __name__=="__main__":
    main()