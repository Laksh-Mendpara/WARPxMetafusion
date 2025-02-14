import pandas as pd
from loguru import logger

def load_csv(file_path: str) -> pd.DataFrame:
    logger.info(f"Loading CSV from {file_path}")
    return pd.read_csv(file_path, header=0, index_col=None)

def create_random_subset(data: pd.DataFrame, n: int) -> pd.DataFrame:
    logger.info(f"Creating random subset of size {n}")
    return data.sample(n)

if __name__=="__main__":
    file_path = "./data/final_data.csv"
    output_path = "./data/subset.csv"
    data = load_csv(file_path)
    n = 45
    subset = create_random_subset(data, n)
    logger.info(f"Subset type: {type(subset)}")
    logger.info(f"Subset shape: {subset.shape}")
    logger.info(f"Saving subset to {output_path}")
    subset.to_csv(output_path, index=False)
    logger.info(f"Subset saved successfully")
