import json

import streamlit as st
import pandas as pd

from aws_services import AWSResourceCollector
from bedrock_utils import BedrockService

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
st.title("☁️ AWS Resource Monitor")

# 탭 생성
tab1, tab2 = st.tabs([
    "AWS Expert Chat",
    "Etc"
])

# 탭 1: AWS Expert Chat
## AI전문가와의 채팅 인터페이스 추가
## 채팅 히스토리 관리
## 컨텍스트 기반 응답

with tab1:
    st.header("💬 Chat with AWS Expert")

    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

    user_question = st.text_input("Ask anything about AWS:", key="aws_expert_input")

    if st.button("Ask Expert", key="ask_expert_button"):
        if user_question:
            try:
                # DataFrame을 dict로 변환
                resources_df = fetch_aws_resources()

                context = {
                    'resources': resources_df.to_dict(orient='records') if not resources_df.empty else []
                }

                # 컨텍스트 데이터 로깅
                debug_print(f"Context data structure: {json.dumps(context, indent=2)}")

                response = bedrock_service.chat_with_aws_expert(user_question, context)

                if response:
                    st.session_state.chat_history.append({
                        "question": user_question,
                        "answer": response
                    })

                    # 최신 응답 표시
                    st.markdown(f"**Q:** {user_question}")
                    st.markdown(f"**A:** {response}")
                    st.markdown("---")
                else:
                    st.error("Failed to get response from AWS Expert")

            except Exception as e:
                st.error(f"Error processing request: {str(e)}")
                debug_print(f"Error details: {str(e)}")
        else:
            st.warning("Please enter a question first.")

    # 이전 채팅 히스토리 표시
    if st.session_state.chat_history:
        st.subheader("Previous Conversations")
        for chat in reversed(st.session_state.chat_history[:-1]):  # 최신 응답 제외
            st.markdown(f"**Q:** {chat['question']}")
            st.markdown(f"**A:** {chat['answer']}")
            st.markdown("---")

df = pd.read_csv("../data/my_data.csv")
st.line_chart(df)

# 푸터
st.markdown("---")
st.markdown("이 Chatbot은 Streamlit과 Amazon Bedrock Claude 3.5 Sonnet을 기반으로 제작되었습니다")
