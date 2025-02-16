# NL2Mongo: Intelligent Query Engine

## Task
The primary objective of this project is to convert Natural Language inputs into SQL Queries within a constrained environment.

---

## Setup Instructions

### Step 1: Pull Docker Image
Pull the pre-built Docker image for the custom LLaMA model:
```bash
docker pull lakshmendpara/llama-cpp-custom
```

---

### Step 2: Environment Setup

#### 1. Install the `uv` Package Manager
To manage the environment, first install the `uv` package manager:
```bash
pip install uv
```

#### 2. Create and Activate a Virtual Environment
Create a Python 3.11 virtual environment using `uv` and activate it:
```bash
uv venv <PATH_TO_VIRTUAL_ENV> --python 3.11
source <PATH_TO_VIRTUAL_ENV>/bin/activate
```

#### 3. Install Dependencies
With the virtual environment activated, install all required dependencies:
```bash
uv pip install -r requirements.txt
```

---

### Step 3: Download the Model
Download the model from Hugging Face using the provided model ID:
```bash
python models/download_model.py --model_id <MODEL_ID> --local_dir <PATH_TO_DOWNLOAD_MODEL>
```
Replace `<MODEL_ID>` with the specific model ID and `<PATH_TO_DOWNLOAD_MODEL>` with the desired local path for saving the model.

---

### Step 4: Convert Model to GGUF Format
Convert the downloaded Hugging Face model to the GGUF format for efficient usage:
```bash
python convert_hf_to_gguf.py <PATH_TO_DOWNLOAD_MODEL> --outfile <OUTPUT_GGUF_FILE_PATH> --outtype <QUANTIZATION_VERSION>
```
#### Available Quantization Versions:
- **f32**: Full precision (gguf.LlamaFileType.ALL_F32)
- **f16**: Half precision (gguf.LlamaFileType.MOSTLY_F16)
- **bf16**: BFLOAT16 precision (gguf.LlamaFileType.MOSTLY_BF16)
- **q8_0**: 8-bit quantization (gguf.LlamaFileType.MOSTLY_Q8_0)
- **tq1_0**: Ternary Quantization 1.0 (gguf.LlamaFileType.MOSTLY_TQ1_0)
- **tq2_0**: Ternary Quantization 2.0 (gguf.LlamaFileType.MOSTLY_TQ2_0)
- **auto**: Automatic quantization type (gguf.LlamaFileType.GUESSED)

Replace `<PATH_TO_DOWNLOAD_MODEL>` with the path to the downloaded model, `<OUTPUT_GGUF_FILE_PATH>` with the desired output file path, and `<QUANTIZATION_VERSION>` with one of the quantization options listed above.

---

### Step 5: Run the Model
Run the converted model using the Docker container:
```bash
docker run -v <PATH_TO_GGUF>:/models/model.gguf lakshmendpara/llama-cpp-custom --run -m /models/model.gguf -p "<USER_PROMPT>"
```
#### Parameters:
- **<PATH_TO_GGUF>**: Path to the GGUF file.
- **<USER_PROMPT>**: The natural language input you want the model to process.

---

### Step 6: Benchmark the Model
Benchmark the model’s performance:
```bash
docker run -v <PATH_TO_GGUF>:/models/model.gguf lakshmendpara/llama-cpp-custom --bench -m /models/model.gguf
```
---

### Notes:
- Ensure all paths provided are correct and accessible by the Docker container.
- Use appropriate quantization based on your computational requirements.

For additional details, read the [docker readme](./docker.md).
---
