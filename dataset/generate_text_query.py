from openai import OpenAI
import os
from typing_extensions import List, Dict, Tuple
from config import (
    NL_GEN_SYS_PROMPT,
    NL_GEN_USER_PROMPT
)
from loguru import logger
from dotenv import load_dotenv
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_text_query(
        schema: str, 
        SQL_query: str
    )-> Tuple[str, str, str]:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "developer", "content": NL_GEN_SYS_PROMPT},
            {
                "role": "user",
                "content": NL_GEN_USER_PROMPT.format(
                    schema=schema,
                    sql_query=SQL_query
                )
            }
        ]
    ).choices[0].message.content
    return (schema, SQL_query, response)

if __name__ == "__main__":
    schema = "employees(employee_id, name, department_id, salary), departments(department_id, name), employee_projects(employee_id, project_id), projects(project_id, project_name, start_date)"
    sql_query = "SELECT e.name FROM employees e WHERE e.department_id = (SELECT department_id FROM departments WHERE name = 'IT');"
    response = get_text_query(schema, sql_query)
    logger.info(response)
