from openai import OpenAI
import os
from typing_extensions import List, Dict, Tuple
from config import (
    NL_GEN_SYS_PROMPT,
    NL_GEN_USER_PROMPT,
    Model
)
from loguru import logger
from dotenv import load_dotenv
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_text_query(
        db: tuple[str, str], 
        mongo_query: str
    )-> List[Tuple[str, str, str, str]]:
    response = client.chat.completions.create(
        model=Model,
        messages=[
            {"role": "system", "content": NL_GEN_SYS_PROMPT},
            {
                "role": "user",
                "content": NL_GEN_USER_PROMPT.format(
                    schema=db[1],
                    mongo_query=mongo_query
                )
            }
        ]
    ).choices[0].message.content.split("<<SEP>>")
    return [(db[0], db[1], mongo_query, response[0]), (db[0], db[1], mongo_query, response[1])]

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
    mongo_query = """db.leaveRecords.aggregate([ { $match: { startDate: { $gte: new Date("2023-01-01") } } }, { $group: { _id: "$leaveType", count: { $sum: 1 } } } ]);"""
    response = get_text_query(("dbid", schema), mongo_query)
    logger.info(response)
