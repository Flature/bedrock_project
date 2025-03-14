import json
import logging
import uuid

import streamlit as st
import pandas as pd

from aws_services import AWSResourceCollector
from bedrock_utils import BedrockService
import re

# 디버그 모드 설정
DEBUG = True


def debug_print(message):
    if DEBUG:
        print(f"DEBUG test: {message}")


# Bedrock 서비스 초기화
bedrock_service = BedrockService()


@st.cache_data(ttl=300)
def fetch_aws_resources():
    debug_print("Fetching AWS resources...")
    collector = AWSResourceCollector()
    resources = collector.collect_all_resources()
    return resources


def debug_print(message):
    if DEBUG:
        print(f"DEBUG: {message}")


# 제목
st.title("☁️ Meerkat Project")

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
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if "session_id" not in st.session_state:
        st.session_state.session_id = None

    st.header("💬 Chat with AWS Expert")

    user_question = st.text_input("Ask anything about AWS:", key="aws_expert_input")
    submit_button = st.button("Ask Expert", key="ask_expert_button")

    if user_question and submit_button:
        # Container for real-time updates
        with st.spinner("generating reasoning"):
            try:
                sessionId = st.session_state.session_id or str(uuid.uuid4())
                print(f"session id : {sessionId}")
                response = bedrock_service.chat_with_aws_expert(user_question=user_question, session_id=sessionId)

                if response:
                    session_id = response.get("sessionId")
                    if session_id:
                        st.session_state.session_id = session_id

                    trace_container.subheader("bedrock_reasoning")

                    output_text = ""
                    function_name = ""

                    for event in response.get("completion"):
                        if "chunk" in event:
                            print("chunk called")
                            chunk = event["chunk"]
                            output_text += chunk["bytes"].decode()

                        if "trace" in event:
                            print("trace called")
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
                                    # trace_container.markdown(f"**Answer**")
                                    # trace_container.write(f"{answer}")

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
                trace_container.markdown(f"**A:** {output_text}")
                trace_container.markdown("---")

                st.session_state.chat_history.append({
                    "question": user_question,
                    "answer": output_text
                })

                if st.session_state.chat_history:
                    trace_container.subheader("Previous Conversations")
                    for chat in reversed(st.session_state.chat_history[:-1]):  # 최신 응답 제외
                        trace_container.markdown(f"**Q:** {chat['question']}")
                        trace_container.markdown(f"**A:** {chat['answer']}")
                        trace_container.markdown("---")

            except Exception as e:
                trace_container.error(f"Error processing request: {str(e)}")
                debug_print(f"Error details: {str(e)}")

# df = pd.read_csv("../data/my_data.csv")
# st.line_chart(df)

# 푸터
st.markdown("---")
st.markdown("이 Chatbot은 Streamlit과 Amazon Bedrock Claude 3.5 Sonnet을 기반으로 제작되었습니다")
