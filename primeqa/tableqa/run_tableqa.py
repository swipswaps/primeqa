import logging
from primeqa.tableqa.metrics.answer_accuracy import compute_denotation_accuracy
from primeqa.tableqa.models.tableqa_model import TableQAModel
from primeqa.tableqa.postprocessor.wikisql import WikiSQLPostprocessor
from primeqa.tableqa.preprocessors.dataset import TableQADataset
from primeqa.tableqa.trainers.tableqa_trainer import TableQATrainer
from dataclasses import dataclass, field
from transformers import TapasConfig
from transformers import (
    DataCollator,
    HfArgumentParser,
    TrainingArguments,
    set_seed,default_data_collator,
)
import pandas as pd
from primeqa.tableqa.utils.data_collator import TapasCollator
from primeqa.tableqa.preprocessors.wikisql_preprocessor import load_data
@dataclass
class TableQAArguments:
    """
    Arguments pertaining to which model/config/tokenizer we are going to fine-tune from.
    """
    data_path_root: str = field(
       default='primeqa/tableqa/preprocessors/data/wikisql/', metadata={"help": "root path to store the preprocessed dataset"}
    )
    train_data_path: str = field(
       default='primeqa/tableqa/preprocessors/data/wikisql/', metadata={"help": "Train data path for training on user's own dataset"}
    )
    dev_data_path: str = field(
       default='primeqa/tableqa/preprocessors/data/wikisql/', metadata={"help": "Dev data path for training on user's own dataset"}
    )

    dataset_name: str = field(
       default='wikisql', metadata={"help": "Name of the dataset to train the tapas model on"}
    )
    num_aggregation_labels: int = field(
       default=4, metadata={"help": "Total number of aggregation labels"}
    )
    use_answer_as_supervision: bool = field(
        default=True, metadata={"help": "Whether to use answer as supervision or not"}
    )
    answer_loss_cutoff: float = field(
        default=0.664694, metadata={"help": "Answer loss cutoff"}
    )
    cell_selection_preference: float = field(
        default=0.207951, metadata={"help": "Cell selection preference"}
    )

    huber_loss_delta: float = field(
        default=0.121194, metadata={"help": "Huber loss delta"}
    )
    init_cell_selection_weights_to_zero: bool = field(
        default=True, metadata={"help": "Init cell selection weights to zero or not"}
    )
    select_one_column: bool = field(
        default=True, metadata={"help": "select one column"}
    )
    allow_empty_column_selection: bool = field(
        default=True, metadata={"help": "Allow empty column selection"}
    )
    temperature: float = field(
        default=0.0352513, metadata={"help": "temperature"}
    )
@dataclass
class TQATrainingArguments(TrainingArguments):
    "TableQA training arguments"
    model_name_or_path: str = field(
       default='PrimeQA/tapas-based-tableqa-wikisql-lookup', metadata={"help": "root path to store the preprocessed dataset"}
    )


def table_qa():
    logger = logging.getLogger(__name__)
    parser = HfArgumentParser((TableQAArguments, TQATrainingArguments))
    tqa_args,training_args = parser.parse_args_into_dataclasses()
    logger.info(f"TableQA arguments are {tqa_args}")
    config = TapasConfig(tqa_args)
    tableqa_model = TableQAModel(training_args.model_name_or_path,config=config)
    model = tableqa_model.model
    tokenizer = tableqa_model.tokenizer
    if training_args.do_train or training_args.do_eval:
        if tqa_args.dataset_name=="wikisql":
            train_dataset,eval_dataset = load_data(tqa_args.data_path_root,tokenizer)
            postprocessor = WikiSQLPostprocessor(tokenizer,tqa_args)
        else:
            tqadataset = TableQADataset(tqa_args.data_path_root,tqa_args.train_data_path,tqa_args.dev_data_path ,tokenizer)
            train_dataset,eval_dataset= tqadataset.load_data()
        trainer = TableQATrainer(model=model,
                                args=training_args,
                                tokenizer=tokenizer,
                                train_dataset=train_dataset if training_args.do_train else None,
                                eval_dataset=eval_dataset if training_args.do_eval else None,
                                data_collator=TapasCollator(),post_process_function=postprocessor.postprocess_prediction,compute_metrics=compute_denotation_accuracy
                                )
        if training_args.do_train:
            train_result = trainer.train()
            trainer.save_model()
            metrics = train_result.metrics
            trainer.log_metrics("train", metrics)
            trainer.save_metrics("train", metrics)
            trainer.save_state()
        if training_args.do_eval:
            logger.info("*** Evaluate ***")
            metrics = trainer.evaluate()
           
            trainer.log_metrics("eval", metrics)
            trainer.save_metrics("eval", metrics)



if __name__ == '__main__':
       table_qa()
    