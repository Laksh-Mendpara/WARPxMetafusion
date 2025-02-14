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
from typing_extensions import Dict, Any
from loguru import logger

def get_trainer(model: Any, 
                train_dataset: Dataset, 
                eval_dataset: Dataset, 
                tokenizer: Any,
                config: Dict[str, Any] = None
    ) -> SFTTrainer:

    merged_sft_config = {**sft_argument, **(config or {})}
    merged_sft_config = {k: merged_sft_config[k] for k in sft_argument.keys()}

    merged_training_config = {**training_argument, **(config or {})}
    merged_training_config = {k: merged_training_config[k] for k in training_argument.keys()}
    
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        data_collator=DataCollatorForSeq2Seq(
            tokenizer=tokenizer
        ),
        **merged_sft_config,
        args = TrainingArguments(
            **merged_training_config
        )
    )
    trainer = train_on_responses_only(
        trainer,
        instruction_part = "<|im_start|>user\n",
        response_part = "<|im_start|>assistant\n",
    )
    return trainer
