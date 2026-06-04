import os
from langfuse import Langfuse
from dotenv import load_dotenv

load_dotenv()
host = os.environ.get("LANGFUSE_HOST") or os.environ.get("LANGFUSE_BASE_URL")
lf = Langfuse(
    public_key=os.environ.get("LANGFUSE_PUBLIC_KEY"),
    secret_key=os.environ.get("LANGFUSE_SECRET_KEY"),
    host=host
)

# Fetch traces
traces = lf.get_traces(limit=5).data
for t in traces:
    print(f"Trace ID: {t.id}, Name: {t.name}, Timestamp: {t.timestamp}")
    scores = lf.get_scores(trace_id=t.id).data
    for s in scores:
        print(f"  -> Score: {s.name} = {s.value}")
