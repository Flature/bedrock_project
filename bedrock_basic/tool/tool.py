import boto3
import yfinance as yf
import sys

# 라이브러리를 사용하여 주식 가격을 가져오는 함수를 정의
# 이 함수는 주어진 티커 심볼의 주식 데이터를 가져오고, 가장 최근의 종가와 날짜를 반환
def get_stock_price(ticker):
    stock_data = yf.Ticker(ticker)
    historical_data = stock_data.history(period='1d')

    date = historical_data.index[0].strftime('%Y-%m-%d')
    current_price = historical_data['Close'].iloc[0]
    return f"{ticker} 종가는 {date} 기준 {current_price:.2f}입니다"

# 주식 가격을 가져오는 도구를 정의
# 이 도구는 주식의 티커심볼을 입력으로 받아 현재 가격을 반환
tool_config = {
    "tools": [
        {
            "toolSpec": {
                "name": "get_stock_price",
                "description": "주어진 ticker의 현재 주식 가격을 가져옵니다.",
                "inputSchema": {
                    "json": {
                        "type": "object",
                        "properties": {
                            "ticker": {
                                "type": "string",
                                "description": "주식의 ticker"
                            }
                        },
                        "required": [
                            "ticker"
                        ]
                    }
                }
            }
        }
    ]
}

# Converse API를 호출하여 도구 구성과 함께 주식 가격 정보를 요청
def get_response(user_question):
    session = boto3.Session()
    bedrock = session.client(service_name='bedrock-runtime')

    response = bedrock.converse(
        modelId='anthropic.claude-3-5-sonnet-20240620-v1:0',
        messages=[{"role": "user", "content": [{"text": user_question}]}],
        toolConfig=tool_config
    )
    return response


# API 응답을 처리하여 주식 가격 정보를 출력
# 응답에서 도구 사용 요청을 확인하고 LLM이 제공한 티커를 사용하여 주식 가격을 가져옴
def handle_tool_use(response):
    if response.get('stopReason') == 'tool_use':
        tool_requests = response['output']['message']['content']
        for tool_request in tool_requests:
            if 'toolUse' in tool_request:
                tool_use = tool_request['toolUse']
                print(f"Bedrock Response : {tool_request}")

                if tool_use['name'] == 'get_stock_price':
                    ticker = tool_use['input']['ticker']
                    return get_stock_price(ticker)

    return response['output']['message']['content'][0]['text']

# 실제 코드 실행 부분
user_question = sys.argv[1]
response = get_response(user_question)
result = handle_tool_use(response)
print(result)

# cd ~/workshop/bedrock_basic_workshop/practice/tool
# python tool.py "아마존의 현재 주식 가격이 얼마인가요?"