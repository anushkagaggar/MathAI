import re
from utils.logger import get_logger

logger = get_logger(__name__)


def _safe_parse(expr_str: str, symbols_dict: dict):
    """Safely parse expression using sympify with declared symbols."""
    import sympy
    import re
    try:
        # Replace ^ with ** for SymPy compatibility FIRST
        expr_str = expr_str.replace("^", "**")
        # Fix implicit multiplication: 5x → 5*x
        # Must NOT touch x**2 (digit after ** is the exponent, not multiplication)
        expr_str = re.sub(r'(\d)([a-zA-Z])', r'\1*\2', expr_str)
        return sympy.sympify(expr_str, locals=symbols_dict)
    except Exception as e:
        raise ValueError(f"Cannot parse expression '{expr_str}': {e}")


def solve_equation(problem_text: str) -> dict:
    """
    Attempts to extract and solve an equation from problem_text.
    Handles: single variable equations, systems of 2 equations.
    Returns: {success, result, symbolic, error}
    """
    import sympy

    try:
        # Strip leading instruction words before any parsing
        text = re.sub(
            r'^\s*(solve|find|compute|evaluate|simplify|factorise|factorize|expand|calculate)\s+',
            '', problem_text, flags=re.IGNORECASE
        ).strip()
        # Normalize
        text = text.replace("^", "**")

        # Detect variables mentioned
        var_matches = re.findall(r'\b([a-zA-Z])\b', text)
        # Filter out common non-variable words
        reserved = {"e", "i", "E", "I"}
        vars_found = [v for v in dict.fromkeys(var_matches) if v not in reserved][:3]

        if not vars_found:
            return {"success": False, "result": "", "symbolic": [], "error": "No variables found in problem"}

        symbols = {v: sympy.Symbol(v) for v in vars_found}
        primary_var = list(symbols.values())[0]

        # Try to extract equation(s) — look for = sign
        equations = []
        parts = re.split(r';|and', text, flags=re.IGNORECASE)

        for part in parts:
            part = part.strip()
            if "=" in part:
                lhs_str, rhs_str = part.split("=", 1)
                lhs = _safe_parse(lhs_str.strip(), symbols)
                rhs = _safe_parse(rhs_str.strip(), symbols)
                equations.append(sympy.Eq(lhs, rhs))
            elif part:
                # Assume expression = 0
                expr = _safe_parse(part, symbols)
                equations.append(sympy.Eq(expr, 0))

        if not equations:
            return {"success": False, "result": "", "symbolic": [], "error": "No equations found"}

        if len(equations) == 1:
            solution = sympy.solve(equations[0], primary_var)
        else:
            solve_vars = list(symbols.values())[:len(equations)]
            solution = sympy.solve(equations, solve_vars)

        solution_str = str(solution)
        logger.info("SymPy solved equation. Variable: %s, Solutions: %s", primary_var, solution_str)

        return {
            "success": True,
            "result": solution_str,
            "symbolic": [str(s) for s in solution] if isinstance(solution, list) else [solution_str],
            "error": ""
        }

    except Exception as e:
        logger.warning("SymPy solve_equation failed: %s", str(e))
        return {"success": False, "result": "", "symbolic": [], "error": str(e)}


def differentiate(expression: str, variable: str = "x", order: int = 1) -> dict:
    """
    Differentiates expression with respect to variable.
    Returns: {success, result, simplified, error}
    """
    import sympy

    try:
        sym = sympy.Symbol(variable)
        expr = _safe_parse(expression, {variable: sym})
        derivative = sympy.diff(expr, sym, order)
        simplified = sympy.simplify(derivative)

        logger.info("SymPy differentiated: d^%d/d%s^%d [%s] = %s", order, variable, order, expression[:40], str(simplified))

        return {
            "success": True,
            "result": str(derivative),
            "simplified": str(simplified),
            "error": ""
        }

    except Exception as e:
        logger.warning("SymPy differentiate failed: %s", str(e))
        return {"success": False, "result": "", "simplified": "", "error": str(e)}


def evaluate_limit(expression: str, variable: str = "x", point: str = "0") -> dict:
    """
    Evaluates limit of expression as variable -> point.
    Returns: {success, result, error}
    """
    import sympy

    try:
        sym = sympy.Symbol(variable)

        # Handle special limit points
        point_clean = point.strip()
        if point_clean in ("oo", "inf", "infinity", "+inf"):
            limit_point = sympy.oo
        elif point_clean in ("-oo", "-inf", "-infinity"):
            limit_point = -sympy.oo
        else:
            limit_point = _safe_parse(point_clean, {variable: sym})

        expr = _safe_parse(expression, {variable: sym})
        result = sympy.limit(expr, sym, limit_point)

        logger.info("SymPy limit: lim %s->%s [%s] = %s", variable, point, expression[:40], str(result))

        return {"success": True, "result": str(result), "error": ""}

    except Exception as e:
        logger.warning("SymPy evaluate_limit failed: %s", str(e))
        return {"success": False, "result": "", "error": str(e)}


