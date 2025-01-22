from openai import OpenAI
import os
from typing_extensions import List, Dict
from config import (
    SQL_GEN_SYS_PROMPT,
    SQL_GEN_USER_PROMPT
)
from loguru import logger
from dotenv import load_dotenv
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_sql_query(
        schema: str, 
        difficulty_level: int
    )-> List[str]:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "developer", "content": SQL_GEN_SYS_PROMPT},
            {
                "role": "user",
                "content": SQL_GEN_USER_PROMPT.format(
                    schema=schema,
                    difficulty_level=difficulty_level
                )
            }
        ]
    ).choices[0].message.content.split("<<SEP>>")
    return response

if __name__ == "__main__":
    schema = "employees(employee_id, name, department_id, salary), departments(department_id, name), employee_projects(employee_id, project_id), projects(project_id, project_name, start_date)"
    difficulty_level = 1
    queries = get_sql_query(schema, difficulty_level)
    print (len(queries))
    print (type(queries))
    for query in queries:
        logger.debug(query)
