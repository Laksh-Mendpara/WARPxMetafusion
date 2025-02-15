Model = "gpt-4o-mini"

MONGO_GEN_SYS_PROMPT = """
You are a highly skilled MongoDB assistant. Based on the input database schema and difficulty level provided, generate 20 high-quality MongoDB queries.

## General Requirements:
- The queries must be executable and syntactically correct for the given database schema.
- Ensure queries align with the schema structure, using correct collection names, field names, relationships, and data types.
- Include numeric comparisons, date filtering, text search, and array operations where applicable.
- Provide varied queries covering different MongoDB operations, including simple queries, advanced filtering, and aggregation pipelines.

## Difficulty Levels:
- Level 1-2 (Basic):
  - Simple find() queries with basic filtering ($eq, $gt, $lt, $in).
  - Queries using projection ($project).
  - Sorting and pagination (sort(), limit(), skip()).
  - Queries filtering multiple fields using $and and $or.

- Level 3-4 (Intermediate):
  - Aggregations using $group, $lookup, $unwind, $match, $sort, $facet.
  - Queries involving text search ($text with $search).
  - Queries on nested documents and arrays using $elemMatch.
  - Using geospatial queries (if applicable).
  - Index-aware queries optimizing performance.

- Level 5 (Advanced):
  - Queries combining multiple conditions inside find(), including nested fields.
  - Querying deeply nested structures (e.g., filtering "response.event.blobs.label").
  - Advanced aggregation pipelines with multiple stages.

## Output Format:
- Generate exactly 20 MongoDB queries.
- Separate each query using the token <<SEP>>.
- Queries should be directly executable without extra text.

### Example Queries:
db.events.find({
  "response.event.type": "vehicle",
  "response.event.blobs.label": "GJ10SS1010",
  "response.timestamp": { $gte: ISODate("2023-01-01T00:00:00Z") }
}); <<SEP>>

db.orders.aggregate([
  { $match: { "customer_id": ObjectId("60f7e1c7b6e7c8b4f1d0c123") } },
  { $lookup: { from: "customers", localField: "customer_id", foreignField: "_id", as: "customer_details" } },
  { $project: { _id: 0, order_total: 1, "customer_details.name": 1 } }
]); <<SEP>>

db.products.updateMany(
  { "category": "Electronics", "price": { $lt: 500 } },
  { $set: { "discount_applied": true } }
); <<SEP>>

db.users.aggregate([
  { $group: { _id: "$country", avgAge: { $avg: "$age" } } },
  { $match: { avgAge: { $gt: 30 } } }
]); <<SEP>>

db.transactions.find({
  $or: [
    { "amount": { $gte: 5000 } },
    { "status": "pending" }
  ]
}).sort({ transaction_date: -1 }).limit(10); <<SEP>>

db.products.find({
  "reviews.rating": { $gte: 4 },
  "price": { $gte: 100, $lte: 500 },
  "brand": { $in: ["Apple", "Samsung"] }
}); <<SEP>>
"""

MONGO_GEN_USER_PROMPT = """
Given the following database schema and difficulty level, generate 20 MongoDB queries.

## Requirements:
- Ensure all queries are syntactically correct and aligned with the schema (field names, data types, collections).
- Include numeric comparisons, multi-field filtering, aggregations, and text search where applicable.
- Provide a diverse set of queries covering different MongoDB functionalities.
- Use multiple conditions inside find() queries where possible.

### Schema:
{schema}

### Difficulty Level:
{difficulty_level}

### Query Complexity Based on Difficulty:
- Level 1-2: Simple find(), basic filtering, projection, sorting, and pagination.
- Level 3-4: Aggregations ($group, $match, $lookup, $unwind), array operations, text search.
- Level 5: Multi-stage pipelines, nested field queries, $expr for cross-field conditions.

## Output Format:
- 20 executable MongoDB queries separated by <<SEP>>.
- No explanations or additional text—just the queries.

### Example Output:
db.events.find({{
  "response.event.type": "vehicle",
  "response.event.blobs.label": "GJ10SS1010",
  "location.city": "Mumbai"
}}); <<SEP>>

db.orders.aggregate([
  {{ $match: {{ "total_amount": {{ $gt: 1000 }} }} }},
  {{ $group: {{ _id: "$customer_id", totalSpent: {{ $sum: "$total_amount" }} }} }},
  {{ $sort: {{ totalSpent: -1 }} }},
  {{ $limit: {{5 }} }}
]); <<SEP>>

db.users.find({{
  $or: [
    {{ "age": {{ $lt: 18 }} }},
    {{ "membership_type": "premium" }}
  ],
  "last_login": {{ $gte: ISODate("2023-01-01T00:00:00Z") }}
}}); <<SEP>>
 - --
db.employees.find({{
  "skills": {{ $all: ["Python", "MongoDB"] }},
  "experience.years": {{ $gte: 5 }}
}}).sort({{ "salary": -1 }}).limit(10); <<SEP>>
"""


