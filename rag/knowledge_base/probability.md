# Probability — Formulas, Rules & Examples

## 1. Classical Probability
P(A) = (Number of favorable outcomes) / (Total number of outcomes)
0 <= P(A) <= 1
P(A) + P(A') = 1  [complement rule]
P(A') = 1 - P(A)

## 2. Addition Rule
P(A ∪ B) = P(A) + P(B) - P(A ∩ B)

### Mutually Exclusive Events (A ∩ B = ∅)
P(A ∪ B) = P(A) + P(B)

## 3. Multiplication Rule
### Independent Events
P(A ∩ B) = P(A) * P(B)

### Dependent Events
P(A ∩ B) = P(A) * P(B|A)

## 4. Conditional Probability
P(A|B) = P(A ∩ B) / P(B),  provided P(B) > 0
P(B|A) = P(A ∩ B) / P(A),  provided P(A) > 0

## 5. Bayes' Theorem
P(A|B) = P(B|A) * P(A) / P(B)

### Extended form (Law of Total Probability in denominator)
P(A_i | B) = P(B|A_i)*P(A_i) / sum_j[P(B|A_j)*P(A_j)]

## 6. Combinatorics

### Permutations (order matters)
nPr = n! / (n-r)!
Number of ways to arrange r items from n distinct items

### Combinations (order does NOT matter)
nCr = n! / (r! * (n-r)!)
Also written as C(n,r) or binomial coefficient

### Pascal's Triangle Identity
C(n,r) = C(n-1, r-1) + C(n-1, r)

### Useful values
C(n,0) = 1
C(n,1) = n
C(n,n) = 1
C(n,2) = n*(n-1)/2

## 7. Binomial Distribution
X ~ Binomial(n, p): n trials, each with success probability p

P(X = k) = C(n,k) * p^k * (1-p)^(n-k)

Mean: E(X) = n*p
Variance: Var(X) = n*p*(1-p)
Standard deviation: σ = sqrt(n*p*(1-p))

## 8. Expected Value and Variance

### Discrete Random Variable
E(X) = sum of [x_i * P(X = x_i)]
Var(X) = E(X^2) - [E(X)]^2
       = sum of [(x_i - μ)^2 * P(X = x_i)]

### Properties
E(aX + b) = a*E(X) + b
Var(aX + b) = a^2 * Var(X)
E(X + Y) = E(X) + E(Y)  [always]
Var(X + Y) = Var(X) + Var(Y)  [only if X, Y independent]

## 9. Geometric Distribution
X = number of trials until first success, p = success probability
P(X = k) = (1-p)^(k-1) * p
E(X) = 1/p
Var(X) = (1-p) / p^2

## 10. Sample Problems

### Problem Type 1: Balls in a bag
A bag has 4 red and 6 blue balls. Two drawn without replacement.
P(both red) = C(4,2)/C(10,2) = 6/45 = 2/15

### Problem Type 2: Cards
P(ace from standard 52-card deck) = 4/52 = 1/13
P(king or queen) = P(king) + P(queen) = 4/52 + 4/52 = 8/52 = 2/13

### Problem Type 3: Dice
P(sum = 7 on two dice) = 6/36 = 1/6
Favorable: (1,6),(2,5),(3,4),(4,3),(5,2),(6,1)

### Problem Type 4: Conditional
Given P(A) = 0.4, P(B) = 0.3, P(A∩B) = 0.12
Check independence: P(A)*P(B) = 0.4*0.3 = 0.12 = P(A∩B) → Independent!
P(A|B) = 0.12/0.3 = 0.4