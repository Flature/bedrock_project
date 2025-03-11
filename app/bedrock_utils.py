import json
import uuid

import boto3
import pandas as pd

# config
AGENT_ID = "VUO6QAAALP"
AGENT_ALIAS_ID = "S7ADNJZET2"


class BedrockService:
    # 클래스 초기화
    ## AWS Bedrock 서비스 클라이언트 초기화
    ## Claude 3 Sonnet 을 기본 모델로 설정 (변경 필요하면 시도해보셔도 좋습니다)

    def __init__(self):
        self.bedrock_runtime = boto3.client(
            service_name='bedrock-runtime',
            region_name='ap-northeast-2'
        )
        self.model_id = 'anthropic.claude-3-5-sonnet-20240620-v1:0'
        self.bedrock_agent = boto3.client(
            service_name='bedrock-agent-runtime',
            region_name='ap-northeast-2'
        )

    # 모델 호출
    ## Bedrock 모델 호출
    ## Prompt: 입력 텍스트
    ## max_tokens : 최대 응답 토큰 수
    ## temperature : 응답의 창의성 정도 (실험 필요시 조정하여 활용하실 수 있습니다)

    def invoke_model(self, prompt, max_tokens=1000, temperature=0.7):
        try:
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": temperature
            }

            response = self.bedrock_runtime.invoke_model(
                modelId=self.model_id,
                body=json.dumps(body)
            )

            response_body = json.loads(response['body'].read())
            return response_body['content'][0]['text']

        except Exception as e:
            print(f"Error invoking Bedrock model: {str(e)}")
            return None

    def invoke_agent(self, session_id, prompt):
        """Get a response from the Bedrock agent using specified parameters."""
        response = self.bedrock_agent.invoke_agent(
            agentId=AGENT_ID,
            agentAliasId=AGENT_ALIAS_ID,
            enableTrace=True,
            sessionId=session_id,
            inputText=prompt,
        )

        return response

    # 추천 사항 강화
    ## AWS 리소스에 대한 최적화 추천사항 제공
    ## 구체적인 행동 계획, 비용 절감 가능성, 성능 영향 등 포함
    ## DataFrame 혹은 dict 형태의 데이터 처리 가능

    def enhance_recommendations(self, resource_data):
        try:
            if isinstance(resource_data, pd.DataFrame):
                resource_data = resource_data.to_dict(orient='records')

            prompt = f"""
            다음 AWS 리소스에 대한 상세한 최적화 전략을 제공해주세요:
            {json.dumps(resource_data)}
            
            다음 내용을 포함하여 자연스러운 문장으로 작성해주세요:
    
            1. 현재 상황 분석과 문제점
            2. 구체적인 최적화 방안과 기대효과
            3. 예상되는 비용 절감 효과
            4. 구현 시 고려사항과 주의점
            5. AWS 모범 사례 기반의 권장사항
    
            기술적인 내용을 포함하되, 이해하기 쉽게 설명해주세요.
            단계별 나열이나 목록 형태를 피하고, 자연스러운 문단 형태로 작성해주세요.
            resource id를 필수로 포함해주시고, tags 등 추가 정보가 있으면 함께 활용해주세요.
            """
            return self.invoke_model(prompt, max_tokens=1000, temperature=0.7)
        except Exception as e:
            print(f"Error enhancing recommendations: {str(e)}")
            return "현재 추천 사항을 생성할 수 없습니다."

    # AWS 전문가 채팅
    ## AWS 관련 질문에 대한 전문가 수준의 응답제공
    ## 추가 컨텍스트 정보 활용
    ## 기술적이면서도 이해하기 쉬운 응답 생성

    def chat_with_aws_expert(self, user_question, context=None):
        try:
            # context가 DataFrame인 경우 dict로 변환
            if isinstance(context, pd.DataFrame):
                context = context.to_dict(orient='records')
            elif isinstance(context, dict):
                for key, value in context.items():
                    if isinstance(value, pd.DataFrame):
                        context[key] = value.to_dict(orient='records')

            prompt = f"""
            You are an AWS expert. Answer this question about AWS resources:
            Question: {user_question}
            
            Context (if available):
            {json.dumps(context) if context else 'No additional context provided'}
            
            Provide a detailed, technical, yet easy to understand response.
            """
            return self.invoke_agent(session_id=str(uuid.uuid4()), prompt=prompt)
        except Exception as e:
            print(f"Error in chat with AWS expert: {str(e)}")
            return "Unable to process your question at this time."
