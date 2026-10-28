
from pprint import pprint

from app.services.qa_service import answer_question

result = answer_question(
    question="Which database is used to store structured data?",
    document_id=999,
)

print("\n--- Generated Answer ---")
print(result.answer)

print("\n--- Citations ---")
pprint(
    [
        citation.model_dump()
        for citation in result.citations
    ]
)
