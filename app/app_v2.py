import json
import logging

import streamlit as st
import pandas as pd

from component.sidebar import sidebar

from aws_services import AWSResourceCollector
from bedrock_utils import BedrockService
import re

MODEL_LIST = ["just", "test", "ui component"]

# Streamlit Page Configuration
st.set_page_config(
    page_title="Stream Bedrock Project Demo",
    layout="wide",
    initial_sidebar_state="auto",
    menu_items={
        "Get help": "https://github.com/Flature/bedrock_project",
        "Report a bug": "https://github.com/Flature/bedrock_project",
        "About": """
            베드락 Streamlit 입니다

            **GitHub**: https://github.com/Flature/bedrock_project
        """
    }
)

with st.sidebar:
    "[Get an OpenAI API key](https://platform.openai.com/account/api-keys)"
    "[View the source code](https://github.com/streamlit/llm-examples/blob/main/Chatbot.py)"
    "[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/streamlit/llm-examples?quickstart=1)"

sidebar()

# Bedrock 서비스 초기화
bedrock_service = BedrockService()

model: str = st.selectbox("Model", options=MODEL_LIST)  # type: ignore

uploaded_file = st.file_uploader(
    "Upload a pdf, docx, or txt file",
    type=["pdf", "docx", "txt"],
    help="Scanned documents are not supported yet!",
)

with st.expander("Advanced Options"):
    return_all_chunks = st.checkbox("Show all chunks retrieved from vector search")
    show_full_doc = st.checkbox("Show parsed contents of the document")


# Streamlit Title
st.title("☁️ AWS Resource Monitor")
st.caption("🚀 A Streamlit chatbot powered by Bedrock Agent")

if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "agent", "content": "How can I help you?"}]


for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# 탭 생성
tab1, tab2 = st.tabs([
    "AWS Expert Chat",
    "Etc"
])

trace_container = st.container()

# 탭 1: AWS Expert Chat
## AI전문가와의 채팅 인터페이스 추가
## 채팅 히스토리 관리
## 컨텍스트 기반 응답

with tab1:
    st.header("💬 Chat with AWS Expert")

    user_question = st.text_input("Ask anything about AWS:", key="aws_expert_input")
    submit_button = st.button("Ask Expert", key="ask_expert_button")

    if user_question and submit_button:
        # Container for real-time updates
        with st.spinner("generating reasoning"):
            try:
                response = bedrock_service.chat_with_aws_expert(user_question)
                if response:
                    trace_container.subheader("bedrock_reasoning")

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
                                    print("trace_container : ", trace_container)
                                    print("trace : ", trace)
                                    answer = json.loads(
                                        trace.get('observation', {}).get('actionGroupInvocationOutput', {}).get('text'))
                                    #trace_container.markdown(f"**Answer**")
                                    #trace_container.write(f"{answer}")

                                    function_name = ""

                                else:
                                    function_name = trace.get('invocationInput', {}).get('actionGroupInvocationInput',
                                                                                         {}).get(
                                        'function', "")
                                    print(f"function_name : {function_name}")

                            elif "guardrailTrace" in each_trace:
                                logging.log("guardrailTrace")

                trace_container.divider()
                trace_container.subheader("analysis_report")
                styled_text = re.sub(
                    r'\{([^}]+)\}',
                    r'<span style="background-color: #ffd700; padding: 2px 6px; border-radius: 3px; font-weight: bold; color: #1e1e1e;">\1</span>',
                    output_text
                )
                trace_container.markdown(styled_text, unsafe_allow_html=True)

                # 최신 응답 표시
                trace_container.divider()
                trace_container.markdown(f"**Q:** {user_question}")
                trace_container.markdown(f"**Raw:** {response}")
                trace_container.markdown(f"**A:** {output_text}")

            except Exception as e:
                trace_container.error(f"Error processing request: {str(e)}")
                print(f"Error details: {str(e)}")

# df = pd.read_csv("../data/my_data.csv")
# st.line_chart(df)

# 푸터
st.markdown("---")
st.markdown("이 Chatbot은 Streamlit과 Amazon Bedrock Claude 3.5 Sonnet을 기반으로 제작되었습니다")
