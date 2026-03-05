# Common Mistakes in JEE Math — With Corrections

## Algebra Mistakes

### Mistake 1: Wrong sign in quadratic formula
WRONG: x = (-b ± sqrt(b^2 - 4ac)) / 2   [missing 'a' in denominator]
CORRECT: x = (-b ± sqrt(b^2 - 4ac)) / (2a)
Always: the full denominator is 2a, not 2.

### Mistake 2: Forgetting ± when taking square root
WRONG: x^2 = 9 → x = 3
CORRECT: x^2 = 9 → x = ±3 (both +3 and -3)

### Mistake 3: Illegal cancellation
WRONG: (x^2 + 4) / x = x + 4   [cannot cancel x with x^2]
CORRECT: (x^2 + 4) / x = x + 4/x

### Mistake 4: Cancelling across addition/subtraction
WRONG: (a + b) / a = 1 + b   [cannot cancel a in numerator]
CORRECT: (a + b) / a = 1 + b/a

### Mistake 5: Dividing both sides by a variable without checking if zero
WRONG: x*sin(x) = 3*x → sin(x) = 3   [divided by x, lost x=0 solution]
CORRECT: x*sin(x) - 3*x = 0 → x(sin(x) - 3) = 0 → x=0 or sin(x)=3 (no solution)

### Mistake 6: Incorrect factoring of difference of squares
WRONG: a^2 - b^2 = (a-b)^2
CORRECT: a^2 - b^2 = (a+b)(a-b)

### Mistake 7: Wrong expansion of (a+b)^2
WRONG: (a+b)^2 = a^2 + b^2
CORRECT: (a+b)^2 = a^2 + 2ab + b^2 (the middle term 2ab is always forgotten)

### Mistake 8: Sign error in completing the square
WRONG: x^2 - 6x = (x - 3)^2
CORRECT: x^2 - 6x = (x-3)^2 - 9  [must subtract the constant added]

## Calculus Mistakes

### Mistake 9: Forgetting chain rule
WRONG: d/dx [sin(x^2)] = cos(x^2)
CORRECT: d/dx [sin(x^2)] = cos(x^2) * 2x   [multiply by derivative of inner function]

### Mistake 10: Wrong quotient rule order
WRONG: d/dx [f/g] = (f*g' - g*f') / g^2
CORRECT: d/dx [f/g] = (f'*g - f*g') / g^2  [numerator: derivative of top times bottom MINUS top times derivative of bottom]
Memory trick: "lo d-hi minus hi d-lo over lo-lo"

### Mistake 11: Forgetting +C in indefinite integrals
WRONG: ∫ x^2 dx = x^3/3
CORRECT: ∫ x^2 dx = x^3/3 + C

### Mistake 12: Power rule for n = -1
WRONG: ∫ x^(-1) dx = x^0/0 + C   [division by zero!]
CORRECT: ∫ x^(-1) dx = ∫ 1/x dx = ln|x| + C

### Mistake 13: L'Hopital applied to non-indeterminate form
WRONG: applying L'Hopital to lim x->2 x^2/x = lim x->2 2x/1   [not 0/0 or ∞/∞!]
CORRECT: lim x->2 x^2/x = lim x->2 x = 2   [direct substitution works]

### Mistake 14: Derivative of e^(f(x)) forgetting chain rule
WRONG: d/dx [e^(x^2)] = e^(x^2)
CORRECT: d/dx [e^(x^2)] = e^(x^2) * 2x

## Probability Mistakes

### Mistake 15: Adding probabilities without subtracting intersection
WRONG: P(A or B) = P(A) + P(B)   [only correct if mutually exclusive]
CORRECT: P(A ∪ B) = P(A) + P(B) - P(A ∩ B)

### Mistake 16: Treating dependent events as independent
WRONG: Drawing 2 cards without replacement: P(both aces) = (4/52)*(4/52)
CORRECT: P(both aces) = (4/52)*(3/51)   [after 1st ace, only 3 aces remain in 51 cards]

### Mistake 17: Probability greater than 1 or less than 0
Any answer with P(event) > 1 or P(event) < 0 is ALWAYS wrong.
Probabilities are always in [0, 1].

### Mistake 18: Confusing nPr and nCr
Use nPr when ORDER MATTERS (arrangements, sequences)
Use nCr when ORDER DOES NOT MATTER (selections, committees)
nPr = n!/(n-r)!  is ALWAYS >= nCr = n!/(r!(n-r)!)

## Linear Algebra Mistakes

### Mistake 19: Matrix multiplication order
WRONG: (AB)^(-1) = A^(-1) * B^(-1)
CORRECT: (AB)^(-1) = B^(-1) * A^(-1)  [order reverses]

### Mistake 20: Assuming AB = BA
Matrix multiplication is NOT commutative in general.
AB ≠ BA for most matrices A, B.