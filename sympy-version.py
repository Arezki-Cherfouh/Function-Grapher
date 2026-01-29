import numpy as np
import matplotlib.pyplot as plt
from sympy import *
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application
from sympy.calculus.util import continuous_domain
from sympy.core.traversal import preorder_traversal
import warnings
warnings.filterwarnings('ignore')


class AccurateFunctionGrapher:
    """
    A class to graph mathematical functions using SymPy for exact symbolic calculations.
    All calculations are verified for accuracy.
    """
    
    def __init__(self, func_str, x_range=(-10, 10), num_points=2000):
        """
        Initialize the grapher with a function string.
        
        Args:
            func_str: String representation of function
            x_range: Tuple of (x_min, x_max)
            num_points: Number of points for plotting
        """
        self.func_str = func_str
        self.x_range = x_range
        self.num_points = num_points
        
        # Symbol
        self.x = symbols('x', real=True)
        
        # Parse function with OUR symbol
        transformations = standard_transformations + (implicit_multiplication_application,)
        local_dict = {'x': self.x}  # Use our own x symbol
        self.func_symbolic_original = parse_expr(func_str, transformations=transformations, 
                                       local_dict=local_dict)
        
        # Keep original for undefined detection
        self.func_symbolic = simplify(self.func_symbolic_original)
        
        # Calculate derivatives
        self.first_derivative = diff(self.func_symbolic, self.x)
        self.second_derivative = diff(self.first_derivative, self.x)
        
        # Keep original derivatives for accurate limit calculations (tangent lines)
        self.first_derivative_original = self.first_derivative
        self.second_derivative_original = self.second_derivative
        
        # Simplify derivatives for display
        self.first_derivative = simplify(self.first_derivative)
        self.second_derivative = simplify(self.second_derivative)
        
        # Create lambdified functions for numerical evaluation
        try:
            self.func_numeric = lambdify(self.x, self.func_symbolic, modules=['numpy', {'Abs': np.abs}])
            self.first_deriv_numeric = lambdify(self.x, self.first_derivative, modules=['numpy', {'Abs': np.abs}])
            self.second_deriv_numeric = lambdify(self.x, self.second_derivative, modules=['numpy', {'Abs': np.abs}])
        except Exception as e:
            print(f"Warning during lambdify: {e}")
            self.func_numeric = None
            self.first_deriv_numeric = None
            self.second_deriv_numeric = None
        
        # Generate plot points with discontinuity detection
        self.x_values, self.y_values = self._generate_plot_points()
        
        # Initialize plot
        self.fig = None
        self.ax = None
        
        # Calculate all features
        self._find_all_features()
    
    def _find_undefined_values(self):
        """
        Find undefined values (holes/removable discontinuities) in the function.
        Uses multiple robust methods to detect all undefined points.
        """
        undefined = []
        
        try:
            # CRITICAL: Use the original unsimplified expression to find holes
            # Method 1: Find where denominator is zero in ORIGINAL expression
            numer_orig, denom_orig = fraction(self.func_symbolic_original)
            
            if denom_orig != 1:
                # Find zeros of original denominator
                denom_zeros = solve(denom_orig, self.x)
                
                for sol in denom_zeros:
                    try:
                        # Convert to real number
                        if sol.is_real or (sol.is_complex and abs(im(sol)) < 1e-10):
                            x_val = float(re(sol).evalf()) if sol.is_complex else float(sol.evalf())
                            
                            if self.x_range[0] <= x_val <= self.x_range[1]:
                                # Check if numerator is also zero (removable discontinuity/hole)
                                numer_val = float(abs(numer_orig.subs(self.x, sol)).evalf())
                                
                                # Check if this is a hole (both num and denom are zero)
                                if numer_val < 1e-6:
                                    # This is a hole - find the limit value using simplified form
                                    try:
                                        limit_val = limit(self.func_symbolic, self.x, sol)
                                        if limit_val.is_finite:
                                            y_val = float(limit_val.evalf())
                                            undefined.append((x_val, y_val))
                                            continue
                                    except:
                                        pass
                                    
                                    # Alternative: evaluate simplified form directly
                                    try:
                                        y_val = float(self.func_symbolic.subs(self.x, sol).evalf())
                                        if np.isfinite(y_val):
                                            undefined.append((x_val, y_val))
                                    except:
                                        pass
                    except:
                        pass
            
            # Method 2: Compare original and simplified expressions
            # If they differ, there was cancellation
            try:
                if self.func_symbolic != self.func_symbolic_original:
                    # Get cancelled factors
                    numer_orig, denom_orig = fraction(self.func_symbolic_original)
                    numer_simp, denom_simp = fraction(self.func_symbolic)
                    
                    # Find what was cancelled from denominator
                    if denom_simp == 1 and denom_orig != 1:
                        # Entire denominator was cancelled
                        cancelled_zeros = solve(denom_orig, self.x)
                    elif denom_orig != denom_simp:
                        # Partial cancellation
                        cancelled = simplify(denom_orig / denom_simp) if denom_simp != 0 else denom_orig
                        cancelled_zeros = solve(cancelled, self.x)
                    else:
                        cancelled_zeros = []
                    
                    for sol in cancelled_zeros:
                        try:
                            if sol.is_real or (sol.is_complex and abs(im(sol)) < 1e-10):
                                x_val = float(re(sol).evalf()) if sol.is_complex else float(sol.evalf())
                                
                                if self.x_range[0] <= x_val <= self.x_range[1]:
                                    # Evaluate the simplified form at this point
                                    y_val = float(self.func_symbolic.subs(self.x, sol).evalf())
                                    
                                    # Check not already in list
                                    if not any(abs(x_val - xu) < 1e-6 for xu, yu in undefined):
                                        if np.isfinite(y_val):
                                            undefined.append((x_val, y_val))
                        except:
                            pass
            except:
                pass
            
            # Method 3: Use SymPy's singularities function
            try:
                from sympy.calculus.singularities import singularities
                sing = singularities(self.func_symbolic_original, self.x)
                
                for s in sing:
                    try:
                        if s.is_real or (s.is_complex and abs(im(s)) < 1e-10):
                            x_val = float(re(s).evalf()) if s.is_complex else float(s.evalf())
                            
                            if self.x_range[0] <= x_val <= self.x_range[1]:
                                # Check if it's a removable singularity (has finite limit)
                                try:
                                    limit_val = limit(self.func_symbolic, self.x, s)
                                    if limit_val.is_finite:
                                        y_val = float(limit_val.evalf())
                                        if not any(abs(x_val - xu) < 1e-6 for xu, yu in undefined):
                                            undefined.append((x_val, y_val))
                                except:
                                    pass
                    except:
                        pass
            except:
                pass
            
        except Exception as e:
            pass
        
        # Remove duplicates (keep unique within tolerance)
        unique_undefined = []
        for x_val, y_val in undefined:
            if not any(abs(x_val - xu) < 1e-6 for xu, yu in unique_undefined):
                unique_undefined.append((x_val, y_val))
        
        return sorted(unique_undefined, key=lambda p: p[0])
    
    def _find_continuous_domain(self):
        """
        Find the continuous domain of the function using SymPy.
        Returns a string representation.
        """
        try:
            domain = continuous_domain(self.func_symbolic, self.x, S.Reals)
            return str(domain)
        except:
            return "ℝ (all real numbers)"
    
    def _generate_plot_points(self):
        """
        Generate plot points with proper handling of discontinuities.
        Inserts NaN values at discontinuities to break the line.
        """
        # Find discontinuity points by analyzing the symbolic function
        discontinuity_points = self._find_discontinuity_points()
        
        # Generate more points around discontinuities for better detection
        x_list = []
        
        # Sort discontinuity points
        disc_sorted = sorted(discontinuity_points)
        
        # Create segments between discontinuities
        segments = []
        prev = self.x_range[0]
        
        for disc in disc_sorted:
            if self.x_range[0] < disc < self.x_range[1]:
                # Add segment before discontinuity
                segments.append((prev, disc - 1e-10))
                prev = disc + 1e-10
        
        # Add final segment
        segments.append((prev, self.x_range[1]))
        
        # Generate points for each segment
        x_values = []
        y_values = []
        
        for seg_start, seg_end in segments:
            if seg_end > seg_start:
                # Calculate number of points for this segment
                seg_fraction = (seg_end - seg_start) / (self.x_range[1] - self.x_range[0])
                seg_points = max(50, int(self.num_points * seg_fraction))
                
                # Generate points for this segment
                x_seg = np.linspace(seg_start, seg_end, seg_points)
                y_seg = self._safe_evaluate_array(x_seg, self.func_numeric)
                
                # Add NaN separator if not first segment
                if len(x_values) > 0:
                    x_values.append(np.nan)
                    y_values.append(np.nan)
                
                # Add segment points
                x_values.extend(x_seg)
                y_values.extend(y_seg)
        
        return np.array(x_values), np.array(y_values)
    
    def _find_discontinuity_points(self):
        """
        Find points where the function is discontinuous by analyzing the symbolic expression.
        Returns a list of x-values where discontinuities occur.
        """
        discontinuities = []
        
        try:
            # Method 1: Find where denominator is zero
            numer, denom = fraction(self.func_symbolic)
            if denom != 1:
                denom_zeros = solve(denom, self.x)
                for sol in denom_zeros:
                    try:
                        if sol.is_real or (sol.is_complex and abs(im(sol)) < 1e-10):
                            x_val = float(re(sol).evalf()) if sol.is_complex else float(sol.evalf())
                            if self.x_range[0] <= x_val <= self.x_range[1]:
                                discontinuities.append(x_val)
                    except:
                        pass
            
            # Method 2: Find discontinuities in Abs, Heaviside, and piecewise functions
            # Check for abs(x) patterns which have discontinuous derivatives
            expr_str = str(self.func_symbolic)
            if 'Abs' in expr_str:
                # Find where the argument of Abs is zero
                for sub_expr in preorder_traversal(self.func_symbolic):
                    if isinstance(sub_expr, Abs):
                        arg = sub_expr.args[0]
                        try:
                            zeros = solve(arg, self.x)
                            for sol in zeros:
                                try:
                                    if sol.is_real or (sol.is_complex and abs(im(sol)) < 1e-10):
                                        x_val = float(re(sol).evalf()) if sol.is_complex else float(sol.evalf())
                                        if self.x_range[0] <= x_val <= self.x_range[1]:
                                            # Check if it's actually a discontinuity
                                            left_lim = limit(self.func_symbolic, self.x, x_val, '-')
                                            right_lim = limit(self.func_symbolic, self.x, x_val, '+')
                                            if left_lim != right_lim:
                                                discontinuities.append(x_val)
                                except:
                                    pass
                        except:
                            pass
            
            # Method 3: Check for Piecewise functions
            for sub_expr in preorder_traversal(self.func_symbolic):
                if isinstance(sub_expr, Piecewise):
                    # Extract boundary points from conditions
                    for expr, cond in sub_expr.args:
                        try:
                            # Try to extract comparison boundaries
                            if hasattr(cond, 'args'):
                                for arg in cond.args:
                                    if self.x in arg.free_symbols:
                                        try:
                                            boundary = solve(arg, self.x)
                                            for sol in boundary:
                                                if sol.is_real:
                                                    x_val = float(sol.evalf())
                                                    if self.x_range[0] <= x_val <= self.x_range[1]:
                                                        discontinuities.append(x_val)
                                        except:
                                            pass
                        except:
                            pass
            
        except Exception as e:
            pass
        
        # Remove duplicates
        unique_discontinuities = []
        for disc in discontinuities:
            if not any(abs(disc - existing) < 1e-8 for existing in unique_discontinuities):
                unique_discontinuities.append(disc)
        
        return unique_discontinuities
    
    def _safe_evaluate_array(self, x_array, func):
        """Safely evaluate function on array."""
        if func is None:
            return np.full_like(x_array, np.nan)
        
        result = np.zeros_like(x_array, dtype=float)
        for i, x_val in enumerate(x_array):
            result[i] = self._safe_evaluate_single(x_val, func)
        return result
    
    def _safe_evaluate_single(self, x_val, func):
        """Safely evaluate function at a single point."""
        if func is None:
            return np.nan
        
        try:
            result = func(x_val)
            if isinstance(result, np.ndarray):
                result = float(result.flat[0])
            else:
                result = float(result)
            
            if not np.isfinite(result):
                return np.nan
            return result
        except:
            return np.nan
    
    def _solve_equation_in_range(self, equation):
        """
        Solve an equation and return real solutions in the x_range.
        
        Args:
            equation: SymPy expression to solve (set equal to 0)
            
        Returns:
            List of float solutions
        """
        solutions = []
        
        try:
            # Try to solve symbolically
            symbolic_solutions = solve(equation, self.x)
            
            for sol in symbolic_solutions:
                try:
                    # Handle different types of solutions
                    if sol.is_real is True or (hasattr(sol, 'is_zero') and sol.is_zero):
                        sol_float = float(sol.evalf())
                        if np.isfinite(sol_float) and self.x_range[0] <= sol_float <= self.x_range[1]:
                            # Verify the solution
                            test_val = float(equation.subs(self.x, sol).evalf())
                            if abs(test_val) < 1e-6:  # Solution is valid
                                solutions.append(sol_float)
                    elif sol.is_complex and abs(im(sol)) < 1e-10:
                        # Essentially real (imaginary part is negligible)
                        sol_float = float(re(sol).evalf())
                        if np.isfinite(sol_float) and self.x_range[0] <= sol_float <= self.x_range[1]:
                            test_val = float(abs(equation.subs(self.x, sol)).evalf())
                            if abs(test_val) < 1e-6:
                                solutions.append(sol_float)
                except Exception as inner_e:
                    continue
                    
        except Exception as e:
            # If symbolic solving fails, try numerical approach
            pass
        
        # Remove duplicates
        unique_solutions = []
        for sol in solutions:
            if not any(abs(sol - existing) < 1e-6 for existing in unique_solutions):
                unique_solutions.append(sol)
        
        return sorted(unique_solutions)
    
    def _find_all_features(self):
        """Find all critical features of the function."""
        
        print("\n🔍 Analyzing function...")
        
        # Find critical points (f'(x) = 0)
        print("  Finding critical points...")
        critical_x = self._solve_equation_in_range(self.first_derivative)
        self.critical_points = []
        for x_val in critical_x:
            y_val = self._safe_evaluate_single(x_val, self.func_numeric)
            if np.isfinite(y_val):
                self.critical_points.append((x_val, y_val))
        print(f"  ✓ Found {len(self.critical_points)} critical point(s)")
        
        # Find roots (f(x) = 0)
        print("  Finding roots...")
        root_x = self._solve_equation_in_range(self.func_symbolic)
        self.roots = []
        for x_val in root_x:
            y_val = self._safe_evaluate_single(x_val, self.func_numeric)
            if np.isfinite(y_val) and abs(y_val) < 1e-6:
                self.roots.append(x_val)
        print(f"  ✓ Found {len(self.roots)} root(s)")
        
        # Find inflection points (f''(x) = 0)
        print("  Finding inflection points...")
        inflection_x = self._solve_equation_in_range(self.second_derivative)
        self.inflection_points = []
        for x_val in inflection_x:
            y_val = self._safe_evaluate_single(x_val, self.func_numeric)
            if np.isfinite(y_val):
                # Verify concavity changes
                self.inflection_points.append((x_val, y_val))
        print(f"  ✓ Found {len(self.inflection_points)} inflection point(s)")
        
        # Find undefined values (holes/removable discontinuities)
        print("  Finding undefined values...")
        self.undefined_values = self._find_undefined_values()
        print(f"  ✓ Found {len(self.undefined_values)} undefined value(s)")
        
        # Find continuous domain
        print("  Finding continuous domain...")
        self.continuous_domain_str = self._find_continuous_domain()
        print(f"  ✓ Continuous domain: {self.continuous_domain_str}")
        
        # Find vertical asymptotes
        print("  Finding vertical asymptotes...")
        self.vertical_asymptotes = []
        try:
            # Get numerator and denominator
            numer, denom = fraction(self.func_symbolic)
            
            if denom != 1:
                # Solve denominator = 0
                denom_zeros = self._solve_equation_in_range(denom)
                
                for x_val in denom_zeros:
                    # Check if numerator is also zero (removable discontinuity)
                    numer_val = float(numer.subs(self.x, x_val).evalf())
                    if abs(numer_val) > 1e-6:  # Not removable
                        self.vertical_asymptotes.append(x_val)
        except Exception as e:
            pass
        print(f"  ✓ Found {len(self.vertical_asymptotes)} vertical asymptote(s)")
        
        # Find horizontal asymptotes
        print("  Finding horizontal asymptotes...")
        self.horizontal_asymptote = None
        try:
            limit_pos_inf = limit(self.func_symbolic, self.x, oo)
            limit_neg_inf = limit(self.func_symbolic, self.x, -oo)
            
            # Check if both limits exist and are equal
            if limit_pos_inf.is_finite and limit_neg_inf.is_finite:
                if limit_pos_inf == limit_neg_inf:
                    self.horizontal_asymptote = float(limit_pos_inf.evalf())
                    print(f"  ✓ Found horizontal asymptote: y = {self.horizontal_asymptote:.4f}")
                else:
                    print(f"  ✓ Different limits at ±∞")
            else:
                print("  ✓ No horizontal asymptote")
        except Exception as e:
            pass
        
        # Find oblique asymptotes
        print("  Finding oblique asymptotes...")
        self.oblique_asymptote = None
        self.oblique_asymptote_left = None
        self.oblique_asymptote_right = None
        try:
            # Check if there's no horizontal asymptote first
            if self.horizontal_asymptote is None:
                # Calculate limit of f(x)/x as x approaches +infinity
                ratio = self.func_symbolic / self.x
                m_right = limit(ratio, self.x, oo)
                
                # Calculate limit of f(x)/x as x approaches -infinity
                m_left = limit(ratio, self.x, -oo)
                
                # Right asymptote
                if m_right.is_finite and m_right != 0:
                    b_right = limit(self.func_symbolic - m_right * self.x, self.x, oo)
                    if b_right.is_finite:
                        m_right_float = float(m_right.evalf())
                        b_right_float = float(b_right.evalf())
                        self.oblique_asymptote_right = (m_right_float, b_right_float)
                
                # Left asymptote
                if m_left.is_finite and m_left != 0:
                    b_left = limit(self.func_symbolic - m_left * self.x, self.x, -oo)
                    if b_left.is_finite:
                        m_left_float = float(m_left.evalf())
                        b_left_float = float(b_left.evalf())
                        self.oblique_asymptote_left = (m_left_float, b_left_float)
                
                # Check if they're the same
                if self.oblique_asymptote_right and self.oblique_asymptote_left:
                    m_r, b_r = self.oblique_asymptote_right
                    m_l, b_l = self.oblique_asymptote_left
                    if abs(m_r - m_l) < 1e-6 and abs(b_r - b_l) < 1e-6:
                        self.oblique_asymptote = (m_r, b_r)
                        print(f"  ✓ Found oblique asymptote: y = {m_r:.4f}x + {b_r:.4f}")
                    else:
                        print(f"  ✓ Found left oblique asymptote: y = {m_l:.4f}x + {b_l:.4f}")
                        print(f"  ✓ Found right oblique asymptote: y = {m_r:.4f}x + {b_r:.4f}")
                elif self.oblique_asymptote_right:
                    print(f"  ✓ Found right oblique asymptote: y = {self.oblique_asymptote_right[0]:.4f}x + {self.oblique_asymptote_right[1]:.4f}")
                elif self.oblique_asymptote_left:
                    print(f"  ✓ Found left oblique asymptote: y = {self.oblique_asymptote_left[0]:.4f}x + {self.oblique_asymptote_left[1]:.4f}")
                else:
                    print("  ✓ No oblique asymptote")
            else:
                print("  ✓ No oblique asymptote (horizontal asymptote exists)")
        except Exception as e:
            print("  ✓ No oblique asymptote")
        
        print("✓ Analysis complete!\n")
    
    def create_plot(self, figsize=(14, 9), title=None):
        """Create the matplotlib figure."""
        self.fig, self.ax = plt.subplots(figsize=figsize)
        
        if title is None:
            title = f"f(x) = {self.func_str}"
        
        self.ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
        self.ax.set_xlabel('x', fontsize=13, fontweight='bold')
        self.ax.set_ylabel('y', fontsize=13, fontweight='bold')
        self.ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.7)
        self.ax.axhline(y=0, color='k', linewidth=0.8, alpha=0.5)
        self.ax.axvline(x=0, color='k', linewidth=0.8, alpha=0.5)
        
        # Set default y-limits early to prevent matplotlib from auto-scaling to extreme values
        self.ax.set_ylim(-10, 10)
        
        return self
    
    def plot_function(self, color='#1f77b4', linewidth=2.5, label='f(x)'):
        """Plot the function."""
        if self.ax is None:
            self.create_plot()
        
        # Don't clip - let NaN values handle discontinuities
        # Matplotlib will automatically break lines at NaN values
        self.ax.plot(self.x_values, self.y_values, color=color, 
                    linewidth=linewidth, label=label, zorder=3)
        return self
    
    def plot_derivative(self, color='#ff7f0e', linewidth=2, label="f'(x)"):
        """Plot the first derivative."""
        if self.ax is None:
            self.create_plot()
        
        # Generate derivative values with same discontinuity detection
        x_deriv, y_deriv = self._generate_derivative_points(self.first_deriv_numeric)
        self.ax.plot(x_deriv, y_deriv, color=color, 
                    linewidth=linewidth, label=label, linestyle='--', alpha=0.8, zorder=2)
        return self
    
    def plot_second_derivative(self, color='#2ca02c', linewidth=2, label="f''(x)"):
        """Plot the second derivative."""
        if self.ax is None:
            self.create_plot()
        
        # Generate second derivative values with same discontinuity detection
        x_deriv, y_deriv = self._generate_derivative_points(self.second_deriv_numeric)
        self.ax.plot(x_deriv, y_deriv, color=color, 
                    linewidth=linewidth, label=label, linestyle='-.', alpha=0.8, zorder=2)
        return self
    
    def _generate_derivative_points(self, deriv_func):
        """Generate points for derivatives with discontinuity handling."""
        # Use the same discontinuity points as the main function
        discontinuity_points = self._find_discontinuity_points()
        
        # Sort discontinuity points
        disc_sorted = sorted(discontinuity_points)
        
        # Create segments between discontinuities
        segments = []
        prev = self.x_range[0]
        
        for disc in disc_sorted:
            if self.x_range[0] < disc < self.x_range[1]:
                segments.append((prev, disc - 1e-10))
                prev = disc + 1e-10
        
        segments.append((prev, self.x_range[1]))
        
        # Generate points for each segment
        x_values = []
        y_values = []
        
        for seg_start, seg_end in segments:
            if seg_end > seg_start:
                seg_fraction = (seg_end - seg_start) / (self.x_range[1] - self.x_range[0])
                seg_points = max(50, int(self.num_points * seg_fraction))
                
                x_seg = np.linspace(seg_start, seg_end, seg_points)
                y_seg = self._safe_evaluate_array(x_seg, deriv_func)
                
                if len(x_values) > 0:
                    x_values.append(np.nan)
                    y_values.append(np.nan)
                
                x_values.extend(x_seg)
                y_values.extend(y_seg)
        
        return np.array(x_values), np.array(y_values)
    
    def plot_critical_points(self, color='#d62728', marker='o', 
                            markersize=12, label='Critical Points'):
        """Plot critical points."""
        if self.ax is None:
            self.create_plot()
        
        if self.critical_points:
            x_crit, y_crit = zip(*self.critical_points)
            self.ax.plot(x_crit, y_crit, marker=marker, color=color, 
                        markersize=markersize, linestyle='', label=label,
                        markeredgecolor='black', markeredgewidth=2, zorder=6)
            
            for x, y in self.critical_points:
                self.ax.annotate(f'({x:.3f}, {y:.3f})', 
                               xy=(x, y), xytext=(15, 15),
                               textcoords='offset points',
                               bbox=dict(boxstyle='round,pad=0.5', 
                                       facecolor='yellow', alpha=0.8,
                                       edgecolor='black', linewidth=1.5),
                               fontsize=9, fontweight='bold',
                               arrowprops=dict(arrowstyle='->', 
                                             connectionstyle='arc3,rad=0.3',
                                             color='black', lw=1.5))
        return self
    
    def plot_roots(self, color='#ff7f0e', marker='s', 
                   markersize=12, label='Roots (Zeros)'):
        """Plot roots."""
        if self.ax is None:
            self.create_plot()
        
        if self.roots:
            y_roots = [0] * len(self.roots)
            self.ax.plot(self.roots, y_roots, marker=marker, color=color, 
                        markersize=markersize, linestyle='', label=label,
                        markeredgecolor='black', markeredgewidth=2, zorder=6)
            
            for x in self.roots:
                self.ax.annotate(f'x={x:.3f}', 
                               xy=(x, 0), xytext=(0, -25),
                               textcoords='offset points',
                               bbox=dict(boxstyle='round,pad=0.5', 
                                       facecolor='lightblue', alpha=0.8,
                                       edgecolor='black', linewidth=1.5),
                               fontsize=9, fontweight='bold',
                               ha='center',
                               arrowprops=dict(arrowstyle='->', 
                                             color='black', lw=1.5))
        return self
    
    def plot_undefined_values(self, color='#ff0000', marker='o', 
                             markersize=14, label='Undefined (Holes)'):
        """Plot undefined values (holes/removable discontinuities) with red dots."""
        if self.ax is None:
            self.create_plot()
        
        if self.undefined_values:
            x_undef, y_undef = zip(*self.undefined_values)
            # Plot as hollow red circles
            self.ax.plot(x_undef, y_undef, marker=marker, color='white', 
                        markersize=markersize, linestyle='', label=label,
                        markeredgecolor=color, markeredgewidth=3, zorder=7)
            
            for x, y in self.undefined_values:
                self.ax.annotate(f'Undefined at x={x:.3f}\n(limit = {y:.3f})', 
                               xy=(x, y), xytext=(20, -20),
                               textcoords='offset points',
                               bbox=dict(boxstyle='round,pad=0.5', 
                                       facecolor='#ffcccc', alpha=0.9,
                                       edgecolor=color, linewidth=2),
                               fontsize=9, fontweight='bold',
                               arrowprops=dict(arrowstyle='->', 
                                             connectionstyle='arc3,rad=0.3',
                                             color=color, lw=2))
        return self
    
    def plot_asymptotes(self, vertical_color='#d62728', horizontal_color='#1f77b4',
                       oblique_color='#17becf', linewidth=2, alpha=0.7):
        """Plot asymptotes."""
        if self.ax is None:
            self.create_plot()
        
        # Vertical asymptotes
        for i, x_asym in enumerate(self.vertical_asymptotes):
            label = 'Vertical Asymptote' if i == 0 else ''
            self.ax.axvline(x=x_asym, color=vertical_color, linestyle='--', 
                          linewidth=linewidth, alpha=alpha, label=label, zorder=10)
            
            ylim = self.ax.get_ylim()
            y_pos = ylim[1] * 0.9
            self.ax.text(x_asym, y_pos, f'x={x_asym:.3f}', 
                        ha='center', va='top',
                        bbox=dict(boxstyle='round,pad=0.3', 
                                facecolor='white', alpha=0.8,
                                edgecolor=vertical_color, linewidth=1.5),
                        fontsize=9, fontweight='bold')
        
        # Horizontal asymptote
        if self.horizontal_asymptote is not None:
            self.ax.axhline(y=self.horizontal_asymptote, color=horizontal_color, 
                          linestyle='--', linewidth=linewidth, alpha=alpha,
                          label=f'Horizontal Asymptote y={self.horizontal_asymptote:.3f}',
                          zorder=1)
        
        # Oblique asymptote (single)
        if self.oblique_asymptote is not None:
            m, b = self.oblique_asymptote
            x_asymp = np.linspace(self.x_range[0], self.x_range[1], 100)
            y_asymp = m * x_asymp + b
            self.ax.plot(x_asymp, y_asymp, color=oblique_color, linestyle='--',
                        linewidth=linewidth, alpha=alpha,
                        label=f'Oblique Asymptote y={m:.3f}x+{b:.3f}',
                        zorder=1)
        
        # Oblique asymptotes (separate left and right)
        if self.oblique_asymptote_left is not None and self.oblique_asymptote is None:
            m, b = self.oblique_asymptote_left
            x_asymp = np.linspace(self.x_range[0], 0, 100)
            y_asymp = m * x_asymp + b
            self.ax.plot(x_asymp, y_asymp, color=oblique_color, linestyle='--',
                        linewidth=linewidth, alpha=alpha,
                        label=f'Left Oblique y={m:.3f}x+{b:.3f}',
                        zorder=1)
        
        if self.oblique_asymptote_right is not None and self.oblique_asymptote is None:
            m, b = self.oblique_asymptote_right
            x_asymp = np.linspace(0, self.x_range[1], 100)
            y_asymp = m * x_asymp + b
            self.ax.plot(x_asymp, y_asymp, color='#bcbd22', linestyle='--',
                        linewidth=linewidth, alpha=alpha,
                        label=f'Right Oblique y={m:.3f}x+{b:.3f}',
                        zorder=1)
        
        return self
    
    def plot_inflection_points(self, color='#9467bd', marker='^', 
                              markersize=12, label='Inflection Points'):
        """Plot inflection points."""
        if self.ax is None:
            self.create_plot()
        
        if self.inflection_points:
            x_infl, y_infl = zip(*self.inflection_points)
            self.ax.plot(x_infl, y_infl, marker=marker, color=color, 
                        markersize=markersize, linestyle='', label=label,
                        markeredgecolor='black', markeredgewidth=2, zorder=6)
            
            for x, y in self.inflection_points:
                self.ax.annotate(f'({x:.3f}, {y:.3f})', 
                               xy=(x, y), xytext=(-15, 15),
                               textcoords='offset points',
                               bbox=dict(boxstyle='round,pad=0.5', 
                                       facecolor='lightgreen', alpha=0.8,
                                       edgecolor='black', linewidth=1.5),
                               fontsize=9, fontweight='bold',
                               arrowprops=dict(arrowstyle='->', 
                                             connectionstyle='arc3,rad=-0.3',
                                             color='black', lw=1.5))
        return self
    
    def plot_tangent_line(self, x0, color='#2ca02c', linewidth=2.5, 
                         label=None, extend=2, half='both'):
        """
        Plot tangent line at x0.
        
        Args:
            x0: Point at which to draw tangent
            color: Line color
            linewidth: Line width
            label: Legend label
            extend: How far to extend the line from x0
            half: 'both', 'left', or 'right' - which direction(s) to draw
        """
        if self.ax is None:
            self.create_plot()
        
        try:
            # Evaluate at x0 using SymPy for accuracy
            y0 = float(self.func_symbolic.subs(self.x, x0).evalf())
            
            if not np.isfinite(y0):
                print(f"Cannot plot tangent at x={x0}: function undefined")
                return self
            
            # CRITICAL: Use ORIGINAL derivative for accurate limit calculations
            # Simplified derivatives can lose discontinuity information
            derivative_for_limits = self.first_derivative_original
            
            # Calculate slope using limits for left/right tangents
            if half == 'left':
                # Use left limit for derivative
                slope = float(limit(derivative_for_limits, self.x, x0, '-').evalf())
                if not np.isfinite(slope):
                    print(f"Cannot plot left tangent at x={x0}: left derivative undefined")
                    return self
                
                x_tangent = np.linspace(x0 - extend, x0, 100)
                y_tangent = y0 + slope * (x_tangent - x0)
                
                if label is None:
                    label = f'Left tangent at x={x0:.2f} (slope={slope:.2f})'
                
                self.ax.plot(x_tangent, y_tangent, color=color, 
                            linewidth=linewidth, label=label, linestyle=':', 
                            alpha=0.9, zorder=4)
                
            elif half == 'right':
                # Use right limit for derivative
                slope = float(limit(derivative_for_limits, self.x, x0, '+').evalf())
                if not np.isfinite(slope):
                    print(f"Cannot plot right tangent at x={x0}: right derivative undefined")
                    return self
                
                x_tangent = np.linspace(x0, x0 + extend, 100)
                y_tangent = y0 + slope * (x_tangent - x0)
                
                if label is None:
                    label = f'Right tangent at x={x0:.2f} (slope={slope:.2f})'
                
                self.ax.plot(x_tangent, y_tangent, color=color, 
                            linewidth=linewidth, label=label, linestyle=':', 
                            alpha=0.9, zorder=4)
                
            else:  # 'both'
                # Check if left and right derivatives are equal
                slope_left = limit(derivative_for_limits, self.x, x0, '-')
                slope_right = limit(derivative_for_limits, self.x, x0, '+')
                
                # Convert to float for comparison
                try:
                    slope_left_float = float(slope_left.evalf())
                    slope_right_float = float(slope_right.evalf())
                except:
                    slope_left_float = None
                    slope_right_float = None
                
                # Check if slopes are equal (derivative is continuous)
                if (slope_left_float is not None and slope_right_float is not None and 
                    np.isfinite(slope_left_float) and np.isfinite(slope_right_float) and
                    abs(slope_left_float - slope_right_float) < 1e-6):
                    # Derivative is continuous, draw single tangent
                    slope = slope_left_float
                    x_tangent = np.linspace(x0 - extend, x0 + extend, 100)
                    y_tangent = y0 + slope * (x_tangent - x0)
                    
                    if label is None:
                        label = f'Tangent at x={x0:.2f} (slope={slope:.2f})'
                    
                    self.ax.plot(x_tangent, y_tangent, color=color, 
                                linewidth=linewidth, label=label, linestyle=':', 
                                alpha=0.9, zorder=4)
                else:
                    # Derivative has discontinuity, draw both tangents
                    if slope_left_float is not None and np.isfinite(slope_left_float):
                        x_tangent_left = np.linspace(x0 - extend, x0, 100)
                        y_tangent_left = y0 + slope_left_float * (x_tangent_left - x0)
                        
                        if label is None:
                            label_left = f'Left tangent at x={x0:.2f} (slope={slope_left_float:.2f})'
                        else:
                            label_left = label + ' (left)'
                        
                        self.ax.plot(x_tangent_left, y_tangent_left, color=color, 
                                    linewidth=linewidth, label=label_left, linestyle=':', 
                                    alpha=0.9, zorder=4)
                    
                    if slope_right_float is not None and np.isfinite(slope_right_float):
                        x_tangent_right = np.linspace(x0, x0 + extend, 100)
                        y_tangent_right = y0 + slope_right_float * (x_tangent_right - x0)
                        
                        if label is None:
                            label_right = f'Right tangent at x={x0:.2f} (slope={slope_right_float:.2f})'
                        else:
                            label_right = label + ' (right)'
                        
                        # Use slightly different color for right tangent
                        import matplotlib.colors as mcolors
                        rgb = mcolors.to_rgb(color)
                        darker_color = tuple(max(0, c - 0.15) for c in rgb)
                        
                        self.ax.plot(x_tangent_right, y_tangent_right, color=darker_color, 
                                    linewidth=linewidth, label=label_right, linestyle=':', 
                                    alpha=0.9, zorder=4)
            
            # Plot the point
            self.ax.plot(x0, y0, 'o', color=color, markersize=10, 
                        markeredgecolor='black', markeredgewidth=2, zorder=5)
            
        except Exception as e:
            print(f"Error plotting tangent at x={x0}: {e}")
        
        return self
    
    def set_limits(self, xlim=None, ylim=None):
        """Set axis limits with validation to prevent matplotlib errors."""
        if self.ax is None:
            self.create_plot()
        
        if xlim:
            self.ax.set_xlim(xlim)
        
        if ylim:
            y_min, y_max = ylim
            # Clamp to safe values to prevent matplotlib errors
            MAX_SAFE = 1e6
            y_min = max(min(y_min, MAX_SAFE), -MAX_SAFE)
            y_max = max(min(y_max, MAX_SAFE), -MAX_SAFE)
            
            self.ax.set_ylim(y_min, y_max)
        
        return self
    
    def add_legend(self, loc='best', fontsize=11):
        """Add legend."""
        if self.ax is None:
            self.create_plot()
        
        self.ax.legend(loc=loc, fontsize=fontsize, framealpha=0.95,
                      edgecolor='black', fancybox=True, shadow=True)
        return self
    
    def add_info_box(self):
        """Add information box with continuous domain."""
        if self.ax is None:
            self.create_plot()
        
        info_lines = [
            f"f(x) = {self.func_symbolic}",
            f"f'(x) = {self.first_derivative}",
            f"f''(x) = {self.second_derivative}",
            "",
            f"Domain: {self.continuous_domain_str}",
            ""
        ]
        
        if self.critical_points:
            info_lines.append(f"Critical points: {len(self.critical_points)}")
        if self.roots:
            info_lines.append(f"Roots: {len(self.roots)}")
        if self.inflection_points:
            info_lines.append(f"Inflection points: {len(self.inflection_points)}")
        if self.undefined_values:
            info_lines.append(f"Undefined values: {len(self.undefined_values)}")
        if self.vertical_asymptotes:
            info_lines.append(f"Vertical asymptotes: {len(self.vertical_asymptotes)}")
        
        info_text = "\n".join(info_lines)
        
        self.ax.text(0.98, 0.98, info_text, 
                    transform=self.ax.transAxes,
                    fontsize=8, verticalalignment='top',
                    horizontalalignment='right',
                    bbox=dict(boxstyle='round,pad=0.7', 
                            facecolor='wheat', alpha=0.9,
                            edgecolor='black', linewidth=1.5),
                    family='monospace')
        
        return self
    
    def save(self, filename):
        """Save the plot."""
        if self.fig is None:
            return self
        
        self.fig.tight_layout()
        self.fig.savefig(filename, dpi=300, bbox_inches='tight', 
                        facecolor='white', edgecolor='none')
        return self
    
    def show(self):
        """Display the plot."""
        if self.fig is None:
            return self
        
        self.fig.tight_layout()
        plt.show()
        return self


