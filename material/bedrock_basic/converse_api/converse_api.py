import boto3
import json
import sys


# 스트리밍된 텍스트 조각을 출력하는 함수를 정의
# 스트림에서 받은 텍스트 조각을 실시간으로 처리하는 역할
def chunk_handler(chunk):
    print(chunk, end='')


# 주어진 프롬프트에 대해 스트리밍 응답을 가져오고,
# 텍스트 조각을 출력하는 함수
# 또한, 응답의 메타데이터에서 사용량 및 메트릭 정보를 출력
def get_streaming_response(prompt, model_id, streaming_callback):
    session = boto3.Session()
    bedrock = session.client(service_name='bedrock-runtime')

    message = {
        "role": "user",
        "content": [{"text": prompt}]
    }

    response = bedrock.converse_stream(
        modelId=model_id,
        messages=[message],
        inferenceConfig={
            "maxTokens": 2000,
            "temperature": 0.0
        }
    )

    print("---- Streaming Response ----")
    stream = response.get('stream')
    for event in stream:
        if "contentBlockDelta" in event:
            streaming_callback(event['contentBlockDelta']['delta']['text'])

        if "metadata" in event:
            print("\n\n---- usage ----")
            print(json.dumps(event['metadata']['usage'], indent=4))
            print("\n---- metrics ----")
            print(json.dumps(event['metadata']['metrics'], indent=4))


# 실제 함수 호출 코드
get_streaming_response(sys.argv[1], sys.argv[2], chunk_handler)

# cd ~/workshop/bedrock_basic_workshop/practice/converse_api
# python converse_api.py "대한민국에 섬은 총 몇개인가요?" "anthropic.claude-3-5-sonnet-20240620-v1:0"
# python converse_api.py "대한민국에 섬은 총 몇개인가요?" "amazon.titan-text-express-v1"
