from app.workflows.graph import build_graph
import pprint

def test_workflow():
    graph = build_graph()
    
    initial_state = {
        "file_path": "test_pii.pdf",
        "extracted_pages": [],
        "violations": [],
        "report_paths": {},
        "errors": []
    }
    
    print("Running workflow...")
    result = graph.invoke(initial_state)
    
    print("\nWorkflow completed. Report paths:")
    pprint.pprint(result.get("report_paths"))
    
if __name__ == "__main__":
    test_workflow()
