FunctionGrapher

FunctionGrapher is a Python tool for plotting mathematical functions and analyzing their behavior. It supports numerical derivatives, tangent lines, roots, critical points, inflection points, and asymptotes, all with clean Matplotlib visualizations.

Features

Plot any callable function f(x)
Numerical first and second derivatives
Tangent lines at arbitrary points
Root (zero) detection
Critical point detection where f'(x) = 0
Inflection point detection where f''(x) = 0
Vertical and horizontal asymptotes
Safe evaluation for undefined values
Export plots as high-resolution images

Dependencies
numpy
matplotlib
scipy

Install with:
pip install numpy matplotlib scipy

Usage

Define a function and pass it to FunctionGrapher:

def f(x):
`return x**3 - 6\*x**2 + 9\*x + 1`

grapher = FunctionGrapher(f, x_range=(-2, 6))
(grapher.create_plot("Polynomial Function")
.plot_function()
.plot_derivative()
.plot_tangent_line(x0=2)
.plot_critical_points()
.plot_roots()
.plot_inflection_points()
.add_legend()
.save("polynomial.png")
.show())

Examples Included

Polynomial functions
Rational functions with asymptotes
Trigonometric functions
Gaussian / exponential functions

Notes

Derivatives are computed numerically using the central difference method
Root and critical point detection uses SciPy’s fsolve
Domain errors are handled safely using NaN filtering
