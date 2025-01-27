# Docker Usage Guide for LLaMA-cpp-Custom

## Step 1: Pull Docker Image
Pull the pre-built Docker image for the custom LLaMA model:
```bash
docker pull lakshmendpara/llama-cpp-custom
```

---

## Available Commands
The Docker image includes several commands for running and managing the LLaMA models. Below is a list of available commands:

- **Run a Model** (`--run` or `-r`):
  Run a model previously converted into the GGML format.
  ```bash
  docker run -v <PATH_TO_MODEL>:/models/model.gguf lakshmendpara/llama-cpp-custom --run -m /models/model.gguf -p "Your prompt here" -n 512
  ```

- **Convert a Model** (`--convert` or `-c`):
  Convert a LLaMA model into the GGML format.
  ```bash
  docker run lakshmendpara/llama-cpp-custom --convert --outtype f16 <PATH_TO_MODEL>
  ```

- **Quantize a Model** (`--quantize` or `-q`):
  Optimize the GGML model using the quantization process.
  ```bash
  docker run lakshmendpara/llama-cpp-custom --quantize <INPUT_PATH> <OUTPUT_PATH> <QUANTIZATION_LEVEL>
  ```

- **Convert and Quantize** (`--all-in-one` or `-a`):
  Perform both conversion and quantization in one step.
  ```bash
  docker run lakshmendpara/llama-cpp-custom --all-in-one <PATH_TO_MODEL> <MODEL_SIZE>
  ```

- **Run as a Server** (`--server` or `-s`):
  Run a model in server mode for API interactions.
  ```bash
  docker run -v <PATH_TO_MODEL>:/models/model.gguf lakshmendpara/llama-cpp-custom --server -m /models/model.gguf --port 8080
  ```

---

## Detailed Command for `--run`
The `--run` command allows you to interact with the model in various ways. Below are examples of its usage.

### 1. Run in Conversation Mode
Models with built-in chat templates will automatically activate conversation mode. If this does not happen, you can manually enable it:

```bash
docker run -v <PATH_TO_MODEL>:/models/model.gguf lakshmendpara/llama-cpp-custom --run -m /models/model.gguf
```

**Example Interaction:**
```text
> hi, who are you?
Hi there! I'm your helpful assistant! I'm an AI-powered chatbot designed to assist and provide information to users like you. I'm here to help answer your questions, provide guidance, and offer support on a wide range of topics. I'm a friendly and knowledgeable AI, and I'm always happy to help with anything you need. What's on your mind, and how can I assist you today?

> what is 1+1?
Easy peasy! The answer to 1+1 is... 2!
```

### 2. Conversation Mode with Custom Chat Template
You can specify a chat template explicitly:

- **Using a Built-In Template**
  ```bash
  docker run -v <PATH_TO_MODEL>:/models/model.gguf lakshmendpara/llama-cpp-custom --run -m /models/model.gguf -cnv --chat-template chatml
  ```

- **Using a Custom Template**
  ```bash
  docker run -v <PATH_TO_MODEL>:/models/model.gguf lakshmendpara/llama-cpp-custom --run -m /models/model.gguf -cnv --in-prefix 'User: ' --reverse-prompt 'User:'
  ```

### 3. Run Simple Text Completion
To disable conversation mode explicitly, use `-no-cnv`:

```bash
docker run -v <PATH_TO_MODEL>:/models/model.gguf lakshmendpara/llama-cpp-custom --run -m /models/model.gguf -p "I believe the meaning of life is" -n 128 -no-cnv
```

**Example Output:**
```text
I believe the meaning of life is to find your own truth and to live in accordance with it. For me, this means being true to myself and following my passions, even if they don't align with societal expectations. I think that's what I love about yoga – it's not just a physical practice, but a spiritual one too. It's about connecting with yourself, listening to your inner voice, and honoring your own unique journey.
```

## Detailed Command for `--bench`

usage: 
```bash
  docker run -v <PATH_TO_GGUF>:/models/model.gguf lakshmendpara/llama-cpp-custom --bench -m /models/model.gguf
```

```

options:
  -h, --help
  -p, --n-prompt <n>                        (default: 512)
  -n, --n-gen <n>                           (default: 128)
  -pg <pp,tg>                               (default: )
  -b, --batch-size <n>                      (default: 2048)
  -ub, --ubatch-size <n>                    (default: 512)
  -ctk, --cache-type-k <t>                  (default: f16)
  -ctv, --cache-type-v <t>                  (default: f16)
  -t, --threads <n>                         (default: 8)
  -C, --cpu-mask <hex,hex>                  (default: 0x0)
  --cpu-strict <0|1>                        (default: 0)
  --poll <0...100>                          (default: 50)
  -ngl, --n-gpu-layers <n>                  (default: 99)
  -rpc, --rpc <rpc_servers>                 (default: )
  -sm, --split-mode <none|layer|row>        (default: layer)
  -mg, --main-gpu <i>                       (default: 0)
  -nkvo, --no-kv-offload <0|1>              (default: 0)
  -fa, --flash-attn <0|1>                   (default: 0)
  -mmp, --mmap <0|1>                        (default: 1)
  --numa <distribute|isolate|numactl>       (default: disabled)
  -embd, --embeddings <0|1>                 (default: 0)
  -ts, --tensor-split <ts0/ts1/..>          (default: 0)
  -r, --repetitions <n>                     (default: 5)
  --prio <0|1|2|3>                          (default: 0)
  --delay <0...N> (seconds)                 (default: 0)
  -o, --output <csv|json|jsonl|md|sql>      (default: md)
  -oe, --output-err <csv|json|jsonl|md|sql> (default: none)
  -v, --verbose                             (default: 0)

Multiple values can be given for each parameter by separating them with ',' or by specifying the parameter multiple times.
```

llama-bench can perform three types of tests:

- Prompt processing (pp): processing a prompt in batches (`-p`)
- Text generation (tg): generating a sequence of tokens (`-n`)
- Prompt processing + text generation (pg): processing a prompt followed by generating a sequence of tokens (`-pg`)

With the exception of `-r`, `-o` and `-v`, all options can be specified multiple times to run multiple tests. Each pp and tg test is run with all combinations of the specified options. To specify multiple values for an option, the values can be separated by commas (e.g. `-n 16,32`), or the option can be specified multiple times (e.g. `-n 16 -n 32`).

Each test is repeated the number of times given by `-r`, and the results are averaged. The results are given in average tokens per second (t/s) and standard deviation. Some output formats (e.g. json) also include the individual results of each repetition.
