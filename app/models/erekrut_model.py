from langchain.output_parsers import StructuredOutputParser, ResponseSchema

response_schemas = [
    ResponseSchema(
        name="job_designations",
        type="Optional[List[str]]",
        description="The job titles or roles the user is qualified for or interested in",
    ),
    ResponseSchema(
        name="years_of_experience",
        type="Optional[Literal['1-3 Years', '4-6 Years', '7-10 Years', '11-15 Years', '16-20 Years', '21-25 Years', '26-30 Years', '30+ Years', 'No Experience', 'Freshers (0-1) Years']]",
        description="The user's total years of professional work experience, categorized into predefined ranges",
    ),
    ResponseSchema(
        name="email", type="Optional[str]", description="The user's email address"
    ),
]

structured_parser = StructuredOutputParser.from_response_schemas(response_schemas)
