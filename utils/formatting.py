import re


def normalize_math_text(text: str) -> str:
    """
    Converts spoken/OCR math phrases into standard math notation.
    Handles common ASR and OCR artifacts.
    """
    if not text:
        return text

    t = text

    # ── Exponents & powers ─────────────────────────────────────────
    t = re.sub(r'\bsquared\b', '^2', t, flags=re.IGNORECASE)
    t = re.sub(r'\bcubed\b', '^3', t, flags=re.IGNORECASE)
    t = re.sub(r'\braised\s+to\s+the\s+power\s+of\s+(\w+)', r'^\1', t, flags=re.IGNORECASE)
    t = re.sub(r'\braised\s+to\s+(\w+)', r'^\1', t, flags=re.IGNORECASE)
    t = re.sub(r'\bto\s+the\s+power\s+of\s+(\w+)', r'^\1', t, flags=re.IGNORECASE)
    t = re.sub(r'\bto\s+the\s+(\w+)\s+power\b', r'^\1', t, flags=re.IGNORECASE)
    t = re.sub(r'\bx\s+square\b', 'x^2', t, flags=re.IGNORECASE)

    # ── Roots ──────────────────────────────────────────────────────
    t = re.sub(r'\bsquare\s+root\s+of\s+([a-zA-Z0-9\(\)]+)', r'sqrt(\1)', t, flags=re.IGNORECASE)
    t = re.sub(r'\bsqrt\s+of\s+([a-zA-Z0-9\(\)]+)', r'sqrt(\1)', t, flags=re.IGNORECASE)
    t = re.sub(r'\bcube\s+root\s+of\s+([a-zA-Z0-9\(\)]+)', r'cbrt(\1)', t, flags=re.IGNORECASE)

    # ── Arithmetic operators ────────────────────────────────────────
    t = re.sub(r'\btimes\b', '*', t, flags=re.IGNORECASE)
    t = re.sub(r'\bmultiplied\s+by\b', '*', t, flags=re.IGNORECASE)
    t = re.sub(r'\bdivided\s+by\b', '/', t, flags=re.IGNORECASE)
    t = re.sub(r'\bover\b', '/', t, flags=re.IGNORECASE)
    t = re.sub(r'\bplus\b', '+', t, flags=re.IGNORECASE)
    t = re.sub(r'\bminus\b', '-', t, flags=re.IGNORECASE)
    t = re.sub(r'\bequals\b', '=', t, flags=re.IGNORECASE)
    t = re.sub(r'\bequal\s+to\b', '=', t, flags=re.IGNORECASE)

    # ── Calculus ───────────────────────────────────────────────────
    t = re.sub(r'\bdy\s+by\s+dx\b', 'dy/dx', t, flags=re.IGNORECASE)
    t = re.sub(r'\bd\s+by\s+dx\b', 'd/dx', t, flags=re.IGNORECASE)
    t = re.sub(r'\bderivative\s+of\b', 'd/dx', t, flags=re.IGNORECASE)
    t = re.sub(r'\bintegral\s+of\b', 'integral', t, flags=re.IGNORECASE)
    t = re.sub(r'\bwith\s+respect\s+to\s+x\b', 'dx', t, flags=re.IGNORECASE)
    t = re.sub(r'\blim\s+as\s+x\s+approaches\b', 'lim x->', t, flags=re.IGNORECASE)

    # ── Constants & symbols ────────────────────────────────────────
    t = re.sub(r'\bpi\b', 'π', t, flags=re.IGNORECASE)
    t = re.sub(r'\binfinity\b', '∞', t, flags=re.IGNORECASE)
    t = re.sub(r'\btheta\b', 'θ', t, flags=re.IGNORECASE)
    t = re.sub(r'\balpha\b', 'α', t, flags=re.IGNORECASE)
    t = re.sub(r'\bbeta\b', 'β', t, flags=re.IGNORECASE)
    t = re.sub(r'\bdelta\b', 'δ', t, flags=re.IGNORECASE)
    t = re.sub(r'\blambda\b', 'λ', t, flags=re.IGNORECASE)
    t = re.sub(r'\bsigma\b', 'σ', t, flags=re.IGNORECASE)

    # ── Curly / smart quotes → straight ───────────────────────────
    t = t.replace('\u2018', "'").replace('\u2019', "'")
    t = t.replace('\u201c', '"').replace('\u201d', '"')

    # ── OCR line-break artifacts ───────────────────────────────────
    t = re.sub(r'(\w)-\n(\w)', r'\1\2', t)  # hyphenated word across line
    t = re.sub(r'\n+', ' ', t)              # newlines to space

    # ── Superscript digits (OCR artifact) ─────────────────────────
    superscripts = {'²': '^2', '³': '^3', '¹': '^1', '⁴': '^4', '⁵': '^5'}
    for sup, repl in superscripts.items():
        t = t.replace(sup, repl)

    return t.strip()


def clean_whitespace(text: str) -> str:
    """
    Collapses multiple spaces, strips leading/trailing whitespace,
    removes null bytes and other control characters.
    """
    if not text:
        return text

    # Remove null bytes and control chars (except newline/tab)
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)

    # Collapse multiple spaces
    text = re.sub(r'[ \t]+', ' ', text)

    # Collapse multiple newlines
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()