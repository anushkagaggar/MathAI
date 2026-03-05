# Solution Templates — Step-by-Step Frameworks

## Template 1: Solving a Quadratic Equation

GIVEN: ax^2 + bx + c = 0

STEP 1 — Identify coefficients
  a = [value], b = [value], c = [value]

STEP 2 — Compute discriminant
  D = b^2 - 4ac = [compute]
  If D < 0: no real roots. If D = 0: one real root. If D > 0: two real roots.

STEP 3 — Apply quadratic formula
  x = (-b ± sqrt(D)) / (2a)
  x1 = (-b + sqrt(D)) / (2a)
  x2 = (-b - sqrt(D)) / (2a)

STEP 4 — Verify using Vieta's formulas
  x1 + x2 should equal -b/a
  x1 * x2 should equal c/a

STEP 5 — State final answer
  x = [x1] or x = [x2]

---

## Template 2: Finding the Derivative

GIVEN: f(x) = [expression], find f'(x)

STEP 1 — Identify the function type
  Polynomial? Use power rule.
  Product of two functions? Use product rule.
  Quotient? Use quotient rule.
  Composite function (function inside function)? Use chain rule.

STEP 2 — Apply the appropriate rule
  Power rule: d/dx[x^n] = n*x^(n-1)
  Product rule: d/dx[u*v] = u'v + uv'
  Quotient rule: d/dx[u/v] = (u'v - uv') / v^2
  Chain rule: d/dx[f(g(x))] = f'(g(x)) * g'(x)

STEP 3 — Simplify the result
  Combine like terms, factor if possible.

STEP 4 — State final answer
  f'(x) = [simplified expression]

---

## Template 3: Evaluating a Limit

GIVEN: lim x->a f(x)/g(x)

STEP 1 — Try direct substitution
  Substitute x = a. If defined → that is the answer.

STEP 2 — If result is 0/0 or ∞/∞ (indeterminate form)
  Option A: Factor numerator and denominator, cancel common factors.
  Option B: Apply L'Hopital's rule: lim f/g = lim f'/g' (differentiate top and bottom separately).
  Option C: Use standard limits table (e.g. lim sin(x)/x = 1 as x->0).

STEP 3 — Evaluate again after transformation
  Substitute the limit value into simplified expression.

STEP 4 — State final answer
  lim x->a f(x) = [value]

---

## Template 4: Probability Word Problem

GIVEN: A scenario with events A, B and their probabilities.

STEP 1 — Define the sample space
  List all possible outcomes or compute total count.

STEP 2 — Identify what is being asked
  P(A), P(A ∩ B), P(A ∪ B), P(A|B), or expected value?

STEP 3 — Check if events are independent or mutually exclusive
  Independent: P(A ∩ B) = P(A)*P(B)
  Mutually exclusive: P(A ∩ B) = 0

STEP 4 — Apply the correct formula
  Addition rule: P(A ∪ B) = P(A) + P(B) - P(A ∩ B)
  Conditional: P(A|B) = P(A ∩ B) / P(B)
  Bayes: P(A|B) = P(B|A)*P(A) / P(B)

STEP 5 — Verify answer is in [0, 1]
  If answer > 1 or < 0, recheck calculation immediately.

STEP 6 — State final answer
  P([event]) = [value]

---

## Template 5: Matrix Determinant & System of Equations

GIVEN: System of equations or matrix A

STEP 1 — Write in matrix form
  Ax = b  where A is coefficient matrix, b is constants vector.

STEP 2 — Compute det(A)
  2×2: det = ad - bc
  3×3: expand along first row using cofactors.

STEP 3 — Determine solution type
  det(A) ≠ 0 → unique solution
  det(A) = 0 → check if b is consistent (infinite or no solutions)

STEP 4 — Solve
  If unique: x = A^(-1)*b   OR use Cramer's rule: x_i = det(A_i)/det(A)
  If infinite: express in terms of free variable.

STEP 5 — Verify solution
  Substitute back into original equations to confirm LHS = RHS.

STEP 6 — State final answer
  x = [value], y = [value], z = [value]