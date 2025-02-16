from unsloth import FastLanguageModel
import argparse

def load_model(path: str):
    model, tokenizer = FastLanguageModel.from_pretrained(
        path,
        max_seq_length=4096,
        load_in_4bit=True
    )
    return model, tokenizer


def save_GGUF(model, tokenizer, output_dir):
    model.save_pretrained_gguf(output_dir, tokenizer, quantization_method = ["q4_k_m", "q8_0", "f16",])

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_path", type=str, required=True)
    parser.add_argument("--output_dir", type=str, required=True)
    
    args = parser.parse_args()

    model, tokenizer = load_model(args.model_path)
    save_GGUF(model, tokenizer, args.output_dir)

if __name__ == "__main__":
    main()