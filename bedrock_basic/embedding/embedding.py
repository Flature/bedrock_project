import json
import boto3
import sys
from numpy import dot
from numpy.linalg import norm

# Amazon Titan Embeddings 모델을 사용하여
# 주어진 텍스트에 대한 임베딩 벡터를 생성하는 함수를 추가
def get_embedding(text):
    session = boto3.Session()
    bedrock = session.client(service_name='bedrock-runtime')

    response = bedrock.invoke_model(
        body=json.dumps({"inputText": text}),
        modelId="amazon.titan-embed-text-v2:0",
        accept="application/json",
        contentType="application/json"
    )

    response_body = json.loads(response['body'].read())
    return response_body['embedding']

# 텍스트와 해당 텍스트의 임베딩 벡터를 저장하는 EmbedItem 클래스와
# 텍스트와 다른 텍스트와의 유사도 점수를 저장하는 클래스를 정의
class EmbedItem:
    def __init__(self, text):
        self.text = text
        self.embedding = get_embedding(text)

class ComparisonResult:
    def __init__(self, text, similarity):
        self.text = text
        self.similarity = similarity

# 두 벡터의 유사도를 비교하는 함수
def calculate_similarity(a, b):
    return dot(a, b) / (norm(a) * norm(b))

# items.txt 파일에서 텍스트 목록을 읽어와 EmbedItem 리스트 생성
with open("items.txt", "r") as f:
    text_items = f.read().splitlines()

items = []
for text in text_items:
    items.append(EmbedItem(text))

# 시스템 인수로 주어진 텍스트에 대한 EmbedItem 객체를 생성
# 이 EmbedItem과 items 리스트의 각 EmbedItem간 유사도를 계산하여 ComparisionResult 객체 리스트 생성
input_item = EmbedItem(sys.argv[1])

print(f"유사도 정렬 : '{input_item.text}'")
print("----------------")
cosine_comparisons = []

for item in items:
    similarity_score = calculate_similarity(input_item.embedding, item.embedding)

    cosine_comparisons.append(ComparisonResult(item.text, similarity_score))  # save the comparisons to a list

cosine_comparisons.sort(key=lambda x: x.similarity, reverse=True)  # list the closest matches first

for c in cosine_comparisons:
    print("%.6f" % c.similarity, "\t", c.text)



# python embedding.py "과일 가게로 가는 길을 알려주세요."