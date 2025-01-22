SQL_GEN_SYS_PROMPT = """
You are a helpful SQL assistant. Based on the input database schema and the difficulty level provided, generate 20 SQL queries. The difficulty level will determine the complexity of the queries you generate:
- If the difficulty level is 1 or 2, provide basic queries (e.g., simple SELECT or JOIN queries).
- If the difficulty level is 3 or 4, provide intermediate queries (e.g., GROUP BY, HAVING, ORDER BY, or queries involving foreign keys).
- If the difficulty level is 5, provide advanced queries involving multiple joins, subqueries, or complex filters.
Return a list of 20 queries separated only by the token <<SEP>> (do not add any numbering or bullet points after each query) and ensure that the list contains exactly 20 queries.
"""

SQL_GEN_USER_PROMPT = """
Given the following database schema and difficulty level, generate 20 SQL queries.

Schema: {schema}
Difficulty Level: {difficulty_level}

If the difficulty level is 1 or 2, provide basic queries (e.g., simple SELECT or JOIN queries).
If the difficulty level is 3 or 4, provide intermediate queries (e.g., GROUP BY, HAVING, ORDER BY, or queries involving foreign keys).
If the difficulty level is 5, provide advanced queries involving multiple joins, subqueries, or complex filters.

For each query, separate them with the token <<SEP>> and return the queries in a list format, containing exactly 20 queries.

Example for difficulty 1-2:
- SELECT * FROM employees WHERE department = 'Sales';
- SELECT first_name, last_name FROM employees JOIN departments ON employees.department_id = departments.department_id;

Example for difficulty 3-4:
- SELECT department, COUNT(*) FROM employees GROUP BY department HAVING COUNT(*) > 10;
- SELECT name, salary FROM employees WHERE salary > 50000 ORDER BY salary DESC;

Example for difficulty 5:
- SELECT e.name, e.salary, p.project_name FROM employees e JOIN employee_projects ep ON e.employee_id = ep.employee_id JOIN projects p ON ep.project_id = p.project_id WHERE e.salary > 60000 AND p.start_date > '2023-01-01';
- SELECT e.name, COUNT(p.project_id) FROM employees e LEFT JOIN employee_projects ep ON e.employee_id = ep.employee_id LEFT JOIN projects p ON ep.project_id = p.project_id GROUP BY e.name HAVING COUNT(p.project_id) > 2;
"""

NL_GEN_SYS_PROMPT = """
You are a helpful assistant for generating the naive natural language text queries. Given the following database schema and SQL query, your task is to generate a clear and concise natural language text query that can be used for dataset generation to fine-tune an LLM model.

For each input, generate a simple, easy-to-understand natural language query that explains what the SQL query does. Do not use SQL syntax, but explain the operation in plain language. The output should describe the SQL query's purpose, what it is selecting, filtering, or grouping, using common terms.

Provide the natural language query as a plain text response.
NOTE: When natural language query and schema is given input to LLM specialized in generating SQL queries, it should generate the same SQL query as input.
"""

NL_GEN_USER_PROMPT = """
Given the following database schema and SQL query, generate the corresponding natural language text query.

Schema: {schema}

SQL Query: {sql_query}

Generate the corresponding natural language text query that describes the SQL query in a simple, easy-to-understand manner. The natural language query should explain what the SQL query does, using common terms and without using any SQL syntax. 

For example:
- Given a schema with employee information and a SQL query that selects employee names and their salaries where the salary is greater than 50,000, the natural language query could be: "Find the names and salaries of employees who earn more than 50,000."

Provide the natural language query as a plain text response.
"""
