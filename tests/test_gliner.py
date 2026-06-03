from app.agents.gliner_agent import run_gliner_pii_scan

pages = [
    {"page_number": 1, "text": "My email is john.doe@example.com and my phone number is 555-1234."}
]

result = run_gliner_pii_scan(pages)
print("Violations found:")
for v in result.get("violations", []):
    print(v)
print("Errors:", result.get("errors", []))
