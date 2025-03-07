import json
import yfinance as yf
from datetime import datetime, timedelta


def get_named_parameter(event, name):
    # Get the value of a specific parameter from the Lambda event
    for param in event['parameters']:
        if param['name'] == name:
            return param['value']
    return None


def get_today():
    today = datetime.today().date()
    return today.strftime('%Y-%m-%d')


def get_company_profile(ticker):
    company = yf.Ticker(ticker)
    info = company.info

    # Combine address information
    address_parts = []
    if info.get('address1'):
        address_parts.append(info.get('address1'))
    if info.get('address2'):
        address_parts.append(info.get('address2'))
    if info.get('city'):
        address_parts.append(info.get('city'))
    if info.get('state'):
        address_parts.append(info.get('state'))
    if info.get('zip'):
        address_parts.append(info.get('zip'))
    if info.get('country'):
        address_parts.append(info.get('country'))

    phone = info.get('phone', '')
    if phone:
        phone = phone.replace(' ', '-')

    # Combine Industry and Sector information
    industry_sector = ' / '.join(filter(None, [info.get('industry', ''), info.get('sector', '')]))

    # Get CEO information (name of the first person only)
    ceo = info.get('companyOfficers', [{}])[0].get('name', '')

    return {
        'Industry Sector': industry_sector,
        'Address': ', '.join(filter(None, address_parts)),
        'Phone': phone,
        'CEO': ceo
    }


def get_stock_chart(ticker):
    # Get historical stock price information through the yfinance package
    today = datetime.today().date()
    start_date = today - timedelta(days=300)

    stock = yf.Ticker(ticker)
    data = stock.history(start=start_date, end=today)

    output = {}
    for index, row in data.iterrows():
        output[index.strftime('%Y-%m-%d')] = {
            'Open': round(row['Open'], 2),
            'High': round(row['High'], 2),
            'Low': round(row['Low'], 2),
            'Close': round(row['Close'], 2)
        }

    return output


def get_stock_balance(ticker):
    # Get financial statements for the last 3 years through the yfinance package
    company = yf.Ticker(ticker)
    balance = company.quarterly_balance_sheet
    if balance.shape[1] >= 3:
        balance = balance.iloc[:, :3]
    balance = balance.dropna(how="any")

    output = {}
    for col in balance.columns:
        output_date = {}
        for item, value in balance[col].items():
            output_date.update({
                item: value
            })
        output.update({col.strftime('%Y-%m-%d'): output_date})

    return output


def get_recommendations(ticker):
    # Get analyst recommendations through the yfinance package
    stock = yf.Ticker(ticker)
    recommendations = stock.recommendations

    output = {}
    for index, row in recommendations.iterrows():
        output.update({
            row['period']: {
                'strongBuy': row['strongBuy'],
                'buy': row['buy'],
                'hold': row['hold'],
                'sell': row['sell'],
                'strongSell': row['strongSell'],

            }
        })
    return output


def lambda_handler(event, context):
    action_group = event.get('actionGroup', '')
    message_version = event.get('messageVersion', '')
    function = event.get('function', '')

    if function == 'get_today':
        output = get_today()

    elif function == 'get_company_profile':
        ticker = get_named_parameter(event, "ticker")
        output = get_company_profile(ticker)

    elif function == 'get_stock_chart':
        ticker = get_named_parameter(event, "ticker")
        output = get_stock_chart(ticker)

    elif function == 'get_stock_balance':
        ticker = get_named_parameter(event, "ticker")
        output = get_stock_balance(ticker)

    elif function == 'get_recommendations':
        ticker = get_named_parameter(event, "ticker")
        output = get_recommendations(ticker)

    else:
        output = 'Invalid function'

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