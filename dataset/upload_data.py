from datasets import Dataset 
import pandas as pd 

df = pd.read_csv("data/final_data.csv")
data = Dataset.from_pandas(df)

data.push_to_hub("ByteMaster01/NLP2SQL")