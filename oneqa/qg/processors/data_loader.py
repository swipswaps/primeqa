from datasets import Dataset
from oneqa.qg.processors.passage_qg.squad_processor import SquadDataset
from oneqa.qg.processors.table_qg.wikisql_processor import WikiSqlDataset

class QGDataLoader():
	def __init__(self, tokenizer, args):
		self.args = args
		self.tokenizer = tokenizer
		self.dataset_name = args.dataset_name
		
	def convert_to_features(self, example_batch):
		input_encodings = self.tokenizer.batch_encode_plus(example_batch['input'], 
										pad_to_max_length=True, max_length=self.args.max_len)
		target_encodings = self.tokenizer.batch_encode_plus(example_batch['question'], 
										pad_to_max_length=True, max_length=self.args.target_max_len)
		encodings = {
			'input_ids': input_encodings['input_ids'], 
			'attention_mask': input_encodings['attention_mask'],
			'target_ids': target_encodings['input_ids'],
			'target_attention_mask': target_encodings['attention_mask']
		}

		return encodings

	def create(self, data_split='train'):
		if self.dataset_name == 'wikisql':
			data = WikiSqlDataset()
		elif self.dataset_name in ['squad', 'squad_v2']:
			data = SquadDataset(self.dataset_name)		
		else:
			raise NotImplementedError("this data not supported")
		processed_data_dict = data.preprocess_data_for_qg(data_split) # list of dict

		processed_data = Dataset.from_dict(processed_data_dict)
		tokenized_data =  processed_data.map(self.convert_to_features, batched=True)
		columns = ['input_ids', 'attention_mask', 'target_ids', 'target_attention_mask']
		tokenized_data.set_format(type='torch', columns=columns)
		return tokenized_data
