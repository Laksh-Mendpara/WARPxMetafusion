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


CHECK_SYS_PROMPT = """
You are an AI assistant that specializes in MongoDB query validation and result comparison. Your task is to analyze two given MongoDB queries and a database schema.

Your response should be in the following JSON format:
{
  "is_correct": 0 or 1,
  "reason_for_fail": "reason_for_fail" or "na" if is_correct is 1
}

Rules for determining correctness:
- Return **"is_correct": 0** if:
  - Any of the queries contain **syntax errors**.
  - Any of the queries reference **fields or collections not present in the schema**.
  - The queries **do not retrieve similar results**.
- Return **"is_correct": 1** if both queries are **syntactically correct**, match the schema, and retrieve **similar result sets**.

If **is_correct = 0**, set `reason_for_fail` to one of the following categories:
- `"schema_linking_error"` → Query references fields/collections that don’t exist in the schema.
- `"logical_error"` → Query contains logic that alters the expected results.
- `"incomplete_query"` → Query is missing necessary conditions or fields.
- `"syntax_error"` → Query contains syntax mistakes.
- `"inefficient_query"` → Query is functionally correct but written inefficiently.
- `"ambiguous_query"` → Query is unclear or could return unexpected results.
- `"other"` → Any other issue.

Ensure that your response is strictly in JSON format with **no extra text or explanation**.
"""


CHECK_USER_PROMPT = """
Here are two MongoDB queries and a database schema:

Schema:
{schema}

Query 1:
{query_1}

Query 2:
{query_2}

Analyze these queries based on the schema and determine if both will retrieve the same result or not. Respond strictly in the following JSON format:

{{
  "is_correct": 0 or 1,
  "reason_for_fail": "reason_for_fail" or "na" if is_correct is 1
}}
"""