from openai import OpenAI
import os
from typing_extensions import List, Dict, Tuple
from config import (
    SCHEMA_LINKING_SYSTEM,
    SCHEMA_LINKING_USER,
    LOGICAL_ERROR_SYSTEM,
    LOGICAL_ERROR_USER,
    INCOMPLETE_QUERY_SYSTEM,
    INCOMPLETE_QUERY_USER,
    SYNTAX_ERROR_SYSTEM,
    SYNTAX_ERROR_USER,
    INEFFICIENT_QUERY_SYSTEM,
    INEFFICIENT_QUERY_USER,
    AMBIGUOUS_QUERY_SYSTEM,
    AMBIGUOUS_QUERY_USER,
    Model
)
from loguru import logger
from dotenv import load_dotenv
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def run_client(system_prompt: str, user_prompt: str):
    response = client.chat.completions.create(
        model=Model,
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": user_prompt
            }
        ]
    ).choices[0].message.content
    return response

def schema_linking_error(
    schema: str, 
    nl_query: str, 
    mongo_query: str
) -> Tuple[str, str, str, str]:
    
    sys_prompt = SCHEMA_LINKING_SYSTEM
    usr_prompt = SCHEMA_LINKING_USER.format(
        schema = schema, 
        nl_query=nl_query,
        correct_query=mongo_query
    )
    res = run_client(sys_prompt, usr_prompt)
    return (schema, nl_query, mongo_query, res)

def logical_error(
    schema: str, 
    nl_query: str, 
    mongo_query: str
) -> Tuple[str, str, str, str]:
    
    sys_prompt = LOGICAL_ERROR_SYSTEM
    usr_prompt = LOGICAL_ERROR_USER.format(
        schema = schema, 
        nl_query=nl_query,
        correct_query=mongo_query
    )
    res = run_client(sys_prompt, usr_prompt)
    return (schema, nl_query, mongo_query, res)

def incomplete_query(
    schema: str, 
    nl_query: str, 
    mongo_query: str
) -> Tuple[str, str, str, str]:
    
    sys_prompt = INCOMPLETE_QUERY_SYSTEM
    usr_prompt = INCOMPLETE_QUERY_USER.format(
        schema = schema, 
        nl_query=nl_query,
        correct_query=mongo_query
    )
    res = run_client(sys_prompt, usr_prompt)
    return (schema, nl_query, mongo_query, res)

def syntax_error(
    schema: str, 
    nl_query: str, 
    mongo_query: str
) -> Tuple[str, str, str, str]:
    
    sys_prompt = SYNTAX_ERROR_SYSTEM
    usr_prompt = SYNTAX_ERROR_USER.format(
        schema = schema, 
        nl_query=nl_query,
        correct_query=mongo_query
    )
    res = run_client(sys_prompt, usr_prompt)
    return (schema, nl_query, mongo_query, res)

def inefficient_query(
    schema: str, 
    nl_query: str, 
    mongo_query: str
) -> Tuple[str, str, str, str]:
    
    sys_prompt = INEFFICIENT_QUERY_SYSTEM
    usr_prompt = INEFFICIENT_QUERY_USER.format(
        schema = schema, 
        nl_query=nl_query,
        correct_query=mongo_query
    )
    res = run_client(sys_prompt, usr_prompt)
    return (schema, nl_query, mongo_query, res)

def ambiguous_query(
    schema: str, 
    nl_query: str, 
    mongo_query: str
) -> Tuple[str, str, str, str]:
    
    sys_prompt = AMBIGUOUS_QUERY_SYSTEM
    usr_prompt = AMBIGUOUS_QUERY_USER.format(
        schema = schema, 
        nl_query=nl_query,
        correct_query=mongo_query
    )
    res = run_client(sys_prompt, usr_prompt)
    return (schema, nl_query, mongo_query, res)
