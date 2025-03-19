from huggingface_hub import HfApi, HfFolder, Repository
import os
import shutil

# ---- CONFIG ----
HF_TOKEN = "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"
repo_id = "Diwanshuydv/qwen2.5-0.5B-coder-Instruct-sft-final-ticktick0"  # Example: "yourusername/my-gguf-model"
local_model_dir = "/home/raid/WARPxMetafusion/out_try01"  # This should be your whole directory
commit_message = "Initial commit of GGUF model directory"

HfFolder.save_token(HF_TOKEN)
api = HfApi()

try:
    api.create_repo(repo_id, exist_ok=True)
except Exception as e:
    print(e)

repo_local_dir = "./temp_hf_repo"
if os.path.exists(repo_local_dir):
    shutil.rmtree(repo_local_dir)  # Clean old repo
repo = Repository(local_dir=repo_local_dir, clone_from=repo_id, use_auth_token=HF_TOKEN)

for item in os.listdir(local_model_dir):
    s = os.path.join(local_model_dir, item)
    d = os.path.join(repo_local_dir, item)
    if os.path.isdir(s):
        shutil.copytree(s, d)
    else:
        shutil.copy2(s, d)

repo.git_add(auto_lfs_track=True)
repo.git_commit(commit_message)
repo.git_push()

print(f"Directory pushed")
