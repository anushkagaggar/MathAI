# Calculus — Limits, Derivatives & Basic Integration

## 1. Limits

### Direct Substitution
lim x->a f(x) = f(a) if f is continuous at a

### Common Limit Indeterminate Forms
0/0, ∞/∞, 0*∞, ∞-∞, 0^0, 1^∞, ∞^0

### Standard Limits
lim x->0 sin(x)/x = 1
lim x->0 (1 - cos(x))/x = 0
lim x->0 (e^x - 1)/x = 1
lim x->0 (1 + x)^(1/x) = e
lim x->∞ (1 + 1/x)^x = e
lim x->0 ln(1+x)/x = 1

### Factoring Technique (0/0 form)
lim x->2 (x^2 - 4)/(x - 2) = lim x->2 (x+2)(x-2)/(x-2) = lim x->2 (x+2) = 4

### L'Hopital's Rule (0/0 or ∞/∞ form)
lim x->a f(x)/g(x) = lim x->a f'(x)/g'(x)

### Squeeze Theorem
If g(x) <= f(x) <= h(x) near a, and lim g(x) = lim h(x) = L, then lim f(x) = L

## 2. Derivatives — Definition
f'(x) = lim h->0 [f(x+h) - f(x)] / h

## 3. Differentiation Rules

### Power Rule
d/dx [x^n] = n * x^(n-1)

### Constant Rule
d/dx [c] = 0

### Sum/Difference Rule
d/dx [f ± g] = f' ± g'

### Product Rule
d/dx [f * g] = f'*g + f*g'

### Quotient Rule
d/dx [f/g] = (f'*g - f*g') / g^2

### Chain Rule
d/dx [f(g(x))] = f'(g(x)) * g'(x)

## 4. Standard Derivatives Table
d/dx [x^n]      = n*x^(n-1)
d/dx [e^x]      = e^x
d/dx [a^x]      = a^x * ln(a)
d/dx [ln(x)]    = 1/x
d/dx [log_a(x)] = 1 / (x * ln(a))
d/dx [sin(x)]   = cos(x)
d/dx [cos(x)]   = -sin(x)
d/dx [tan(x)]   = sec^2(x)
d/dx [cot(x)]   = -csc^2(x)
d/dx [sec(x)]   = sec(x)*tan(x)
d/dx [csc(x)]   = -csc(x)*cot(x)
d/dx [arcsin(x)] = 1/sqrt(1-x^2)
d/dx [arccos(x)] = -1/sqrt(1-x^2)
d/dx [arctan(x)] = 1/(1+x^2)
d/dx [sqrt(x)]  = 1/(2*sqrt(x))

## 5. Higher Order Derivatives
f''(x) = d^2f/dx^2 = second derivative
f'''(x) = d^3f/dx^3 = third derivative

## 6. Optimization Using Derivatives

### Finding Critical Points
Step 1: Find f'(x)
Step 2: Set f'(x) = 0, solve for x → critical points
Step 3: Check endpoints if on a closed interval

### Second Derivative Test
f''(x) > 0 at critical point → local minimum
f''(x) < 0 at critical point → local maximum
f''(x) = 0 → inconclusive (use first derivative test)

### First Derivative Test
f'(x) changes + to - → local maximum
f'(x) changes - to + → local minimum

## 7. Integration (Anti-differentiation)

### Power Rule for Integration
∫ x^n dx = x^(n+1)/(n+1) + C,  n ≠ -1
∫ x^(-1) dx = ln|x| + C

### Standard Integrals
∫ e^x dx       = e^x + C
∫ a^x dx       = a^x / ln(a) + C
∫ sin(x) dx    = -cos(x) + C
∫ cos(x) dx    = sin(x) + C
∫ sec^2(x) dx  = tan(x) + C
∫ 1/(1+x^2) dx = arctan(x) + C
∫ 1/sqrt(1-x^2) dx = arcsin(x) + C
∫ ln(x) dx     = x*ln(x) - x + C

### Substitution Method (u-substitution)
Let u = g(x), then du = g'(x)dx
∫ f(g(x))*g'(x) dx = ∫ f(u) du

### Definite Integral (Fundamental Theorem of Calculus)
∫_a^b f(x) dx = F(b) - F(a), where F'(x) = f(x)

## 8. Increasing / Decreasing Functions
f'(x) > 0 on interval → f is increasing on that interval
f'(x) < 0 on interval → f is decreasing on that interval

## 9. Concavity and Inflection Points
f''(x) > 0 → concave up (cup shape)
f''(x) < 0 → concave down (cap shape)
Inflection point: where f''(x) changes sign