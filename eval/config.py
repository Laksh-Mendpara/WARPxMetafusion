OUTPUT_SYS_PROMPT = "You are a helpful assistant that converts natural language queries into MongoDB queries based on a given database schema."

FINETUNNED_USER_PROMPT = """
You are a seasoned expert in translating natural language requests into precise MongoDB queries. Your task is to analyze the provided database schema and natural language query, and generate ONLY the final, correct MongoDB query with no extra commentary or explanation.

Schema: {schema}
NL Query: {query}

Your response should contain nothing but the exact MongoDB query that satisfies the natural language request."""

OUTPUT_USER_PROMPT = """The task is to convert the following natural language query into a MongoDB query. Please output only the MongoDB query, with no explanation or additional text.

Database Schema:
{schema}

Natural Language Query:
{query}
"""

test_schema = """// Employees Collection ?@\employees?@]: { _id: ObjectId, employeeId: String, firstName: String, lastName: String, email: String, phone: String, department: String, position: String, salary: Decimal128, hireDate: Date, status: String, managerId: ObjectId, EmergencyContact: { name: String, relationship: String, phone: String } }, // Departments Collection ?@\departments?@]: { _id: ObjectId, name: String, description: String, headId: ObjectId, budget: Decimal128, location: String, createdAt: Date }, // Leave Records Collection leaveRecords: { _id: ObjectId, employeeId: ObjectId, leaveType: String, startDate: Date, endDate: Date, status: String, reason: String, approvedBy: ObjectId, appliedDate: Date, lastUpdated: Date } }"""
test_query = "Get employees in the 'Sales' department."


CHECK_SYS_PROMPT = """You are an AI assistant that specializes in MongoDB query validation and result comparison. Your task is to analyze two given MongoDB queries and a database schema. 

Your response should strictly be:
- Return "0" if:
  - Any of the queries contain syntax errors.
  - Any of the queries reference fields or collections not present in the schema.
- Return "1" if both queries are syntactically correct, match the schema, and retrieve similar result set.

Ensure that your response is only a single binary digit (0 or 1). and do not be too much strict."""

CHECK_USER_PROMPT = """Here are two MongoDB queries and a database schema:

Schema:
{schema}

Query 1:
{query_1}

Query 2:
{query_2}

Analyze these queries based on the schema and determine if both will retrieve the same result or not. Respond with either "0" or "1" as per the system instructions."""
