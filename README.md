## How to Use

### ec2 환경 설치
```commandline
sudo yum install git

sudo yum install python3.11
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