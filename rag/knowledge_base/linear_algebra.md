# Linear Algebra — Vectors, Matrices & Systems

## 1. Vectors

### Basic Operations
Addition: (a1,a2) + (b1,b2) = (a1+b1, a2+b2)
Scalar multiplication: k*(a1,a2) = (k*a1, k*a2)
Magnitude: |v| = sqrt(a1^2 + a2^2 + a3^2)
Unit vector: v_hat = v / |v|

### Dot Product
a · b = a1*b1 + a2*b2 + a3*b3
a · b = |a| * |b| * cos(θ)
If a · b = 0 → vectors are perpendicular (orthogonal)

### Cross Product (3D)
a × b = |i   j   k  |
        |a1  a2  a3 |
        |b1  b2  b3 |
= (a2*b3 - a3*b2)i - (a1*b3 - a3*b1)j + (a1*b2 - a2*b1)k
|a × b| = |a| * |b| * sin(θ)

## 2. Matrices

### Matrix Addition
(A + B)_ij = A_ij + B_ij  [must have same dimensions]

### Scalar Multiplication
(kA)_ij = k * A_ij

### Matrix Multiplication
(AB)_ij = sum_k A_ik * B_kj
A is m×n, B is n×p → AB is m×p
AB ≠ BA in general (not commutative)

### Transpose
(A^T)_ij = A_ji
(AB)^T = B^T * A^T

### Identity Matrix (I)
Square matrix with 1s on diagonal, 0s elsewhere
A * I = I * A = A

## 3. Determinants

### 2×2 Determinant
|a  b|
|c  d|  = ad - bc

### 3×3 Determinant (Cofactor Expansion along row 1)
|a  b  c|
|d  e  f|  = a*(ei - fh) - b*(di - fg) + c*(dh - eg)
|g  h  i|

### Properties of Determinants
det(AB) = det(A) * det(B)
det(A^T) = det(A)
det(kA) = k^n * det(A) for n×n matrix
If det(A) = 0 → A is singular (not invertible)

## 4. Inverse Matrix

### 2×2 Inverse
A = |a  b|      A^(-1) = (1/det(A)) * | d  -b|
    |c  d|                              |-c   a|

A^(-1) exists only if det(A) ≠ 0

### Properties
A * A^(-1) = A^(-1) * A = I
(AB)^(-1) = B^(-1) * A^(-1)

## 5. Systems of Linear Equations

### Matrix Form
Ax = b
where A is coefficient matrix, x is variable vector, b is constant vector

### Cramer's Rule (n×n system)
x_i = det(A_i) / det(A)
where A_i = A with column i replaced by b
Only works when det(A) ≠ 0

### Gaussian Elimination (Row Reduction)
Augmented matrix [A|b], apply row operations:
- Swap two rows
- Multiply a row by non-zero scalar
- Add multiple of one row to another

### Solution Cases
det(A) ≠ 0 → unique solution: x = A^(-1)*b
det(A) = 0 and b in column space of A → infinitely many solutions
det(A) = 0 and b not in column space of A → no solution

## 6. Rank of a Matrix
Rank = number of linearly independent rows (or columns)
Rank = number of non-zero rows in row echelon form
For m×n matrix: rank <= min(m, n)

## 7. Eigenvalues and Eigenvectors
Av = λv  (v is eigenvector, λ is eigenvalue)
det(A - λI) = 0  → characteristic equation, solve for λ
Substitute each λ back to find eigenvector v

### For 2×2 matrix:
Characteristic equation: λ^2 - trace(A)*λ + det(A) = 0
trace(A) = sum of diagonal elements