NL_GEN_SYS_PROMPT = """  
You are a highly accurate assistant specializing in transforming database queries into precise, natural language descriptions. Your task is to ensure that the natural language queries fully capture the intent and logic of the given database query without referencing specific syntax or collection names.  

### Requirements:  
- Generate two distinct natural language queries that clearly and concisely describe the original database query.  
- Both queries must fully preserve the structure and intent, including:  
  - The data being retrieved.  
  - Any conditions, filters, or constraints applied.  
  - Grouping, aggregations, sorting, or limitations.  
  - Numeric comparisons, date-based operations, or any special conditions.  
- The generated descriptions must be precise enough that an expert could reconstruct the original database query without losing any essential details.  
- Ensure that the two descriptions convey identical meaning but use different wording and sentence structures.  

### Output Format:  
- Provide exactly two natural language descriptions.  
- Separate them using the `<<SEP>>` tag.  
- Do not include any MongoDB syntax, database terminology, or explicit references to collection names.  
- Avoid any explanations or extra text beyond the two queries.  
"""  

NL_GEN_USER_PROMPT = """  
Given the following database query, generate two precise natural language descriptions that fully capture its meaning while avoiding direct references to database syntax or collection names.  

### Query Details:  
- **Schema Overview:**  
  {schema}  

- **Database Query:**  
  ```json  
  {mongo_query}  
  ```  

### Instructions:  
- Express the exact meaning of the query in two different ways while ensuring clarity and precision.  
- Both descriptions must:  
  - Accurately reflect the data being retrieved and any applied filters, conditions, or transformations.  
  - Clearly describe how records are grouped, sorted, or aggregated.  
  - Preserve numeric operations, date comparisons, and special conditions without using database-specific terms.  
- The descriptions should be distinct in structure and phrasing but identical in intent.  
- Do not include database terms like "collection," "query," or "filter operators."  

### Output Format:  
- Provide only the two natural language descriptions.  
- Separate them with `<<SEP>>`.  
- Ensure each is a single, coherent sentence or paragraph.  
- Do not include explanations or additional commentary.  

#### Example Output:  
```  
Retrieve the names and total purchase amounts of customers who have placed orders worth more than $100 since January 1, 2023. The results should be sorted in descending order based on the total purchase amount, showing only the top five customers.  
<<SEP>>  
List the top five customers who made purchases exceeding $100 starting from January 1, 2023. Show only their names and total spending, with results ranked from highest to lowest purchase amount.  
```  
"""

DATA_CHECK_SYS_PROMPT = """
You are a validation assistant for MongoDB-related datasets. Your task is to evaluate if a given natural language query accurately corresponds to the provided MongoDB query based on the database schema. 

For each input, analyze the relationship between:
1. The database schema (which defines the structure of the data).
2. The natural language query (which describes the intent in plain language).
3. The MongoDB query (which should correctly implement the intent of the natural language query).

Return `1` if the MongoDB query correctly matches the natural language query and adheres to the database schema. Return `0` otherwise. Your evaluation should be precise and consider the correctness of collection names, field names, filters, joins, and other MongoDB logic based on the schema and intent.

Respond with either `1` or `0` only, with no additional text.
"""

DATA_CHECK_USER_PROMPT = """
Evaluate the following data point for correctness.

Database Schema:
{schema}

Natural Language Query:
{natural_language_query}

MongoDB Query:
{mongo_query}

Does the MongoDB query correctly implement the intent of the natural language query based on the database schema? Respond with `1` if correct and `0` if incorrect. Only respond with `1` or `0`.
"""


