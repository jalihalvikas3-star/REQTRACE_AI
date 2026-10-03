from app.models.requirement import Requirement
from app.services.semantic_retrieval import find_similar_requirements


requirements = [
    Requirement(
        "REQ-001",
        "Functional",
        "The system shall allow users to search for available books."
    ),
    Requirement(
        "REQ-002",
        "Functional",
        "Users shall be able to find books in the catalogue."
    ),
    Requirement(
        "REQ-003",
        "Functional",
        "The system shall generate PDF reports."
    )
]


print("Starting semantic retrieval test...")

results = find_similar_requirements(
    requirements,
    top_k=2
)

print("\nRESULTS:\n")

for result in results:
    print(result)

print("\nTEST COMPLETE")