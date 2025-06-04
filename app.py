import gradio as gr
import json
import requests
from loguru import logger
from data_v3.data_utils.line_based_parsing import parse_line_based_query, convert_to_lines
from data_v3.data_utils.base_conversion_utils import (
    build_schema_maps,
    convert_modified_to_actual_code_string
)
from data_v3.data_utils.schema_utils import schema_to_line_based
from sft.config.prompt_config_v3 import SYSTEM_PROMPT_V3, MODEL_PROMPT_V3

LLAMA_SERVER_URL = "http://127.0.0.1:8080/v1/chat/completions"

def convert_line_parsed_to_mongo(line_parsed: str, schema: dict) -> str:
    try:
        modified_query = parse_line_based_query(line_parsed)
        collection_name = schema["collections"][0]["name"]
        in2out, _ = build_schema_maps(schema)
        reconstructed_query = convert_modified_to_actual_code_string(modified_query, in2out, collection_name)
        return reconstructed_query
    except Exception as e:
        logger.error(f"Error converting line parsed to MongoDB query: {e}")
        return ""

def process_query(schema_text: str, nl_query: str, additional_info: str = "") -> str:
    try:
        # Parse schema from string to dict
        schema = json.loads(schema_text)
        
        # Convert schema to line-based format
        line_based_schema = schema_to_line_based(schema)
        
        # Format prompt with line-based schema
        prompt = MODEL_PROMPT_V3.format(
            schema=line_based_schema,
            natural_language_query=nl_query,
            additional_info=additional_info
        )
        
        # Prepare request payload
        payload = {
            "slot_id": 0,
            "temperature": 0.1,
            "n_keep": -1,
            "cache_prompt": True,
            "messages": [
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT_V3,
                },
                {
                    "role": "user",
                    "content": prompt
                },
            ]
        }
        
        # Make request to llama.cpp server
        response = requests.post(LLAMA_SERVER_URL, json=payload)
        response.raise_for_status()
        
        # Extract output from response
        output = response.json()["choices"][0]["message"]["content"].strip()
        logger.info(f"Model output: {output}")
        
        # Convert line-based output to MongoDB query
        mongo_query = convert_line_parsed_to_mongo(output, schema)
        
        return [
            mongo_query,
            output
        ]
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        error_msg = f"Error: {str(e)}"
        return [error_msg, error_msg, error_msg]

def create_interface():
    # Create Gradio interface
    iface = gr.Interface(
        fn=process_query,
        inputs=[
            gr.Textbox(
                label="Schema (JSON format)", 
                placeholder="Enter your MongoDB schema in JSON format...",
                lines=10
            ),
            gr.Textbox(
                label="Natural Language Query",
                placeholder="Enter your query in natural language..."
            ),
            gr.Textbox(
                label="Additional Info (Optional)",
                placeholder="Enter any additional context (timestamps, etc)..."
            )
        ],
        outputs=[
            gr.Code(label="MongoDB Query", language="javascript", lines=1),
            gr.Textbox(label="Line-based Query")
        ],
        title="Natural Language to MongoDB Query Converter",
        description="Convert natural language queries to MongoDB queries based on your schema.",
        examples=[
            [
                '''{
    "collections": [{
        "name": "events",
        "document": {
            "properties": {
                "timestamp": {"bsonType": "int"},
                "severity": {"bsonType": "int"},
                "location": {
                    "bsonType": "object",
                    "properties": {
                        "lat": {"bsonType": "double"},
                        "lon": {"bsonType": "double"}
                    }
                }
            }
        }
    }]}''',
                "Find all events with severity greater than 5",
                ""
            ],
            [
                '''{
    "collections": [{
        "name": "vehicles",
        "document": {
            "properties": {
                "timestamp": {"bsonType": "int"},
                "vehicle_details": {
                    "bsonType": "object",
                    "properties": {
                        "license_plate": {"bsonType": "string"},
                        "make": {"bsonType": "string"},
                        "model": {"bsonType": "string"},
                        "year": {"bsonType": "int"},
                        "color": {"bsonType": "string"}
                    }
                },
                "speed": {"bsonType": "double"},
                "location": {
                    "bsonType": "object",
                    "properties": {
                        "lat": {"bsonType": "double"},
                        "lon": {"bsonType": "double"}
                    }
                }
            }
        }
    }]}''',
                "Find red Toyota vehicles manufactured after 2020 with speed above 60",
                ""
            ],
            [
                '''{
    "collections": [{
        "name": "sensors",
        "document": {
            "properties": {
                "sensor_id": {"bsonType": "string"},
                "readings": {
                    "bsonType": "object",
                    "properties": {
                        "temperature": {"bsonType": "double"},
                        "humidity": {"bsonType": "double"},
                        "pressure": {"bsonType": "double"}
                    }
                },
                "timestamp": {"bsonType": "date"},
                "status": {"bsonType": "string"}
            }
        }
    }]}''',
                "Find active sensors with temperature above 30 degrees in the last one day",
                '''current date is 21 january 2025'''
            ],
            [
                '''{
    "collections": [{
        "name": "orders",
        "document": {
            "properties": {
                "order_id": {"bsonType": "string"},
                "customer": {
                    "bsonType": "object",
                    "properties": {
                        "id": {"bsonType": "string"},
                        "name": {"bsonType": "string"},
                        "email": {"bsonType": "string"}
                    }
                },
                "items": {
                    "bsonType": "array",
                    "items": {
                        "bsonType": "object",
                        "properties": {
                            "product_id": {"bsonType": "string"},
                            "quantity": {"bsonType": "int"},
                            "price": {"bsonType": "double"}
                        }
                    }
                },
                "total_amount": {"bsonType": "double"},
                "status": {"bsonType": "string"},
                "created_at": {"bsonType": "int"}
            }
        }
    }]}''',
                "Find orders with total amount greater than $100 that contain more than 3 items and were created in the last 24 hours",
                '''{"current_time": 1685890800, "last_24_hours": 1685804400}'''
            ]
        ]
    )
    return iface

if __name__ == "__main__":
    import subprocess
    import sys
    import time
    import threading
    
    # Start the llama.cpp server in a separate process
    print("Starting llama.cpp server...")
    server_process = subprocess.Popen([
        sys.executable,
        "-m",
        "llama_cpp.server",
        "--model",
        "./models/unsloth.Q8_0.gguf",
        "--port",
        "8080"
    ])
    
    # Function to check if server is ready
    def wait_for_server():
        max_attempts = 10
        attempt = 0
        while attempt < max_attempts:
            try:
                requests.get("http://127.0.0.1:8080/v1/models")
                print("Server is ready!")
                return True
            except requests.exceptions.ConnectionError:
                attempt += 1
                print(f"Waiting for server to start... ({attempt}/{max_attempts})")
                time.sleep(2)
        return False
    
    # Wait for server to start
    if not wait_for_server():
        print("Failed to start server. Exiting...")
        server_process.terminate()
        sys.exit(1)
    
    try:
        # Launch the Gradio interface
        print("Starting Gradio interface...")
        iface = create_interface()
        iface.launch()
    finally:
        # Clean up the server process when the script exits
        print("\nShutting down server...")
        server_process.terminate()
        server_process.wait()