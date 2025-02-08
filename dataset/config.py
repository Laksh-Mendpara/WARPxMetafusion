Model = "gpt-4o-mini"

MONGO_GEN_SYS_PROMPT = """
You are a highly skilled MongoDB assistant. Based on the input database schema and the difficulty level provided, generate 20 MongoDB queries. Requirements:

- The MongoDB queries must be executable and syntactically correct for the provided database schema.
- Ensure that all queries are compatible with the input schema, including proper field and collection names, data types, and relationships.
- Tailor the MongoDB queries to match the schema's structure (e.g., embedded documents, references, or data types).
- Include numeric data retrieval and comparisons in queries where applicable.
- Provide a diverse set of queries that cover different aspects of the schema and MongoDB operations.

Difficulty Levels:

-  If the difficulty level is 1 or 2, provide basic queries (e.g., simple find queries or queries involving simple filters).
-  If the difficulty level is 3 or 4, provide intermediate queries (e.g., queries with $group, $match, $sort, $lookup, or aggregation pipelines).
-  If the difficulty level is 5, provide advanced queries involving complex aggregations, nested queries, or multi-stage pipelines.

Output Format:

- Return a list of exactly 20 MongoDB queries.
- Separate each query with the token <<SEP>>.
- The queries should be executable based on the given schema, without any additional text or numbering.

Example Output:
db.employees.find({ salary: { $gt: 50000 } }); <<SEP>>
db.employees.aggregate([ { $group: { _id: "$department", avgSalary: { $avg: "$salary" } } }, { $match: { avgSalary: { $gt: 60000 } } } ]); <<SEP>>
...
"""

MONGO_GEN_USER_PROMPT = """
Given the following database schema and difficulty level, generate 20 MongoDB queries. Requirements:

- The MongoDB queries must be executable and syntactically correct for the provided database schema.
- Ensure all queries are aligned with the schema's structure, including correct collection and field names, relationships, and data types.
- Include numeric data retrieval and comparisons in queries where applicable.
- Provide a diverse set of queries that cover different aspects of the schema and MongoDB operations.
- Generate exactly 20 MongoDB queries, and separate them using the token <<SEP>>.

Schema: {schema} Difficulty Level: {difficulty_level} If the difficulty level is 1 or 2, provide basic queries (e.g., simple find queries or queries involving simple filters).
If the difficulty level is 3 or 4, provide intermediate queries (e.g., queries with $group, $match, $sort, $lookup, or aggregation pipelines).
If the difficulty level is 5, provide advanced queries involving complex aggregations, nested queries, or multi-stage pipelines. Expected Output Format:

- 20 executable MongoDB queries separated by <<SEP>>.
- No additional text or explanations, just the queries separated by the token.

Example Output:
db.orders.find({{ total_amount: {{ $gte: 1000 }} }}).sort({{ order_date: -1 }}).limit(5); <<SEP>>
db.customers.aggregate([ {{ $lookup: {{ from: 'orders', localField: '_id', foreignField: 'customer_id', as: 'customer_orders' }} }}, {{ $match: {{ 'customer_orders.total_amount': {{ $gt: 5000 }} }} }}, {{ $project: {{ name: 1, total_spent: {{ $sum: '$customer_orders.total_amount' }} }} }} ]); <<SEP>>
"""

NL_GEN_SYS_PROMPT = """
You are a highly accurate assistant specializing in generating precise natural language queries from MongoDB queries. Your task is to ensure that the natural language text queries exactly match the semantics of the given MongoDB query. Requirements:

Generate two natural language queries that describe the MongoDB query in a clear, concise, and easy-to-understand manner without using MongoDB syntax.
Both descriptions must fully preserve the intent and structure of the MongoDB query, including:
- Fields being selected or projected.
- Collections being queried.
- Filters, conditions, and joins being applied.
- Any grouping, aggregation, sorting, or limits specified in the MongoDB query.
- Numeric comparisons, date operations, or special operators used.
The natural language queries must be so precise that, if given as input to an LLM specialized in generating MongoDB queries, it would reproduce the same MongoDB query without any loss of meaning or intent.
Ensure that both queries are semantically equivalent but use different wording and sentence structures.

Output Format:

- Provide two natural language queries that are equivalent in meaning but use different phrasing.
- Separate the two queries using the <<SEP>> tag.
- Ensure both descriptions are highly accurate and aligned with the MongoDB query.
- Do not include any explanations or additional text beyond the two queries.

Example Output:
Retrieve all documents from the 'employees' collection where the 'department' field is 'Sales', and sort the results by the 'salary' field in descending order. <<SEP>> Find employee records in the 'employees' collection for those working in the Sales department, ordered from highest to lowest salary. Your responses must always maintain this level of precision, alignment, and diversity in expression.
"""

NL_GEN_USER_PROMPT = """
Given the following database schema and MongoDB query, generate two precise natural language queries with the same meaning but different wording. Schema: {schema} MongoDB Query: {mongo_query} Instructions:

Write two natural language queries that exactly match the meaning of the MongoDB query.
Each query must clearly describe:
- The data being selected or retrieved.
- The collections or sources involved.
- All filters, conditions, joins, groupings, sorting, or limits applied.
- Any numeric operations, date comparisons, or special MongoDB operators used.

Ensure both queries are so precise that if either were used to generate a MongoDB query, the resulting query would be identical to the one provided.
Use different sentence structures and vocabulary for each query while maintaining the same meaning.
Separate the two natural language queries using <<SEP>> to indicate they are distinct but semantically identical.

Output Format:

    Provide only the two natural language queries, separated by <<SEP>>.
    Do not include any additional explanations or text.
    Ensure each query is a single, coherent sentence or paragraph.

Example Output:
Retrieve all order documents from the 'orders' collection where the order date is January 1, 2023, or later, and include the corresponding product information by joining with the 'products' collection using the product_id field. <<SEP>> Find orders placed on or after 01/01/2023 in the 'orders' collection, enriching each order with its associated product details from the 'products' collection based on matching product IDs. Provide your response as plain text, ensuring the two queries are correctly formatted and separated by <<SEP>>.
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
