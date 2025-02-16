from huggingface_hub import snapshot_download
from loguru import logger
from argparse import ArgumentParser

def download_model(model_id: str, local_dir: str) -> None:
    logger.info(f"Downloading model {model_id} to {local_dir}")
    snapshot_download(repo_id=model_id, local_dir=local_dir,
                    local_dir_use_symlinks=False, revision="main")
    logger.info(f"Model {model_id} downloaded to {local_dir}")

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--model_id", type=str, required=True)
    parser.add_argument("--local_dir", default=None, type=str, required=False)
    args = parser.parse_args()  
    if args.local_dir is None:
        args.local_dir = args.model_id
    download_model(args.model_id, args.local_dir)