def integrate_expression(expression: str, variable: str = "x") -> dict:
    """
    Computes indefinite integral of expression.
    Returns: {success, result, error}
    """
    import sympy

    try:
        sym = sympy.Symbol(variable)
        expr = _safe_parse(expression, {variable: sym})
        result = sympy.integrate(expr, sym)

        result_str = str(result) + " + C"
        logger.info("SymPy integrated: ∫[%s]d%s = %s", expression[:40], variable, result_str)

        return {"success": True, "result": result_str, "error": ""}

    except Exception as e:
        logger.warning("SymPy integrate_expression failed: %s", str(e))
        return {"success": False, "result": "", "error": str(e)}


def compute_matrix_det(matrix_list: list) -> dict:
    """
    Computes determinant of a matrix.
    matrix_list: list of lists, e.g. [[1,2],[3,4]]
    Returns: {success, result, error}
    """
    import sympy

    try:
        mat = sympy.Matrix(matrix_list)
        det = mat.det()
        logger.info("SymPy matrix det computed: %s", str(det))
        return {"success": True, "result": str(det), "error": ""}

    except Exception as e:
        logger.warning("SymPy compute_matrix_det failed: %s", str(e))
        return {"success": False, "result": "", "error": str(e)}


def dispatch(topic: str, problem_text: str, parsed_problem: dict) -> dict:
    """
    Master dispatcher — called by Solver Agent.
    Routes to correct SymPy function based on topic and problem content.
    Always returns {success, result, error}.
    """
    text_lower = problem_text.lower()

    # Probability: SymPy not used — pure LLM
    if topic == "probability":
        logger.debug("SymPy dispatch: probability topic — skipping SymPy")
        return {"success": False, "result": "", "error": "SymPy not used for probability"}

    # Calculus: detect operation type
    if topic == "calculus":
        if any(kw in text_lower for kw in ["differentiate", "derivative", "d/dx", "dy/dx", "diff"]):
            var = parsed_problem.get("variables", ["x"])[0] if parsed_problem.get("variables") else "x"
            # Extract expression — everything after key phrases
            expr = re.sub(r'(find|compute|differentiate|derivative of|d/dx of|dy/dx of)\s*', '', problem_text, flags=re.IGNORECASE).strip()
            expr = re.sub(r'\s+with respect to \w+', '', expr, flags=re.IGNORECASE).strip()
            return differentiate(expr, variable=var)

        elif any(kw in text_lower for kw in ["integrate", "integral", "antiderivative"]):
            var = parsed_problem.get("variables", ["x"])[0] if parsed_problem.get("variables") else "x"
            expr = re.sub(r'(find|compute|integrate|integral of|antiderivative of)\s*', '', problem_text, flags=re.IGNORECASE).strip()
            return integrate_expression(expr, variable=var)

        elif any(kw in text_lower for kw in ["limit", "lim", "approaches"]):
            # Try to extract variable and point from problem text
            var_match = re.search(r'as\s+([a-zA-Z])\s*(->|approaches|tends to)\s*([\w\+\-\.]+)', text_lower)
            variable = var_match.group(1) if var_match else "x"
            point = var_match.group(3) if var_match else "0"
            expr = re.sub(r'(find|compute|evaluate|limit of|lim)\s*', '', problem_text, flags=re.IGNORECASE).strip()
            expr = re.sub(r'as\s+\w+\s*(->|approaches|tends to)\s*[\w\+\-\.]+', '', expr, flags=re.IGNORECASE).strip()
            return evaluate_limit(expr, variable=variable, point=point)

        else:
            # Fallback: try to solve as equation
            return solve_equation(problem_text)

    # Linear algebra: matrix operations
    if topic == "linear_algebra":
        if any(kw in text_lower for kw in ["determinant", "det"]):
            # Cannot reliably parse matrix from free text — return not available
            return {"success": False, "result": "", "error": "Matrix parsing from free text not supported — using LLM"}
        else:
            return solve_equation(problem_text)

    # Algebra: solve equations
    if topic == "algebra":
        # Strip common instruction words so SymPy only sees the equation
        equation_text = re.sub(
            r'^\s*(solve|find|compute|evaluate|simplify|factorise|factorize|expand)\s+',
            '', problem_text, flags=re.IGNORECASE
        ).strip()
        return solve_equation(equation_text)

    # Unknown: attempt solve after stripping instruction words
    logger.warning("SymPy dispatch: unknown topic '%s' — attempting solve_equation", topic)
    equation_text = re.sub(
        r'^\s*(solve|find|compute|evaluate|simplify)\s+',
        '', problem_text, flags=re.IGNORECASE
    ).strip()
    return solve_equation(equation_text)