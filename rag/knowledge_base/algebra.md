# Algebra — Formulas, Identities & Solution Templates

## 1. Quadratic Equations

### Standard Form
ax^2 + bx + c = 0

### Quadratic Formula
x = (-b ± sqrt(b^2 - 4ac)) / (2a)

### Discriminant (D)
D = b^2 - 4ac
- D > 0 → two distinct real roots
- D = 0 → one repeated real root: x = -b / (2a)
- D < 0 → two complex conjugate roots (no real roots)

### Vieta's Formulas (sum and product of roots)
If x1, x2 are roots of ax^2 + bx + c = 0:
- x1 + x2 = -b/a
- x1 * x2 = c/a

### Completing the Square
ax^2 + bx + c = a(x + b/(2a))^2 + (c - b^2/(4a))

## 2. Algebraic Identities

### Binomial Squares
(a + b)^2 = a^2 + 2ab + b^2
(a - b)^2 = a^2 - 2ab + b^2

### Difference of Squares
(a + b)(a - b) = a^2 - b^2

### Cube Identities
(a + b)^3 = a^3 + 3a^2*b + 3a*b^2 + b^3
(a - b)^3 = a^3 - 3a^2*b + 3a*b^2 - b^3

### Sum and Difference of Cubes
a^3 + b^3 = (a + b)(a^2 - ab + b^2)
a^3 - b^3 = (a - b)(a^2 + ab + b^2)

## 3. Factoring Techniques

### Greatest Common Factor (GCF)
Always extract GCF first: 6x^2 + 9x = 3x(2x + 3)

### Factoring Trinomials (a=1)
x^2 + bx + c = (x + p)(x + q) where p + q = b and p * q = c

### Factoring Trinomials (a≠1) — Split the Middle Term
ax^2 + bx + c: find p, q such that p + q = b and p * q = a*c
Then split: ax^2 + px + qx + c and factor by grouping

## 4. Systems of Equations

### Substitution Method
Solve one equation for one variable, substitute into the other.

### Elimination Method
Multiply equations to make coefficients equal, then add/subtract.

### Cramer's Rule (2x2)
For: a1*x + b1*y = c1 and a2*x + b2*y = c2
D = a1*b2 - a2*b1
x = (c1*b2 - c2*b1) / D
y = (a1*c2 - a2*c1) / D

## 5. Inequalities

### Linear Inequality Rules
- Adding/subtracting the same number: inequality sign unchanged
- Multiplying/dividing by positive number: inequality sign unchanged
- Multiplying/dividing by negative number: FLIP the inequality sign

### Absolute Value Inequalities
|x| < a  →  -a < x < a
|x| > a  →  x < -a or x > a
|x - k| < r  →  k - r < x < k + r (interval centered at k, radius r)

## 6. Arithmetic & Geometric Progressions

### AP (Arithmetic Progression)
nth term: a_n = a + (n-1)*d
Sum of n terms: S_n = n/2 * (2a + (n-1)*d) = n/2 * (a + a_n)

### GP (Geometric Progression)
nth term: a_n = a * r^(n-1)
Sum of n terms: S_n = a*(r^n - 1)/(r - 1) for r ≠ 1
Sum to infinity (|r| < 1): S = a / (1 - r)

## 7. AM-GM Inequality
For non-negative a, b:
(a + b)/2 >= sqrt(a*b)
Equality holds when a = b

For n non-negative numbers:
AM = (a1 + a2 + ... + an)/n >= (a1 * a2 * ... * an)^(1/n) = GM

## 8. Logarithm Laws
log(a*b) = log(a) + log(b)
log(a/b) = log(a) - log(b)
log(a^n) = n * log(a)
log_b(a) = log(a) / log(b)   [change of base]
log_b(b) = 1
log_b(1) = 0

## 9. Modular Arithmetic / Remainder
If a = q*b + r, then a mod b = r
Fermat's Little Theorem: a^(p-1) ≡ 1 (mod p) for prime p and gcd(a,p)=1