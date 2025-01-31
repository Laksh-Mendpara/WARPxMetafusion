from openai import OpenAI
import os
from typing_extensions import List, Dict
from config import (
    MONGO_GEN_SYS_PROMPT,
    MONGO_GEN_USER_PROMPT
)
from loguru import logger
from dotenv import load_dotenv
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_mongo_query(
        schema: str, 
        difficulty_level: int
    )-> List[str]:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "developer", "content": MONGO_GEN_SYS_PROMPT},
            {
                "role": "user",
                "content": MONGO_GEN_USER_PROMPT.format(
                    schema=schema,
                    difficulty_level=difficulty_level
                )
            }
        ]
    ).choices[0].message.content.split("<<SEP>>")
    return response

if __name__ == "__main__":
    schema = """{
  // Employees Collection
  “employees”: {
    _id: ObjectId,
    employeeId: String,
    firstName: String,
    lastName: String,
    email: String,
    phone: String,
    department: String,
    position: String,
    salary: Decimal128,
    hireDate: Date,
    status: String,
    managerId: ObjectId,
    EmergencyContact: {
      name: String,
      relationship: String,
      phone: String
    }
  },

  // Departments Collection
  “departments”: {
    _id: ObjectId,
    name: String,
    description: String,
    headId: ObjectId,
    budget: Decimal128,
    location: String,
    createdAt: Date
  },

  // Leave Records Collection
  leaveRecords: {
    _id: ObjectId,
    employeeId: ObjectId,
    leaveType: String,
    startDate: Date,
    endDate: Date,
    status: String,
    reason: String,
    approvedBy: ObjectId,
    appliedDate: Date,
    lastUpdated: Date
  }
}
"""
    difficulty_level = 3
    queries = get_mongo_query(schema, difficulty_level)
    print (len(queries))
    print (type(queries))
    for query in queries:
        logger.debug(query)
