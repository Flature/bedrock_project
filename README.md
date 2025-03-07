## How to Use

### ec2 환경 설치
```commandline
sudo yum install git

sudo yum install python3.11
```

### git repository 연동
```zsh
https://github.com/Flature/bedrock_project.git
```

### 가상환경 설치
```zsh
python -m venv _bedrock-project
```

### 가상환경 활성화
```zsh
source _bedrock-project/bin/activate
```

### pip 설치
```commandline
pip install -r requirements.txt
```

### streamlit 실행
```zsh
cd ./app

streamlit run app.py --server.port 20000
```

### 테스트용 EC2 주소
```
http://13.209.16.128:20000/
```