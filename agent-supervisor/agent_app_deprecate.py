import json
import re
import uuid

import streamlit as st

import agent_lib_deprecate as glib
import guardrails_deprecate

# config
AGENT_ID = "NGK1G2NQP2"
AGENT_ALIAS_ID = "PJKGMNTGGR"

# Load language data from JSON file
with open('localization_deprecate.json', 'r', encoding='utf-8') as f:
    LANG = json.load(f)

# main page
st.set_page_config(page_title="Stock Analyzer")

# Sidebar for language selection
st.sidebar.title("Language")
language = st.sidebar.radio("Select Language", ('English', '한국어'))
lang = 'en' if language == 'English' else 'ko'

st.title(LANG[lang]['title'])
input_text = st.text_input(LANG[lang]['input_prompt'])
submit_button = st.button(LANG[lang]['analyze_button'], type="primary")

# Container for real-time updates
trace_container = st.container()

if submit_button and input_text:
    with st.spinner(LANG[lang]['generating_response']):
        response = glib.get_agent_response(
            AGENT_ID,
            AGENT_ALIAS_ID,
            str(uuid.uuid4()),
            input_text
        )

        trace_container.subheader(LANG[lang]['bedrock_reasoning'])

        output_text = ""
        function_name = ""

        for event in response.get("completion"):
            if "chunk" in event:
                chunk = event["chunk"]
                output_text += chunk["bytes"].decode()

            if "trace" in event:
                each_trace = event["trace"]["trace"]

                if "orchestrationTrace" in each_trace:
                    trace = event["trace"]["trace"]["orchestrationTrace"]

                    if "rationale" in trace:
                        with trace_container.chat_message("ai"):
                            st.markdown(trace['rationale']['text'])

                    elif function_name != "":
                        if function_name == "get_today":
                            display_today(trace_container, trace)
                        elif function_name == "get_company_profile":
                            display_company_profile(trace_container, trace)
                        elif function_name == "get_stock_chart":
                            display_stock_chart(trace_container, trace)
                        elif function_name == "get_stock_balance":
                            display_stock_balance(trace_container, trace)
                        elif function_name == "get_recommendations":
                            display_recommendations(trace_container, trace)

                        function_name = ""

                    else:
                        function_name = trace.get('invocationInput', {}).get('actionGroupInvocationInput', {}).get(
                            'function', "")

                elif "guardrailTrace" in each_trace:
                    guardrails.display_guardrail_trace(trace_container, each_trace["guardrailTrace"])

        trace_container.divider()
        trace_container.subheader(LANG[lang]['analysis_report'])
        styled_text = re.sub(
            r'\{([^}]+)\}',
            r'<span style="background-color: #ffd700; padding: 2px 6px; border-radius: 3px; font-weight: bold; color: #1e1e1e;">\1</span>',
            output_text
        )
        trace_container.markdown(styled_text, unsafe_allow_html=True)