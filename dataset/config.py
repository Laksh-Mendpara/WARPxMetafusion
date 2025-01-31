MONGO_GEN_SYS_PROMPT = """
You are a highly skilled MongoDB assistant. Based on the input database schema and the difficulty level provided, generate 20 MongoDB queries.

Requirements:
1. The MongoDB queries must be executable and syntactically correct for the provided database schema.
2. Ensure that all queries are compatible with the input schema, including proper field and collection names, data types, and relationships.
3. Tailor the MongoDB queries to match the schema's structure (e.g., embedded documents, references, or data types).

Difficulty Levels:
- If the difficulty level is 1 or 2, provide basic queries (e.g., simple find queries or queries involving simple filters).
- If the difficulty level is 3 or 4, provide intermediate queries (e.g., queries with `$group`, `$match`, `$sort`, `$lookup`, or aggregation pipelines).
- If the difficulty level is 5, provide advanced queries involving complex aggregations, nested queries, or multi-stage pipelines.

Output Format:
- Return a list of exactly 20 MongoDB queries.
- Separate each query with the token <<SEP>>.
- The queries should be executable based on the given schema, without any additional text or numbering.

Example Output:
db.employees.find({ department: 'Sales' }); <<SEP>> 
db.employees.aggregate([ { $lookup: { from: 'departments', localField: 'department_id', foreignField: 'department_id', as: 'department_info' } } ]); <<SEP>>
...
"""

MONGO_GEN_USER_PROMPT = """
Given the following database schema and difficulty level, generate 20 MongoDB queries.

Requirements:
1. The MongoDB queries must be executable and syntactically correct for the provided database schema.
2. Ensure all queries are aligned with the schema's structure, including correct collection and field names, relationships, and data types.
3. Generate exactly 20 MongoDB queries, and separate them using the token <<SEP>>.

Schema: {schema}

Difficulty Level: {difficulty_level}

If the difficulty level is 1 or 2, provide basic queries (e.g., simple find queries or queries involving simple filters).
If the difficulty level is 3 or 4, provide intermediate queries (e.g., queries with `$group`, `$match`, `$sort`, `$lookup`, or aggregation pipelines).
If the difficulty level is 5, provide advanced queries involving complex aggregations, nested queries, or multi-stage pipelines.

Expected Output Format:
- 20 executable MongoDB queries separated by <<SEP>>.
- No additional text or explanations, just the queries separated by the token.

Example Output:
db.employees.aggregate([ {{ $group: {{ _id: "$department", count: {{ $sum: 1 }} }} }}, {{ $match: {{ count: {{ $gt: 10 }} }} }} ]); <<SEP>> 
db.employees.aggregate([ {{ $lookup: {{ from: 'projects', localField: 'employee_id', foreignField: 'employee_id', as: 'projects' }} }}, {{ $match: {{ 'salary': {{ $gt: 60000 }}, 'projects.start_date': {{ $gt: '2023-01-01' }} }} }} ]); <<SEP>>
"""

NL_GEN_SYS_PROMPT = """
You are a highly accurate assistant specializing in generating precise natural language queries from MongoDB queries. Your task is to ensure that the natural language text query exactly matches the semantics of the given MongoDB query. 

Requirements:
1. The natural language query must describe the MongoDB query in a clear, concise, and easy-to-understand manner without using MongoDB syntax.
2. The description must fully preserve the intent and structure of the MongoDB query, including:
   - Fields being selected.
   - Collections being queried.
   - Filters, conditions, and joins being applied.
   - Any grouping, aggregation, sorting, or limits specified in the MongoDB query.
3. The natural language query must be so precise that, if given as input to an LLM specialized in generating MongoDB queries, it would reproduce the same MongoDB query without any loss of meaning or intent.

Output:
- Provide the natural language query as a plain text response, strictly aligned with the given MongoDB query.
- Avoid any ambiguity or omissions in the natural language description to ensure exact alignment.

Example:
For the schema and MongoDB query:
- Schema: An employee database with collections for employees, departments, and salaries.
- MongoDB Query: db.employees.find({ department: 'Sales' }).sort({ salary: -1 });
- Output: "Retrieve the documents of employees from the 'employees' collection who belong to the 'Sales' department, sorted by their salary in descending order."

Your responses must always maintain this level of precision and alignment.
"""

NL_GEN_USER_PROMPT = """
Given the following database schema and MongoDB query, generate a precise natural language query.

Schema: {schema}

MongoDB Query: {mongo_query}

Instructions:
1. Write a natural language query that exactly matches the meaning of the MongoDB query.
2. The natural language query must clearly describe:
   - What the MongoDB query is selecting.
   - From which collections or sources the data is being retrieved.
   - Any filters, conditions, groupings, sorting, or limits in the query.
3. Ensure the natural language query is so precise that if it were used to generate a MongoDB query, the resulting MongoDB query would be identical to the one provided.

Output Example:
- Schema: An e-commerce database with collections for orders, customers, and products.
- MongoDB Query: db.orders.aggregate([ {{ $lookup: {{ from: 'products', localField: 'product_id', foreignField: 'product_id', as: 'product_info' }} }}, {{ $match: {{ order_date: {{ $gte: '2023-01-01' }} }} }} ]);
- Output: "Find all orders from the 'orders' collection where the 'order_date' is on or after January 1, 2023, and include related product information from the 'products' collection."

Provide your response as a plain text natural language query without any additional text or formatting.
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
