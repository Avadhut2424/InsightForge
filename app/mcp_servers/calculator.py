import simpleeval
from typing import Dict, Any

def calculate(expression: str) -> Dict[str, Any]:
    try:
        s = simpleeval.SimpleEval()
        s.functions = {}
        s.names = {}
        result = s.eval(expression)
        return {"success": True, "data": {"result": float(result), "expression": expression}}
    except simpleeval.InvalidExpression as e:
        return {"success": False, "error": {"type": "invalid_expression", "detail": "The provided expression is invalid or malformed."}}
    except simpleeval.FunctionNotDefined as e:
        return {"success": False, "error": {"type": "unsafe_evaluation", "detail": "Functions are not allowed."}}
    except simpleeval.NameNotDefined as e:
        return {"success": False, "error": {"type": "unsafe_evaluation", "detail": "Variables/names are not allowed."}}
    except simpleeval.FeatureNotAvailable as e:
        return {"success": False, "error": {"type": "unsafe_evaluation", "detail": "This language feature is not allowed."}}
    except Exception as e:
        return {"success": False, "error": {"type": "evaluation_error", "detail": str(e)}}