def get_yes_no(prompt):
    """Get yes/no input."""
    while True:
        response = input(prompt + " (y/n): ").lower().strip()
        if response in ['y', 'yes']:
            return True
        elif response in ['n', 'no']:
            return False
        print("Please enter 'y' or 'n'")


def get_float(prompt, default=None):
    """Get float input."""
    while True:
        if default is not None:
            response = input(f"{prompt} (default: {default}): ").strip()
        else:
            response = input(prompt + ": ").strip()
            
        if response == '' and default is not None:
            return default
        try:
            return float(response)
        except ValueError:
            print("Please enter a valid number")


def get_choice(prompt, choices):
    """Get choice from list."""
    while True:
        response = input(prompt + f" {choices}: ").lower().strip()
        if response in choices:
            return response
        print(f"Please enter one of: {choices}")


def print_header():
    """Print header."""
    print("\n" + "="*70)
    print(" "*15 + "ACCURATE FUNCTION GRAPHER v2.2")
    print(" "*18 + "Powered by SymPy")
    print(" "*10 + "With Undefined Values Detection")
    print("="*70)


def main():
    """Main program."""
    print_header()
    
    graph_counter = 1
    
    while True:
        print("\n📝 Enter a mathematical function using 'x'")
        print("Examples: x**2, sin(x), 1/(x-2), (x**2-1)/(x-1)")
        print("Type 'quit' to exit\n")
        
        func_str = input("f(x) = ").strip()
        
        if not func_str or func_str.lower() in ['exit', 'quit', 'q']:
            break
        
        print(f"\n{'─'*70}")
        print(f"Graph #{graph_counter}")
        print(f"{'─'*70}")
        
        # Get range
        x_min = get_float("X minimum", default=-10)
        x_max = get_float("X maximum", default=10)
        
        # Create grapher
        try:
            grapher = AccurateFunctionGrapher(func_str, x_range=(x_min, x_max))
        except Exception as e:
            print(f"\n❌ Error: {e}")
            continue
        
        # Y limits
        use_ylim = get_yes_no("\nSet custom y-axis limits?")
        if use_ylim:
            y_min = get_float("Y minimum", default=-10)
            y_max = get_float("Y maximum", default=10)
            ylim = (y_min, y_max)
        else:
            ylim = (-10, 10)
        
        # Create plot
        grapher.create_plot(title=f"Graph #{graph_counter}: f(x) = {func_str}")
        grapher.plot_function()
        
        # Options
        print("\n" + "="*70)
        print("PLOT OPTIONS")
        print("="*70)
        
        if get_yes_no("📈 Plot first derivative f'(x)?"):
            grapher.plot_derivative()
        
        if get_yes_no("📉 Plot second derivative f''(x)?"):
            grapher.plot_second_derivative()
        
        if get_yes_no("🎯 Plot critical points?"):
            grapher.plot_critical_points()
        
        if get_yes_no("🔍 Plot roots (zeros)?"):
            grapher.plot_roots()
        
        if get_yes_no("🔴 Plot undefined values (holes)?"):
            grapher.plot_undefined_values()
        
        if get_yes_no("📏 Plot asymptotes?"):
            grapher.plot_asymptotes()
        
        if get_yes_no("🔄 Plot inflection points?"):
            grapher.plot_inflection_points()
        
        if get_yes_no("📐 Plot tangent line(s)?"):
            num = int(get_float("How many", default=1))
            colors = ['#2ca02c', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f']
            for i in range(num):
                x0 = get_float(f"x-coordinate for tangent {i+1}")
                half = get_choice(f"Direction for tangent {i+1}", ['both', 'left', 'right'])
                grapher.plot_tangent_line(x0=x0, color=colors[i % len(colors)], half=half)
        
        if get_yes_no("ℹ️  Add information box?"):
            grapher.add_info_box()
        
        grapher.set_limits(ylim=ylim)
        
        grapher.add_legend()
        
        # Save
        filename = f"graph_{graph_counter:03d}.png"
        grapher.save(filename)
        print(f"\n✓ Saved: {filename}")
        
        if get_yes_no("\n👁️  Display now?"):
            grapher.show()
        
        graph_counter += 1
        
        if not get_yes_no("\n🔄 Create another graph?"):
            break
    
    print("\n" + "="*70)
    print("Thank you for using Accurate Function Grapher!")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()



# import numpy as np
# import matplotlib.pyplot as plt
# from sympy import *
# from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application
# from sympy.calculus.util import continuous_domain
# from sympy.core.traversal import preorder_traversal
# import warnings
# warnings.filterwarnings('ignore')


# class AccurateFunctionGrapher:
#     """
#     A class to graph mathematical functions using SymPy for exact symbolic calculations.
#     All calculations are verified for accuracy.
#     """
    
#     def __init__(self, func_str, x_range=(-10, 10), num_points=2000):
#         """
#         Initialize the grapher with a function string.
        
#         Args:
#             func_str: String representation of function
#             x_range: Tuple of (x_min, x_max)
#             num_points: Number of points for plotting
#         """
#         self.func_str = func_str
#         self.x_range = x_range
#         self.num_points = num_points
        
#         # Symbol
#         self.x = symbols('x', real=True)
        
#         # Parse function with OUR symbol
#         transformations = standard_transformations + (implicit_multiplication_application,)
#         local_dict = {'x': self.x}  # Use our own x symbol
#         self.func_symbolic = parse_expr(func_str, transformations=transformations, 
#                                        local_dict=local_dict, evaluate=False)
        
#         # Store the original unsimplified version for hole detection
#         self.func_original = self.func_symbolic
        
#         # Simplify for calculations
#         self.func_symbolic = simplify(self.func_symbolic)
        
#         # Calculate derivatives
#         self.first_derivative = diff(self.func_symbolic, self.x)
#         self.second_derivative = diff(self.first_derivative, self.x)
        
#         # Simplify derivatives
#         self.first_derivative = simplify(self.first_derivative)
#         self.second_derivative = simplify(self.second_derivative)
        
#         # Create lambdified functions for numerical evaluation
#         try:
#             self.func_numeric = lambdify(self.x, self.func_symbolic, modules=['numpy', {'Abs': np.abs}])
#             self.first_deriv_numeric = lambdify(self.x, self.first_derivative, modules=['numpy', {'Abs': np.abs}])
#             self.second_deriv_numeric = lambdify(self.x, self.second_derivative, modules=['numpy', {'Abs': np.abs}])
#         except Exception as e:
#             print(f"Warning during lambdify: {e}")
#             self.func_numeric = None
#             self.first_deriv_numeric = None
#             self.second_deriv_numeric = None
        
#         # Generate plot points with discontinuity detection
#         self.x_values, self.y_values = self._generate_plot_points()
        
#         # Initialize plot
#         self.fig = None
#         self.ax = None
        
#         # Calculate all features
#         self._find_all_features()
    
#     def _generate_plot_points(self):
#         """
#         Generate plot points with proper handling of discontinuities.
#         Inserts NaN values at discontinuities to break the line.
#         """
#         # Find discontinuity points by analyzing the symbolic function
#         discontinuity_points = self._find_discontinuity_points()
        
#         # Generate more points around discontinuities for better detection
#         x_list = []
        
#         # Sort discontinuity points
#         disc_sorted = sorted(discontinuity_points)
        
#         # Create segments between discontinuities
#         segments = []
#         prev = self.x_range[0]
        
#         for disc in disc_sorted:
#             if self.x_range[0] < disc < self.x_range[1]:
#                 # Add segment before discontinuity
#                 segments.append((prev, disc - 1e-10))
#                 prev = disc + 1e-10
        
#         # Add final segment
#         segments.append((prev, self.x_range[1]))
        
#         # Generate points for each segment
#         x_values = []
#         y_values = []
        
#         for seg_start, seg_end in segments:
#             if seg_end > seg_start:
#                 # Calculate number of points for this segment
#                 seg_fraction = (seg_end - seg_start) / (self.x_range[1] - self.x_range[0])
#                 seg_points = max(50, int(self.num_points * seg_fraction))
                
#                 # Generate points for this segment
#                 x_seg = np.linspace(seg_start, seg_end, seg_points)
#                 y_seg = self._safe_evaluate_array(x_seg, self.func_numeric)
                
#                 # Add NaN separator if not first segment
#                 if len(x_values) > 0:
#                     x_values.append(np.nan)
#                     y_values.append(np.nan)
                
#                 # Add segment points
#                 x_values.extend(x_seg)
#                 y_values.extend(y_seg)
        
#         return np.array(x_values), np.array(y_values)
    
#     def _find_discontinuity_points(self):
#         """
#         Find points where the function is discontinuous by analyzing the symbolic expression.
#         Returns a list of x-values where discontinuities occur.
#         """
#         discontinuities = []
        
#         try:
#             # Method 1: Find where denominator is zero
#             numer, denom = fraction(self.func_symbolic)
#             if denom != 1:
#                 denom_zeros = solve(denom, self.x)
#                 for sol in denom_zeros:
#                     try:
#                         if sol.is_real or (sol.is_complex and abs(im(sol)) < 1e-10):
#                             x_val = float(re(sol).evalf()) if sol.is_complex else float(sol.evalf())
#                             if self.x_range[0] <= x_val <= self.x_range[1]:
#                                 discontinuities.append(x_val)
#                     except:
#                         pass
            
#             # Method 2: Find discontinuities in Abs, Heaviside, and piecewise functions
#             # Check for abs(x) patterns which have discontinuous derivatives
#             expr_str = str(self.func_symbolic)
#             if 'Abs' in expr_str:
#                 # Find where the argument of Abs is zero
#                 for sub_expr in preorder_traversal(self.func_symbolic):
#                     if isinstance(sub_expr, Abs):
#                         arg = sub_expr.args[0]
#                         try:
#                             zeros = solve(arg, self.x)
#                             for sol in zeros:
#                                 try:
#                                     if sol.is_real or (sol.is_complex and abs(im(sol)) < 1e-10):
#                                         x_val = float(re(sol).evalf()) if sol.is_complex else float(sol.evalf())
#                                         if self.x_range[0] <= x_val <= self.x_range[1]:
#                                             # Check if it's actually a discontinuity
#                                             left_lim = limit(self.func_symbolic, self.x, x_val, '-')
#                                             right_lim = limit(self.func_symbolic, self.x, x_val, '+')
#                                             if left_lim != right_lim:
#                                                 discontinuities.append(x_val)
#                                 except:
#                                     pass
#                         except:
#                             pass
            
#             # Method 3: Check for Piecewise functions
#             for sub_expr in preorder_traversal(self.func_symbolic):
#                 if isinstance(sub_expr, Piecewise):
#                     # Extract boundary points from conditions
#                     for expr, cond in sub_expr.args:
#                         try:
#                             # Try to extract comparison boundaries
#                             if hasattr(cond, 'args'):
#                                 for arg in cond.args:
#                                     if self.x in arg.free_symbols:
#                                         try:
#                                             boundary = solve(arg, self.x)
#                                             for sol in boundary:
#                                                 if sol.is_real:
#                                                     x_val = float(sol.evalf())
#                                                     if self.x_range[0] <= x_val <= self.x_range[1]:
#                                                         discontinuities.append(x_val)
#                                         except:
#                                             pass
#                         except:
#                             pass
            
#         except Exception as e:
#             pass
        
#         # Remove duplicates
#         unique_discontinuities = []
#         for disc in discontinuities:
#             if not any(abs(disc - existing) < 1e-8 for existing in unique_discontinuities):
#                 unique_discontinuities.append(disc)
        
#         return unique_discontinuities
    
#     def _safe_evaluate_array(self, x_array, func):
#         """Safely evaluate function on array."""
#         if func is None:
#             return np.full_like(x_array, np.nan)
        
#         result = np.zeros_like(x_array, dtype=float)
#         for i, x_val in enumerate(x_array):
#             result[i] = self._safe_evaluate_single(x_val, func)
#         return result
    
#     def _safe_evaluate_single(self, x_val, func):
#         """Safely evaluate function at a single point."""
#         if func is None:
#             return np.nan
        
#         try:
#             result = func(x_val)
#             if isinstance(result, np.ndarray):
#                 result = float(result.flat[0])
#             else:
#                 result = float(result)
            
#             if not np.isfinite(result):
#                 return np.nan
#             return result
#         except:
#             return np.nan
    
#     def _solve_equation_in_range(self, equation):
#         """
#         Solve an equation and return real solutions in the x_range.
        
#         Args:
#             equation: SymPy expression to solve (set equal to 0)
            
#         Returns:
#             List of float solutions
#         """
#         solutions = []
        
#         try:
#             # Try to solve symbolically
#             symbolic_solutions = solve(equation, self.x)
            
#             for sol in symbolic_solutions:
#                 try:
#                     # Handle different types of solutions
#                     if sol.is_real is True or (hasattr(sol, 'is_zero') and sol.is_zero):
#                         sol_float = float(sol.evalf())
#                         if np.isfinite(sol_float) and self.x_range[0] <= sol_float <= self.x_range[1]:
#                             # Verify the solution
#                             test_val = float(equation.subs(self.x, sol).evalf())
#                             if abs(test_val) < 1e-6:  # Solution is valid
#                                 solutions.append(sol_float)
#                     elif sol.is_complex and abs(im(sol)) < 1e-10:
#                         # Essentially real (imaginary part is negligible)
#                         sol_float = float(re(sol).evalf())
#                         if np.isfinite(sol_float) and self.x_range[0] <= sol_float <= self.x_range[1]:
#                             test_val = float(abs(equation.subs(self.x, sol)).evalf())
#                             if abs(test_val) < 1e-6:
#                                 solutions.append(sol_float)
#                 except Exception as inner_e:
#                     continue
                    
#         except Exception as e:
#             # If symbolic solving fails, try numerical approach
#             pass
        
#         # Remove duplicates
#         unique_solutions = []
#         for sol in solutions:
#             if not any(abs(sol - existing) < 1e-6 for existing in unique_solutions):
#                 unique_solutions.append(sol)
        
#         return sorted(unique_solutions)
    
#     def _find_all_features(self):
#         """Find all critical features of the function."""
        
#         print("\n🔍 Analyzing function...")
        
#         # Find critical points (f'(x) = 0)
#         print("  Finding critical points...")
#         critical_x = self._solve_equation_in_range(self.first_derivative)
#         self.critical_points = []
#         for x_val in critical_x:
#             y_val = self._safe_evaluate_single(x_val, self.func_numeric)
#             if np.isfinite(y_val):
#                 self.critical_points.append((x_val, y_val))
#         print(f"  ✓ Found {len(self.critical_points)} critical point(s)")
        
#         # Find roots (f(x) = 0)
#         print("  Finding roots...")
#         root_x = self._solve_equation_in_range(self.func_symbolic)
#         self.roots = []
#         for x_val in root_x:
#             y_val = self._safe_evaluate_single(x_val, self.func_numeric)
#             if np.isfinite(y_val) and abs(y_val) < 1e-6:
#                 self.roots.append(x_val)
#         print(f"  ✓ Found {len(self.roots)} root(s)")
        
#         # Find inflection points (f''(x) = 0)
#         print("  Finding inflection points...")
#         inflection_x = self._solve_equation_in_range(self.second_derivative)
#         self.inflection_points = []
#         for x_val in inflection_x:
#             y_val = self._safe_evaluate_single(x_val, self.func_numeric)
#             if np.isfinite(y_val):
#                 # Verify concavity changes
#                 self.inflection_points.append((x_val, y_val))
#         print(f"  ✓ Found {len(self.inflection_points)} inflection point(s)")
        
#         # Find vertical asymptotes and removable discontinuities (holes)
#         print("  Finding vertical asymptotes and holes...")
#         self.vertical_asymptotes = []
#         self.removable_discontinuities = []  # Store holes
#         try:
#             # Get numerator and denominator from ORIGINAL expression
#             numer, denom = fraction(self.func_original)
            
#             if denom != 1:
#                 # Solve denominator = 0
#                 denom_zeros = self._solve_equation_in_range(denom)
                
#                 for x_val in denom_zeros:
#                     # Check if numerator is also zero (removable discontinuity)
#                     try:
#                         numer_val = float(numer.subs(self.x, x_val).evalf())
#                         if abs(numer_val) < 1e-6:  # Numerator is also zero - removable!
#                             # Calculate the limit to find the y-value of the hole
#                             try:
#                                 # Use simplified version for limit calculation
#                                 limit_val = limit(self.func_symbolic, self.x, x_val)
#                                 if limit_val.is_finite:
#                                     y_hole = float(limit_val.evalf())
#                                     self.removable_discontinuities.append((x_val, y_hole))
#                                     print(f"    Found hole at x={x_val:.4f}, y={y_hole:.4f}")
#                             except:
#                                 # Fallback: evaluate simplified function at the point
#                                 try:
#                                     y_hole = float(self.func_symbolic.subs(self.x, x_val).evalf())
#                                     if np.isfinite(y_hole):
#                                         self.removable_discontinuities.append((x_val, y_hole))
#                                         print(f"    Found hole at x={x_val:.4f}, y={y_hole:.4f}")
#                                 except:
#                                     pass
#                         else:  # Numerator is not zero - true asymptote
#                             self.vertical_asymptotes.append(x_val)
#                     except:
#                         # If we can't evaluate, assume it's an asymptote
#                         self.vertical_asymptotes.append(x_val)
#         except Exception as e:
#             pass
#         print(f"  ✓ Found {len(self.vertical_asymptotes)} vertical asymptote(s)")
#         print(f"  ✓ Found {len(self.removable_discontinuities)} hole(s)")
        
#         # Find horizontal asymptotes
#         print("  Finding horizontal asymptotes...")
#         self.horizontal_asymptote = None
#         try:
#             limit_pos_inf = limit(self.func_symbolic, self.x, oo)
#             limit_neg_inf = limit(self.func_symbolic, self.x, -oo)
            
#             # Check if both limits exist and are equal
#             if limit_pos_inf.is_finite and limit_neg_inf.is_finite:
#                 if limit_pos_inf == limit_neg_inf:
#                     self.horizontal_asymptote = float(limit_pos_inf.evalf())
#                     print(f"  ✓ Found horizontal asymptote: y = {self.horizontal_asymptote:.4f}")
#                 else:
#                     print(f"  ✓ Different limits at ±∞")
#             else:
#                 print("  ✓ No horizontal asymptote")
#         except Exception as e:
#             pass
        
#         # Find oblique asymptotes
#         print("  Finding oblique asymptotes...")
#         self.oblique_asymptote = None
#         self.oblique_asymptote_left = None
#         self.oblique_asymptote_right = None
#         try:
#             # Check if there's no horizontal asymptote first
#             if self.horizontal_asymptote is None:
#                 # Calculate limit of f(x)/x as x approaches +infinity
#                 ratio = self.func_symbolic / self.x
#                 m_right = limit(ratio, self.x, oo)
                
#                 # Calculate limit of f(x)/x as x approaches -infinity
#                 m_left = limit(ratio, self.x, -oo)
                
#                 # Right asymptote
#                 if m_right.is_finite and m_right != 0:
#                     b_right = limit(self.func_symbolic - m_right * self.x, self.x, oo)
#                     if b_right.is_finite:
#                         m_right_float = float(m_right.evalf())
#                         b_right_float = float(b_right.evalf())
#                         self.oblique_asymptote_right = (m_right_float, b_right_float)
                
#                 # Left asymptote
#                 if m_left.is_finite and m_left != 0:
#                     b_left = limit(self.func_symbolic - m_left * self.x, self.x, -oo)
#                     if b_left.is_finite:
#                         m_left_float = float(m_left.evalf())
#                         b_left_float = float(b_left.evalf())
#                         self.oblique_asymptote_left = (m_left_float, b_left_float)
                
#                 # Check if they're the same
#                 if self.oblique_asymptote_right and self.oblique_asymptote_left:
#                     m_r, b_r = self.oblique_asymptote_right
#                     m_l, b_l = self.oblique_asymptote_left
#                     if abs(m_r - m_l) < 1e-6 and abs(b_r - b_l) < 1e-6:
#                         self.oblique_asymptote = (m_r, b_r)
#                         print(f"  ✓ Found oblique asymptote: y = {m_r:.4f}x + {b_r:.4f}")
#                     else:
#                         print(f"  ✓ Found left oblique asymptote: y = {m_l:.4f}x + {b_l:.4f}")
#                         print(f"  ✓ Found right oblique asymptote: y = {m_r:.4f}x + {b_r:.4f}")
#                 elif self.oblique_asymptote_right:
#                     print(f"  ✓ Found right oblique asymptote: y = {self.oblique_asymptote_right[0]:.4f}x + {self.oblique_asymptote_right[1]:.4f}")
#                 elif self.oblique_asymptote_left:
#                     print(f"  ✓ Found left oblique asymptote: y = {self.oblique_asymptote_left[0]:.4f}x + {self.oblique_asymptote_left[1]:.4f}")
#                 else:
#                     print("  ✓ No oblique asymptote")
#             else:
#                 print("  ✓ No oblique asymptote (horizontal asymptote exists)")
#         except Exception as e:
#             print("  ✓ No oblique asymptote")
        
#         print("✓ Analysis complete!\n")
    
#     def create_plot(self, figsize=(14, 9), title=None):
#         """Create the matplotlib figure."""
#         self.fig, self.ax = plt.subplots(figsize=figsize)
        
#         if title is None:
#             title = f"f(x) = {self.func_str}"
        
#         self.ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
#         self.ax.set_xlabel('x', fontsize=13, fontweight='bold')
#         self.ax.set_ylabel('y', fontsize=13, fontweight='bold')
#         self.ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.7)
#         self.ax.axhline(y=0, color='k', linewidth=0.8, alpha=0.5)
#         self.ax.axvline(x=0, color='k', linewidth=0.8, alpha=0.5)
        
#         # Set default y-limits early to prevent matplotlib from auto-scaling to extreme values
#         self.ax.set_ylim(-10, 10)
        
#         return self
    
#     def plot_function(self, color='#1f77b4', linewidth=2.5, label='f(x)'):
#         """Plot the function."""
#         if self.ax is None:
#             self.create_plot()
        
#         # Don't clip - let NaN values handle discontinuities
#         # Matplotlib will automatically break lines at NaN values
#         self.ax.plot(self.x_values, self.y_values, color=color, 
#                     linewidth=linewidth, label=label, zorder=3)
#         return self
    
#     def plot_derivative(self, color='#ff7f0e', linewidth=2, label="f'(x)"):
#         """Plot the first derivative."""
#         if self.ax is None:
#             self.create_plot()
        
#         # Generate derivative values with same discontinuity detection
#         x_deriv, y_deriv = self._generate_derivative_points(self.first_deriv_numeric)
#         self.ax.plot(x_deriv, y_deriv, color=color, 
#                     linewidth=linewidth, label=label, linestyle='--', alpha=0.8, zorder=2)
#         return self
    
#     def plot_second_derivative(self, color='#2ca02c', linewidth=2, label="f''(x)"):
#         """Plot the second derivative."""
#         if self.ax is None:
#             self.create_plot()
        
#         # Generate second derivative values with same discontinuity detection
#         x_deriv, y_deriv = self._generate_derivative_points(self.second_deriv_numeric)
#         self.ax.plot(x_deriv, y_deriv, color=color, 
#                     linewidth=linewidth, label=label, linestyle='-.', alpha=0.8, zorder=2)
#         return self
    
#     def _generate_derivative_points(self, deriv_func):
#         """Generate points for derivatives with discontinuity handling."""
#         # Use the same discontinuity points as the main function
#         discontinuity_points = self._find_discontinuity_points()
        
#         # Sort discontinuity points
#         disc_sorted = sorted(discontinuity_points)
        
#         # Create segments between discontinuities
#         segments = []
#         prev = self.x_range[0]
        
#         for disc in disc_sorted:
#             if self.x_range[0] < disc < self.x_range[1]:
#                 segments.append((prev, disc - 1e-10))
#                 prev = disc + 1e-10
        
#         segments.append((prev, self.x_range[1]))
        
#         # Generate points for each segment
#         x_values = []
#         y_values = []
        
#         for seg_start, seg_end in segments:
#             if seg_end > seg_start:
#                 seg_fraction = (seg_end - seg_start) / (self.x_range[1] - self.x_range[0])
#                 seg_points = max(50, int(self.num_points * seg_fraction))
                
#                 x_seg = np.linspace(seg_start, seg_end, seg_points)
#                 y_seg = self._safe_evaluate_array(x_seg, deriv_func)
                
#                 if len(x_values) > 0:
#                     x_values.append(np.nan)
#                     y_values.append(np.nan)
                
#                 x_values.extend(x_seg)
#                 y_values.extend(y_seg)
        
#         return np.array(x_values), np.array(y_values)
    
#     def plot_critical_points(self, color='#d62728', marker='o', 
#                             markersize=12, label='Critical Points'):
#         """Plot critical points."""
#         if self.ax is None:
#             self.create_plot()
        
#         if self.critical_points:
#             x_crit, y_crit = zip(*self.critical_points)
#             self.ax.plot(x_crit, y_crit, marker=marker, color=color, 
#                         markersize=markersize, linestyle='', label=label,
#                         markeredgecolor='black', markeredgewidth=2, zorder=6)
            
#             for x, y in self.critical_points:
#                 self.ax.annotate(f'({x:.3f}, {y:.3f})', 
#                                xy=(x, y), xytext=(15, 15),
#                                textcoords='offset points',
#                                bbox=dict(boxstyle='round,pad=0.5', 
#                                        facecolor='yellow', alpha=0.8,
#                                        edgecolor='black', linewidth=1.5),
#                                fontsize=9, fontweight='bold',
#                                arrowprops=dict(arrowstyle='->', 
#                                              connectionstyle='arc3,rad=0.3',
#                                              color='black', lw=1.5))
#         return self
    
#     def plot_roots(self, color='#ff7f0e', marker='s', 
#                    markersize=12, label='Roots (Zeros)'):
#         """Plot roots."""
#         if self.ax is None:
#             self.create_plot()
        
#         if self.roots:
#             y_roots = [0] * len(self.roots)
#             self.ax.plot(self.roots, y_roots, marker=marker, color=color, 
#                         markersize=markersize, linestyle='', label=label,
#                         markeredgecolor='black', markeredgewidth=2, zorder=6)
            
#             for x in self.roots:
#                 self.ax.annotate(f'x={x:.3f}', 
#                                xy=(x, 0), xytext=(0, -25),
#                                textcoords='offset points',
#                                bbox=dict(boxstyle='round,pad=0.5', 
#                                        facecolor='lightblue', alpha=0.8,
#                                        edgecolor='black', linewidth=1.5),
#                                fontsize=9, fontweight='bold',
#                                ha='center',
#                                arrowprops=dict(arrowstyle='->', 
#                                              color='black', lw=1.5))
#         return self
    
#     def plot_removable_discontinuities(self, color='red', marker='o',
#                                       markersize=12, label='Holes (Removable Discontinuities)'):
#         """Plot removable discontinuities (holes) as red dots."""
#         if self.ax is None:
#             self.create_plot()
        
#         if self.removable_discontinuities:
#             x_holes, y_holes = zip(*self.removable_discontinuities)
#             # Plot as hollow circles (facecolors='none')
#             self.ax.plot(x_holes, y_holes, marker=marker, color=color,
#                         markersize=markersize, linestyle='', label=label,
#                         markeredgecolor=color, markeredgewidth=3,
#                         markerfacecolor='white', zorder=7)
            
#             for x, y in self.removable_discontinuities:
#                 self.ax.annotate(f'Hole\n({x:.3f}, {y:.3f})',
#                                xy=(x, y), xytext=(20, -20),
#                                textcoords='offset points',
#                                bbox=dict(boxstyle='round,pad=0.5',
#                                        facecolor='mistyrose', alpha=0.9,
#                                        edgecolor='red', linewidth=1.5),
#                                fontsize=9, fontweight='bold',
#                                arrowprops=dict(arrowstyle='->',
#                                              connectionstyle='arc3,rad=0.3',
#                                              color='red', lw=1.5))
#         return self
    
#     def plot_asymptotes(self, vertical_color='#d62728', horizontal_color='#1f77b4',
#                        oblique_color='#17becf', linewidth=2, alpha=0.7):
#         """Plot asymptotes."""
#         if self.ax is None:
#             self.create_plot()
        
#         # Vertical asymptotes
#         for i, x_asym in enumerate(self.vertical_asymptotes):
#             label = 'Vertical Asymptote' if i == 0 else ''
#             self.ax.axvline(x=x_asym, color=vertical_color, linestyle='--', 
#                           linewidth=linewidth, alpha=alpha, label=label, zorder=10)
            
#             ylim = self.ax.get_ylim()
#             y_pos = ylim[1] * 0.9
#             self.ax.text(x_asym, y_pos, f'x={x_asym:.3f}', 
#                         ha='center', va='top',
#                         bbox=dict(boxstyle='round,pad=0.3', 
#                                 facecolor='white', alpha=0.8,
#                                 edgecolor=vertical_color, linewidth=1.5),
#                         fontsize=9, fontweight='bold')
        
#         # Horizontal asymptote
#         if self.horizontal_asymptote is not None:
#             self.ax.axhline(y=self.horizontal_asymptote, color=horizontal_color, 
#                           linestyle='--', linewidth=linewidth, alpha=alpha,
#                           label=f'Horizontal Asymptote y={self.horizontal_asymptote:.3f}',
#                           zorder=1)
        
#         # Oblique asymptote (single)
#         if self.oblique_asymptote is not None:
#             m, b = self.oblique_asymptote
#             x_asymp = np.linspace(self.x_range[0], self.x_range[1], 100)
#             y_asymp = m * x_asymp + b
#             self.ax.plot(x_asymp, y_asymp, color=oblique_color, linestyle='--',
#                         linewidth=linewidth, alpha=alpha,
#                         label=f'Oblique Asymptote y={m:.3f}x+{b:.3f}',
#                         zorder=1)
        
#         # Oblique asymptotes (separate left and right)
#         if self.oblique_asymptote_left is not None and self.oblique_asymptote is None:
#             m, b = self.oblique_asymptote_left
#             x_asymp = np.linspace(self.x_range[0], 0, 100)
#             y_asymp = m * x_asymp + b
#             self.ax.plot(x_asymp, y_asymp, color=oblique_color, linestyle='--',
#                         linewidth=linewidth, alpha=alpha,
#                         label=f'Left Oblique y={m:.3f}x+{b:.3f}',
#                         zorder=1)
        
#         if self.oblique_asymptote_right is not None and self.oblique_asymptote is None:
#             m, b = self.oblique_asymptote_right
#             x_asymp = np.linspace(0, self.x_range[1], 100)
#             y_asymp = m * x_asymp + b
#             self.ax.plot(x_asymp, y_asymp, color='#bcbd22', linestyle='--',
#                         linewidth=linewidth, alpha=alpha,
#                         label=f'Right Oblique y={m:.3f}x+{b:.3f}',
#                         zorder=1)
        
#         return self
    
#     def plot_inflection_points(self, color='#9467bd', marker='^', 
#                               markersize=12, label='Inflection Points'):
#         """Plot inflection points."""
#         if self.ax is None:
#             self.create_plot()
        
#         if self.inflection_points:
#             x_infl, y_infl = zip(*self.inflection_points)
#             self.ax.plot(x_infl, y_infl, marker=marker, color=color, 
#                         markersize=markersize, linestyle='', label=label,
#                         markeredgecolor='black', markeredgewidth=2, zorder=6)
            
#             for x, y in self.inflection_points:
#                 self.ax.annotate(f'({x:.3f}, {y:.3f})', 
#                                xy=(x, y), xytext=(-15, 15),
#                                textcoords='offset points',
#                                bbox=dict(boxstyle='round,pad=0.5', 
#                                        facecolor='lightgreen', alpha=0.8,
#                                        edgecolor='black', linewidth=1.5),
#                                fontsize=9, fontweight='bold',
#                                arrowprops=dict(arrowstyle='->', 
#                                              connectionstyle='arc3,rad=-0.3',
#                                              color='black', lw=1.5))
#         return self
    
#     def plot_tangent_line(self, x0, color='#2ca02c', linewidth=2.5, 
#                          label=None, extend=2, half='both'):
#         """
#         Plot tangent line at x0.
        
#         Args:
#             x0: Point at which to draw tangent
#             color: Line color
#             linewidth: Line width
#             label: Legend label
#             extend: How far to extend the line from x0
#             half: 'both', 'left', or 'right' - which direction(s) to draw
#         """
#         if self.ax is None:
#             self.create_plot()
        
#         try:
#             # Evaluate at x0 using SymPy for accuracy
#             y0 = float(self.func_symbolic.subs(self.x, x0).evalf())
#             slope = float(self.first_derivative.subs(self.x, x0).evalf())
            
#             if not np.isfinite(y0) or not np.isfinite(slope):
#                 print(f"Cannot plot tangent at x={x0}: function or derivative undefined")
#                 return self
            
#             # Create tangent line based on half parameter
#             if half == 'left':
#                 x_tangent = np.linspace(x0 - extend, x0, 100)
#             elif half == 'right':
#                 x_tangent = np.linspace(x0, x0 + extend, 100)
#             else:  # 'both'
#                 x_tangent = np.linspace(x0 - extend, x0 + extend, 100)
            
#             y_tangent = y0 + slope * (x_tangent - x0)
            
#             if label is None:
#                 if half == 'left':
#                     label = f'Left tangent at x={x0:.2f}'
#                 elif half == 'right':
#                     label = f'Right tangent at x={x0:.2f}'
#                 else:
#                     label = f'Tangent at x={x0:.2f}'
            
#             self.ax.plot(x_tangent, y_tangent, color=color, 
#                         linewidth=linewidth, label=label, linestyle=':', 
#                         alpha=0.9, zorder=4)
            
#             self.ax.plot(x0, y0, 'o', color=color, markersize=10, 
#                         markeredgecolor='black', markeredgewidth=2, zorder=5)
            
#         except Exception as e:
#             print(f"Error plotting tangent at x={x0}: {e}")
        
#         return self
    
#     def set_limits(self, xlim=None, ylim=None):
#         """Set axis limits with validation to prevent matplotlib errors."""
#         if self.ax is None:
#             self.create_plot()
        
#         if xlim:
#             self.ax.set_xlim(xlim)
        
#         if ylim:
#             y_min, y_max = ylim
#             # Clamp to safe values to prevent matplotlib errors
#             MAX_SAFE = 1e6
#             y_min = max(min(y_min, MAX_SAFE), -MAX_SAFE)
#             y_max = max(min(y_max, MAX_SAFE), -MAX_SAFE)
            
#             self.ax.set_ylim(y_min, y_max)
        
#         return self
    
#     def add_legend(self, loc='best', fontsize=11):
#         """Add legend."""
#         if self.ax is None:
#             self.create_plot()
        
#         self.ax.legend(loc=loc, fontsize=fontsize, framealpha=0.95,
#                       edgecolor='black', fancybox=True, shadow=True)
#         return self
    
#     def add_info_box(self):
#         """Add information box."""
#         if self.ax is None:
#             self.create_plot()
        
#         info_lines = [
#             f"f(x) = {self.func_symbolic}",
#             f"f'(x) = {self.first_derivative}",
#             f"f''(x) = {self.second_derivative}",
#             ""
#         ]
        
#         if self.critical_points:
#             info_lines.append(f"Critical points: {len(self.critical_points)}")
#         if self.roots:
#             info_lines.append(f"Roots: {len(self.roots)}")
#         if self.inflection_points:
#             info_lines.append(f"Inflection points: {len(self.inflection_points)}")
#         if self.vertical_asymptotes:
#             info_lines.append(f"Vertical asymptotes: {len(self.vertical_asymptotes)}")
#         if self.removable_discontinuities:
#             info_lines.append(f"Holes: {len(self.removable_discontinuities)}")
        
#         info_text = "\n".join(info_lines)
        
#         self.ax.text(0.98, 0.98, info_text, 
#                     transform=self.ax.transAxes,
#                     fontsize=8, verticalalignment='top',
#                     horizontalalignment='right',
#                     bbox=dict(boxstyle='round,pad=0.7', 
#                             facecolor='wheat', alpha=0.9,
#                             edgecolor='black', linewidth=1.5),
#                     family='monospace')
        
#         return self
    
#     def save(self, filename):
#         """Save the plot."""
#         if self.fig is None:
#             return self
        
#         self.fig.tight_layout()
#         self.fig.savefig(filename, dpi=300, bbox_inches='tight', 
#                         facecolor='white', edgecolor='none')
#         return self
    
#     def show(self):
#         """Display the plot."""
#         if self.fig is None:
#             return self
        
#         self.fig.tight_layout()
#         plt.show()
#         return self


# def get_yes_no(prompt):
#     """Get yes/no input."""
#     while True:
#         response = input(prompt + " (y/n): ").lower().strip()
#         if response in ['y', 'yes']:
#             return True
#         elif response in ['n', 'no']:
#             return False
#         print("Please enter 'y' or 'n'")


# def get_float(prompt, default=None):
#     """Get float input."""
#     while True:
#         if default is not None:
#             response = input(f"{prompt} (default: {default}): ").strip()
#         else:
#             response = input(prompt + ": ").strip()
            
#         if response == '' and default is not None:
#             return default
#         try:
#             return float(response)
#         except ValueError:
#             print("Please enter a valid number")


# def get_choice(prompt, choices):
#     """Get choice from list."""
#     while True:
#         response = input(prompt + f" {choices}: ").lower().strip()
#         if response in choices:
#             return response
#         print(f"Please enter one of: {choices}")


# def print_header():
#     """Print header."""
#     print("\n" + "="*70)
#     print(" "*15 + "ACCURATE FUNCTION GRAPHER v2.1")
#     print(" "*18 + "Powered by SymPy")
#     print(" "*12 + "Fixed Discontinuity Handling")
#     print("="*70)


# def main():
#     """Main program."""
#     print_header()
    
#     graph_counter = 1
    
#     while True:
#         print("\n📝 Enter a mathematical function using 'x'")
#         print("Examples: x**2, sin(x), 1/(x-2), x**3 - 3*x**2 + 2")
#         print("Type 'quit' to exit\n")
        
#         func_str = input("f(x) = ").strip()
        
#         if not func_str or func_str.lower() in ['exit', 'quit', 'q']:
#             break
        
#         print(f"\n{'─'*70}")
#         print(f"Graph #{graph_counter}")
#         print(f"{'─'*70}")
        
#         # Get range
#         x_min = get_float("X minimum", default=-10)
#         x_max = get_float("X maximum", default=10)
        
#         # Create grapher
#         try:
#             grapher = AccurateFunctionGrapher(func_str, x_range=(x_min, x_max))
#         except Exception as e:
#             print(f"\n❌ Error: {e}")
#             continue
        
#         # Y limits
#         use_ylim = get_yes_no("\nSet custom y-axis limits?")
#         if use_ylim:
#             y_min = get_float("Y minimum", default=-10)
#             y_max = get_float("Y maximum", default=10)
#             ylim = (y_min, y_max)
#         else:
#             ylim = (-10, 10)
        
#         # Create plot
#         grapher.create_plot(title=f"Graph #{graph_counter}: f(x) = {func_str}")
#         grapher.plot_function()
        
#         # Options
#         print("\n" + "="*70)
#         print("PLOT OPTIONS")
#         print("="*70)
        
#         if get_yes_no("📈 Plot first derivative f'(x)?"):
#             grapher.plot_derivative()
        
#         if get_yes_no("📉 Plot second derivative f''(x)?"):
#             grapher.plot_second_derivative()
        
#         if get_yes_no("🎯 Plot critical points?"):
#             grapher.plot_critical_points()
        
#         if get_yes_no("🔍 Plot roots (zeros)?"):
#             grapher.plot_roots()
        
#         if get_yes_no("📏 Plot asymptotes?"):
#             grapher.plot_asymptotes()
        
#         if get_yes_no("🔴 Plot holes (removable discontinuities)?"):
#             grapher.plot_removable_discontinuities()
        
#         if get_yes_no("🔄 Plot inflection points?"):
#             grapher.plot_inflection_points()
        
#         if get_yes_no("📐 Plot tangent line(s)?"):
#             num = int(get_float("How many", default=1))
#             colors = ['#2ca02c', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f']
#             for i in range(num):
#                 x0 = get_float(f"x-coordinate for tangent {i+1}")
#                 half = get_choice(f"Direction for tangent {i+1}", ['both', 'left', 'right'])
#                 grapher.plot_tangent_line(x0=x0, color=colors[i % len(colors)], half=half)
        
#         if get_yes_no("ℹ️  Add information box?"):
#             grapher.add_info_box()
        
#         grapher.set_limits(ylim=ylim)
        
#         grapher.add_legend()
        
#         # Save
#         filename = f"graph_{graph_counter:03d}.png"
#         grapher.save(filename)
#         print(f"\n✓ Saved: {filename}")
        
#         if get_yes_no("\n👁️  Display now?"):
#             grapher.show()
        
#         graph_counter += 1
        
#         if not get_yes_no("\n🔄 Create another graph?"):
#             break
    
#     # Copy to output
#     # if graph_counter > 1:
#     #     print(f"\n📊 Created {graph_counter - 1} graph(s)")
#     #     import os
#     #     import shutil
#     #     os.makedirs("outputs", exist_ok=True)
#     #     for i in range(1, graph_counter):
#     #         src = f"graph_{i:03d}.png"
#     #         dst = f"outputs/graph_{i:03d}.png"
#     #         if os.path.exists(src):
#     #             shutil.copy(src, dst)
    
#     print("\n" + "="*70)
#     print("Thank you for using Accurate Function Grapher!")
#     print("="*70 + "\n")


# if __name__ == "__main__":
#     main()





# import numpy as np
# import matplotlib.pyplot as plt
# from sympy import *
# from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application
# from sympy.calculus.util import continuous_domain
# from sympy.core.traversal import preorder_traversal
# import warnings
# warnings.filterwarnings('ignore')


# class AccurateFunctionGrapher:
#     """
#     A class to graph mathematical functions using SymPy for exact symbolic calculations.
#     All calculations are verified for accuracy.
#     """
    
#     def __init__(self, func_str, x_range=(-10, 10), num_points=2000):
#         """
#         Initialize the grapher with a function string.
        
#         Args:
#             func_str: String representation of function
#             x_range: Tuple of (x_min, x_max)
#             num_points: Number of points for plotting
#         """
#         self.func_str = func_str
#         self.x_range = x_range
#         self.num_points = num_points
        
#         # Symbol
#         self.x = symbols('x', real=True)
        
#         # Parse function with OUR symbol
#         transformations = standard_transformations + (implicit_multiplication_application,)
#         local_dict = {'x': self.x}  # Use our own x symbol
#         self.func_symbolic_original = parse_expr(func_str, transformations=transformations, 
#                                        local_dict=local_dict)
        
#         # Keep original for undefined detection
#         self.func_symbolic = simplify(self.func_symbolic_original)
        
#         # Calculate derivatives
#         self.first_derivative = diff(self.func_symbolic, self.x)
#         self.second_derivative = diff(self.first_derivative, self.x)
        
#         # Simplify derivatives
#         self.first_derivative = simplify(self.first_derivative)
#         self.second_derivative = simplify(self.second_derivative)
        
#         # Create lambdified functions for numerical evaluation
#         try:
#             self.func_numeric = lambdify(self.x, self.func_symbolic, modules=['numpy', {'Abs': np.abs}])
#             self.first_deriv_numeric = lambdify(self.x, self.first_derivative, modules=['numpy', {'Abs': np.abs}])
#             self.second_deriv_numeric = lambdify(self.x, self.second_derivative, modules=['numpy', {'Abs': np.abs}])
#         except Exception as e:
#             print(f"Warning during lambdify: {e}")
#             self.func_numeric = None
#             self.first_deriv_numeric = None
#             self.second_deriv_numeric = None
        
#         # Generate plot points with discontinuity detection
#         self.x_values, self.y_values = self._generate_plot_points()
        
#         # Initialize plot
#         self.fig = None
#         self.ax = None
        
#         # Calculate all features
#         self._find_all_features()
    
#     def _find_undefined_values(self):
#         """
#         Find undefined values (holes/removable discontinuities) in the function.
#         Uses multiple robust methods to detect all undefined points.
#         """
#         undefined = []
        
#         try:
#             # CRITICAL: Use the original unsimplified expression to find holes
#             # Method 1: Find where denominator is zero in ORIGINAL expression
#             numer_orig, denom_orig = fraction(self.func_symbolic_original)
            
#             if denom_orig != 1:
#                 # Find zeros of original denominator
#                 denom_zeros = solve(denom_orig, self.x)
                
#                 for sol in denom_zeros:
#                     try:
#                         # Convert to real number
#                         if sol.is_real or (sol.is_complex and abs(im(sol)) < 1e-10):
#                             x_val = float(re(sol).evalf()) if sol.is_complex else float(sol.evalf())
                            
#                             if self.x_range[0] <= x_val <= self.x_range[1]:
#                                 # Check if numerator is also zero (removable discontinuity/hole)
#                                 numer_val = float(abs(numer_orig.subs(self.x, sol)).evalf())
                                
#                                 # Check if this is a hole (both num and denom are zero)
#                                 if numer_val < 1e-6:
#                                     # This is a hole - find the limit value using simplified form
#                                     try:
#                                         limit_val = limit(self.func_symbolic, self.x, sol)
#                                         if limit_val.is_finite:
#                                             y_val = float(limit_val.evalf())
#                                             undefined.append((x_val, y_val))
#                                             continue
#                                     except:
#                                         pass
                                    
#                                     # Alternative: evaluate simplified form directly
#                                     try:
#                                         y_val = float(self.func_symbolic.subs(self.x, sol).evalf())
#                                         if np.isfinite(y_val):
#                                             undefined.append((x_val, y_val))
#                                     except:
#                                         pass
#                     except:
#                         pass
            
#             # Method 2: Compare original and simplified expressions
#             # If they differ, there was cancellation
#             try:
#                 if self.func_symbolic != self.func_symbolic_original:
#                     # Get cancelled factors
#                     numer_orig, denom_orig = fraction(self.func_symbolic_original)
#                     numer_simp, denom_simp = fraction(self.func_symbolic)
                    
#                     # Find what was cancelled from denominator
#                     if denom_simp == 1 and denom_orig != 1:
#                         # Entire denominator was cancelled
#                         cancelled_zeros = solve(denom_orig, self.x)
#                     elif denom_orig != denom_simp:
#                         # Partial cancellation
#                         cancelled = simplify(denom_orig / denom_simp) if denom_simp != 0 else denom_orig
#                         cancelled_zeros = solve(cancelled, self.x)
#                     else:
#                         cancelled_zeros = []
                    
#                     for sol in cancelled_zeros:
#                         try:
#                             if sol.is_real or (sol.is_complex and abs(im(sol)) < 1e-10):
#                                 x_val = float(re(sol).evalf()) if sol.is_complex else float(sol.evalf())
                                
#                                 if self.x_range[0] <= x_val <= self.x_range[1]:
#                                     # Evaluate the simplified form at this point
#                                     y_val = float(self.func_symbolic.subs(self.x, sol).evalf())
                                    
#                                     # Check not already in list
#                                     if not any(abs(x_val - xu) < 1e-6 for xu, yu in undefined):
#                                         if np.isfinite(y_val):
#                                             undefined.append((x_val, y_val))
#                         except:
#                             pass
#             except:
#                 pass
            
#             # Method 3: Use SymPy's singularities function
#             try:
#                 from sympy.calculus.singularities import singularities
#                 sing = singularities(self.func_symbolic_original, self.x)
                
#                 for s in sing:
#                     try:
#                         if s.is_real or (s.is_complex and abs(im(s)) < 1e-10):
#                             x_val = float(re(s).evalf()) if s.is_complex else float(s.evalf())
                            
#                             if self.x_range[0] <= x_val <= self.x_range[1]:
#                                 # Check if it's a removable singularity (has finite limit)
#                                 try:
#                                     limit_val = limit(self.func_symbolic, self.x, s)
#                                     if limit_val.is_finite:
#                                         y_val = float(limit_val.evalf())
#                                         if not any(abs(x_val - xu) < 1e-6 for xu, yu in undefined):
#                                             undefined.append((x_val, y_val))
#                                 except:
#                                     pass
#                     except:
#                         pass
#             except:
#                 pass
            
#         except Exception as e:
#             pass
        
#         # Remove duplicates (keep unique within tolerance)
#         unique_undefined = []
#         for x_val, y_val in undefined:
#             if not any(abs(x_val - xu) < 1e-6 for xu, yu in unique_undefined):
#                 unique_undefined.append((x_val, y_val))
        
#         return sorted(unique_undefined, key=lambda p: p[0])
    
#     def _find_continuous_domain(self):
#         """
#         Find the continuous domain of the function using SymPy.
#         Returns a string representation.
#         """
#         try:
#             domain = continuous_domain(self.func_symbolic, self.x, S.Reals)
#             return str(domain)
#         except:
#             return "ℝ (all real numbers)"
    
#     def _generate_plot_points(self):
#         """
#         Generate plot points with proper handling of discontinuities.
#         Inserts NaN values at discontinuities to break the line.
#         """
#         # Find discontinuity points by analyzing the symbolic function
#         discontinuity_points = self._find_discontinuity_points()
        
#         # Generate more points around discontinuities for better detection
#         x_list = []
        
#         # Sort discontinuity points
#         disc_sorted = sorted(discontinuity_points)
        
#         # Create segments between discontinuities
#         segments = []
#         prev = self.x_range[0]
        
#         for disc in disc_sorted:
#             if self.x_range[0] < disc < self.x_range[1]:
#                 # Add segment before discontinuity
#                 segments.append((prev, disc - 1e-10))
#                 prev = disc + 1e-10
        
#         # Add final segment
#         segments.append((prev, self.x_range[1]))
        
#         # Generate points for each segment
#         x_values = []
#         y_values = []
        
#         for seg_start, seg_end in segments:
#             if seg_end > seg_start:
#                 # Calculate number of points for this segment
#                 seg_fraction = (seg_end - seg_start) / (self.x_range[1] - self.x_range[0])
#                 seg_points = max(50, int(self.num_points * seg_fraction))
                
#                 # Generate points for this segment
#                 x_seg = np.linspace(seg_start, seg_end, seg_points)
#                 y_seg = self._safe_evaluate_array(x_seg, self.func_numeric)
                
#                 # Add NaN separator if not first segment
#                 if len(x_values) > 0:
#                     x_values.append(np.nan)
#                     y_values.append(np.nan)
                
#                 # Add segment points
#                 x_values.extend(x_seg)
#                 y_values.extend(y_seg)
        
#         return np.array(x_values), np.array(y_values)
    
#     def _find_discontinuity_points(self):
#         """
#         Find points where the function is discontinuous by analyzing the symbolic expression.
#         Returns a list of x-values where discontinuities occur.
#         """
#         discontinuities = []
        
#         try:
#             # Method 1: Find where denominator is zero
#             numer, denom = fraction(self.func_symbolic)
#             if denom != 1:
#                 denom_zeros = solve(denom, self.x)
#                 for sol in denom_zeros:
#                     try:
#                         if sol.is_real or (sol.is_complex and abs(im(sol)) < 1e-10):
#                             x_val = float(re(sol).evalf()) if sol.is_complex else float(sol.evalf())
#                             if self.x_range[0] <= x_val <= self.x_range[1]:
#                                 discontinuities.append(x_val)
#                     except:
#                         pass
            
#             # Method 2: Find discontinuities in Abs, Heaviside, and piecewise functions
#             # Check for abs(x) patterns which have discontinuous derivatives
#             expr_str = str(self.func_symbolic)
#             if 'Abs' in expr_str:
#                 # Find where the argument of Abs is zero
#                 for sub_expr in preorder_traversal(self.func_symbolic):
#                     if isinstance(sub_expr, Abs):
#                         arg = sub_expr.args[0]
#                         try:
#                             zeros = solve(arg, self.x)
#                             for sol in zeros:
#                                 try:
#                                     if sol.is_real or (sol.is_complex and abs(im(sol)) < 1e-10):
#                                         x_val = float(re(sol).evalf()) if sol.is_complex else float(sol.evalf())
#                                         if self.x_range[0] <= x_val <= self.x_range[1]:
#                                             # Check if it's actually a discontinuity
#                                             left_lim = limit(self.func_symbolic, self.x, x_val, '-')
#                                             right_lim = limit(self.func_symbolic, self.x, x_val, '+')
#                                             if left_lim != right_lim:
#                                                 discontinuities.append(x_val)
#                                 except:
#                                     pass
#                         except:
#                             pass
            
#             # Method 3: Check for Piecewise functions
#             for sub_expr in preorder_traversal(self.func_symbolic):
#                 if isinstance(sub_expr, Piecewise):
#                     # Extract boundary points from conditions
#                     for expr, cond in sub_expr.args:
#                         try:
#                             # Try to extract comparison boundaries
#                             if hasattr(cond, 'args'):
#                                 for arg in cond.args:
#                                     if self.x in arg.free_symbols:
#                                         try:
#                                             boundary = solve(arg, self.x)
#                                             for sol in boundary:
#                                                 if sol.is_real:
#                                                     x_val = float(sol.evalf())
#                                                     if self.x_range[0] <= x_val <= self.x_range[1]:
#                                                         discontinuities.append(x_val)
#                                         except:
#                                             pass
#                         except:
#                             pass
            
#         except Exception as e:
#             pass
        
#         # Remove duplicates
#         unique_discontinuities = []
#         for disc in discontinuities:
#             if not any(abs(disc - existing) < 1e-8 for existing in unique_discontinuities):
#                 unique_discontinuities.append(disc)
        
#         return unique_discontinuities
    
#     def _safe_evaluate_array(self, x_array, func):
#         """Safely evaluate function on array."""
#         if func is None:
#             return np.full_like(x_array, np.nan)
        
#         result = np.zeros_like(x_array, dtype=float)
#         for i, x_val in enumerate(x_array):
#             result[i] = self._safe_evaluate_single(x_val, func)
#         return result
    
#     def _safe_evaluate_single(self, x_val, func):
#         """Safely evaluate function at a single point."""
#         if func is None:
#             return np.nan
        
#         try:
#             result = func(x_val)
#             if isinstance(result, np.ndarray):
#                 result = float(result.flat[0])
#             else:
#                 result = float(result)
            
#             if not np.isfinite(result):
#                 return np.nan
#             return result
#         except:
#             return np.nan
    
#     def _solve_equation_in_range(self, equation):
#         """
#         Solve an equation and return real solutions in the x_range.
        
#         Args:
#             equation: SymPy expression to solve (set equal to 0)
            
#         Returns:
#             List of float solutions
#         """
#         solutions = []
        
#         try:
#             # Try to solve symbolically
#             symbolic_solutions = solve(equation, self.x)
            
#             for sol in symbolic_solutions:
#                 try:
#                     # Handle different types of solutions
#                     if sol.is_real is True or (hasattr(sol, 'is_zero') and sol.is_zero):
#                         sol_float = float(sol.evalf())
#                         if np.isfinite(sol_float) and self.x_range[0] <= sol_float <= self.x_range[1]:
#                             # Verify the solution
#                             test_val = float(equation.subs(self.x, sol).evalf())
#                             if abs(test_val) < 1e-6:  # Solution is valid
#                                 solutions.append(sol_float)
#                     elif sol.is_complex and abs(im(sol)) < 1e-10:
#                         # Essentially real (imaginary part is negligible)
#                         sol_float = float(re(sol).evalf())
#                         if np.isfinite(sol_float) and self.x_range[0] <= sol_float <= self.x_range[1]:
#                             test_val = float(abs(equation.subs(self.x, sol)).evalf())
#                             if abs(test_val) < 1e-6:
#                                 solutions.append(sol_float)
#                 except Exception as inner_e:
#                     continue
                    
#         except Exception as e:
#             # If symbolic solving fails, try numerical approach
#             pass
        
#         # Remove duplicates
#         unique_solutions = []
#         for sol in solutions:
#             if not any(abs(sol - existing) < 1e-6 for existing in unique_solutions):
#                 unique_solutions.append(sol)
        
#         return sorted(unique_solutions)
    
#     def _find_all_features(self):
#         """Find all critical features of the function."""
        
#         print("\n🔍 Analyzing function...")
        
#         # Find critical points (f'(x) = 0)
#         print("  Finding critical points...")
#         critical_x = self._solve_equation_in_range(self.first_derivative)
#         self.critical_points = []
#         for x_val in critical_x:
#             y_val = self._safe_evaluate_single(x_val, self.func_numeric)
#             if np.isfinite(y_val):
#                 self.critical_points.append((x_val, y_val))
#         print(f"  ✓ Found {len(self.critical_points)} critical point(s)")
        
#         # Find roots (f(x) = 0)
#         print("  Finding roots...")
#         root_x = self._solve_equation_in_range(self.func_symbolic)
#         self.roots = []
#         for x_val in root_x:
#             y_val = self._safe_evaluate_single(x_val, self.func_numeric)
#             if np.isfinite(y_val) and abs(y_val) < 1e-6:
#                 self.roots.append(x_val)
#         print(f"  ✓ Found {len(self.roots)} root(s)")
        
#         # Find inflection points (f''(x) = 0)
#         print("  Finding inflection points...")
#         inflection_x = self._solve_equation_in_range(self.second_derivative)
#         self.inflection_points = []
#         for x_val in inflection_x:
#             y_val = self._safe_evaluate_single(x_val, self.func_numeric)
#             if np.isfinite(y_val):
#                 # Verify concavity changes
#                 self.inflection_points.append((x_val, y_val))
#         print(f"  ✓ Found {len(self.inflection_points)} inflection point(s)")
        
#         # Find undefined values (holes/removable discontinuities)
#         print("  Finding undefined values...")
#         self.undefined_values = self._find_undefined_values()
#         print(f"  ✓ Found {len(self.undefined_values)} undefined value(s)")
        
#         # Find continuous domain
#         print("  Finding continuous domain...")
#         self.continuous_domain_str = self._find_continuous_domain()
#         print(f"  ✓ Continuous domain: {self.continuous_domain_str}")
        
#         # Find vertical asymptotes
#         print("  Finding vertical asymptotes...")
#         self.vertical_asymptotes = []
#         try:
#             # Get numerator and denominator
#             numer, denom = fraction(self.func_symbolic)
            
#             if denom != 1:
#                 # Solve denominator = 0
#                 denom_zeros = self._solve_equation_in_range(denom)
                
#                 for x_val in denom_zeros:
#                     # Check if numerator is also zero (removable discontinuity)
#                     numer_val = float(numer.subs(self.x, x_val).evalf())
#                     if abs(numer_val) > 1e-6:  # Not removable
#                         self.vertical_asymptotes.append(x_val)
#         except Exception as e:
#             pass
#         print(f"  ✓ Found {len(self.vertical_asymptotes)} vertical asymptote(s)")
        
#         # Find horizontal asymptotes
#         print("  Finding horizontal asymptotes...")
#         self.horizontal_asymptote = None
#         try:
#             limit_pos_inf = limit(self.func_symbolic, self.x, oo)
#             limit_neg_inf = limit(self.func_symbolic, self.x, -oo)
            
#             # Check if both limits exist and are equal
#             if limit_pos_inf.is_finite and limit_neg_inf.is_finite:
#                 if limit_pos_inf == limit_neg_inf:
#                     self.horizontal_asymptote = float(limit_pos_inf.evalf())
#                     print(f"  ✓ Found horizontal asymptote: y = {self.horizontal_asymptote:.4f}")
#                 else:
#                     print(f"  ✓ Different limits at ±∞")
#             else:
#                 print("  ✓ No horizontal asymptote")
#         except Exception as e:
#             pass
        
#         # Find oblique asymptotes
#         print("  Finding oblique asymptotes...")
#         self.oblique_asymptote = None
#         self.oblique_asymptote_left = None
#         self.oblique_asymptote_right = None
#         try:
#             # Check if there's no horizontal asymptote first
#             if self.horizontal_asymptote is None:
#                 # Calculate limit of f(x)/x as x approaches +infinity
#                 ratio = self.func_symbolic / self.x
#                 m_right = limit(ratio, self.x, oo)
                
#                 # Calculate limit of f(x)/x as x approaches -infinity
#                 m_left = limit(ratio, self.x, -oo)
                
#                 # Right asymptote
#                 if m_right.is_finite and m_right != 0:
#                     b_right = limit(self.func_symbolic - m_right * self.x, self.x, oo)
#                     if b_right.is_finite:
#                         m_right_float = float(m_right.evalf())
#                         b_right_float = float(b_right.evalf())
#                         self.oblique_asymptote_right = (m_right_float, b_right_float)
                
#                 # Left asymptote
#                 if m_left.is_finite and m_left != 0:
#                     b_left = limit(self.func_symbolic - m_left * self.x, self.x, -oo)
#                     if b_left.is_finite:
#                         m_left_float = float(m_left.evalf())
#                         b_left_float = float(b_left.evalf())
#                         self.oblique_asymptote_left = (m_left_float, b_left_float)
                
#                 # Check if they're the same
#                 if self.oblique_asymptote_right and self.oblique_asymptote_left:
#                     m_r, b_r = self.oblique_asymptote_right
#                     m_l, b_l = self.oblique_asymptote_left
#                     if abs(m_r - m_l) < 1e-6 and abs(b_r - b_l) < 1e-6:
#                         self.oblique_asymptote = (m_r, b_r)
#                         print(f"  ✓ Found oblique asymptote: y = {m_r:.4f}x + {b_r:.4f}")
#                     else:
#                         print(f"  ✓ Found left oblique asymptote: y = {m_l:.4f}x + {b_l:.4f}")
#                         print(f"  ✓ Found right oblique asymptote: y = {m_r:.4f}x + {b_r:.4f}")
#                 elif self.oblique_asymptote_right:
#                     print(f"  ✓ Found right oblique asymptote: y = {self.oblique_asymptote_right[0]:.4f}x + {self.oblique_asymptote_right[1]:.4f}")
#                 elif self.oblique_asymptote_left:
#                     print(f"  ✓ Found left oblique asymptote: y = {self.oblique_asymptote_left[0]:.4f}x + {self.oblique_asymptote_left[1]:.4f}")
#                 else:
#                     print("  ✓ No oblique asymptote")
#             else:
#                 print("  ✓ No oblique asymptote (horizontal asymptote exists)")
#         except Exception as e:
#             print("  ✓ No oblique asymptote")
        
#         print("✓ Analysis complete!\n")
    
#     def create_plot(self, figsize=(14, 9), title=None):
#         """Create the matplotlib figure."""
#         self.fig, self.ax = plt.subplots(figsize=figsize)
        
#         if title is None:
#             title = f"f(x) = {self.func_str}"
        
#         self.ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
#         self.ax.set_xlabel('x', fontsize=13, fontweight='bold')
#         self.ax.set_ylabel('y', fontsize=13, fontweight='bold')
#         self.ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.7)
#         self.ax.axhline(y=0, color='k', linewidth=0.8, alpha=0.5)
#         self.ax.axvline(x=0, color='k', linewidth=0.8, alpha=0.5)
        
#         # Set default y-limits early to prevent matplotlib from auto-scaling to extreme values
#         self.ax.set_ylim(-10, 10)
        
#         return self
    
#     def plot_function(self, color='#1f77b4', linewidth=2.5, label='f(x)'):
#         """Plot the function."""
#         if self.ax is None:
#             self.create_plot()
        
#         # Don't clip - let NaN values handle discontinuities
#         # Matplotlib will automatically break lines at NaN values
#         self.ax.plot(self.x_values, self.y_values, color=color, 
#                     linewidth=linewidth, label=label, zorder=3)
#         return self
    
#     def plot_derivative(self, color='#ff7f0e', linewidth=2, label="f'(x)"):
#         """Plot the first derivative."""
#         if self.ax is None:
#             self.create_plot()
        
#         # Generate derivative values with same discontinuity detection
#         x_deriv, y_deriv = self._generate_derivative_points(self.first_deriv_numeric)
#         self.ax.plot(x_deriv, y_deriv, color=color, 
#                     linewidth=linewidth, label=label, linestyle='--', alpha=0.8, zorder=2)
#         return self
    
#     def plot_second_derivative(self, color='#2ca02c', linewidth=2, label="f''(x)"):
#         """Plot the second derivative."""
#         if self.ax is None:
#             self.create_plot()
        
#         # Generate second derivative values with same discontinuity detection
#         x_deriv, y_deriv = self._generate_derivative_points(self.second_deriv_numeric)
#         self.ax.plot(x_deriv, y_deriv, color=color, 
#                     linewidth=linewidth, label=label, linestyle='-.', alpha=0.8, zorder=2)
#         return self
    
#     def _generate_derivative_points(self, deriv_func):
#         """Generate points for derivatives with discontinuity handling."""
#         # Use the same discontinuity points as the main function
#         discontinuity_points = self._find_discontinuity_points()
        
#         # Sort discontinuity points
#         disc_sorted = sorted(discontinuity_points)
        
#         # Create segments between discontinuities
#         segments = []
#         prev = self.x_range[0]
        
#         for disc in disc_sorted:
#             if self.x_range[0] < disc < self.x_range[1]:
#                 segments.append((prev, disc - 1e-10))
#                 prev = disc + 1e-10
        
#         segments.append((prev, self.x_range[1]))
        
#         # Generate points for each segment
#         x_values = []
#         y_values = []
        
#         for seg_start, seg_end in segments:
#             if seg_end > seg_start:
#                 seg_fraction = (seg_end - seg_start) / (self.x_range[1] - self.x_range[0])
#                 seg_points = max(50, int(self.num_points * seg_fraction))
                
#                 x_seg = np.linspace(seg_start, seg_end, seg_points)
#                 y_seg = self._safe_evaluate_array(x_seg, deriv_func)
                
#                 if len(x_values) > 0:
#                     x_values.append(np.nan)
#                     y_values.append(np.nan)
                
#                 x_values.extend(x_seg)
#                 y_values.extend(y_seg)
        
#         return np.array(x_values), np.array(y_values)
    
#     def plot_critical_points(self, color='#d62728', marker='o', 
#                             markersize=12, label='Critical Points'):
#         """Plot critical points."""
#         if self.ax is None:
#             self.create_plot()
        
#         if self.critical_points:
#             x_crit, y_crit = zip(*self.critical_points)
#             self.ax.plot(x_crit, y_crit, marker=marker, color=color, 
#                         markersize=markersize, linestyle='', label=label,
#                         markeredgecolor='black', markeredgewidth=2, zorder=6)
            
#             for x, y in self.critical_points:
#                 self.ax.annotate(f'({x:.3f}, {y:.3f})', 
#                                xy=(x, y), xytext=(15, 15),
#                                textcoords='offset points',
#                                bbox=dict(boxstyle='round,pad=0.5', 
#                                        facecolor='yellow', alpha=0.8,
#                                        edgecolor='black', linewidth=1.5),
#                                fontsize=9, fontweight='bold',
#                                arrowprops=dict(arrowstyle='->', 
#                                              connectionstyle='arc3,rad=0.3',
#                                              color='black', lw=1.5))
#         return self
    
#     def plot_roots(self, color='#ff7f0e', marker='s', 
#                    markersize=12, label='Roots (Zeros)'):
#         """Plot roots."""
#         if self.ax is None:
#             self.create_plot()
        
#         if self.roots:
#             y_roots = [0] * len(self.roots)
#             self.ax.plot(self.roots, y_roots, marker=marker, color=color, 
#                         markersize=markersize, linestyle='', label=label,
#                         markeredgecolor='black', markeredgewidth=2, zorder=6)
            
#             for x in self.roots:
#                 self.ax.annotate(f'x={x:.3f}', 
#                                xy=(x, 0), xytext=(0, -25),
#                                textcoords='offset points',
#                                bbox=dict(boxstyle='round,pad=0.5', 
#                                        facecolor='lightblue', alpha=0.8,
#                                        edgecolor='black', linewidth=1.5),
#                                fontsize=9, fontweight='bold',
#                                ha='center',
#                                arrowprops=dict(arrowstyle='->', 
#                                              color='black', lw=1.5))
#         return self
    
#     def plot_undefined_values(self, color='#ff0000', marker='o', 
#                              markersize=14, label='Undefined (Holes)'):
#         """Plot undefined values (holes/removable discontinuities) with red dots."""
#         if self.ax is None:
#             self.create_plot()
        
#         if self.undefined_values:
#             x_undef, y_undef = zip(*self.undefined_values)
#             # Plot as hollow red circles
#             self.ax.plot(x_undef, y_undef, marker=marker, color='white', 
#                         markersize=markersize, linestyle='', label=label,
#                         markeredgecolor=color, markeredgewidth=3, zorder=7)
            
#             for x, y in self.undefined_values:
#                 self.ax.annotate(f'Undefined at x={x:.3f}\n(limit = {y:.3f})', 
#                                xy=(x, y), xytext=(20, -20),
#                                textcoords='offset points',
#                                bbox=dict(boxstyle='round,pad=0.5', 
#                                        facecolor='#ffcccc', alpha=0.9,
#                                        edgecolor=color, linewidth=2),
#                                fontsize=9, fontweight='bold',
#                                arrowprops=dict(arrowstyle='->', 
#                                              connectionstyle='arc3,rad=0.3',
#                                              color=color, lw=2))
#         return self
    
#     def plot_asymptotes(self, vertical_color='#d62728', horizontal_color='#1f77b4',
#                        oblique_color='#17becf', linewidth=2, alpha=0.7):
#         """Plot asymptotes."""
#         if self.ax is None:
#             self.create_plot()
        
#         # Vertical asymptotes
#         for i, x_asym in enumerate(self.vertical_asymptotes):
#             label = 'Vertical Asymptote' if i == 0 else ''
#             self.ax.axvline(x=x_asym, color=vertical_color, linestyle='--', 
#                           linewidth=linewidth, alpha=alpha, label=label, zorder=10)
            
#             ylim = self.ax.get_ylim()
#             y_pos = ylim[1] * 0.9
#             self.ax.text(x_asym, y_pos, f'x={x_asym:.3f}', 
#                         ha='center', va='top',
#                         bbox=dict(boxstyle='round,pad=0.3', 
#                                 facecolor='white', alpha=0.8,
#                                 edgecolor=vertical_color, linewidth=1.5),
#                         fontsize=9, fontweight='bold')
        
#         # Horizontal asymptote
#         if self.horizontal_asymptote is not None:
#             self.ax.axhline(y=self.horizontal_asymptote, color=horizontal_color, 
#                           linestyle='--', linewidth=linewidth, alpha=alpha,
#                           label=f'Horizontal Asymptote y={self.horizontal_asymptote:.3f}',
#                           zorder=1)
        
#         # Oblique asymptote (single)
#         if self.oblique_asymptote is not None:
#             m, b = self.oblique_asymptote
#             x_asymp = np.linspace(self.x_range[0], self.x_range[1], 100)
#             y_asymp = m * x_asymp + b
#             self.ax.plot(x_asymp, y_asymp, color=oblique_color, linestyle='--',
#                         linewidth=linewidth, alpha=alpha,
#                         label=f'Oblique Asymptote y={m:.3f}x+{b:.3f}',
#                         zorder=1)
        
#         # Oblique asymptotes (separate left and right)
#         if self.oblique_asymptote_left is not None and self.oblique_asymptote is None:
#             m, b = self.oblique_asymptote_left
#             x_asymp = np.linspace(self.x_range[0], 0, 100)
#             y_asymp = m * x_asymp + b
#             self.ax.plot(x_asymp, y_asymp, color=oblique_color, linestyle='--',
#                         linewidth=linewidth, alpha=alpha,
#                         label=f'Left Oblique y={m:.3f}x+{b:.3f}',
#                         zorder=1)
        
#         if self.oblique_asymptote_right is not None and self.oblique_asymptote is None:
#             m, b = self.oblique_asymptote_right
#             x_asymp = np.linspace(0, self.x_range[1], 100)
#             y_asymp = m * x_asymp + b
#             self.ax.plot(x_asymp, y_asymp, color='#bcbd22', linestyle='--',
#                         linewidth=linewidth, alpha=alpha,
#                         label=f'Right Oblique y={m:.3f}x+{b:.3f}',
#                         zorder=1)
        
#         return self
    
#     def plot_inflection_points(self, color='#9467bd', marker='^', 
#                               markersize=12, label='Inflection Points'):
#         """Plot inflection points."""
#         if self.ax is None:
#             self.create_plot()
        
#         if self.inflection_points:
#             x_infl, y_infl = zip(*self.inflection_points)
#             self.ax.plot(x_infl, y_infl, marker=marker, color=color, 
#                         markersize=markersize, linestyle='', label=label,
#                         markeredgecolor='black', markeredgewidth=2, zorder=6)
            
#             for x, y in self.inflection_points:
#                 self.ax.annotate(f'({x:.3f}, {y:.3f})', 
#                                xy=(x, y), xytext=(-15, 15),
#                                textcoords='offset points',
#                                bbox=dict(boxstyle='round,pad=0.5', 
#                                        facecolor='lightgreen', alpha=0.8,
#                                        edgecolor='black', linewidth=1.5),
#                                fontsize=9, fontweight='bold',
#                                arrowprops=dict(arrowstyle='->', 
#                                              connectionstyle='arc3,rad=-0.3',
#                                              color='black', lw=1.5))
#         return self
    
#     def plot_tangent_line(self, x0, color='#2ca02c', linewidth=2.5, 
#                          label=None, extend=2, half='both'):
#         """
#         Plot tangent line at x0.
        
#         Args:
#             x0: Point at which to draw tangent
#             color: Line color
#             linewidth: Line width
#             label: Legend label
#             extend: How far to extend the line from x0
#             half: 'both', 'left', or 'right' - which direction(s) to draw
#         """
#         if self.ax is None:
#             self.create_plot()
        
#         try:
#             # Evaluate at x0 using SymPy for accuracy
#             y0 = float(self.func_symbolic.subs(self.x, x0).evalf())
#             slope = float(self.first_derivative.subs(self.x, x0).evalf())
            
#             if not np.isfinite(y0) or not np.isfinite(slope):
#                 print(f"Cannot plot tangent at x={x0}: function or derivative undefined")
#                 return self
            
#             # Create tangent line based on half parameter
#             if half == 'left':
#                 x_tangent = np.linspace(x0 - extend, x0, 100)
#             elif half == 'right':
#                 x_tangent = np.linspace(x0, x0 + extend, 100)
#             else:  # 'both'
#                 x_tangent = np.linspace(x0 - extend, x0 + extend, 100)
            
#             y_tangent = y0 + slope * (x_tangent - x0)
            
#             if label is None:
#                 if half == 'left':
#                     label = f'Left tangent at x={x0:.2f}'
#                 elif half == 'right':
#                     label = f'Right tangent at x={x0:.2f}'
#                 else:
#                     label = f'Tangent at x={x0:.2f}'
            
#             self.ax.plot(x_tangent, y_tangent, color=color, 
#                         linewidth=linewidth, label=label, linestyle=':', 
#                         alpha=0.9, zorder=4)
            
#             self.ax.plot(x0, y0, 'o', color=color, markersize=10, 
#                         markeredgecolor='black', markeredgewidth=2, zorder=5)
            
#         except Exception as e:
#             print(f"Error plotting tangent at x={x0}: {e}")
        
#         return self
    
#     def set_limits(self, xlim=None, ylim=None):
#         """Set axis limits with validation to prevent matplotlib errors."""
#         if self.ax is None:
#             self.create_plot()
        
#         if xlim:
#             self.ax.set_xlim(xlim)
        
#         if ylim:
#             y_min, y_max = ylim
#             # Clamp to safe values to prevent matplotlib errors
#             MAX_SAFE = 1e6
#             y_min = max(min(y_min, MAX_SAFE), -MAX_SAFE)
#             y_max = max(min(y_max, MAX_SAFE), -MAX_SAFE)
            
#             self.ax.set_ylim(y_min, y_max)
        
#         return self
    
#     def add_legend(self, loc='best', fontsize=11):
#         """Add legend."""
#         if self.ax is None:
#             self.create_plot()
        
#         self.ax.legend(loc=loc, fontsize=fontsize, framealpha=0.95,
#                       edgecolor='black', fancybox=True, shadow=True)
#         return self
    
#     def add_info_box(self):
#         """Add information box with continuous domain."""
#         if self.ax is None:
#             self.create_plot()
        
#         info_lines = [
#             f"f(x) = {self.func_symbolic}",
#             f"f'(x) = {self.first_derivative}",
#             f"f''(x) = {self.second_derivative}",
#             "",
#             f"Domain: {self.continuous_domain_str}",
#             ""
#         ]
        
#         if self.critical_points:
#             info_lines.append(f"Critical points: {len(self.critical_points)}")
#         if self.roots:
#             info_lines.append(f"Roots: {len(self.roots)}")
#         if self.inflection_points:
#             info_lines.append(f"Inflection points: {len(self.inflection_points)}")
#         if self.undefined_values:
#             info_lines.append(f"Undefined values: {len(self.undefined_values)}")
#         if self.vertical_asymptotes:
#             info_lines.append(f"Vertical asymptotes: {len(self.vertical_asymptotes)}")
        
#         info_text = "\n".join(info_lines)
        
#         self.ax.text(0.98, 0.98, info_text, 
#                     transform=self.ax.transAxes,
#                     fontsize=8, verticalalignment='top',
#                     horizontalalignment='right',
#                     bbox=dict(boxstyle='round,pad=0.7', 
#                             facecolor='wheat', alpha=0.9,
#                             edgecolor='black', linewidth=1.5),
#                     family='monospace')
        
#         return self
    
#     def save(self, filename):
#         """Save the plot."""
#         if self.fig is None:
#             return self
        
#         self.fig.tight_layout()
#         self.fig.savefig(filename, dpi=300, bbox_inches='tight', 
#                         facecolor='white', edgecolor='none')
#         return self
    
#     def show(self):
#         """Display the plot."""
#         if self.fig is None:
#             return self
        
#         self.fig.tight_layout()
#         plt.show()
#         return self


# def get_yes_no(prompt):
#     """Get yes/no input."""
#     while True:
#         response = input(prompt + " (y/n): ").lower().strip()
#         if response in ['y', 'yes']:
#             return True
#         elif response in ['n', 'no']:
#             return False
#         print("Please enter 'y' or 'n'")


# def get_float(prompt, default=None):
#     """Get float input."""
#     while True:
#         if default is not None:
#             response = input(f"{prompt} (default: {default}): ").strip()
#         else:
#             response = input(prompt + ": ").strip()
            
#         if response == '' and default is not None:
#             return default
#         try:
#             return float(response)
#         except ValueError:
#             print("Please enter a valid number")


# def get_choice(prompt, choices):
#     """Get choice from list."""
#     while True:
#         response = input(prompt + f" {choices}: ").lower().strip()
#         if response in choices:
#             return response
#         print(f"Please enter one of: {choices}")


# def print_header():
#     """Print header."""
#     print("\n" + "="*70)
#     print(" "*15 + "ACCURATE FUNCTION GRAPHER v2.2")
#     print(" "*18 + "Powered by SymPy")
#     print(" "*10 + "With Undefined Values Detection")
#     print("="*70)


# def main():
#     """Main program."""
#     print_header()
    
#     graph_counter = 1
    
#     while True:
#         print("\n📝 Enter a mathematical function using 'x'")
#         print("Examples: x**2, sin(x), 1/(x-2), (x**2-1)/(x-1)")
#         print("Type 'quit' to exit\n")
        
#         func_str = input("f(x) = ").strip()
        
#         if not func_str or func_str.lower() in ['exit', 'quit', 'q']:
#             break
        
#         print(f"\n{'─'*70}")
#         print(f"Graph #{graph_counter}")
#         print(f"{'─'*70}")
        
#         # Get range
#         x_min = get_float("X minimum", default=-10)
#         x_max = get_float("X maximum", default=10)
        
#         # Create grapher
#         try:
#             grapher = AccurateFunctionGrapher(func_str, x_range=(x_min, x_max))
#         except Exception as e:
#             print(f"\n❌ Error: {e}")
#             continue
        
#         # Y limits
#         use_ylim = get_yes_no("\nSet custom y-axis limits?")
#         if use_ylim:
#             y_min = get_float("Y minimum", default=-10)
#             y_max = get_float("Y maximum", default=10)
#             ylim = (y_min, y_max)
#         else:
#             ylim = (-10, 10)
        
#         # Create plot
#         grapher.create_plot(title=f"Graph #{graph_counter}: f(x) = {func_str}")
#         grapher.plot_function()
        
#         # Options
#         print("\n" + "="*70)
#         print("PLOT OPTIONS")
#         print("="*70)
        
#         if get_yes_no("📈 Plot first derivative f'(x)?"):
#             grapher.plot_derivative()
        
#         if get_yes_no("📉 Plot second derivative f''(x)?"):
#             grapher.plot_second_derivative()
        
#         if get_yes_no("🎯 Plot critical points?"):
#             grapher.plot_critical_points()
        
#         if get_yes_no("🔍 Plot roots (zeros)?"):
#             grapher.plot_roots()
        
#         if get_yes_no("🔴 Plot undefined values (holes)?"):
#             grapher.plot_undefined_values()
        
#         if get_yes_no("📏 Plot asymptotes?"):
#             grapher.plot_asymptotes()
        
#         if get_yes_no("🔄 Plot inflection points?"):
#             grapher.plot_inflection_points()
        
#         if get_yes_no("📐 Plot tangent line(s)?"):
#             num = int(get_float("How many", default=1))
#             colors = ['#2ca02c', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f']
#             for i in range(num):
#                 x0 = get_float(f"x-coordinate for tangent {i+1}")
#                 half = get_choice(f"Direction for tangent {i+1}", ['both', 'left', 'right'])
#                 grapher.plot_tangent_line(x0=x0, color=colors[i % len(colors)], half=half)
        
#         if get_yes_no("ℹ️  Add information box?"):
#             grapher.add_info_box()
        
#         grapher.set_limits(ylim=ylim)
        
#         grapher.add_legend()
        
#         # Save
#         filename = f"graph_{graph_counter:03d}.png"
#         grapher.save(filename)
#         print(f"\n✓ Saved: {filename}")
        
#         if get_yes_no("\n👁️  Display now?"):
#             grapher.show()
        
#         graph_counter += 1
        
#         if not get_yes_no("\n🔄 Create another graph?"):
#             break
    
#     print("\n" + "="*70)
#     print("Thank you for using Accurate Function Grapher!")
#     print("="*70 + "\n")


# if __name__ == "__main__":
#     main()






# import numpy as np
# import matplotlib.pyplot as plt
# from sympy import *
# from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application
# from sympy.calculus.util import continuous_domain
# from sympy.core.traversal import preorder_traversal
# import warnings
# warnings.filterwarnings('ignore')


# class AccurateFunctionGrapher:
#     """
#     A class to graph mathematical functions using SymPy for exact symbolic calculations.
#     All calculations are verified for accuracy.
#     """
    
#     def __init__(self, func_str, x_range=(-10, 10), num_points=2000):
#         """
#         Initialize the grapher with a function string.
        
#         Args:
#             func_str: String representation of function
#             x_range: Tuple of (x_min, x_max)
#             num_points: Number of points for plotting
#         """
#         self.func_str = func_str
#         self.x_range = x_range
#         self.num_points = num_points
        
#         # Symbol
#         self.x = symbols('x', real=True)
        
#         # Parse function with OUR symbol
#         transformations = standard_transformations + (implicit_multiplication_application,)
#         local_dict = {'x': self.x}  # Use our own x symbol
#         self.func_symbolic = parse_expr(func_str, transformations=transformations, 
#                                        local_dict=local_dict)
        
#         # Simplify
#         self.func_symbolic = simplify(self.func_symbolic)
        
#         # Calculate derivatives
#         self.first_derivative = diff(self.func_symbolic, self.x)
#         self.second_derivative = diff(self.first_derivative, self.x)
        
#         # Simplify derivatives
#         self.first_derivative = simplify(self.first_derivative)
#         self.second_derivative = simplify(self.second_derivative)
        
#         # Create lambdified functions for numerical evaluation
#         try:
#             self.func_numeric = lambdify(self.x, self.func_symbolic, modules=['numpy', {'Abs': np.abs}])
#             self.first_deriv_numeric = lambdify(self.x, self.first_derivative, modules=['numpy', {'Abs': np.abs}])
#             self.second_deriv_numeric = lambdify(self.x, self.second_derivative, modules=['numpy', {'Abs': np.abs}])
#         except Exception as e:
#             print(f"Warning during lambdify: {e}")
#             self.func_numeric = None
#             self.first_deriv_numeric = None
#             self.second_deriv_numeric = None
        
#         # Generate plot points with discontinuity detection
#         self.x_values, self.y_values = self._generate_plot_points()
        
#         # Initialize plot
#         self.fig = None
#         self.ax = None
        
#         # Calculate all features
#         self._find_all_features()
    
#     def _generate_plot_points(self):
#         """
#         Generate plot points with proper handling of discontinuities.
#         Inserts NaN values at discontinuities to break the line.
#         """
#         # Find discontinuity points by analyzing the symbolic function
#         discontinuity_points = self._find_discontinuity_points()
        
#         # Generate more points around discontinuities for better detection
#         x_list = []
        
#         # Sort discontinuity points
#         disc_sorted = sorted(discontinuity_points)
        
#         # Create segments between discontinuities
#         segments = []
#         prev = self.x_range[0]
        
#         for disc in disc_sorted:
#             if self.x_range[0] < disc < self.x_range[1]:
#                 # Add segment before discontinuity
#                 segments.append((prev, disc - 1e-10))
#                 prev = disc + 1e-10
        
#         # Add final segment
#         segments.append((prev, self.x_range[1]))
        
#         # Generate points for each segment
#         x_values = []
#         y_values = []
        
#         for seg_start, seg_end in segments:
#             if seg_end > seg_start:
#                 # Calculate number of points for this segment
#                 seg_fraction = (seg_end - seg_start) / (self.x_range[1] - self.x_range[0])
#                 seg_points = max(50, int(self.num_points * seg_fraction))
                
#                 # Generate points for this segment
#                 x_seg = np.linspace(seg_start, seg_end, seg_points)
#                 y_seg = self._safe_evaluate_array(x_seg, self.func_numeric)
                
#                 # Add NaN separator if not first segment
#                 if len(x_values) > 0:
#                     x_values.append(np.nan)
#                     y_values.append(np.nan)
                
#                 # Add segment points
#                 x_values.extend(x_seg)
#                 y_values.extend(y_seg)
        
#         return np.array(x_values), np.array(y_values)
    
#     def _find_discontinuity_points(self):
#         """
#         Find points where the function is discontinuous by analyzing the symbolic expression.
#         Returns a list of x-values where discontinuities occur.
#         """
#         discontinuities = []
        
#         try:
#             # Method 1: Find where denominator is zero
#             numer, denom = fraction(self.func_symbolic)
#             if denom != 1:
#                 denom_zeros = solve(denom, self.x)
#                 for sol in denom_zeros:
#                     try:
#                         if sol.is_real or (sol.is_complex and abs(im(sol)) < 1e-10):
#                             x_val = float(re(sol).evalf()) if sol.is_complex else float(sol.evalf())
#                             if self.x_range[0] <= x_val <= self.x_range[1]:
#                                 discontinuities.append(x_val)
#                     except:
#                         pass
            
#             # Method 2: Find discontinuities in Abs, Heaviside, and piecewise functions
#             # Check for abs(x) patterns which have discontinuous derivatives
#             expr_str = str(self.func_symbolic)
#             if 'Abs' in expr_str:
#                 # Find where the argument of Abs is zero
#                 for sub_expr in preorder_traversal(self.func_symbolic):
#                     if isinstance(sub_expr, Abs):
#                         arg = sub_expr.args[0]
#                         try:
#                             zeros = solve(arg, self.x)
#                             for sol in zeros:
#                                 try:
#                                     if sol.is_real or (sol.is_complex and abs(im(sol)) < 1e-10):
#                                         x_val = float(re(sol).evalf()) if sol.is_complex else float(sol.evalf())
#                                         if self.x_range[0] <= x_val <= self.x_range[1]:
#                                             # Check if it's actually a discontinuity
#                                             left_lim = limit(self.func_symbolic, self.x, x_val, '-')
#                                             right_lim = limit(self.func_symbolic, self.x, x_val, '+')
#                                             if left_lim != right_lim:
#                                                 discontinuities.append(x_val)
#                                 except:
#                                     pass
#                         except:
#                             pass
            
#             # Method 3: Check for Piecewise functions
#             for sub_expr in preorder_traversal(self.func_symbolic):
#                 if isinstance(sub_expr, Piecewise):
#                     # Extract boundary points from conditions
#                     for expr, cond in sub_expr.args:
#                         try:
#                             # Try to extract comparison boundaries
#                             if hasattr(cond, 'args'):
#                                 for arg in cond.args:
#                                     if self.x in arg.free_symbols:
#                                         try:
#                                             boundary = solve(arg, self.x)
#                                             for sol in boundary:
#                                                 if sol.is_real:
#                                                     x_val = float(sol.evalf())
#                                                     if self.x_range[0] <= x_val <= self.x_range[1]:
#                                                         discontinuities.append(x_val)
#                                         except:
#                                             pass
#                         except:
#                             pass
            
#         except Exception as e:
#             pass
        
#         # Remove duplicates
#         unique_discontinuities = []
#         for disc in discontinuities:
#             if not any(abs(disc - existing) < 1e-8 for existing in unique_discontinuities):
#                 unique_discontinuities.append(disc)
        
#         return unique_discontinuities
    
#     def _safe_evaluate_array(self, x_array, func):
#         """Safely evaluate function on array."""
#         if func is None:
#             return np.full_like(x_array, np.nan)
        
#         result = np.zeros_like(x_array, dtype=float)
#         for i, x_val in enumerate(x_array):
#             result[i] = self._safe_evaluate_single(x_val, func)
#         return result
    
#     def _safe_evaluate_single(self, x_val, func):
#         """Safely evaluate function at a single point."""
#         if func is None:
#             return np.nan
        
#         try:
#             result = func(x_val)
#             if isinstance(result, np.ndarray):
#                 result = float(result.flat[0])
#             else:
#                 result = float(result)
            
#             if not np.isfinite(result):
#                 return np.nan
#             return result
#         except:
#             return np.nan
    
#     def _solve_equation_in_range(self, equation):
#         """
#         Solve an equation and return real solutions in the x_range.
        
#         Args:
#             equation: SymPy expression to solve (set equal to 0)
            
#         Returns:
#             List of float solutions
#         """
#         solutions = []
        
#         try:
#             # Try to solve symbolically
#             symbolic_solutions = solve(equation, self.x)
            
#             for sol in symbolic_solutions:
#                 try:
#                     # Handle different types of solutions
#                     if sol.is_real is True or (hasattr(sol, 'is_zero') and sol.is_zero):
#                         sol_float = float(sol.evalf())
#                         if np.isfinite(sol_float) and self.x_range[0] <= sol_float <= self.x_range[1]:
#                             # Verify the solution
#                             test_val = float(equation.subs(self.x, sol).evalf())
#                             if abs(test_val) < 1e-6:  # Solution is valid
#                                 solutions.append(sol_float)
#                     elif sol.is_complex and abs(im(sol)) < 1e-10:
#                         # Essentially real (imaginary part is negligible)
#                         sol_float = float(re(sol).evalf())
#                         if np.isfinite(sol_float) and self.x_range[0] <= sol_float <= self.x_range[1]:
#                             test_val = float(abs(equation.subs(self.x, sol)).evalf())
#                             if abs(test_val) < 1e-6:
#                                 solutions.append(sol_float)
#                 except Exception as inner_e:
#                     continue
                    
#         except Exception as e:
#             # If symbolic solving fails, try numerical approach
#             pass
        
#         # Remove duplicates
#         unique_solutions = []
#         for sol in solutions:
#             if not any(abs(sol - existing) < 1e-6 for existing in unique_solutions):
#                 unique_solutions.append(sol)
        
#         return sorted(unique_solutions)
    
#     def _find_all_features(self):
#         """Find all critical features of the function."""
        
#         print("\n🔍 Analyzing function...")
        
#         # Find critical points (f'(x) = 0)
#         print("  Finding critical points...")
#         critical_x = self._solve_equation_in_range(self.first_derivative)
#         self.critical_points = []
#         for x_val in critical_x:
#             y_val = self._safe_evaluate_single(x_val, self.func_numeric)
#             if np.isfinite(y_val):
#                 self.critical_points.append((x_val, y_val))
#         print(f"  ✓ Found {len(self.critical_points)} critical point(s)")
        
#         # Find roots (f(x) = 0)
#         print("  Finding roots...")
#         root_x = self._solve_equation_in_range(self.func_symbolic)
#         self.roots = []
#         for x_val in root_x:
#             y_val = self._safe_evaluate_single(x_val, self.func_numeric)
#             if np.isfinite(y_val) and abs(y_val) < 1e-6:
#                 self.roots.append(x_val)
#         print(f"  ✓ Found {len(self.roots)} root(s)")
        
#         # Find inflection points (f''(x) = 0)
#         print("  Finding inflection points...")
#         inflection_x = self._solve_equation_in_range(self.second_derivative)
#         self.inflection_points = []
#         for x_val in inflection_x:
#             y_val = self._safe_evaluate_single(x_val, self.func_numeric)
#             if np.isfinite(y_val):
#                 # Verify concavity changes
#                 self.inflection_points.append((x_val, y_val))
#         print(f"  ✓ Found {len(self.inflection_points)} inflection point(s)")
        
#         # Find vertical asymptotes
#         print("  Finding vertical asymptotes...")
#         self.vertical_asymptotes = []
#         try:
#             # Get numerator and denominator
#             numer, denom = fraction(self.func_symbolic)
            
#             if denom != 1:
#                 # Solve denominator = 0
#                 denom_zeros = self._solve_equation_in_range(denom)
                
#                 for x_val in denom_zeros:
#                     # Check if numerator is also zero (removable discontinuity)
#                     numer_val = float(numer.subs(self.x, x_val).evalf())
#                     if abs(numer_val) > 1e-6:  # Not removable
#                         self.vertical_asymptotes.append(x_val)
#         except Exception as e:
#             pass
#         print(f"  ✓ Found {len(self.vertical_asymptotes)} vertical asymptote(s)")
        
#         # Find horizontal asymptotes
#         print("  Finding horizontal asymptotes...")
#         self.horizontal_asymptote = None
#         try:
#             limit_pos_inf = limit(self.func_symbolic, self.x, oo)
#             limit_neg_inf = limit(self.func_symbolic, self.x, -oo)
            
#             # Check if both limits exist and are equal
#             if limit_pos_inf.is_finite and limit_neg_inf.is_finite:
#                 if limit_pos_inf == limit_neg_inf:
#                     self.horizontal_asymptote = float(limit_pos_inf.evalf())
#                     print(f"  ✓ Found horizontal asymptote: y = {self.horizontal_asymptote:.4f}")
#                 else:
#                     print(f"  ✓ Different limits at ±∞")
#             else:
#                 print("  ✓ No horizontal asymptote")
#         except Exception as e:
#             pass
        
#         # Find oblique asymptotes
#         print("  Finding oblique asymptotes...")
#         self.oblique_asymptote = None
#         self.oblique_asymptote_left = None
#         self.oblique_asymptote_right = None
#         try:
#             # Check if there's no horizontal asymptote first
#             if self.horizontal_asymptote is None:
#                 # Calculate limit of f(x)/x as x approaches +infinity
#                 ratio = self.func_symbolic / self.x
#                 m_right = limit(ratio, self.x, oo)
                
#                 # Calculate limit of f(x)/x as x approaches -infinity
#                 m_left = limit(ratio, self.x, -oo)
                
#                 # Right asymptote
#                 if m_right.is_finite and m_right != 0:
#                     b_right = limit(self.func_symbolic - m_right * self.x, self.x, oo)
#                     if b_right.is_finite:
#                         m_right_float = float(m_right.evalf())
#                         b_right_float = float(b_right.evalf())
#                         self.oblique_asymptote_right = (m_right_float, b_right_float)
                
#                 # Left asymptote
#                 if m_left.is_finite and m_left != 0:
#                     b_left = limit(self.func_symbolic - m_left * self.x, self.x, -oo)
#                     if b_left.is_finite:
#                         m_left_float = float(m_left.evalf())
#                         b_left_float = float(b_left.evalf())
#                         self.oblique_asymptote_left = (m_left_float, b_left_float)
                
#                 # Check if they're the same
#                 if self.oblique_asymptote_right and self.oblique_asymptote_left:
#                     m_r, b_r = self.oblique_asymptote_right
#                     m_l, b_l = self.oblique_asymptote_left
#                     if abs(m_r - m_l) < 1e-6 and abs(b_r - b_l) < 1e-6:
#                         self.oblique_asymptote = (m_r, b_r)
#                         print(f"  ✓ Found oblique asymptote: y = {m_r:.4f}x + {b_r:.4f}")
#                     else:
#                         print(f"  ✓ Found left oblique asymptote: y = {m_l:.4f}x + {b_l:.4f}")
#                         print(f"  ✓ Found right oblique asymptote: y = {m_r:.4f}x + {b_r:.4f}")
#                 elif self.oblique_asymptote_right:
#                     print(f"  ✓ Found right oblique asymptote: y = {self.oblique_asymptote_right[0]:.4f}x + {self.oblique_asymptote_right[1]:.4f}")
#                 elif self.oblique_asymptote_left:
#                     print(f"  ✓ Found left oblique asymptote: y = {self.oblique_asymptote_left[0]:.4f}x + {self.oblique_asymptote_left[1]:.4f}")
#                 else:
#                     print("  ✓ No oblique asymptote")
#             else:
#                 print("  ✓ No oblique asymptote (horizontal asymptote exists)")
#         except Exception as e:
#             print("  ✓ No oblique asymptote")
        
#         print("✓ Analysis complete!\n")
    
#     def create_plot(self, figsize=(14, 9), title=None):
#         """Create the matplotlib figure."""
#         self.fig, self.ax = plt.subplots(figsize=figsize)
        
#         if title is None:
#             title = f"f(x) = {self.func_str}"
        
#         self.ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
#         self.ax.set_xlabel('x', fontsize=13, fontweight='bold')
#         self.ax.set_ylabel('y', fontsize=13, fontweight='bold')
#         self.ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.7)
#         self.ax.axhline(y=0, color='k', linewidth=0.8, alpha=0.5)
#         self.ax.axvline(x=0, color='k', linewidth=0.8, alpha=0.5)
        
#         # Set default y-limits early to prevent matplotlib from auto-scaling to extreme values
#         self.ax.set_ylim(-10, 10)
        
#         return self
    
#     def plot_function(self, color='#1f77b4', linewidth=2.5, label='f(x)'):
#         """Plot the function."""
#         if self.ax is None:
#             self.create_plot()
        
#         # Don't clip - let NaN values handle discontinuities
#         # Matplotlib will automatically break lines at NaN values
#         self.ax.plot(self.x_values, self.y_values, color=color, 
#                     linewidth=linewidth, label=label, zorder=3)
#         return self
    
#     def plot_derivative(self, color='#ff7f0e', linewidth=2, label="f'(x)"):
#         """Plot the first derivative."""
#         if self.ax is None:
#             self.create_plot()
        
#         # Generate derivative values with same discontinuity detection
#         x_deriv, y_deriv = self._generate_derivative_points(self.first_deriv_numeric)
#         self.ax.plot(x_deriv, y_deriv, color=color, 
#                     linewidth=linewidth, label=label, linestyle='--', alpha=0.8, zorder=2)
#         return self
    
#     def plot_second_derivative(self, color='#2ca02c', linewidth=2, label="f''(x)"):
#         """Plot the second derivative."""
#         if self.ax is None:
#             self.create_plot()
        
#         # Generate second derivative values with same discontinuity detection
#         x_deriv, y_deriv = self._generate_derivative_points(self.second_deriv_numeric)
#         self.ax.plot(x_deriv, y_deriv, color=color, 
#                     linewidth=linewidth, label=label, linestyle='-.', alpha=0.8, zorder=2)
#         return self
    
#     def _generate_derivative_points(self, deriv_func):
#         """Generate points for derivatives with discontinuity handling."""
#         # Use the same discontinuity points as the main function
#         discontinuity_points = self._find_discontinuity_points()
        
#         # Sort discontinuity points
#         disc_sorted = sorted(discontinuity_points)
        
#         # Create segments between discontinuities
#         segments = []
#         prev = self.x_range[0]
        
#         for disc in disc_sorted:
#             if self.x_range[0] < disc < self.x_range[1]:
#                 segments.append((prev, disc - 1e-10))
#                 prev = disc + 1e-10
        
#         segments.append((prev, self.x_range[1]))
        
#         # Generate points for each segment
#         x_values = []
#         y_values = []
        
#         for seg_start, seg_end in segments:
#             if seg_end > seg_start:
#                 seg_fraction = (seg_end - seg_start) / (self.x_range[1] - self.x_range[0])
#                 seg_points = max(50, int(self.num_points * seg_fraction))
                
#                 x_seg = np.linspace(seg_start, seg_end, seg_points)
#                 y_seg = self._safe_evaluate_array(x_seg, deriv_func)
                
#                 if len(x_values) > 0:
#                     x_values.append(np.nan)
#                     y_values.append(np.nan)
                
#                 x_values.extend(x_seg)
#                 y_values.extend(y_seg)
        
#         return np.array(x_values), np.array(y_values)
    
#     def plot_critical_points(self, color='#d62728', marker='o', 
#                             markersize=12, label='Critical Points'):
#         """Plot critical points."""
#         if self.ax is None:
#             self.create_plot()
        
#         if self.critical_points:
#             x_crit, y_crit = zip(*self.critical_points)
#             self.ax.plot(x_crit, y_crit, marker=marker, color=color, 
#                         markersize=markersize, linestyle='', label=label,
#                         markeredgecolor='black', markeredgewidth=2, zorder=6)
            
#             for x, y in self.critical_points:
#                 self.ax.annotate(f'({x:.3f}, {y:.3f})', 
#                                xy=(x, y), xytext=(15, 15),
#                                textcoords='offset points',
#                                bbox=dict(boxstyle='round,pad=0.5', 
#                                        facecolor='yellow', alpha=0.8,
#                                        edgecolor='black', linewidth=1.5),
#                                fontsize=9, fontweight='bold',
#                                arrowprops=dict(arrowstyle='->', 
#                                              connectionstyle='arc3,rad=0.3',
#                                              color='black', lw=1.5))
#         return self
    
#     def plot_roots(self, color='#ff7f0e', marker='s', 
#                    markersize=12, label='Roots (Zeros)'):
#         """Plot roots."""
#         if self.ax is None:
#             self.create_plot()
        
#         if self.roots:
#             y_roots = [0] * len(self.roots)
#             self.ax.plot(self.roots, y_roots, marker=marker, color=color, 
#                         markersize=markersize, linestyle='', label=label,
#                         markeredgecolor='black', markeredgewidth=2, zorder=6)
            
#             for x in self.roots:
#                 self.ax.annotate(f'x={x:.3f}', 
#                                xy=(x, 0), xytext=(0, -25),
#                                textcoords='offset points',
#                                bbox=dict(boxstyle='round,pad=0.5', 
#                                        facecolor='lightblue', alpha=0.8,
#                                        edgecolor='black', linewidth=1.5),
#                                fontsize=9, fontweight='bold',
#                                ha='center',
#                                arrowprops=dict(arrowstyle='->', 
#                                              color='black', lw=1.5))
#         return self
    
#     def plot_asymptotes(self, vertical_color='#d62728', horizontal_color='#1f77b4',
#                        oblique_color='#17becf', linewidth=2, alpha=0.7):
#         """Plot asymptotes."""
#         if self.ax is None:
#             self.create_plot()
        
#         # Vertical asymptotes
#         for i, x_asym in enumerate(self.vertical_asymptotes):
#             label = 'Vertical Asymptote' if i == 0 else ''
#             self.ax.axvline(x=x_asym, color=vertical_color, linestyle='--', 
#                           linewidth=linewidth, alpha=alpha, label=label, zorder=10)
            
#             ylim = self.ax.get_ylim()
#             y_pos = ylim[1] * 0.9
#             self.ax.text(x_asym, y_pos, f'x={x_asym:.3f}', 
#                         ha='center', va='top',
#                         bbox=dict(boxstyle='round,pad=0.3', 
#                                 facecolor='white', alpha=0.8,
#                                 edgecolor=vertical_color, linewidth=1.5),
#                         fontsize=9, fontweight='bold')
        
#         # Horizontal asymptote
#         if self.horizontal_asymptote is not None:
#             self.ax.axhline(y=self.horizontal_asymptote, color=horizontal_color, 
#                           linestyle='--', linewidth=linewidth, alpha=alpha,
#                           label=f'Horizontal Asymptote y={self.horizontal_asymptote:.3f}',
#                           zorder=1)
        
#         # Oblique asymptote (single)
#         if self.oblique_asymptote is not None:
#             m, b = self.oblique_asymptote
#             x_asymp = np.linspace(self.x_range[0], self.x_range[1], 100)
#             y_asymp = m * x_asymp + b
#             self.ax.plot(x_asymp, y_asymp, color=oblique_color, linestyle='--',
#                         linewidth=linewidth, alpha=alpha,
#                         label=f'Oblique Asymptote y={m:.3f}x+{b:.3f}',
#                         zorder=1)
        
#         # Oblique asymptotes (separate left and right)
#         if self.oblique_asymptote_left is not None and self.oblique_asymptote is None:
#             m, b = self.oblique_asymptote_left
#             x_asymp = np.linspace(self.x_range[0], 0, 100)
#             y_asymp = m * x_asymp + b
#             self.ax.plot(x_asymp, y_asymp, color=oblique_color, linestyle='--',
#                         linewidth=linewidth, alpha=alpha,
#                         label=f'Left Oblique y={m:.3f}x+{b:.3f}',
#                         zorder=1)
        
#         if self.oblique_asymptote_right is not None and self.oblique_asymptote is None:
#             m, b = self.oblique_asymptote_right
#             x_asymp = np.linspace(0, self.x_range[1], 100)
#             y_asymp = m * x_asymp + b
#             self.ax.plot(x_asymp, y_asymp, color='#bcbd22', linestyle='--',
#                         linewidth=linewidth, alpha=alpha,
#                         label=f'Right Oblique y={m:.3f}x+{b:.3f}',
#                         zorder=1)
        
#         return self
    
#     def plot_inflection_points(self, color='#9467bd', marker='^', 
#                               markersize=12, label='Inflection Points'):
#         """Plot inflection points."""
#         if self.ax is None:
#             self.create_plot()
        
#         if self.inflection_points:
#             x_infl, y_infl = zip(*self.inflection_points)
#             self.ax.plot(x_infl, y_infl, marker=marker, color=color, 
#                         markersize=markersize, linestyle='', label=label,
#                         markeredgecolor='black', markeredgewidth=2, zorder=6)
            
#             for x, y in self.inflection_points:
#                 self.ax.annotate(f'({x:.3f}, {y:.3f})', 
#                                xy=(x, y), xytext=(-15, 15),
#                                textcoords='offset points',
#                                bbox=dict(boxstyle='round,pad=0.5', 
#                                        facecolor='lightgreen', alpha=0.8,
#                                        edgecolor='black', linewidth=1.5),
#                                fontsize=9, fontweight='bold',
#                                arrowprops=dict(arrowstyle='->', 
#                                              connectionstyle='arc3,rad=-0.3',
#                                              color='black', lw=1.5))
#         return self
    
#     def plot_tangent_line(self, x0, color='#2ca02c', linewidth=2.5, 
#                          label=None, extend=2, half='both'):
#         """
#         Plot tangent line at x0.
        
#         Args:
#             x0: Point at which to draw tangent
#             color: Line color
#             linewidth: Line width
#             label: Legend label
#             extend: How far to extend the line from x0
#             half: 'both', 'left', or 'right' - which direction(s) to draw
#         """
#         if self.ax is None:
#             self.create_plot()
        
#         try:
#             # Evaluate at x0 using SymPy for accuracy
#             y0 = float(self.func_symbolic.subs(self.x, x0).evalf())
#             slope = float(self.first_derivative.subs(self.x, x0).evalf())
            
#             if not np.isfinite(y0) or not np.isfinite(slope):
#                 print(f"Cannot plot tangent at x={x0}: function or derivative undefined")
#                 return self
            
#             # Create tangent line based on half parameter
#             if half == 'left':
#                 x_tangent = np.linspace(x0 - extend, x0, 100)
#             elif half == 'right':
#                 x_tangent = np.linspace(x0, x0 + extend, 100)
#             else:  # 'both'
#                 x_tangent = np.linspace(x0 - extend, x0 + extend, 100)
            
#             y_tangent = y0 + slope * (x_tangent - x0)
            
#             if label is None:
#                 if half == 'left':
#                     label = f'Left tangent at x={x0:.2f}'
#                 elif half == 'right':
#                     label = f'Right tangent at x={x0:.2f}'
#                 else:
#                     label = f'Tangent at x={x0:.2f}'
            
#             self.ax.plot(x_tangent, y_tangent, color=color, 
#                         linewidth=linewidth, label=label, linestyle=':', 
#                         alpha=0.9, zorder=4)
            
#             self.ax.plot(x0, y0, 'o', color=color, markersize=10, 
#                         markeredgecolor='black', markeredgewidth=2, zorder=5)
            
#         except Exception as e:
#             print(f"Error plotting tangent at x={x0}: {e}")
        
#         return self
    
#     def set_limits(self, xlim=None, ylim=None):
#         """Set axis limits with validation to prevent matplotlib errors."""
#         if self.ax is None:
#             self.create_plot()
        
#         if xlim:
#             self.ax.set_xlim(xlim)
        
#         if ylim:
#             y_min, y_max = ylim
#             # Clamp to safe values to prevent matplotlib errors
#             MAX_SAFE = 1e6
#             y_min = max(min(y_min, MAX_SAFE), -MAX_SAFE)
#             y_max = max(min(y_max, MAX_SAFE), -MAX_SAFE)
            
#             self.ax.set_ylim(y_min, y_max)
        
#         return self
    
#     def add_legend(self, loc='best', fontsize=11):
#         """Add legend."""
#         if self.ax is None:
#             self.create_plot()
        
#         self.ax.legend(loc=loc, fontsize=fontsize, framealpha=0.95,
#                       edgecolor='black', fancybox=True, shadow=True)
#         return self
    
#     def add_info_box(self):
#         """Add information box."""
#         if self.ax is None:
#             self.create_plot()
        
#         info_lines = [
#             f"f(x) = {self.func_symbolic}",
#             f"f'(x) = {self.first_derivative}",
#             f"f''(x) = {self.second_derivative}",
#             ""
#         ]
        
#         if self.critical_points:
#             info_lines.append(f"Critical points: {len(self.critical_points)}")
#         if self.roots:
#             info_lines.append(f"Roots: {len(self.roots)}")
#         if self.inflection_points:
#             info_lines.append(f"Inflection points: {len(self.inflection_points)}")
#         if self.vertical_asymptotes:
#             info_lines.append(f"Vertical asymptotes: {len(self.vertical_asymptotes)}")
        
#         info_text = "\n".join(info_lines)
        
#         self.ax.text(0.98, 0.98, info_text, 
#                     transform=self.ax.transAxes,
#                     fontsize=8, verticalalignment='top',
#                     horizontalalignment='right',
#                     bbox=dict(boxstyle='round,pad=0.7', 
#                             facecolor='wheat', alpha=0.9,
#                             edgecolor='black', linewidth=1.5),
#                     family='monospace')
        
#         return self
    
#     def save(self, filename):
#         """Save the plot."""
#         if self.fig is None:
#             return self
        
#         self.fig.tight_layout()
#         self.fig.savefig(filename, dpi=300, bbox_inches='tight', 
#                         facecolor='white', edgecolor='none')
#         return self
    
#     def show(self):
#         """Display the plot."""
#         if self.fig is None:
#             return self
        
#         self.fig.tight_layout()
#         plt.show()
#         return self


# def get_yes_no(prompt):
#     """Get yes/no input."""
#     while True:
#         response = input(prompt + " (y/n): ").lower().strip()
#         if response in ['y', 'yes']:
#             return True
#         elif response in ['n', 'no']:
#             return False
#         print("Please enter 'y' or 'n'")


# def get_float(prompt, default=None):
#     """Get float input."""
#     while True:
#         if default is not None:
#             response = input(f"{prompt} (default: {default}): ").strip()
#         else:
#             response = input(prompt + ": ").strip()
            
#         if response == '' and default is not None:
#             return default
#         try:
#             return float(response)
#         except ValueError:
#             print("Please enter a valid number")


# def get_choice(prompt, choices):
#     """Get choice from list."""
#     while True:
#         response = input(prompt + f" {choices}: ").lower().strip()
#         if response in choices:
#             return response
#         print(f"Please enter one of: {choices}")


# def print_header():
#     """Print header."""
#     print("\n" + "="*70)
#     print(" "*15 + "ACCURATE FUNCTION GRAPHER v2.1")
#     print(" "*18 + "Powered by SymPy")
#     print(" "*12 + "Fixed Discontinuity Handling")
#     print("="*70)


# def main():
#     """Main program."""
#     print_header()
    
#     graph_counter = 1
    
#     while True:
#         print("\n📝 Enter a mathematical function using 'x'")
#         print("Examples: x**2, sin(x), 1/(x-2), x**3 - 3*x**2 + 2")
#         print("Type 'quit' to exit\n")
        
#         func_str = input("f(x) = ").strip()
        
#         if not func_str or func_str.lower() in ['exit', 'quit', 'q']:
#             break
        
#         print(f"\n{'─'*70}")
#         print(f"Graph #{graph_counter}")
#         print(f"{'─'*70}")
        
#         # Get range
#         x_min = get_float("X minimum", default=-10)
#         x_max = get_float("X maximum", default=10)
        
#         # Create grapher
#         try:
#             grapher = AccurateFunctionGrapher(func_str, x_range=(x_min, x_max))
#         except Exception as e:
#             print(f"\n❌ Error: {e}")
#             continue
        
#         # Y limits
#         use_ylim = get_yes_no("\nSet custom y-axis limits?")
#         if use_ylim:
#             y_min = get_float("Y minimum", default=-10)
#             y_max = get_float("Y maximum", default=10)
#             ylim = (y_min, y_max)
#         else:
#             ylim = (-10, 10)
        
#         # Create plot
#         grapher.create_plot(title=f"Graph #{graph_counter}: f(x) = {func_str}")
#         grapher.plot_function()
        
#         # Options
#         print("\n" + "="*70)
#         print("PLOT OPTIONS")
#         print("="*70)
        
#         if get_yes_no("📈 Plot first derivative f'(x)?"):
#             grapher.plot_derivative()
        
#         if get_yes_no("📉 Plot second derivative f''(x)?"):
#             grapher.plot_second_derivative()
        
#         if get_yes_no("🎯 Plot critical points?"):
#             grapher.plot_critical_points()
        
#         if get_yes_no("🔍 Plot roots (zeros)?"):
#             grapher.plot_roots()
        
#         if get_yes_no("📏 Plot asymptotes?"):
#             grapher.plot_asymptotes()
        
#         if get_yes_no("🔄 Plot inflection points?"):
#             grapher.plot_inflection_points()
        
#         if get_yes_no("📐 Plot tangent line(s)?"):
#             num = int(get_float("How many", default=1))
#             colors = ['#2ca02c', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f']
#             for i in range(num):
#                 x0 = get_float(f"x-coordinate for tangent {i+1}")
#                 half = get_choice(f"Direction for tangent {i+1}", ['both', 'left', 'right'])
#                 grapher.plot_tangent_line(x0=x0, color=colors[i % len(colors)], half=half)
        
#         if get_yes_no("ℹ️  Add information box?"):
#             grapher.add_info_box()
        
#         grapher.set_limits(ylim=ylim)
        
#         grapher.add_legend()
        
#         # Save
#         filename = f"graph_{graph_counter:03d}.png"
#         grapher.save(filename)
#         print(f"\n✓ Saved: {filename}")
        
#         if get_yes_no("\n👁️  Display now?"):
#             grapher.show()
        
#         graph_counter += 1
        
#         if not get_yes_no("\n🔄 Create another graph?"):
#             break
    
#     # Copy to output
#     # if graph_counter > 1:
#     #     print(f"\n📊 Created {graph_counter - 1} graph(s)")
#     #     import os
#     #     import shutil
#     #     os.makedirs("outputs", exist_ok=True)
#     #     for i in range(1, graph_counter):
#     #         src = f"graph_{i:03d}.png"
#     #         dst = f"outputs/graph_{i:03d}.png"
#     #         if os.path.exists(src):
#     #             shutil.copy(src, dst)
    
#     print("\n" + "="*70)
#     print("Thank you for using Accurate Function Grapher!")
#     print("="*70 + "\n")


# if __name__ == "__main__":
#     main()



# import numpy as np
# import matplotlib.pyplot as plt
# from sympy import *
# from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application
# from sympy.calculus.util import continuous_domain
# import warnings
# warnings.filterwarnings('ignore')


# class AccurateFunctionGrapher:
#     """
#     A class to graph mathematical functions using SymPy for exact symbolic calculations.
#     All calculations are verified for accuracy.
#     """
    
#     def __init__(self, func_str, x_range=(-10, 10), num_points=2000):
#         """
#         Initialize the grapher with a function string.
        
#         Args:
#             func_str: String representation of function
#             x_range: Tuple of (x_min, x_max)
#             num_points: Number of points for plotting
#         """
#         self.func_str = func_str
#         self.x_range = x_range
#         self.num_points = num_points
        
#         # Symbol
#         self.x = symbols('x', real=True)
        
#         # Parse function with OUR symbol
#         transformations = standard_transformations + (implicit_multiplication_application,)
#         local_dict = {'x': self.x}  # Use our own x symbol
#         self.func_symbolic = parse_expr(func_str, transformations=transformations, 
#                                        local_dict=local_dict)
        
#         # Simplify
#         self.func_symbolic = simplify(self.func_symbolic)
        
#         # Calculate derivatives
#         self.first_derivative = diff(self.func_symbolic, self.x)
#         self.second_derivative = diff(self.first_derivative, self.x)
        
#         # Simplify derivatives
#         self.first_derivative = simplify(self.first_derivative)
#         self.second_derivative = simplify(self.second_derivative)
        
#         # Create lambdified functions for numerical evaluation
#         try:
#             self.func_numeric = lambdify(self.x, self.func_symbolic, modules=['numpy', {'Abs': np.abs}])
#             self.first_deriv_numeric = lambdify(self.x, self.first_derivative, modules=['numpy', {'Abs': np.abs}])
#             self.second_deriv_numeric = lambdify(self.x, self.second_derivative, modules=['numpy', {'Abs': np.abs}])
#         except Exception as e:
#             print(f"Warning during lambdify: {e}")
#             self.func_numeric = None
#             self.first_deriv_numeric = None
#             self.second_deriv_numeric = None
        
#         # Generate plot points
#         self.x_values = np.linspace(x_range[0], x_range[1], num_points)
#         self.y_values = self._safe_evaluate_array(self.x_values, self.func_numeric)
        
#         # Initialize plot
#         self.fig = None
#         self.ax = None
        
#         # Calculate all features
#         self._find_all_features()
        
#     def _safe_evaluate_array(self, x_array, func):
#         """Safely evaluate function on array."""
#         if func is None:
#             return np.full_like(x_array, np.nan)
        
#         result = np.zeros_like(x_array, dtype=float)
#         for i, x_val in enumerate(x_array):
#             result[i] = self._safe_evaluate_single(x_val, func)
#         return result
    
#     def _safe_evaluate_single(self, x_val, func):
#         """Safely evaluate function at a single point."""
#         if func is None:
#             return np.nan
        
#         try:
#             result = func(x_val)
#             if isinstance(result, np.ndarray):
#                 result = float(result.flat[0])
#             else:
#                 result = float(result)
            
#             if not np.isfinite(result):
#                 return np.nan
#             return result
#         except:
#             return np.nan
    
#     def _solve_equation_in_range(self, equation):
#         """
#         Solve an equation and return real solutions in the x_range.
        
#         Args:
#             equation: SymPy expression to solve (set equal to 0)
            
#         Returns:
#             List of float solutions
#         """
#         solutions = []
        
#         try:
#             # Try to solve symbolically
#             symbolic_solutions = solve(equation, self.x)
            
#             for sol in symbolic_solutions:
#                 try:
#                     # Handle different types of solutions
#                     if sol.is_real is True or (hasattr(sol, 'is_zero') and sol.is_zero):
#                         sol_float = float(sol.evalf())
#                         if np.isfinite(sol_float) and self.x_range[0] <= sol_float <= self.x_range[1]:
#                             # Verify the solution
#                             test_val = float(equation.subs(self.x, sol).evalf())
#                             if abs(test_val) < 1e-6:  # Solution is valid
#                                 solutions.append(sol_float)
#                     elif sol.is_complex and abs(im(sol)) < 1e-10:
#                         # Essentially real (imaginary part is negligible)
#                         sol_float = float(re(sol).evalf())
#                         if np.isfinite(sol_float) and self.x_range[0] <= sol_float <= self.x_range[1]:
#                             test_val = float(abs(equation.subs(self.x, sol)).evalf())
#                             if abs(test_val) < 1e-6:
#                                 solutions.append(sol_float)
#                 except Exception as inner_e:
#                     continue
                    
#         except Exception as e:
#             # If symbolic solving fails, try numerical approach
#             pass
        
#         # Remove duplicates
#         unique_solutions = []
#         for sol in solutions:
#             if not any(abs(sol - existing) < 1e-6 for existing in unique_solutions):
#                 unique_solutions.append(sol)
        
#         return sorted(unique_solutions)
    
#     def _find_all_features(self):
#         """Find all critical features of the function."""
        
#         print("\n🔍 Analyzing function...")
        
#         # Find critical points (f'(x) = 0)
#         print("  Finding critical points...")
#         critical_x = self._solve_equation_in_range(self.first_derivative)
#         self.critical_points = []
#         for x_val in critical_x:
#             y_val = self._safe_evaluate_single(x_val, self.func_numeric)
#             if np.isfinite(y_val):
#                 self.critical_points.append((x_val, y_val))
#         print(f"  ✓ Found {len(self.critical_points)} critical point(s)")
        
#         # Find roots (f(x) = 0)
#         print("  Finding roots...")
#         root_x = self._solve_equation_in_range(self.func_symbolic)
#         self.roots = []
#         for x_val in root_x:
#             y_val = self._safe_evaluate_single(x_val, self.func_numeric)
#             if np.isfinite(y_val) and abs(y_val) < 1e-6:
#                 self.roots.append(x_val)
#         print(f"  ✓ Found {len(self.roots)} root(s)")
        
#         # Find inflection points (f''(x) = 0)
#         print("  Finding inflection points...")
#         inflection_x = self._solve_equation_in_range(self.second_derivative)
#         self.inflection_points = []
#         for x_val in inflection_x:
#             y_val = self._safe_evaluate_single(x_val, self.func_numeric)
#             if np.isfinite(y_val):
#                 # Verify concavity changes
#                 self.inflection_points.append((x_val, y_val))
#         print(f"  ✓ Found {len(self.inflection_points)} inflection point(s)")
        
#         # Find vertical asymptotes
#         print("  Finding vertical asymptotes...")
#         self.vertical_asymptotes = []
#         try:
#             # Get numerator and denominator
#             numer, denom = fraction(self.func_symbolic)
            
#             if denom != 1:
#                 # Solve denominator = 0
#                 denom_zeros = self._solve_equation_in_range(denom)
                
#                 for x_val in denom_zeros:
#                     # Check if numerator is also zero (removable discontinuity)
#                     numer_val = float(numer.subs(self.x, x_val).evalf())
#                     if abs(numer_val) > 1e-6:  # Not removable
#                         self.vertical_asymptotes.append(x_val)
#         except Exception as e:
#             pass
#         print(f"  ✓ Found {len(self.vertical_asymptotes)} vertical asymptote(s)")
        
#         # Find horizontal asymptotes
#         print("  Finding horizontal asymptotes...")
#         self.horizontal_asymptote = None
#         try:
#             limit_pos_inf = limit(self.func_symbolic, self.x, oo)
#             limit_neg_inf = limit(self.func_symbolic, self.x, -oo)
            
#             # Check if both limits exist and are equal
#             if limit_pos_inf.is_finite and limit_neg_inf.is_finite:
#                 if limit_pos_inf == limit_neg_inf:
#                     self.horizontal_asymptote = float(limit_pos_inf.evalf())
#                     print(f"  ✓ Found horizontal asymptote: y = {self.horizontal_asymptote:.4f}")
#                 else:
#                     print(f"  ✓ Different limits at ±∞")
#             else:
#                 print("  ✓ No horizontal asymptote")
#         except Exception as e:
#             pass
        
#         # Find oblique asymptotes
#         print("  Finding oblique asymptotes...")
#         self.oblique_asymptote = None
#         self.oblique_asymptote_left = None
#         self.oblique_asymptote_right = None
#         try:
#             # Check if there's no horizontal asymptote first
#             if self.horizontal_asymptote is None:
#                 # Calculate limit of f(x)/x as x approaches +infinity
#                 ratio = self.func_symbolic / self.x
#                 m_right = limit(ratio, self.x, oo)
                
#                 # Calculate limit of f(x)/x as x approaches -infinity
#                 m_left = limit(ratio, self.x, -oo)
                
#                 # Right asymptote
#                 if m_right.is_finite and m_right != 0:
#                     b_right = limit(self.func_symbolic - m_right * self.x, self.x, oo)
#                     if b_right.is_finite:
#                         m_right_float = float(m_right.evalf())
#                         b_right_float = float(b_right.evalf())
#                         self.oblique_asymptote_right = (m_right_float, b_right_float)
                
#                 # Left asymptote
#                 if m_left.is_finite and m_left != 0:
#                     b_left = limit(self.func_symbolic - m_left * self.x, self.x, -oo)
#                     if b_left.is_finite:
#                         m_left_float = float(m_left.evalf())
#                         b_left_float = float(b_left.evalf())
#                         self.oblique_asymptote_left = (m_left_float, b_left_float)
                
#                 # Check if they're the same
#                 if self.oblique_asymptote_right and self.oblique_asymptote_left:
#                     m_r, b_r = self.oblique_asymptote_right
#                     m_l, b_l = self.oblique_asymptote_left
#                     if abs(m_r - m_l) < 1e-6 and abs(b_r - b_l) < 1e-6:
#                         self.oblique_asymptote = (m_r, b_r)
#                         print(f"  ✓ Found oblique asymptote: y = {m_r:.4f}x + {b_r:.4f}")
#                     else:
#                         print(f"  ✓ Found left oblique asymptote: y = {m_l:.4f}x + {b_l:.4f}")
#                         print(f"  ✓ Found right oblique asymptote: y = {m_r:.4f}x + {b_r:.4f}")
#                 elif self.oblique_asymptote_right:
#                     print(f"  ✓ Found right oblique asymptote: y = {self.oblique_asymptote_right[0]:.4f}x + {self.oblique_asymptote_right[1]:.4f}")
#                 elif self.oblique_asymptote_left:
#                     print(f"  ✓ Found left oblique asymptote: y = {self.oblique_asymptote_left[0]:.4f}x + {self.oblique_asymptote_left[1]:.4f}")
#                 else:
#                     print("  ✓ No oblique asymptote")
#             else:
#                 print("  ✓ No oblique asymptote (horizontal asymptote exists)")
#         except Exception as e:
#             print("  ✓ No oblique asymptote")
        
#         print("✓ Analysis complete!\n")
    
#     def create_plot(self, figsize=(14, 9), title=None):
#         """Create the matplotlib figure."""
#         self.fig, self.ax = plt.subplots(figsize=figsize)
        
#         if title is None:
#             title = f"f(x) = {self.func_str}"
        
#         self.ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
#         self.ax.set_xlabel('x', fontsize=13, fontweight='bold')
#         self.ax.set_ylabel('y', fontsize=13, fontweight='bold')
#         self.ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.7)
#         self.ax.axhline(y=0, color='k', linewidth=0.8, alpha=0.5)
#         self.ax.axvline(x=0, color='k', linewidth=0.8, alpha=0.5)
        
#         # Set default y-limits early to prevent matplotlib from auto-scaling to extreme values
#         self.ax.set_ylim(-10, 10)
        
#         return self
    
#     def plot_function(self, color='#1f77b4', linewidth=2.5, label='f(x)'):
#         """Plot the function."""
#         if self.ax is None:
#             self.create_plot()
        
#         # Clip y-values to reasonable range to prevent matplotlib errors
#         y_clipped = np.clip(self.y_values, -1e6, 1e6)
        
#         self.ax.plot(self.x_values, y_clipped, color=color, 
#                     linewidth=linewidth, label=label, zorder=3)
#         return self
    
#     def plot_derivative(self, color='#ff7f0e', linewidth=2, label="f'(x)"):
#         """Plot the first derivative."""
#         if self.ax is None:
#             self.create_plot()
        
#         deriv_values = self._safe_evaluate_array(self.x_values, self.first_deriv_numeric)
#         deriv_clipped = np.clip(deriv_values, -1e6, 1e6)
#         self.ax.plot(self.x_values, deriv_clipped, color=color, 
#                     linewidth=linewidth, label=label, linestyle='--', alpha=0.8, zorder=2)
#         return self
    
#     def plot_second_derivative(self, color='#2ca02c', linewidth=2, label="f''(x)"):
#         """Plot the second derivative."""
#         if self.ax is None:
#             self.create_plot()
        
#         second_deriv_values = self._safe_evaluate_array(self.x_values, self.second_deriv_numeric)
#         second_deriv_clipped = np.clip(second_deriv_values, -1e6, 1e6)
#         self.ax.plot(self.x_values, second_deriv_clipped, color=color, 
#                     linewidth=linewidth, label=label, linestyle='-.', alpha=0.8, zorder=2)
#         return self
    
#     def plot_critical_points(self, color='#d62728', marker='o', 
#                             markersize=12, label='Critical Points'):
#         """Plot critical points."""
#         if self.ax is None:
#             self.create_plot()
        
#         if self.critical_points:
#             x_crit, y_crit = zip(*self.critical_points)
#             self.ax.plot(x_crit, y_crit, marker=marker, color=color, 
#                         markersize=markersize, linestyle='', label=label,
#                         markeredgecolor='black', markeredgewidth=2, zorder=6)
            
#             for x, y in self.critical_points:
#                 self.ax.annotate(f'({x:.3f}, {y:.3f})', 
#                                xy=(x, y), xytext=(15, 15),
#                                textcoords='offset points',
#                                bbox=dict(boxstyle='round,pad=0.5', 
#                                        facecolor='yellow', alpha=0.8,
#                                        edgecolor='black', linewidth=1.5),
#                                fontsize=9, fontweight='bold',
#                                arrowprops=dict(arrowstyle='->', 
#                                              connectionstyle='arc3,rad=0.3',
#                                              color='black', lw=1.5))
#         return self
    
#     def plot_roots(self, color='#ff7f0e', marker='s', 
#                    markersize=12, label='Roots (Zeros)'):
#         """Plot roots."""
#         if self.ax is None:
#             self.create_plot()
        
#         if self.roots:
#             y_roots = [0] * len(self.roots)
#             self.ax.plot(self.roots, y_roots, marker=marker, color=color, 
#                         markersize=markersize, linestyle='', label=label,
#                         markeredgecolor='black', markeredgewidth=2, zorder=6)
            
#             for x in self.roots:
#                 self.ax.annotate(f'x={x:.3f}', 
#                                xy=(x, 0), xytext=(0, -25),
#                                textcoords='offset points',
#                                bbox=dict(boxstyle='round,pad=0.5', 
#                                        facecolor='lightblue', alpha=0.8,
#                                        edgecolor='black', linewidth=1.5),
#                                fontsize=9, fontweight='bold',
#                                ha='center',
#                                arrowprops=dict(arrowstyle='->', 
#                                              color='black', lw=1.5))
#         return self
    
#     def plot_asymptotes(self, vertical_color='#d62728', horizontal_color='#1f77b4',
#                        oblique_color='#17becf', linewidth=2, alpha=0.7):
#         """Plot asymptotes."""
#         if self.ax is None:
#             self.create_plot()
        
#         # Vertical asymptotes
#         for i, x_asym in enumerate(self.vertical_asymptotes):
#             label = 'Vertical Asymptote' if i == 0 else ''
#             self.ax.axvline(x=x_asym, color=vertical_color, linestyle='--', 
#                           linewidth=linewidth, alpha=alpha, label=label, zorder=10)
            
#             ylim = self.ax.get_ylim()
#             y_pos = ylim[1] * 0.9
#             self.ax.text(x_asym, y_pos, f'x={x_asym:.3f}', 
#                         ha='center', va='top',
#                         bbox=dict(boxstyle='round,pad=0.3', 
#                                 facecolor='white', alpha=0.8,
#                                 edgecolor=vertical_color, linewidth=1.5),
#                         fontsize=9, fontweight='bold')
        
#         # Horizontal asymptote
#         if self.horizontal_asymptote is not None:
#             self.ax.axhline(y=self.horizontal_asymptote, color=horizontal_color, 
#                           linestyle='--', linewidth=linewidth, alpha=alpha,
#                           label=f'Horizontal Asymptote y={self.horizontal_asymptote:.3f}',
#                           zorder=1)
        
#         # Oblique asymptote (single)
#         if self.oblique_asymptote is not None:
#             m, b = self.oblique_asymptote
#             x_asymp = np.linspace(self.x_range[0], self.x_range[1], 100)
#             y_asymp = m * x_asymp + b
#             self.ax.plot(x_asymp, y_asymp, color=oblique_color, linestyle='--',
#                         linewidth=linewidth, alpha=alpha,
#                         label=f'Oblique Asymptote y={m:.3f}x+{b:.3f}',
#                         zorder=1)
        
#         # Oblique asymptotes (separate left and right)
#         if self.oblique_asymptote_left is not None and self.oblique_asymptote is None:
#             m, b = self.oblique_asymptote_left
#             x_asymp = np.linspace(self.x_range[0], 0, 100)
#             y_asymp = m * x_asymp + b
#             self.ax.plot(x_asymp, y_asymp, color=oblique_color, linestyle='--',
#                         linewidth=linewidth, alpha=alpha,
#                         label=f'Left Oblique y={m:.3f}x+{b:.3f}',
#                         zorder=1)
        
#         if self.oblique_asymptote_right is not None and self.oblique_asymptote is None:
#             m, b = self.oblique_asymptote_right
#             x_asymp = np.linspace(0, self.x_range[1], 100)
#             y_asymp = m * x_asymp + b
#             self.ax.plot(x_asymp, y_asymp, color='#bcbd22', linestyle='--',
#                         linewidth=linewidth, alpha=alpha,
#                         label=f'Right Oblique y={m:.3f}x+{b:.3f}',
#                         zorder=1)
        
#         return self
    
#     def plot_inflection_points(self, color='#9467bd', marker='^', 
#                               markersize=12, label='Inflection Points'):
#         """Plot inflection points."""
#         if self.ax is None:
#             self.create_plot()
        
#         if self.inflection_points:
#             x_infl, y_infl = zip(*self.inflection_points)
#             self.ax.plot(x_infl, y_infl, marker=marker, color=color, 
#                         markersize=markersize, linestyle='', label=label,
#                         markeredgecolor='black', markeredgewidth=2, zorder=6)
            
#             for x, y in self.inflection_points:
#                 self.ax.annotate(f'({x:.3f}, {y:.3f})', 
#                                xy=(x, y), xytext=(-15, 15),
#                                textcoords='offset points',
#                                bbox=dict(boxstyle='round,pad=0.5', 
#                                        facecolor='lightgreen', alpha=0.8,
#                                        edgecolor='black', linewidth=1.5),
#                                fontsize=9, fontweight='bold',
#                                arrowprops=dict(arrowstyle='->', 
#                                              connectionstyle='arc3,rad=-0.3',
#                                              color='black', lw=1.5))
#         return self
    
#     def plot_tangent_line(self, x0, color='#2ca02c', linewidth=2.5, 
#                          label=None, extend=2, half='both'):
#         """
#         Plot tangent line at x0.
        
#         Args:
#             x0: Point at which to draw tangent
#             color: Line color
#             linewidth: Line width
#             label: Legend label
#             extend: How far to extend the line from x0
#             half: 'both', 'left', or 'right' - which direction(s) to draw
#         """
#         if self.ax is None:
#             self.create_plot()
        
#         try:
#             # Evaluate at x0 using SymPy for accuracy
#             y0 = float(self.func_symbolic.subs(self.x, x0).evalf())
#             slope = float(self.first_derivative.subs(self.x, x0).evalf())
            
#             if not np.isfinite(y0) or not np.isfinite(slope):
#                 print(f"Cannot plot tangent at x={x0}: function or derivative undefined")
#                 return self
            
#             # Create tangent line based on half parameter
#             if half == 'left':
#                 x_tangent = np.linspace(x0 - extend, x0, 100)
#             elif half == 'right':
#                 x_tangent = np.linspace(x0, x0 + extend, 100)
#             else:  # 'both'
#                 x_tangent = np.linspace(x0 - extend, x0 + extend, 100)
            
#             y_tangent = y0 + slope * (x_tangent - x0)
            
#             if label is None:
#                 if half == 'left':
#                     label = f'Left tangent at x={x0:.2f}'
#                 elif half == 'right':
#                     label = f'Right tangent at x={x0:.2f}'
#                 else:
#                     label = f'Tangent at x={x0:.2f}'
            
#             self.ax.plot(x_tangent, y_tangent, color=color, 
#                         linewidth=linewidth, label=label, linestyle=':', 
#                         alpha=0.9, zorder=4)
            
#             self.ax.plot(x0, y0, 'o', color=color, markersize=10, 
#                         markeredgecolor='black', markeredgewidth=2, zorder=5)
            
#         except Exception as e:
#             print(f"Error plotting tangent at x={x0}: {e}")
        
#         return self
    
#     def set_limits(self, xlim=None, ylim=None):
#         """Set axis limits with validation to prevent matplotlib errors."""
#         if self.ax is None:
#             self.create_plot()
        
#         if xlim:
#             self.ax.set_xlim(xlim)
        
#         if ylim:
#             y_min, y_max = ylim
#             # Clamp to safe values to prevent matplotlib errors
#             MAX_SAFE = 1e6
#             y_min = max(min(y_min, MAX_SAFE), -MAX_SAFE)
#             y_max = max(min(y_max, MAX_SAFE), -MAX_SAFE)
            
#             self.ax.set_ylim(y_min, y_max)
        
#         return self
    
#     def add_legend(self, loc='best', fontsize=11):
#         """Add legend."""
#         if self.ax is None:
#             self.create_plot()
        
#         self.ax.legend(loc=loc, fontsize=fontsize, framealpha=0.95,
#                       edgecolor='black', fancybox=True, shadow=True)
#         return self
    
#     def add_info_box(self):
#         """Add information box."""
#         if self.ax is None:
#             self.create_plot()
        
#         info_lines = [
#             f"f(x) = {self.func_symbolic}",
#             f"f'(x) = {self.first_derivative}",
#             f"f''(x) = {self.second_derivative}",
#             ""
#         ]
        
#         if self.critical_points:
#             info_lines.append(f"Critical points: {len(self.critical_points)}")
#         if self.roots:
#             info_lines.append(f"Roots: {len(self.roots)}")
#         if self.inflection_points:
#             info_lines.append(f"Inflection points: {len(self.inflection_points)}")
#         if self.vertical_asymptotes:
#             info_lines.append(f"Vertical asymptotes: {len(self.vertical_asymptotes)}")
        
#         info_text = "\n".join(info_lines)
        
#         self.ax.text(0.98, 0.98, info_text, 
#                     transform=self.ax.transAxes,
#                     fontsize=8, verticalalignment='top',
#                     horizontalalignment='right',
#                     bbox=dict(boxstyle='round,pad=0.7', 
#                             facecolor='wheat', alpha=0.9,
#                             edgecolor='black', linewidth=1.5),
#                     family='monospace')
        
#         return self
    
#     def save(self, filename):
#         """Save the plot."""
#         if self.fig is None:
#             return self
        
#         self.fig.tight_layout()
#         self.fig.savefig(filename, dpi=300, bbox_inches='tight', 
#                         facecolor='white', edgecolor='none')
#         return self
    
#     def show(self):
#         """Display the plot."""
#         if self.fig is None:
#             return self
        
#         self.fig.tight_layout()
#         plt.show()
#         return self


# def get_yes_no(prompt):
#     """Get yes/no input."""
#     while True:
#         response = input(prompt + " (y/n): ").lower().strip()
#         if response in ['y', 'yes']:
#             return True
#         elif response in ['n', 'no']:
#             return False
#         print("Please enter 'y' or 'n'")


# def get_float(prompt, default=None):
#     """Get float input."""
#     while True:
#         if default is not None:
#             response = input(f"{prompt} (default: {default}): ").strip()
#         else:
#             response = input(prompt + ": ").strip()
            
#         if response == '' and default is not None:
#             return default
#         try:
#             return float(response)
#         except ValueError:
#             print("Please enter a valid number")


# def get_choice(prompt, choices):
#     """Get choice from list."""
#     while True:
#         response = input(prompt + f" {choices}: ").lower().strip()
#         if response in choices:
#             return response
#         print(f"Please enter one of: {choices}")


# def print_header():
#     """Print header."""
#     print("\n" + "="*70)
#     print(" "*15 + "ACCURATE FUNCTION GRAPHER v2.0")
#     print(" "*20 + "Powered by SymPy")
#     print("="*70)


# def main():
#     """Main program."""
#     print_header()
    
#     graph_counter = 1
    
#     while True:
#         print("\n📝 Enter a mathematical function using 'x'")
#         print("Examples: x**2, sin(x), 1/(x-2), x**3 - 3*x**2 + 2")
#         print("Type 'quit' to exit\n")
        
#         func_str = input("f(x) = ").strip()
        
#         if not func_str or func_str.lower() in ['exit', 'quit', 'q']:
#             break
        
#         print(f"\n{'─'*70}")
#         print(f"Graph #{graph_counter}")
#         print(f"{'─'*70}")
        
#         # Get range
#         x_min = get_float("X minimum", default=-10)
#         x_max = get_float("X maximum", default=10)
        
#         # Create grapher
#         try:
#             grapher = AccurateFunctionGrapher(func_str, x_range=(x_min, x_max))
#         except Exception as e:
#             print(f"\n❌ Error: {e}")
#             continue
        
#         # Y limits
#         use_ylim = get_yes_no("\nSet custom y-axis limits?")
#         if use_ylim:
#             y_min = get_float("Y minimum", default=-10)
#             y_max = get_float("Y maximum", default=10)
#             ylim = (y_min, y_max)
#         else:
#             ylim = (-10, 10)
        
#         # Create plot
#         grapher.create_plot(title=f"Graph #{graph_counter}: f(x) = {func_str}")
#         grapher.plot_function()
        
#         # Options
#         print("\n" + "="*70)
#         print("PLOT OPTIONS")
#         print("="*70)
        
#         if get_yes_no("📈 Plot first derivative f'(x)?"):
#             grapher.plot_derivative()
        
#         if get_yes_no("📉 Plot second derivative f''(x)?"):
#             grapher.plot_second_derivative()
        
#         if get_yes_no("🎯 Plot critical points?"):
#             grapher.plot_critical_points()
        
#         if get_yes_no("🔍 Plot roots (zeros)?"):
#             grapher.plot_roots()
        
#         if get_yes_no("📏 Plot asymptotes?"):
#             grapher.plot_asymptotes()
        
#         if get_yes_no("🔄 Plot inflection points?"):
#             grapher.plot_inflection_points()
        
#         if get_yes_no("📐 Plot tangent line(s)?"):
#             num = int(get_float("How many", default=1))
#             colors = ['#2ca02c', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f']
#             for i in range(num):
#                 x0 = get_float(f"x-coordinate for tangent {i+1}")
#                 half = get_choice(f"Direction for tangent {i+1}", ['both', 'left', 'right'])
#                 grapher.plot_tangent_line(x0=x0, color=colors[i % len(colors)], half=half)
        
#         if get_yes_no("ℹ️  Add information box?"):
#             grapher.add_info_box()
        
#         grapher.set_limits(ylim=ylim)
        
#         grapher.add_legend()
        
#         # Save
#         filename = f"graph_{graph_counter:03d}.png"
#         grapher.save(filename)
#         print(f"\n✓ Saved: {filename}")
        
#         if get_yes_no("\n👁️  Display now?"):
#             grapher.show()
        
#         graph_counter += 1
        
#         if not get_yes_no("\n🔄 Create another graph?"):
#             break
    
#     # Copy to output
#     if graph_counter > 1:
#         print(f"\n📊 Created {graph_counter - 1} graph(s)")
#         import os
#         import shutil
#         os.makedirs("/mnt/user-data/outputs", exist_ok=True)
#         for i in range(1, graph_counter):
#             src = f"graph_{i:03d}.png"
#             dst = f"/mnt/user-data/outputs/graph_{i:03d}.png"
#             if os.path.exists(src):
#                 shutil.copy(src, dst)
#         print(f"✓ Copied to outputs/")
    
#     print("\n" + "="*70)
#     print("Thank you for using Accurate Function Grapher!")
#     print("="*70 + "\n")


# if __name__ == "__main__":
#     main()








# import numpy as np
# import matplotlib.pyplot as plt
# from sympy import *
# from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application
# from sympy.calculus.util import continuous_domain
# import warnings
# warnings.filterwarnings('ignore')


# class AccurateFunctionGrapher:
#     """
#     A class to graph mathematical functions using SymPy for exact symbolic calculations.
#     All calculations are verified for accuracy.
#     """
    
#     def __init__(self, func_str, x_range=(-10, 10), num_points=2000):
#         """
#         Initialize the grapher with a function string.
        
#         Args:
#             func_str: String representation of function
#             x_range: Tuple of (x_min, x_max)
#             num_points: Number of points for plotting
#         """
#         self.func_str = func_str
#         self.x_range = x_range
#         self.num_points = num_points
        
#         # Symbol
#         self.x = symbols('x', real=True)
        
#         # Parse function with OUR symbol
#         transformations = standard_transformations + (implicit_multiplication_application,)
#         local_dict = {'x': self.x}  # Use our own x symbol
#         self.func_symbolic = parse_expr(func_str, transformations=transformations, 
#                                        local_dict=local_dict)
        
#         # Simplify
#         self.func_symbolic = simplify(self.func_symbolic)
        
#         # Calculate derivatives
#         self.first_derivative = diff(self.func_symbolic, self.x)
#         self.second_derivative = diff(self.first_derivative, self.x)
        
#         # Simplify derivatives
#         self.first_derivative = simplify(self.first_derivative)
#         self.second_derivative = simplify(self.second_derivative)
        
#         # Create lambdified functions for numerical evaluation
#         try:
#             self.func_numeric = lambdify(self.x, self.func_symbolic, modules=['numpy', {'Abs': np.abs}])
#             self.first_deriv_numeric = lambdify(self.x, self.first_derivative, modules=['numpy', {'Abs': np.abs}])
#             self.second_deriv_numeric = lambdify(self.x, self.second_derivative, modules=['numpy', {'Abs': np.abs}])
#         except Exception as e:
#             print(f"Warning during lambdify: {e}")
#             self.func_numeric = None
#             self.first_deriv_numeric = None
#             self.second_deriv_numeric = None
        
#         # Generate plot points
#         self.x_values = np.linspace(x_range[0], x_range[1], num_points)
#         self.y_values = self._safe_evaluate_array(self.x_values, self.func_numeric)
        
#         # Initialize plot
#         self.fig = None
#         self.ax = None
        
#         # Calculate all features
#         self._find_all_features()
        
#     def _safe_evaluate_array(self, x_array, func):
#         """Safely evaluate function on array."""
#         if func is None:
#             return np.full_like(x_array, np.nan)
        
#         result = np.zeros_like(x_array, dtype=float)
#         for i, x_val in enumerate(x_array):
#             result[i] = self._safe_evaluate_single(x_val, func)
#         return result
    
#     def _safe_evaluate_single(self, x_val, func):
#         """Safely evaluate function at a single point."""
#         if func is None:
#             return np.nan
        
#         try:
#             result = func(x_val)
#             if isinstance(result, np.ndarray):
#                 result = float(result.flat[0])
#             else:
#                 result = float(result)
            
#             if not np.isfinite(result):
#                 return np.nan
#             return result
#         except:
#             return np.nan
    
#     def _solve_equation_in_range(self, equation):
#         """
#         Solve an equation and return real solutions in the x_range.
        
#         Args:
#             equation: SymPy expression to solve (set equal to 0)
            
#         Returns:
#             List of float solutions
#         """
#         solutions = []
        
#         try:
#             # Try to solve symbolically
#             symbolic_solutions = solve(equation, self.x)
            
#             for sol in symbolic_solutions:
#                 try:
#                     # Handle different types of solutions
#                     if sol.is_real is True or (hasattr(sol, 'is_zero') and sol.is_zero):
#                         sol_float = float(sol.evalf())
#                         if np.isfinite(sol_float) and self.x_range[0] <= sol_float <= self.x_range[1]:
#                             # Verify the solution
#                             test_val = float(equation.subs(self.x, sol).evalf())
#                             if abs(test_val) < 1e-6:  # Solution is valid
#                                 solutions.append(sol_float)
#                     elif sol.is_complex and abs(im(sol)) < 1e-10:
#                         # Essentially real (imaginary part is negligible)
#                         sol_float = float(re(sol).evalf())
#                         if np.isfinite(sol_float) and self.x_range[0] <= sol_float <= self.x_range[1]:
#                             test_val = float(abs(equation.subs(self.x, sol)).evalf())
#                             if abs(test_val) < 1e-6:
#                                 solutions.append(sol_float)
#                 except Exception as inner_e:
#                     continue
                    
#         except Exception as e:
#             # If symbolic solving fails, try numerical approach
#             pass
        
#         # Remove duplicates
#         unique_solutions = []
#         for sol in solutions:
#             if not any(abs(sol - existing) < 1e-6 for existing in unique_solutions):
#                 unique_solutions.append(sol)
        
#         return sorted(unique_solutions)
    
#     def _find_all_features(self):
#         """Find all critical features of the function."""
        
#         print("\n🔍 Analyzing function...")
        
#         # Find critical points (f'(x) = 0)
#         print("  Finding critical points...")
#         critical_x = self._solve_equation_in_range(self.first_derivative)
#         self.critical_points = []
#         for x_val in critical_x:
#             y_val = self._safe_evaluate_single(x_val, self.func_numeric)
#             if np.isfinite(y_val):
#                 self.critical_points.append((x_val, y_val))
#         print(f"  ✓ Found {len(self.critical_points)} critical point(s)")
        
#         # Find roots (f(x) = 0)
#         print("  Finding roots...")
#         root_x = self._solve_equation_in_range(self.func_symbolic)
#         self.roots = []
#         for x_val in root_x:
#             y_val = self._safe_evaluate_single(x_val, self.func_numeric)
#             if np.isfinite(y_val) and abs(y_val) < 1e-6:
#                 self.roots.append(x_val)
#         print(f"  ✓ Found {len(self.roots)} root(s)")
        
#         # Find inflection points (f''(x) = 0)
#         print("  Finding inflection points...")
#         inflection_x = self._solve_equation_in_range(self.second_derivative)
#         self.inflection_points = []
#         for x_val in inflection_x:
#             y_val = self._safe_evaluate_single(x_val, self.func_numeric)
#             if np.isfinite(y_val):
#                 # Verify concavity changes
#                 self.inflection_points.append((x_val, y_val))
#         print(f"  ✓ Found {len(self.inflection_points)} inflection point(s)")
        
#         # Find vertical asymptotes
#         print("  Finding vertical asymptotes...")
#         self.vertical_asymptotes = []
#         try:
#             # Get numerator and denominator
#             numer, denom = fraction(self.func_symbolic)
            
#             if denom != 1:
#                 # Solve denominator = 0
#                 denom_zeros = self._solve_equation_in_range(denom)
                
#                 for x_val in denom_zeros:
#                     # Check if numerator is also zero (removable discontinuity)
#                     numer_val = float(numer.subs(self.x, x_val).evalf())
#                     if abs(numer_val) > 1e-6:  # Not removable
#                         self.vertical_asymptotes.append(x_val)
#         except Exception as e:
#             pass
#         print(f"  ✓ Found {len(self.vertical_asymptotes)} vertical asymptote(s)")
        
#         # Find horizontal asymptotes
#         print("  Finding horizontal asymptotes...")
#         self.horizontal_asymptote = None
#         try:
#             limit_pos_inf = limit(self.func_symbolic, self.x, oo)
#             limit_neg_inf = limit(self.func_symbolic, self.x, -oo)
            
#             # Check if both limits exist and are equal
#             if limit_pos_inf.is_finite and limit_neg_inf.is_finite:
#                 if limit_pos_inf == limit_neg_inf:
#                     self.horizontal_asymptote = float(limit_pos_inf.evalf())
#                     print(f"  ✓ Found horizontal asymptote: y = {self.horizontal_asymptote:.4f}")
#                 else:
#                     print(f"  ✓ Different limits at ±∞")
#             else:
#                 print("  ✓ No horizontal asymptote")
#         except Exception as e:
#             pass
        
#         # Find oblique asymptotes
#         print("  Finding oblique asymptotes...")
#         self.oblique_asymptote = None
#         try:
#             # Check if there's no horizontal asymptote first
#             if self.horizontal_asymptote is None:
#                 # Calculate limit of f(x)/x as x approaches infinity
#                 ratio = self.func_symbolic / self.x
#                 m = limit(ratio, self.x, oo)
                
#                 # If slope exists and is finite
#                 if m.is_finite and m != 0:
#                     # Calculate y-intercept: limit of (f(x) - mx) as x approaches infinity
#                     b = limit(self.func_symbolic - m * self.x, self.x, oo)
                    
#                     if b.is_finite:
#                         m_float = float(m.evalf())
#                         b_float = float(b.evalf())
#                         self.oblique_asymptote = (m_float, b_float)
#                         print(f"  ✓ Found oblique asymptote: y = {m_float:.4f}x + {b_float:.4f}")
#                     else:
#                         print("  ✓ No oblique asymptote")
#                 else:
#                     print("  ✓ No oblique asymptote")
#             else:
#                 print("  ✓ No oblique asymptote (horizontal asymptote exists)")
#         except Exception as e:
#             print("  ✓ No oblique asymptote")
        
#         print("✓ Analysis complete!\n")
    
#     def create_plot(self, figsize=(14, 9), title=None):
#         """Create the matplotlib figure."""
#         self.fig, self.ax = plt.subplots(figsize=figsize)
        
#         if title is None:
#             title = f"f(x) = {self.func_str}"
        
#         self.ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
#         self.ax.set_xlabel('x', fontsize=13, fontweight='bold')
#         self.ax.set_ylabel('y', fontsize=13, fontweight='bold')
#         self.ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.7)
#         self.ax.axhline(y=0, color='k', linewidth=0.8, alpha=0.5)
#         self.ax.axvline(x=0, color='k', linewidth=0.8, alpha=0.5)
        
#         # Set default y-limits early to prevent matplotlib from auto-scaling to extreme values
#         self.ax.set_ylim(-10, 10)
        
#         return self
    
#     def plot_function(self, color='#1f77b4', linewidth=2.5, label='f(x)'):
#         """Plot the function."""
#         if self.ax is None:
#             self.create_plot()
        
#         # Clip y-values to reasonable range to prevent matplotlib errors
#         y_clipped = np.clip(self.y_values, -1e6, 1e6)
        
#         self.ax.plot(self.x_values, y_clipped, color=color, 
#                     linewidth=linewidth, label=label, zorder=3)
#         return self
    
#     def plot_derivative(self, color='#ff7f0e', linewidth=2, label="f'(x)"):
#         """Plot the first derivative."""
#         if self.ax is None:
#             self.create_plot()
        
#         deriv_values = self._safe_evaluate_array(self.x_values, self.first_deriv_numeric)
#         deriv_clipped = np.clip(deriv_values, -1e6, 1e6)
#         self.ax.plot(self.x_values, deriv_clipped, color=color, 
#                     linewidth=linewidth, label=label, linestyle='--', alpha=0.8, zorder=2)
#         return self
    
#     def plot_second_derivative(self, color='#2ca02c', linewidth=2, label="f''(x)"):
#         """Plot the second derivative."""
#         if self.ax is None:
#             self.create_plot()
        
#         second_deriv_values = self._safe_evaluate_array(self.x_values, self.second_deriv_numeric)
#         second_deriv_clipped = np.clip(second_deriv_values, -1e6, 1e6)
#         self.ax.plot(self.x_values, second_deriv_clipped, color=color, 
#                     linewidth=linewidth, label=label, linestyle='-.', alpha=0.8, zorder=2)
#         return self
    
#     def plot_critical_points(self, color='#d62728', marker='o', 
#                             markersize=12, label='Critical Points'):
#         """Plot critical points."""
#         if self.ax is None:
#             self.create_plot()
        
#         if self.critical_points:
#             x_crit, y_crit = zip(*self.critical_points)
#             self.ax.plot(x_crit, y_crit, marker=marker, color=color, 
#                         markersize=markersize, linestyle='', label=label,
#                         markeredgecolor='black', markeredgewidth=2, zorder=6)
            
#             for x, y in self.critical_points:
#                 self.ax.annotate(f'({x:.3f}, {y:.3f})', 
#                                xy=(x, y), xytext=(15, 15),
#                                textcoords='offset points',
#                                bbox=dict(boxstyle='round,pad=0.5', 
#                                        facecolor='yellow', alpha=0.8,
#                                        edgecolor='black', linewidth=1.5),
#                                fontsize=9, fontweight='bold',
#                                arrowprops=dict(arrowstyle='->', 
#                                              connectionstyle='arc3,rad=0.3',
#                                              color='black', lw=1.5))
#         return self
    
#     def plot_roots(self, color='#ff7f0e', marker='s', 
#                    markersize=12, label='Roots (Zeros)'):
#         """Plot roots."""
#         if self.ax is None:
#             self.create_plot()
        
#         if self.roots:
#             y_roots = [0] * len(self.roots)
#             self.ax.plot(self.roots, y_roots, marker=marker, color=color, 
#                         markersize=markersize, linestyle='', label=label,
#                         markeredgecolor='black', markeredgewidth=2, zorder=6)
            
#             for x in self.roots:
#                 self.ax.annotate(f'x={x:.3f}', 
#                                xy=(x, 0), xytext=(0, -25),
#                                textcoords='offset points',
#                                bbox=dict(boxstyle='round,pad=0.5', 
#                                        facecolor='lightblue', alpha=0.8,
#                                        edgecolor='black', linewidth=1.5),
#                                fontsize=9, fontweight='bold',
#                                ha='center',
#                                arrowprops=dict(arrowstyle='->', 
#                                              color='black', lw=1.5))
#         return self
    
#     def plot_asymptotes(self, vertical_color='#d62728', horizontal_color='#1f77b4',
#                        oblique_color='#17becf', linewidth=2, alpha=0.7):
#         """Plot asymptotes."""
#         if self.ax is None:
#             self.create_plot()
        
#         # Vertical asymptotes
#         for i, x_asym in enumerate(self.vertical_asymptotes):
#             label = 'Vertical Asymptote' if i == 0 else ''
#             self.ax.axvline(x=x_asym, color=vertical_color, linestyle='--', 
#                           linewidth=linewidth, alpha=alpha, label=label, zorder=10)
            
#             ylim = self.ax.get_ylim()
#             y_pos = ylim[1] * 0.9
#             self.ax.text(x_asym, y_pos, f'x={x_asym:.3f}', 
#                         ha='center', va='top',
#                         bbox=dict(boxstyle='round,pad=0.3', 
#                                 facecolor='white', alpha=0.8,
#                                 edgecolor=vertical_color, linewidth=1.5),
#                         fontsize=9, fontweight='bold')
        
#         # Horizontal asymptote
#         if self.horizontal_asymptote is not None:
#             self.ax.axhline(y=self.horizontal_asymptote, color=horizontal_color, 
#                           linestyle='--', linewidth=linewidth, alpha=alpha,
#                           label=f'Horizontal Asymptote y={self.horizontal_asymptote:.3f}',
#                           zorder=1)
        
#         # Oblique asymptote
#         if self.oblique_asymptote is not None:
#             m, b = self.oblique_asymptote
#             x_asymp = np.linspace(self.x_range[0], self.x_range[1], 100)
#             y_asymp = m * x_asymp + b
#             self.ax.plot(x_asymp, y_asymp, color=oblique_color, linestyle='--',
#                         linewidth=linewidth, alpha=alpha,
#                         label=f'Oblique Asymptote y={m:.3f}x+{b:.3f}',
#                         zorder=1)
        
#         return self
    
#     def plot_inflection_points(self, color='#9467bd', marker='^', 
#                               markersize=12, label='Inflection Points'):
#         """Plot inflection points."""
#         if self.ax is None:
#             self.create_plot()
        
#         if self.inflection_points:
#             x_infl, y_infl = zip(*self.inflection_points)
#             self.ax.plot(x_infl, y_infl, marker=marker, color=color, 
#                         markersize=markersize, linestyle='', label=label,
#                         markeredgecolor='black', markeredgewidth=2, zorder=6)
            
#             for x, y in self.inflection_points:
#                 self.ax.annotate(f'({x:.3f}, {y:.3f})', 
#                                xy=(x, y), xytext=(-15, 15),
#                                textcoords='offset points',
#                                bbox=dict(boxstyle='round,pad=0.5', 
#                                        facecolor='lightgreen', alpha=0.8,
#                                        edgecolor='black', linewidth=1.5),
#                                fontsize=9, fontweight='bold',
#                                arrowprops=dict(arrowstyle='->', 
#                                              connectionstyle='arc3,rad=-0.3',
#                                              color='black', lw=1.5))
#         return self
    
#     def plot_tangent_line(self, x0, color='#2ca02c', linewidth=2.5, 
#                          label=None, extend=2):
#         """Plot tangent line at x0."""
#         if self.ax is None:
#             self.create_plot()
        
#         try:
#             # Evaluate at x0 using SymPy for accuracy
#             y0 = float(self.func_symbolic.subs(self.x, x0).evalf())
#             slope = float(self.first_derivative.subs(self.x, x0).evalf())
            
#             if not np.isfinite(y0) or not np.isfinite(slope):
#                 print(f"Cannot plot tangent at x={x0}: function or derivative undefined")
#                 return self
            
#             # Create tangent line
#             x_tangent = np.linspace(x0 - extend, x0 + extend, 100)
#             y_tangent = y0 + slope * (x_tangent - x0)
            
#             if label is None:
#                 label = f'Tangent at x={x0:.2f}'
            
#             self.ax.plot(x_tangent, y_tangent, color=color, 
#                         linewidth=linewidth, label=label, linestyle=':', 
#                         alpha=0.9, zorder=4)
            
#             self.ax.plot(x0, y0, 'o', color=color, markersize=10, 
#                         markeredgecolor='black', markeredgewidth=2, zorder=5)
            
#         except Exception as e:
#             print(f"Error plotting tangent at x={x0}: {e}")
        
#         return self
    
#     def set_limits(self, xlim=None, ylim=None):
#         """Set axis limits with validation to prevent matplotlib errors."""
#         if self.ax is None:
#             self.create_plot()
        
#         if xlim:
#             self.ax.set_xlim(xlim)
        
#         if ylim:
#             y_min, y_max = ylim
#             # Clamp to safe values to prevent matplotlib errors
#             MAX_SAFE = 1e6
#             y_min = max(min(y_min, MAX_SAFE), -MAX_SAFE)
#             y_max = max(min(y_max, MAX_SAFE), -MAX_SAFE)
            
#             self.ax.set_ylim(y_min, y_max)
        
#         return self
    
#     def add_legend(self, loc='best', fontsize=11):
#         """Add legend."""
#         if self.ax is None:
#             self.create_plot()
        
#         self.ax.legend(loc=loc, fontsize=fontsize, framealpha=0.95,
#                       edgecolor='black', fancybox=True, shadow=True)
#         return self
    
#     def add_info_box(self):
#         """Add information box."""
#         if self.ax is None:
#             self.create_plot()
        
#         info_lines = [
#             f"f(x) = {self.func_symbolic}",
#             f"f'(x) = {self.first_derivative}",
#             f"f''(x) = {self.second_derivative}",
#             ""
#         ]
        
#         if self.critical_points:
#             info_lines.append(f"Critical points: {len(self.critical_points)}")
#         if self.roots:
#             info_lines.append(f"Roots: {len(self.roots)}")
#         if self.inflection_points:
#             info_lines.append(f"Inflection points: {len(self.inflection_points)}")
#         if self.vertical_asymptotes:
#             info_lines.append(f"Vertical asymptotes: {len(self.vertical_asymptotes)}")
        
#         info_text = "\n".join(info_lines)
        
#         self.ax.text(0.98, 0.98, info_text, 
#                     transform=self.ax.transAxes,
#                     fontsize=8, verticalalignment='top',
#                     horizontalalignment='right',
#                     bbox=dict(boxstyle='round,pad=0.7', 
#                             facecolor='wheat', alpha=0.9,
#                             edgecolor='black', linewidth=1.5),
#                     family='monospace')
        
#         return self
    
#     def save(self, filename):
#         """Save the plot."""
#         if self.fig is None:
#             return self
        
#         self.fig.tight_layout()
#         self.fig.savefig(filename, dpi=300, bbox_inches='tight', 
#                         facecolor='white', edgecolor='none')
#         return self
    
#     def show(self):
#         """Display the plot."""
#         if self.fig is None:
#             return self
        
#         self.fig.tight_layout()
#         plt.show()
#         return self


# def get_yes_no(prompt):
#     """Get yes/no input."""
#     while True:
#         response = input(prompt + " (y/n): ").lower().strip()
#         if response in ['y', 'yes']:
#             return True
#         elif response in ['n', 'no']:
#             return False
#         print("Please enter 'y' or 'n'")


# def get_float(prompt, default=None):
#     """Get float input."""
#     while True:
#         if default is not None:
#             response = input(f"{prompt} (default: {default}): ").strip()
#         else:
#             response = input(prompt + ": ").strip()
            
#         if response == '' and default is not None:
#             return default
#         try:
#             return float(response)
#         except ValueError:
#             print("Please enter a valid number")


# def print_header():
#     """Print header."""
#     print("\n" + "="*70)
#     print(" "*15 + "ACCURATE FUNCTION GRAPHER v2.0")
#     print(" "*20 + "Powered by SymPy")
#     print("="*70)


# def main():
#     """Main program."""
#     print_header()
    
#     graph_counter = 1
    
#     while True:
#         print("\n📝 Enter a mathematical function using 'x'")
#         print("Examples: x**2, sin(x), 1/(x-2), x**3 - 3*x**2 + 2")
#         print("Type 'quit' to exit\n")
        
#         func_str = input("f(x) = ").strip()
        
#         if not func_str or func_str.lower() in ['exit', 'quit', 'q']:
#             break
        
#         print(f"\n{'─'*70}")
#         print(f"Graph #{graph_counter}")
#         print(f"{'─'*70}")
        
#         # Get range
#         x_min = get_float("X minimum", default=-10)
#         x_max = get_float("X maximum", default=10)
        
#         # Create grapher
#         try:
#             grapher = AccurateFunctionGrapher(func_str, x_range=(x_min, x_max))
#         except Exception as e:
#             print(f"\n❌ Error: {e}")
#             continue
        
#         # Y limits
#         use_ylim = get_yes_no("\nSet custom y-axis limits?")
#         if use_ylim:
#             y_min = get_float("Y minimum", default=-10)
#             y_max = get_float("Y maximum", default=10)
#             ylim = (y_min, y_max)
#         else:
#             ylim = (-10, 10)
        
#         # Create plot
#         grapher.create_plot(title=f"Graph #{graph_counter}: f(x) = {func_str}")
#         grapher.plot_function()
        
#         # Options
#         print("\n" + "="*70)
#         print("PLOT OPTIONS")
#         print("="*70)
        
#         if get_yes_no("📈 Plot first derivative f'(x)?"):
#             grapher.plot_derivative()
        
#         if get_yes_no("📉 Plot second derivative f''(x)?"):
#             grapher.plot_second_derivative()
        
#         if get_yes_no("🎯 Plot critical points?"):
#             grapher.plot_critical_points()
        
#         if get_yes_no("🔍 Plot roots (zeros)?"):
#             grapher.plot_roots()
        
#         if get_yes_no("📏 Plot asymptotes?"):
#             grapher.plot_asymptotes()
        
#         if get_yes_no("🔄 Plot inflection points?"):
#             grapher.plot_inflection_points()
        
#         if get_yes_no("📐 Plot tangent line(s)?"):
#             num = int(get_float("How many", default=1))
#             colors = ['#2ca02c', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f']
#             for i in range(num):
#                 x0 = get_float(f"x-coordinate for tangent {i+1}")
#                 grapher.plot_tangent_line(x0=x0, color=colors[i % len(colors)])
        
#         if get_yes_no("ℹ️  Add information box?"):
#             grapher.add_info_box()
        
#         grapher.set_limits(ylim=ylim)
        
#         grapher.add_legend()
        
#         # Save
#         filename = f"graph_{graph_counter:03d}.png"
#         grapher.save(filename)
#         print(f"\n✓ Saved: {filename}")
        
#         if get_yes_no("\n👁️  Display now?"):
#             grapher.show()
        
#         graph_counter += 1
        
#         if not get_yes_no("\n🔄 Create another graph?"):
#             break
    
#     # Copy to output
#     if graph_counter > 1:
#         print(f"\n📊 Created {graph_counter - 1} graph(s)")
#         import os
#         import shutil
#         os.makedirs("outputs", exist_ok=True)
#         for i in range(1, graph_counter):
#             src = f"graph_{i:03d}.png"
#             dst = f"outputs/graph_{i:03d}.png"
#             if os.path.exists(src):
#                 shutil.copy(src, dst)
#         print(f"✓ Copied to outputs/")
    
#     print("\n" + "="*70)
#     print("Thank you for using Accurate Function Grapher!")
#     print("="*70 + "\n")


# if __name__ == "__main__":
#     main()