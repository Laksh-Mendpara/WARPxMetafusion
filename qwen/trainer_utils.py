from trl import SFTTrainer
from transformers import (
    TrainingArguments,
    DataCollatorForSeq2Seq
)
from config.training_config import (
    sft_argument,
    training_argument
)
from unsloth.chat_templates import train_on_responses_only
from datasets import Dataset
from typing_extensions import Any 
from loguru import logger

def get_trainer(model: Any, 
                train_dataset: Dataset, 
                eval_dataset: Dataset, 
                tokenizer: Any
    ) -> SFTTrainer:
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        data_collator=DataCollatorForSeq2Seq(
            tokenizer=tokenizer
        ),
        **sft_argument,
        args = TrainingArguments(
            **training_argument
        )
    )
    trainer = train_on_responses_only(
        trainer,
        instruction_part = "<|im_start|>user\n",
        response_part = "<|im_start|>assistant\n",
    )
    return trainer
