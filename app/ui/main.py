import streamlit as st
from dotenv import load_dotenv
import os
import pandas as pd
import json
import base64
from app.workflows.graph import build_graph
from app.config.rules import DEFAULT_RULES, CORE_RULES
from app.utils.logger import get_logger

# Load environment variables
load_dotenv()

logger = get_logger(__name__)

def main():
    st.set_page_config(page_title="AI PDF Compliance Scanner", page_icon="📄", layout="wide")
    
    # Modern CSS Injection
    st.markdown("""
        <style>
        .stButton>button { border-radius: 8px; transition: all 0.3s ease; font-weight: 600; }
        .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 4px 6px -1px rgba(0,0,0,0.2); }
        div[data-testid="stExpander"] { border-radius: 12px; border: 1px solid rgba(150, 150, 150, 0.2); box-shadow: 0 1px 3px 0 rgba(0,0,0,0.1); }
        div[data-testid="stMetricValue"] { font-size: 2rem !important; font-weight: 700 !important; }
        .success-box { padding: 1rem; border-radius: 8px; background-color: rgba(34, 197, 94, 0.15); border: 1px solid rgba(34, 197, 94, 0.3); margin-bottom: 1rem; }
        </style>
    """, unsafe_allow_html=True)
    
    st.title("📄 AI-Powered PDF Compliance Scanner")
    
    tab1, tab2 = st.tabs(["🔍 Scanner & Dashboard", "📝 Rules"])
    
    with tab1:
        # Four beautiful boxes highlighting the default rules
        st.markdown("### Intelligent Core Scanners")
        st.markdown("This AI engine continuously scans your document for 4 major risk categories. You can toggle these or add Custom Rules in the **📝 Rules** tab.")
        st.write("")
        
        c1, c2, c3, c4 = st.columns(4)
        
        c1.markdown("<div style='background-color: rgba(139, 92, 246, 0.1); padding: 1.5rem; border-radius: 12px; border: 1px solid rgba(139, 92, 246, 0.3); height: 100%;'>"
                    "<h4 style='margin-top: 0; color: #6d28d9;'>🟣 PII Detection</h4>"
                    "<p style='color: #4c1d95; margin-bottom: 0; font-size: 0.9rem;'>Instantly flags Social Security Numbers, Emails, Phone Numbers, and Credit Cards.</p>"
                    "</div>", unsafe_allow_html=True)
                    
        c2.markdown("<div style='background-color: rgba(239, 68, 68, 0.1); padding: 1.5rem; border-radius: 12px; border: 1px solid rgba(239, 68, 68, 0.3); height: 100%;'>"
                    "<h4 style='margin-top: 0; color: #b91c1c;'>🔴 Confidentiality</h4>"
                    "<p style='color: #7f1d1d; margin-bottom: 0; font-size: 0.9rem;'>Detects 'Internal Use Only', proprietary code names, and unreleased financial data.</p>"
                    "</div>", unsafe_allow_html=True)
                    
        c3.markdown("<div style='background-color: rgba(234, 179, 8, 0.1); padding: 1.5rem; border-radius: 12px; border: 1px solid rgba(234, 179, 8, 0.3); height: 100%;'>"
                    "<h4 style='margin-top: 0; color: #a16207;'>🟡 Toxicity</h4>"
                    "<p style='color: #713f12; margin-bottom: 0; font-size: 0.9rem;'>Identifies abusive, hateful, discriminatory, or highly unprofessional language.</p>"
                    "</div>", unsafe_allow_html=True)
                    
        c4.markdown("<div style='background-color: rgba(34, 197, 94, 0.1); padding: 1.5rem; border-radius: 12px; border: 1px solid rgba(34, 197, 94, 0.3); height: 100%;'>"
                    "<h4 style='margin-top: 0; color: #15803d;'>🟢 Obfuscation</h4>"
                    "<p style='color: #14532d; margin-bottom: 0; font-size: 0.9rem;'>Spots suspicious garbled Unicode, hidden Base64 blocks, and format hacking.</p>"
                    "</div>", unsafe_allow_html=True)
        
        st.write("")
        st.write("")
        
        with st.container():
            st.markdown("### Upload Document")
            st.markdown("<p style='color: #64748b; font-size: 0.9rem; margin-top: -0.5rem; margin-bottom: 0.5rem;'>⚡ <b>Max Limit:</b> 150 pages per document</p>", unsafe_allow_html=True)
            uploaded_file = st.file_uploader("Select a PDF to scan", type=["pdf"], label_visibility="collapsed")
            
            if uploaded_file is None:
                st.session_state.pop("result_state", None)
            else:
                # File Size Validation (10MB limit)
                if uploaded_file.size > 10 * 1024 * 1024:
                    st.error("❌ File exceeds the 10MB limit. Please upload a smaller PDF.")
                else:
                    st.markdown(f"<div class='success-box'>File <b>'{uploaded_file.name}'</b> uploaded successfully! Ready for analysis.</div>", unsafe_allow_html=True)
                    
                    if st.button("🚀 Run Compliance Scan", type="primary", use_container_width=True):
                        # Dynamic Loader
                        with st.status("🚀 Processing document...", expanded=True) as status:
                            try:
                                # 1. Grab file bytes
                                pdf_bytes = uploaded_file.getvalue()
                                status.write("📄 Reading PDF into memory...")
                                
                                # 2. Build Graph
                                graph = build_graph()
                                
                                # 3. Define Initial State
                                initial_state = {
                                    "file_name": uploaded_file.name,
                                    "pdf_bytes": pdf_bytes,
                                    "extracted_pages": [],
                                    "violations": [],
                                    "report_pdf_bytes": b"",
                                    "report_json_str": "",
                                    "errors": [],
                                    "custom_rules": st.session_state.get("rules", DEFAULT_RULES),
                                    "core_rules": st.session_state.get("core_rules", CORE_RULES)
                                }
                                
                                status.write("🧠 Handing off batched pages to Unified AI Agent...")
                                
                                # 4. Invoke Graph
                                result = graph.invoke(initial_state)
                                
                                # 5. Handle Results
                                if result.get("errors"):
                                    status.update(label="Scan failed with errors.", state="error", expanded=True)
                                    st.error("Errors encountered during scan:")
                                    for err in result["errors"]:
                                        st.write(f"- {err}")
                                else:
                                    status.update(label="Scan completed successfully!", state="complete", expanded=False)
                                    st.session_state["result_state"] = result
                                    
                            except Exception as e:
                                status.update(label="Workflow execution failed", state="error", expanded=True)
                                st.error(f"Workflow execution failed: {e}")
                                logger.error(f"Workflow error: {e}")
                            
            if "result_state" in st.session_state:
                result_state = st.session_state["result_state"]
                st.divider()
                
                st.subheader("📥 Download Reports")
                col_json, col_pdf = st.columns(2)
                
                report_json_str = result_state.get("report_json_str", "")
                report_pdf_bytes = result_state.get("report_pdf_bytes", b"")
                
                if report_json_str:
                    col_json.download_button(
                        label="📊 Download JSON Report",
                        data=report_json_str,
                        file_name="compliance_data.json",
                        mime="application/json",
                        use_container_width=True
                    )
                else:
                    col_json.info("JSON report not available.")
                    
                if report_pdf_bytes:
                    col_pdf.download_button(
                        label="📄 Download Beautiful PDF Report",
                        data=report_pdf_bytes,
                        file_name="compliance_report.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                        type="primary"
                    )
                else:
                    col_pdf.info("PDF report not available.")
                    
                st.divider()
                st.header("📊 Violations Dashboard")
                violations = result_state.get("violations", [])
                
                if not violations:
                    st.success("🎉 No compliance violations detected! The document is clean.")
                else:
                    # KPIs
                    st.subheader("Summary")
                    col1, col2, col3, col4, col5 = st.columns(5)
                    
                    critical = sum(1 for v in violations if v.get("severity") == "Critical")
                    high = sum(1 for v in violations if v.get("severity") == "High")
                    medium = sum(1 for v in violations if v.get("severity") == "Medium")
                    low = sum(1 for v in violations if v.get("severity") == "Low")
                    
                    col1.metric("Total", len(violations))
                    col2.metric("🟣 Critical", critical)
                    col3.metric("🔴 High", high)
                    col4.metric("🟡 Medium", medium)
                    col5.metric("🟢 Low", low)
                    
                    st.divider()
                    st.subheader("Document & Detailed Violations")
                    
                    doc_col, table_col = st.columns([1, 1.2])
                    
                    with doc_col:
                        st.markdown("#### Document Viewer")
                        pdf_bytes_preview = result_state.get("pdf_bytes", b"")
                        if pdf_bytes_preview:
                            base64_pdf = base64.b64encode(pdf_bytes_preview).decode('utf-8')
                            pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="800px" type="application/pdf" style="border: 1px solid #ccc; border-radius: 8px;"></iframe>'
                            st.markdown(pdf_display, unsafe_allow_html=True)
                        else:
                            st.info("PDF preview not available.")
                            
                    with table_col:
                        st.markdown("#### Violations")
                        # Convert list of dicts to DataFrame for better display
                        df = pd.DataFrame(violations)
                        # Reorder columns if they exist
                        cols_order = ["page", "type", "subtype", "severity", "confidence_score", "value", "reasoning"]
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
                                height=800,
                                column_config={
                                    "value": st.column_config.TextColumn("Value", width="large", help="The exact text of the extracted violation"),
                                    "reasoning": st.column_config.TextColumn("Reasoning", width="large", help="LLM's step-by-step reasoning for flagging this violation"),
                                    "confidence_score": st.column_config.ProgressColumn("Confidence", help="LLM Confidence Score", format="%.2f", min_value=0, max_value=1)
                                }
                            )
                
    with tab2:
        st.header("📝 Rules Engine")
        st.write("Manage dynamic rules for the compliance agents. Disable core rules if you don't need them, or add your own custom prompts.")
        
        # Initialize session state for rules if not present
        if "rules" not in st.session_state:
            st.session_state["rules"] = DEFAULT_RULES
            
        if "core_rules" not in st.session_state:
            st.session_state["core_rules"] = CORE_RULES.copy()
            
        st.subheader("🛡️ Core Rules (Built-in)")
        st.write("Toggle built-in compliance checks.")
        
        # Core rules display (read only except for toggle)
        for rule_key, rule_data in st.session_state["core_rules"].items():
            ccol1, ccol2 = st.columns([1, 9])
            st.session_state["core_rules"][rule_key]["enabled"] = ccol1.toggle(
                "Enable", 
                value=rule_data.get("enabled", True), 
                key=f"core_{rule_key}", 
                label_visibility="collapsed"
            )
            ccol2.markdown(f"**{rule_data.get('name')}**: {rule_data.get('description')}")
            
        st.divider()
            
        st.subheader("⚙️ Custom Rules")
        st.write("Edit rules directly below, or click the delete button to remove them. Click 'Save Custom Rules' when done.")
        
        # Header row
        hcol1, hcol2, hcol3, hcol4, hcol5 = st.columns([1, 2, 4, 2, 1])
        hcol1.markdown("**Enabled**")
        hcol2.markdown("**Rule Name**")
        hcol3.markdown("**Description**")
        hcol4.markdown("**Severity**")
        hcol5.markdown("**Action**")
        
        to_delete = None
        severity_options = ["Auto (LLM Decides)", "Critical", "High", "Medium", "Low"]
        for i, rule in enumerate(st.session_state["rules"]):
            col1, col2, col3, col4, col5 = st.columns([1, 2, 4, 2, 1])
            st.session_state["rules"][i]["enabled"] = col1.checkbox("Enabled", value=rule.get("enabled", True), key=f"en_{i}", label_visibility="collapsed")
            st.session_state["rules"][i]["name"] = col2.text_input("Name", value=rule.get("name", ""), key=f"nm_{i}", label_visibility="collapsed")
            st.session_state["rules"][i]["description"] = col3.text_input("Description", value=rule.get("description", ""), key=f"desc_{i}", label_visibility="collapsed")
            
            # Severity Dropdown
            current_sev = rule.get("severity", "Auto (LLM Decides)")
            if current_sev not in severity_options:
                current_sev = "Auto (LLM Decides)"
            st.session_state["rules"][i]["severity"] = col4.selectbox("Severity", severity_options, index=severity_options.index(current_sev), key=f"sev_{i}", label_visibility="collapsed")
            
            if col5.button("🗑️ Delete", key=f"del_{i}"):
                to_delete = i
                
        if to_delete is not None:
            st.session_state["rules"].pop(to_delete)
            st.rerun()
            
        st.write("")

        with st.expander("➕ Add New Custom Rule", expanded=False):
            with st.form("add_rule_form", clear_on_submit=True):
                new_rule_name = st.text_input("Rule Name", placeholder="e.g., Salary Check")
                new_rule_desc = st.text_area("Rule Description", placeholder="e.g., Flag any mention of employee salaries.")
                new_rule_severity = st.selectbox("Target Severity", ["Auto (LLM Decides)", "Critical", "High", "Medium", "Low"])
                
                submitted = st.form_submit_button("Add Rule")
                
                if submitted:
                    if not new_rule_name.strip() or not new_rule_desc.strip():
                        st.error("❌ Both Rule Name and Rule Description are required to add a rule.")
                    else:
                        st.session_state["rules"].append({
                            "name": new_rule_name.strip(),
                            "description": new_rule_desc.strip(),
                            "severity": new_rule_severity,
                            "enabled": True
                        })
                        st.success(f"Rule '{new_rule_name}' added to the table above!")
                        st.rerun()
            
        st.write("")
        if st.button("💾 Save Custom Rules", type="primary"):
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
                        
                    st.success("Rules saved successfully! The next scan will use these settings.")
                except Exception as e:
                    st.error(f"Failed to save rules. Details: {e}")

if __name__ == "__main__":
    main()
