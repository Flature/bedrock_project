import pymysql
import os
import json

# 환경 변수에서 RDS 연결 정보 가져오기
RDS_HOST = os.getenv('RDS_HOST', 'hcc-mk-01-rds-data.cw1fzoksxumz.ap-northeast-2.rds.amazonaws.com')
RDS_PORT = int(os.getenv('RDS_PORT', 3306))
RDS_USER = os.getenv('RDS_USER', 'admin')
RDS_PASSWORD = os.getenv('RDS_PASSWORD', 'Guszk11!')
RDS_DB = os.getenv('RDS_DB', 'poc')


def lambda_handler(event, context):
    print(event)
    action_group = event.get('actionGroup', '')
    message_version = event.get('messageVersion', '')
    function = event.get('function', '')
    output = ''
    sql = ''

    if function in (
    'get_account_info', 'get_universe_info', 'get_etc_system_info', 'get_fault_info', 'modify_information',
    'collect_top_n'):
        print(function, 'called......')
        # output = {"answer": "현대카드는 엄청 많은 계정을 사용하고 습니다.  '099923232' 개발계, '424727373' 운영계 입니다. "}
        print("=========Lambda 함수 실행 시 RDS(MySQL)에서 데이터를 조회")
        # MySQL 연결
        connection = pymysql.connect(
            host=RDS_HOST,
            port=RDS_PORT,
            user=RDS_USER,
            password=RDS_PASSWORD,
            database=RDS_DB,
            cursorclass=pymysql.cursors.DictCursor
        )
        print("RDS연결 성공")
        with connection.cursor() as cursor:
            # 실행할 SQL 쿼리
            if function == 'get_account_info':
                sql = "select account,account_name,serivce,account_desc FROM account LIMIT 10"
            elif function == 'get_universe_info':
                sql = "select service, owner from service limit 10"
            elif function == 'get_etc_system_info':
                sql = "select service, owner from service limit 10"
            elif function == 'get_fault_info':
                sql = "select service, id, remark from service_config limit 10"
            elif function == 'collect_top_n':
                sql = "SELECT ID, USER, HOST, DB, COMMAND, TIME, STATE, INFO FROM information_schema.PROCESSLIST WHERE COMMAND != 'Sleep' ORDER BY TIME DESC LIMIT 5"
            cursor.execute(sql)
            result = cursor.fetchall()

            json_result = json.dumps(result, indent=4, ensure_ascii=False)  # 들여쓰기
            output = json_result
            print("====================+>" + output)
        connection.close()
    # elif event.get('function') == 'get_universe_info':
    #    output = {"answer": "유니버스는 현대카드에서 개발하고 운영하는 ai 시스템입니다. "}
    # elif event.get('function') == 'get_etc_system_info':
    #    output = {"answer": "gpt나 팔콘 시스템의 담당자는 Cloud개빌2팀 김아름님 입니다."}
    elif function == 'test_account_db':
        connection = pymysql.connect(
            host=RDS_HOST,
            port=RDS_PORT,
            user=RDS_USER,
            password=RDS_PASSWORD,
            database=RDS_DB,
            cursorclass=pymysql.cursors.DictCursor
        )
        with connection.cursor() as cursor:
            sql = "UPDATE service SET owner = '홍길순3' WHERE service = 'universe'"
            cursor.execute(sql)
            connection.commit()  # 변경사항 저장
            print("=========>commit")
    elif event.get('function') == 'write_sql':
        long_text = """

        각 테이블 별 역할은 아래와 같습니다.
        'account' : aws Account 정보를 관리하는 테이블
        'service' : 유니버스, 팔콘 등 현대카드에서 관리하는 시스템 정보 테이블

        테이블 스키마는 다음과 같습니다.
        CREATE TABLE `account` (
        `account` varchar(100) NOT NULL COMMENT 'Account',
        `account_name` varchar(100) NOT NULL COMMENT 'Account이름',
        `serivce` varchar(100) NOT NULL COMMENT '서비스',
        `account_desc` varchar(100) NOT NULL COMMENT 'Account설명'
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='aws Account 현황 테이블';

        CREATE TABLE `service` (
        `service` varchar(100) NOT NULL COMMENT '서비스',
        `owner` varchar(100) NOT NULL COMMENT '담당자'
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='유니버스, 팔콘 등 시스템 정보 관리 테이블';

        CREATE TABLE `service_config` (
        `service` varchar(100) NOT NULL,
        `id` varchar(50) NOT NULL,
        `remark` text,
        UNIQUE KEY `id` (`id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci comment ='리소스별 필수여부 테이블';
        CREATE TABLE `user` (
        `user_id` varchar(100) NOT NULL COMMENT '사용자ID',
        `user_name` varchar(100) NOT NULL COMMENT '사용자이름'
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='현대카드 운영 담당자 정보 테이블';
        이 스키마를 이용하여 update문을 만들어야 합니다.

        """
        print("=========테스트")
        output = {"answer": long_text}
    else:
        print("=========RDS접속 테스트")
        # result = pymysql_test()
        return {
            "statusCode": 200,
            "body": json.dumps(result)
        }

    action_response = {
        'actionGroup': action_group,
        'function': function,
        'functionResponse': {
            'responseBody': {'TEXT': {'body': json.dumps(output)}}
        }
    }

    function_response = {'response': action_response, 'messageVersion': message_version}
    print("Response: {}".format(function_response))

    return function_response


def pymysql_test():
    """Lambda 함수 실행 시 RDS(MySQL)에서 데이터를 조회"""
    print("=========Lambda 함수 실행 시 RDS(MySQL)에서 데이터를 조회")
    try:
        # MySQL 연결
        connection = pymysql.connect(
            host=RDS_HOST,
            port=RDS_PORT,
            user=RDS_USER,
            password=RDS_PASSWORD,
            database=RDS_DB,
            cursorclass=pymysql.cursors.DictCursor
        )
        print("RDS연결 성공")
        with connection.cursor() as cursor:
            # 실행할 SQL 쿼리
            if event.get('function') == 'test_account_db':
                sql = "select account,account_name,serivce,account_desc FROM account LIMIT 10;"
            cursor.execute(sql)
            result = cursor.fetchall()

            json_result = json.dumps(result, indent=4, ensure_ascii=False)  # 들여쓰기
            print("========>" + json_result)

            output = json_result

            action_response = {
                'actionGroup': action_group,
                'function': function,
                'functionResponse': {
                    'responseBody': {'TEXT': {'body': json.dumps(output)}}
                }
            }

            function_response = {'response': action_response, 'messageVersion': message_version}
            print("Response: {}".format(function_response))

            return function_response
        print("RDS연결 끝")
        # 연결 종료
        connection.close()
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }