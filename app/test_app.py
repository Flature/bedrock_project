import streamlit as st
import boto3

from bedrock_utils import BedrockService

# AWS Bedrock 클라이언트 설정
bedrock_client = boto3.client("bedrock-runtime", region_name="ap-northeast-2")

# Streamlit 세션 상태 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []

# 채팅 UI
st.title("AWS Bedrock Agent Chatbot")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

user_input = st.chat_input("Say something...")
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Bedrock API 호출 (예시 모델: Claude)
    response = bedrock_client.invoke_model(
        modelId="anthropic.claude-v2",
        body={
            "prompt": user_input,
            "max_tokens_to_sample": 200
        }
    )
    bot_response = response["body"].read().decode("utf-8")

    st.session_state.messages.append({"role": "assistant", "content": bot_response})

    # Streamlit 채팅 UI 업데이트
    with st.chat_message("assistant"):
        st.markdown(bot_response)