DATA_REFINE_SYS_PROMPT = """
You are a highly skilled assistant for refining MongoDB queries and aligning them with natural language descriptions based on a given database schema. Your primary goal is to ensure that the MongoDB query and natural language query are both correct, aligned, executable, and as simple as possible while preserving their meaning.

Rules:
1. **Correctness**: The MongoDB query must be valid and executable on the given schema. It should fully align with the intent of the natural language query.
2. **Simplicity**: Simplify the MongoDB query and natural language query if possible, but ensure they are unambiguous, precise, and adhere to the original intent of the input MongoDB query.
3. **Alignment**: If the MongoDB query and natural language query are misaligned, adjust one or both to ensure they are consistent and match the database schema.
4. **Executability**: The MongoDB query must strictly conform to the database schema and be syntactically and semantically correct.
5. **Precision**: The natural language query must have a single, clear meaning with no ambiguity. Avoid vague or overly broad descriptions.

Output Format:
- Return a dictionary with exactly two keys: `adjusted_mongo_query` and `adjusted_natural_language_query`.
- The `adjusted_mongo_query` key must contain the updated MongoDB query as a string, fully executable and aligned with the schema.
- The `adjusted_natural_language_query` key must contain the updated natural language query as a string, precise and fully aligned with the MongoDB query.

Your response must strictly follow this JSON format:
{
    "adjusted_mongo_query": "<UPDATED_MONGO_QUERY>",
    "adjusted_natural_language_query": "<UPDATED_NATURAL_LANGUAGE_QUERY>"
}

Do not include any additional text, explanations, or formatting outside the specified dictionary.
"""



DATA_REFINE_USER_PROMPT = """
Given the following database schema, natural language query, and MongoDB query, ensure alignment between the MongoDB query and the natural language query. Simplify both while preserving their meaning and correctness. 

Database Schema:
{schema}

Natural Language Query:
{natural_language_query}

MongoDB Query:
{mongo_query}

Instructions:
1. Verify the MongoDB query's correctness and executability on the given schema. Adjust it if needed to ensure it is valid and aligned with the natural language query.
2. Simplify the MongoDB query and/or the natural language query if possible, but maintain their correctness and intent.
3. Ensure the natural language query has a single, clear meaning and fully describes the MongoDB query's purpose.
4. If the MongoDB query and natural language query are misaligned, adjust one or both to achieve consistency.
5. Return the updated MongoDB query and natural language query in the strict format below.

Output Format:
{{
    "adjusted_mongo_query": "<UPDATED_MONGO_QUERY>",
    "adjusted_natural_language_query": "<UPDATED_NATURAL_LANGUAGE_QUERY>"
}}

Do not include any additional text, explanations, or comments. Only return the dictionary.
"""

# -----------------------------------

SCHEMA_LINKING_SYSTEM = """You are an expert in MongoDB queries. Your task is to generate REJECTED MongoDB queries by introducing a Schema Linking Error.

Schema Linking Errors include:
- Using incorrect field names that do not exist in the schema.
- Using a different collection name.
- Changing the data type of a field (e.g., string instead of int).
- Keeping the query structure close to the correct version.

Ensure the syntax remains valid while making the schema error.

NOTE - return only the required anwer without any extra things or explaination."""

SCHEMA_LINKING_USER = """### Schema:
{schema}

### Natural Language Query:
{nl_query}

### Correct MongoDB Query:
{correct_query}

### Instructions:
- Modify the field names to ones that do not exist in the schema.
- Use a different collection name if possible.
- Change the data type of a field incorrectly.
- Maintain valid MongoDB syntax.

Now, generate the incorrect MongoDB query.

NOTE - return only the required anwer without any extra things or explaination."""

LOGICAL_ERROR_SYSTEM = """You are an expert in MongoDB queries. Your task is to generate REJECTED MongoDB queries by introducing a Logical Error.

Logical Errors include:
- Incorrect usage of comparison operators (e.g., `$gt` vs. `$lt`).
- Swapping `$and` and `$or`.
- Contradictory conditions that change the logic of the query.

Ensure the query remains structurally valid while containing logical mistakes.

NOTE - return only the required anwer without any extra things or explaination."""

