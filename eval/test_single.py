from llama_cpp import Llama
from llama_cpp.llama_grammar import LlamaGrammar
from loguru import logger

def load_model(model_path: str) -> Llama:
    logger.info(f"Loading model from {model_path}")

    return Llama(
        model_path=model_path,
        verbose=False,
        # n_gpu_layers=-1, # Uncomment to use GPU acceleration
        # seed=1337, # Uncomment to set a specific seed
        n_ctx=2048 # Uncomment to increase the context window,
    )

def get_output(llm: Llama, prompt:str) -> str:
    logger.info(f"Generating output")

    # prompt = OUTPUT_USER_PROMPT.format(
    #                 schema=schema,
    #                 query=query
    #             )

    # return llm.create_chat_completion(
    #     messages = [
    #         {"role": "system", "content": OUTPUT_SYS_PROMPT},
    #         {
    #             "role": "user",
    #             "content": prompt
    #         }
    #     ],
    #     grammar=grammar,
    #     max_tokens=100,
    # )["choices"][0]["message"]["content"]


    return llm.create_chat_completion(
        messages = [
            {
                "role": "user",
                "content": prompt
            }
        ],
    )["choices"][0]["message"]["content"]


if __name__=="__main__":
    path = "/data/meta/eval/unsloth.Q4_K_M.gguf"
    prompt = """You are a seasoned expert in translating natural language requests into precise MongoDB queries. Your task is to analyze the provided database schema and natural language query, and generate ONLY the final, correct MongoDB query with no extra commentary or explanation.

Schema:
{
  "collections": [
    {
      "name": "events",
      "document": {
        "properties": {
          "identifier": {
            "bsonType": "object",
            "properties": {
              "camgroup_id": {
                "description": "Use this to filter events by group",
              },
              "task_id": {
                "description": "Use this to filter events by tasks",
              }
              "camera_id": {
                "description": "Use this to filter events by camera",
              }
            }
          },
          "response": {
            "bsonType": "object",
            "properties": {
              "event": {
                "bsonType": "object",
                "properties": {
                  "severity": {
                    "description": "Can be Low, Medium, Critical"
                  },
                  "type": {
                    "description": "Type of the event. Use this to filter events of person and vehicle"
                  },
                  "blobs": {
                    "bsonType": "array",
                    "items": {
                      "bsonType": "object",
                      "properties": {
                        "url": {
                        },
                        "attribs": {
                          "description": "Use this for attributes like Gender (Only Male, Female), Upper Clothing, Lower Clothing, Age (Ranges like 20-30, 30-40 and so on) for people and Make (like maruti suzuki, toyota, tata), Color, Type (like Hatchback, sedan, xuv), label (like car, truck, van, three wheeler, motorcycle) for Vehicles"
                        },
                        "label": {
                          "description": "Use this label for number plate"
                        },
                        "score": {
                          "description": "Use this for confidence for the blob"
                        },
                        "match_id": {
                          "description": "Use this match_id for name of the person"
                        },
                        "severity": {
                        },
                        "subclass": {
                          "description": "Use this for subclass for the blob"
                        }
                      }
                    },
                  },
                  "c_timestamp": {
                    "description": "Use this for timestamp"
                  },
                  "label": {
                    "description": "Use this label for number plate"
                  }
                }You are a seasoned expert in translating natural language requests into precise MongoDB queries. Your task is to analyze the provided database schema and natural language query, and generate ONLY the final, correct MongoDB query with no extra commentary or explanation.

Schema:
{
  "collections": [
    {
      "name": "events",
      "document": {
        "properties": {
          "identifier": {
            "bsonType": "object",
            "properties": {
              "camgroup_id": {
                "description": "Use this to filter events by group",
              },
              "task_id": {
                "description": "Use this to filter events by tasks",
              }
              "camera_id": {
                "description": "Use this to filter events by camera",
              }
            }
          },
          "response": {
            "bsonType": "object",
            "properties": {
              "event": {
                "bsonType": "object",
                "properties": {
                  "severity": {
                    "description": "Can be Low, Medium, Critical"
                  },
                  "type": {
                    "description": "Type of the event. Use this to filter events of person and vehicle"
                  },
                  "blobs": {
                    "bsonType": "array",
                    "items": {
                      "bsonType": "object",
                      "properties": {
                        "url": {
                        },
                        "attribs": {
                          "description": "Use this for attributes like Gender (Only Male, Female), Upper Clothing, Lower Clothing, Age (Ranges like 20-30, 30-40 and so on) for people and Make (like maruti suzuki, toyota, tata), Color, Type (like Hatchback, sedan, xuv), label (like car, truck, van, three wheeler, motorcycle) for Vehicles"
                        },
                        "label": {
                          "description": "Use this label for number plate"
                        },
                        "score": {
                          "description": "Use this for confidence for the blob"
                        },
                        "match_id": {
                          "description": "Use this match_id for name of the person"
                        },
                        "severity": {
                        },
                        "subclass": {
                          "description": "Use this for subclass for the blob"
                        }
                      }
                    },
                  },
                  "c_timestamp": {
                    "description": "Use this for timestamp"
                  },
                  "label": {
                    "description": "Use this label for number plate"
                  }
                }
              }
            }
          }
        }
      }
    }
  ],
  "version": 1
}

NL Query: Find Yash

Your response should contain nothing but the exact MongoDB query that satisfies the natural language request.
              }
            }
          }
        }
      }
    }
  ],
  "version": 1
}

NL Query: Find Yash

Your response should contain nothing but the exact MongoDB query that satisfies the natural language request.
"""
    llm = load_model(path)
    output = get_output(llm, prompt)
    print(output)
    