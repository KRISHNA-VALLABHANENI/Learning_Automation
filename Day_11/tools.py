from datetime import datetime
from langchain.tools import tool

@tool
def calculator(expression: str) -> str:
    '''
    calculates the given expression.
    use when user asks for a calculation.
    '''
    try: 
        return str(eval(expression, {'__builtins__': {}},{}))
    except ZeroDivisionError as e:
        return f'Can not divide by Zero: {e}'
    except Exception as e:
        return f'Error: {e}'


@tool
def get_datetime() -> str:
    '''
    gets the current date and time.
    use when user asks for date or time.
    '''
    return datetime.now().strftime('%d %m %y - %I %M')


