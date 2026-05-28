import streamlit as st
from dotenv import load_dotenv
import os
import pandas as pd
import json
from app.workflows.graph import build_graph
from app.config.rules import load_rules, save_rules
from app.utils.logger import get_logger

# Load environment variables
load_dotenv()

logger = get_logger(__name__)

UPLOADS_DIR = "data/uploads"

def main():
    st.set_page_config(page_title="AI PDF Compliance Scanner", page_icon="📄", layout="wide")
    
    st.title("📄 AI-Powered PDF Compliance Scanner")
    
    tab1, tab2 = st.tabs(["🔍 Scanner & Dashboard", "📝 Rules"])
    
    with tab1:
        st.header("Upload and Scan")
        st.write("Upload a PDF to extract its text and run compliance checks via LangGraph orchestration.")
        
        uploaded_file = st.file_uploader("Choose a PDF file", type="pdf", key="pdf_uploader")
        
        if uploaded_file is not None:
            if st.button("Run Compliance Scan", type="primary"):
                with st.status("Executing LangGraph Pipeline...", expanded=True) as status:
                    try:
                        # 1. Save uploaded file temporarily
                        st.write("Saving uploaded file...")
                        file_path = os.path.join(UPLOADS_DIR, uploaded_file.name)
                        os.makedirs(UPLOADS_DIR, exist_ok=True)
                        with open(file_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        logger.info(f"Saved uploaded file to {file_path}")
                        
                        # 2. Compile Graph
                        st.write("Building workflow graph...")
                        graph = build_graph()
                        
                        # 3. Define Initial State
                        initial_state = {
                            "file_path": file_path,
                            "extracted_pages": [],
                            "violations": [],
                            "report_paths": {},
                            "errors": []
                        }
                        
                        # 4. Invoke Graph
                        st.write("Running compliance agents...")
                        result_state = graph.invoke(initial_state)
                        
                        if result_state.get("errors"):
                            status.update(label="Workflow encountered errors", state="error", expanded=False)
                            st.error(f"Workflow encountered errors: {result_state['errors']}")
                        else:
                            status.update(label="Workflow executed successfully!", state="complete", expanded=False)
                            st.success("Scan completed successfully!")
                            
                            st.session_state["result_state"] = result_state
                            
                    except Exception as e:
                        status.update(label="Workflow execution failed", state="error", expanded=False)
                        st.error(f"Workflow execution failed: {e}")
                        logger.error(f"Workflow error: {e}")
                        
        if "result_state" in st.session_state:
            result_state = st.session_state["result_state"]
            st.divider()
            
            st.subheader("📥 Download Reports")
            report_paths = result_state.get("report_paths", {})
            col_json, col_pdf = st.columns(2)
            
            json_path = report_paths.get("json")
            pdf_path = report_paths.get("pdf")
            
            if json_path and os.path.exists(json_path):
                with open(json_path, "r") as f:
                    json_data = f.read()
                col_json.download_button(
                    label="Download JSON Report",
                    data=json_data,
                    file_name=os.path.basename(json_path),
                    mime="application/json",
                    use_container_width=True
                )
            else:
                col_json.info("JSON report not available.")
                
            if pdf_path and os.path.exists(pdf_path):
                with open(pdf_path, "rb") as f:
                    pdf_data = f.read()
                col_pdf.download_button(
                    label="Download PDF Report",
                    data=pdf_data,
                    file_name=os.path.basename(pdf_path),
                    mime="application/pdf",
                    type="primary",
                    use_container_width=True
                )
            else:
                col_pdf.info("PDF report not available.")
                
            st.divider()
            st.header("📊 Violations Dashboard")
            violations = result_state.get("violations", [])
            
            if not violations:
                st.success("No compliance violations detected!")
            else:
                # KPIs
                st.subheader("Summary")
                col1, col2, col3, col4, col5 = st.columns(5)
                
                critical = sum(1 for v in violations if v.get("severity") == "Critical")
                high = sum(1 for v in violations if v.get("severity") == "High")
                medium = sum(1 for v in violations if v.get("severity") == "Medium")
                low = sum(1 for v in violations if v.get("severity") == "Low")
                
                col1.metric("Total", len(violations))
                col2.metric("Critical", critical)
                col3.metric("High", high)
                col4.metric("Medium", medium)
                col5.metric("Low", low)
                
                st.divider()
                st.subheader("Detailed Violations")
                
                # Convert list of dicts to DataFrame for better display
                df = pd.DataFrame(violations)
                # Reorder columns if they exist
                cols_order = ["page", "type", "subtype", "severity", "value"]
                # Keep only columns that exist
                cols_order = [c for c in cols_order if c in df.columns]
                
                # Optionally add remaining columns
                for c in df.columns:
                    if c not in cols_order:
                        cols_order.append(c)
                        
                if not df.empty:
                    df = df[cols_order]
                    # Enforce text wrapping using st.column_config.TextColumn
                    st.dataframe(
                        df, 
                        use_container_width=True, 
                        hide_index=True,
                        column_config={
                            "value": st.column_config.TextColumn("Value", width="large", help="The exact text of the extracted violation")
                        }
                    )
            
    with tab2:
        st.header("📝 Custom Rules Engine")
        st.write("Manage dynamic rules for the compliance agents. You can enable/disable rules or add your own custom prompts.")
        
        # Initialize session state for rules if not present
        if "rules" not in st.session_state:
            st.session_state["rules"] = load_rules()
            
        st.subheader("Current Rules")
        st.write("Edit rules directly below, or click the delete button to remove them. Click 'Save All Changes' when done.")
        
        # Header row
        hcol1, hcol2, hcol3, hcol4 = st.columns([1, 3, 5, 1])
        hcol1.markdown("**Enabled**")
        hcol2.markdown("**Rule Name**")
        hcol3.markdown("**Description**")
        hcol4.markdown("**Action**")
        
        to_delete = None
        for i, rule in enumerate(st.session_state["rules"]):
            col1, col2, col3, col4 = st.columns([1, 3, 5, 1])
            st.session_state["rules"][i]["enabled"] = col1.checkbox("Enabled", value=rule.get("enabled", True), key=f"en_{i}", label_visibility="collapsed")
            st.session_state["rules"][i]["name"] = col2.text_input("Name", value=rule.get("name", ""), key=f"nm_{i}", label_visibility="collapsed")
            st.session_state["rules"][i]["description"] = col3.text_input("Description", value=rule.get("description", ""), key=f"desc_{i}", label_visibility="collapsed")
            if col4.button("🗑️ Delete", key=f"del_{i}"):
                to_delete = i
                
        if to_delete is not None:
            st.session_state["rules"].pop(to_delete)
            st.rerun()
            
        st.divider()

        with st.expander("➕ Add New Custom Rule", expanded=False):
            with st.form("add_rule_form", clear_on_submit=True):
                new_rule_name = st.text_input("Rule Name", placeholder="e.g., Salary Check")
                new_rule_desc = st.text_area("Rule Description", placeholder="e.g., Flag any mention of employee salaries.")
                
                submitted = st.form_submit_button("Add Rule")
                
                if submitted:
                    if not new_rule_name.strip() or not new_rule_desc.strip():
                        st.error("❌ Both Rule Name and Rule Description are required to add a rule.")
                    else:
                        st.session_state["rules"].append({
                            "name": new_rule_name.strip(),
                            "description": new_rule_desc.strip(),
                            "enabled": True
                        })
                        st.success(f"Rule '{new_rule_name}' added to the table above!")
                        st.rerun()
            
        st.write("")
        if st.button("💾 Save All Changes", type="primary"):
            has_empty_fields = False
            for rule in st.session_state["rules"]:
                if not rule.get("name", "").strip() or not rule.get("description", "").strip():
                    has_empty_fields = True
                    break
                    
            if has_empty_fields:
                st.error("❌ Cannot save! One or more rules have an empty Name or Description. Please fill them out or delete the empty rules.")
            else:
                try:
                    # Strip inputs before saving
                    for rule in st.session_state["rules"]:
                        rule["name"] = rule["name"].strip()
                        rule["description"] = rule["description"].strip()
                        
                    save_rules(st.session_state["rules"])
                    st.success("Rules saved successfully! The next scan will use these settings.")
                except Exception as e:
                    st.error(f"Failed to save rules. Details: {e}")

if __name__ == "__main__":
    main()