LOGICAL_ERROR_USER = """### Schema:
{schema}

### Natural Language Query:
{nl_query}

### Correct MongoDB Query:
{correct_query}

### Instructions:
- Swap logical operators (e.g., `$gt` ↔ `$lt`).
- Replace `$and` with `$or` incorrectly.
- Introduce a contradictory condition.
- Keep the structure similar to the correct query.

Now, generate the incorrect MongoDB query.

NOTE - return only the required anwer without any extra things or explaination."""

INCOMPLETE_QUERY_SYSTEM = """You are an expert in MongoDB queries. Your task is to generate REJECTED MongoDB queries by introducing an Incomplete Query Error.

Incomplete Queries include:
- Missing essential filter conditions.
- Omitting important projection fields.
- Keeping the syntax valid but the query logically incomplete.

NOTE - return only the required anwer without any extra things or explaination."""

INCOMPLETE_QUERY_USER = """### Schema:
{schema}

### Natural Language Query:
{nl_query}

### Correct MongoDB Query:
{correct_query}

### Instructions:
- Remove a key filter condition.
- Omit necessary projection fields.
- Keep the syntax correct but make the query incomplete.

Now, generate the incorrect MongoDB query.

NOTE - return only the required anwer without any extra things or explaination."""

SYNTAX_ERROR_SYSTEM = """You are an expert in MongoDB queries. Your task is to generate REJECTED MongoDB queries by introducing a Syntax Error.

Syntax Errors include:
- Missing brackets, commas, or incorrect JSON formatting.
- Invalid usage of MongoDB operators.
- Any structural mistake that causes the query to be invalid.

Ensure the query is syntactically incorrect while keeping its intent similar to the correct version.

NOTE - return only the required anwer without any extra things or explaination."""

SYNTAX_ERROR_USER = """### Schema:
{schema}

### Natural Language Query:
{nl_query}

### Correct MongoDB Query:
{correct_query}

### Instructions:
- Introduce missing brackets, commas, or invalid JSON formatting.
- Misuse an operator in an incorrect way.
- Ensure the query is not executable in MongoDB.

Now, generate the incorrect MongoDB query.

NOTE - return only the required anwer without any extra things or explaination."""

INEFFICIENT_QUERY_SYSTEM = """You are an expert in MongoDB queries. Your task is to generate REJECTED MongoDB queries by introducing an Inefficiency Error.

Inefficiencies include:
- Using an inefficient operator instead of a direct match.
- Adding redundant conditions.
- Using expensive operations unnecessarily (e.g., regex when an equality match is enough).

Ensure the query is valid but suboptimal in performance.

NOTE - return only the required anwer without any extra things or explaination."""

INEFFICIENT_QUERY_USER = """### Schema:
{schema}

### Natural Language Query:
{nl_query}

### Correct MongoDB Query:
{correct_query}

### Instructions:
- Use an inefficient operator (e.g., `$regex` for exact match).
- Add unnecessary `$or` clauses.
- Introduce redundant conditions that increase query cost.

Now, generate the incorrect MongoDB query.

NOTE - return only the required anwer without any extra things or explaination."""

AMBIGUOUS_QUERY_SYSTEM = """You are an expert in MongoDB queries. Your task is to generate REJECTED MongoDB queries by introducing an Ambiguity Error.

Ambiguous Queries include:
- Modifying a query so that its meaning is unclear.
- Removing constraints that change the intent subtly.
- Making the query interpretable in multiple ways.

Ensure the query is not obviously wrong but is ambiguous in intent.

NOTE - return only the required anwer without any extra things or explaination."""

AMBIGUOUS_QUERY_USER = """### Schema:
{schema}

### Natural Language Query:
{nl_query}

### Correct MongoDB Query:
{correct_query}

### Instructions:
- Modify the query to be unclear in its intent.
- Remove constraints that alter the query’s meaning subtly.
- Ensure the query could be interpreted in different ways.

Now, generate the incorrect MongoDB query.

NOTE - return only the required anwer without any extra things or explaination."""
