import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import fsolve
import warnings
warnings.filterwarnings('ignore')


def derivative(func, x, dx=1e-5):
    """Calculate numerical derivative using central difference method."""
    return (func(x + dx) - func(x - dx)) / (2 * dx)


class FunctionGrapher:
    """
    A class to graph mathematical functions and their properties.
    
    Attributes:
        func: The mathematical function to graph
        x_range: Tuple of (min, max) for x-axis
        num_points: Number of points to plot
    """
    
    def __init__(self, func, x_range=(-10, 10), num_points=1000):
        """
        Initialize the FunctionGrapher.
        
        Args:
            func: A callable function f(x)
            x_range: Tuple of (x_min, x_max)
            num_points: Number of points for smooth plotting
        """
        self.func = func
        self.x_range = x_range
        self.num_points = num_points
        self.x_values = np.linspace(x_range[0], x_range[1], num_points)
        
        # Calculate y values, handling potential errors
        self.y_values = self._safe_evaluate(self.x_values, self.func)
        
        # Initialize plot elements
        self.fig = None
        self.ax = None
        self.legend_elements = []
        
    def _safe_evaluate(self, x_vals, func):
        """Safely evaluate function, handling domain errors."""
        y_vals = np.zeros_like(x_vals)
        for i, x in enumerate(x_vals):
            try:
                y_vals[i] = func(x)
                # Check for inf or nan
                if not np.isfinite(y_vals[i]):
                    y_vals[i] = np.nan
            except:
                y_vals[i] = np.nan
        return y_vals
    
    def create_plot(self, figsize=(12, 8), title="Function Graph"):
        """Create the matplotlib figure and axes."""
        self.fig, self.ax = plt.subplots(figsize=figsize)
        self.ax.set_title(title, fontsize=16, fontweight='bold')
        self.ax.set_xlabel('x', fontsize=12)
        self.ax.set_ylabel('y', fontsize=12)
        self.ax.grid(True, alpha=0.3, linestyle='--')
        self.ax.axhline(y=0, color='k', linewidth=0.5)
        self.ax.axvline(x=0, color='k', linewidth=0.5)
        return self
    
    def plot_function(self, color='blue', linewidth=2, label='f(x)'):
        """Plot the original function."""
        if self.ax is None:
            self.create_plot()
        
        self.ax.plot(self.x_values, self.y_values, color=color, 
                    linewidth=linewidth, label=label)
        return self
    
    def plot_derivative(self, color='red', linewidth=2, label="f'(x)", dx=1e-5):
        """
        Plot the derivative of the function.
        
        Args:
            color: Line color
            linewidth: Line width
            label: Legend label
            dx: Step size for numerical differentiation
        """
        if self.ax is None:
            self.create_plot()
        
        # Calculate derivative numerically
        derivative_vals = np.zeros_like(self.x_values)
        for i, x in enumerate(self.x_values):
            try:
                derivative_vals[i] = derivative(self.func, x, dx=dx)
                if not np.isfinite(derivative_vals[i]):
                    derivative_vals[i] = np.nan
            except:
                derivative_vals[i] = np.nan
        
        self.ax.plot(self.x_values, derivative_vals, color=color, 
                    linewidth=linewidth, label=label, linestyle='--')
        return self
    
    def plot_tangent_line(self, x0, color='green', linewidth=2, 
                         label=None, dx=1e-5, extend=2):
        """
        Plot the tangent line at a specific point x0.
        
        Args:
            x0: Point at which to draw tangent
            color: Line color
            linewidth: Line width
            label: Legend label
            dx: Step size for derivative calculation
            extend: How far to extend the tangent line on each side
        """
        if self.ax is None:
            self.create_plot()
        
        # Calculate function value and derivative at x0
        try:
            y0 = self.func(x0)
            slope = derivative(self.func, x0, dx=dx)
            
            # Create tangent line: y - y0 = slope * (x - x0)
            x_tangent = np.linspace(x0 - extend, x0 + extend, 100)
            y_tangent = y0 + slope * (x_tangent - x0)
            
            if label is None:
                label = f'Tangent at x={x0:.2f}'
            
            self.ax.plot(x_tangent, y_tangent, color=color, 
                        linewidth=linewidth, label=label, linestyle=':')
            
            # Mark the point of tangency
            self.ax.plot(x0, y0, 'o', color=color, markersize=8, 
                        markeredgecolor='black', markeredgewidth=1.5)
            
        except Exception as e:
            print(f"Could not plot tangent at x={x0}: {e}")
        
        return self
    
    def plot_critical_points(self, color='purple', marker='o', 
                            markersize=10, label='Critical Points'):
        """
        Find and plot critical points (where derivative = 0).
        
        Args:
            color: Marker color
            marker: Marker style
            markersize: Size of markers
            label: Legend label
        """
        if self.ax is None:
            self.create_plot()
        
        critical_points = []
        
        # Search for points where derivative is approximately 0
        def derivative_func(x):
            try:
                return derivative(self.func, x, dx=1e-5)
            except:
                return np.nan
        
        # Search in intervals
        search_points = np.linspace(self.x_range[0], self.x_range[1], 20)
        
        for i in range(len(search_points) - 1):
            try:
                # Try to find a root in this interval
                root = fsolve(derivative_func, (search_points[i] + search_points[i+1])/2)[0]
                
                # Check if root is in our range and derivative is actually close to 0
                if (self.x_range[0] <= root <= self.x_range[1] and 
                    abs(derivative_func(root)) < 0.01):
                    # Check if we haven't already found this root
                    if not any(abs(root - cp[0]) < 0.1 for cp in critical_points):
                        y_val = self.func(root)
                        if np.isfinite(y_val):
                            critical_points.append((root, y_val))
            except:
                continue
        
        if critical_points:
            x_crit, y_crit = zip(*critical_points)
            self.ax.plot(x_crit, y_crit, marker=marker, color=color, 
                        markersize=markersize, linestyle='', label=label,
                        markeredgecolor='black', markeredgewidth=1.5)
            
            # Annotate critical points
            for x, y in critical_points:
                self.ax.annotate(f'({x:.2f}, {y:.2f})', 
                               xy=(x, y), xytext=(10, 10),
                               textcoords='offset points',
                               bbox=dict(boxstyle='round,pad=0.5', 
                                       facecolor='yellow', alpha=0.7),
                               fontsize=8)
        
        return self
    
    def plot_roots(self, color='orange', marker='s', 
                   markersize=10, label='Roots (Zeros)'):
        """
        Find and plot roots (where f(x) = 0).
        
        Args:
            color: Marker color
            marker: Marker style
            markersize: Size of markers
            label: Legend label
        """
        if self.ax is None:
            self.create_plot()
        
        roots = []
        
        # Search for sign changes
        for i in range(len(self.y_values) - 1):
            if np.isfinite(self.y_values[i]) and np.isfinite(self.y_values[i+1]):
                if self.y_values[i] * self.y_values[i+1] < 0:
                    # Sign change detected, refine with fsolve
                    try:
                        root = fsolve(self.func, self.x_values[i])[0]
                        if (self.x_range[0] <= root <= self.x_range[1] and 
                            abs(self.func(root)) < 0.01):
                            if not any(abs(root - r) < 0.1 for r in roots):
                                roots.append(root)
                    except:
                        continue
        
        if roots:
            y_roots = [0] * len(roots)
            self.ax.plot(roots, y_roots, marker=marker, color=color, 
                        markersize=markersize, linestyle='', label=label,
                        markeredgecolor='black', markeredgewidth=1.5)
            
            # Annotate roots
            for x in roots:
                self.ax.annotate(f'x={x:.2f}', 
                               xy=(x, 0), xytext=(0, -20),
                               textcoords='offset points',
                               bbox=dict(boxstyle='round,pad=0.5', 
                                       facecolor='lightblue', alpha=0.7),
                               fontsize=8,
                               ha='center')
        
        return self
    
    def plot_asymptotes(self, vertical_color='red', horizontal_color='blue',
                       linewidth=1.5, alpha=0.7):
        """
        Detect and plot vertical and horizontal asymptotes.
        
        Args:
            vertical_color: Color for vertical asymptotes
            horizontal_color: Color for horizontal asymptotes
            linewidth: Width of asymptote lines
            alpha: Transparency of asymptote lines
        """
        if self.ax is None:
            self.create_plot()
        
        # Detect vertical asymptotes (where function goes to infinity)
        vertical_asymptotes = []
        threshold = 1e3
        
        for i in range(len(self.y_values) - 1):
            if (np.isfinite(self.y_values[i]) and 
                (not np.isfinite(self.y_values[i+1]) or 
                 abs(self.y_values[i+1] - self.y_values[i]) > threshold)):
                vertical_asymptotes.append(self.x_values[i+1])
        
        # Plot vertical asymptotes
        for x in vertical_asymptotes:
            self.ax.axvline(x=x, color=vertical_color, linestyle='--', 
                          linewidth=linewidth, alpha=alpha,
                          label='Vertical Asymptote' if x == vertical_asymptotes[0] else '')
        
        # Detect horizontal asymptote (limit as x -> ±infinity)
        try:
            # Check behavior at edges
            left_vals = self.y_values[:50]
            right_vals = self.y_values[-50:]
            
            left_finite = left_vals[np.isfinite(left_vals)]
            right_finite = right_vals[np.isfinite(right_vals)]
            
            if len(left_finite) > 10 and len(right_finite) > 10:
                left_limit = np.mean(left_finite[-10:])
                right_limit = np.mean(right_finite[-10:])
                
                # If both limits are similar, there's a horizontal asymptote
                if abs(left_limit - right_limit) < 1:
                    y_asymptote = (left_limit + right_limit) / 2
                    self.ax.axhline(y=y_asymptote, color=horizontal_color, 
                                  linestyle='--', linewidth=linewidth, 
                                  alpha=alpha, label=f'Horizontal Asymptote y={y_asymptote:.2f}')
        except:
            pass
        
        return self
    
    def plot_inflection_points(self, color='magenta', marker='^', 
                              markersize=10, label='Inflection Points'):
        """
        Find and plot inflection points (where second derivative = 0).
        
        Args:
            color: Marker color
            marker: Marker style
            markersize: Size of markers
            label: Legend label
        """
        if self.ax is None:
            self.create_plot()
        
        inflection_points = []
        
        # Calculate second derivative
        def second_derivative(x):
            try:
                return derivative(lambda t: derivative(self.func, t, dx=1e-5), 
                                x, dx=1e-5)
            except:
                return np.nan
        
        # Search for points where second derivative changes sign
        search_points = np.linspace(self.x_range[0], self.x_range[1], 20)
        
        for i in range(len(search_points) - 1):
            try:
                root = fsolve(second_derivative, (search_points[i] + search_points[i+1])/2)[0]
                
                if (self.x_range[0] <= root <= self.x_range[1] and 
                    abs(second_derivative(root)) < 0.1):
                    if not any(abs(root - ip[0]) < 0.1 for ip in inflection_points):
                        y_val = self.func(root)
                        if np.isfinite(y_val):
                            inflection_points.append((root, y_val))
            except:
                continue
        
        if inflection_points:
            x_infl, y_infl = zip(*inflection_points)
            self.ax.plot(x_infl, y_infl, marker=marker, color=color, 
                        markersize=markersize, linestyle='', label=label,
                        markeredgecolor='black', markeredgewidth=1.5)
        
        return self
    
    def set_limits(self, xlim=None, ylim=None):
        """
        Set axis limits.
        
        Args:
            xlim: Tuple of (xmin, xmax) or None for auto
            ylim: Tuple of (ymin, ymax) or None for auto
        """
        if self.ax is None:
            self.create_plot()
        
        if xlim:
            self.ax.set_xlim(xlim)
        if ylim:
            self.ax.set_ylim(ylim)
        
        return self
    
    def add_legend(self, loc='best', fontsize=10):
        """Add legend to the plot."""
        if self.ax is None:
            self.create_plot()
        
        self.ax.legend(loc=loc, fontsize=fontsize, framealpha=0.9)
        return self
    
    def save(self, filename='function_graph.png', dpi=300):
        """Save the plot to a file."""
        if self.fig is None:
            print("No plot to save. Create a plot first.")
            return self
        
        self.fig.tight_layout()
        self.fig.savefig(filename, dpi=dpi, bbox_inches='tight')
        print(f"Plot saved to {filename}")
        return self
    
    def show(self):
        """Display the plot."""
        if self.fig is None:
            print("No plot to show. Create a plot first.")
            return self
        
        self.fig.tight_layout()
        plt.show()
        return self


# Example usage and demonstration
if __name__ == "__main__":
    
    # Example 1: Polynomial function
    print("Example 1: Polynomial function f(x) = x³ - 6x² + 9x + 1")
    
    def polynomial(x):
        return x**3 - 6*x**2 + 9*x + 1
    
    grapher1 = FunctionGrapher(polynomial, x_range=(-2, 6))
    (grapher1.create_plot(title="Polynomial Function: f(x) = x³ - 6x² + 9x + 1")
              .plot_function(color='blue', label='f(x)')
              .plot_derivative(color='red', label="f'(x)")
              .plot_tangent_line(x0=2, color='green')
              .plot_critical_points()
              .plot_roots()
              .plot_inflection_points()
              .set_limits(ylim=(-5, 10))
              .add_legend()
              .save('polynomial_graph.png')
              .show())
    
    # Example 2: Rational function with asymptotes
    print("\nExample 2: Rational function f(x) = 1/(x-2)")
    
    def rational(x):
        if x == 2:
            return np.nan
        return 1 / (x - 2)
    
    grapher2 = FunctionGrapher(rational, x_range=(-5, 10))
    (grapher2.create_plot(title="Rational Function: f(x) = 1/(x-2)")
              .plot_function(color='blue', label='f(x)')
              .plot_derivative(color='red', label="f'(x)")
              .plot_asymptotes()
              .set_limits(ylim=(-5, 5))
              .add_legend()
              .save('rational_graph.png')
              .show())
    
    # Example 3: Trigonometric function
    print("\nExample 3: Trigonometric function f(x) = sin(x) + cos(2x)")
    
    def trig(x):
        return np.sin(x) + np.cos(2*x)
    
    grapher3 = FunctionGrapher(trig, x_range=(-2*np.pi, 2*np.pi))
    (grapher3.create_plot(title="Trigonometric Function: f(x) = sin(x) + cos(2x)")
              .plot_function(color='blue', label='f(x)')
              .plot_derivative(color='red', label="f'(x)")
              .plot_tangent_line(x0=np.pi/2, color='green')
              .plot_tangent_line(x0=-np.pi, color='purple')
              .plot_critical_points()
              .plot_roots()
              .set_limits(ylim=(-3, 3))
              .add_legend()
              .save('trig_graph.png')
              .show())
    
    # Example 4: Exponential function
    print("\nExample 4: Exponential function f(x) = e^(-x²/2)")
    
    def gaussian(x):
        return np.exp(-x**2 / 2)
    
    grapher4 = FunctionGrapher(gaussian, x_range=(-5, 5))
    (grapher4.create_plot(title="Gaussian Function: f(x) = e^(-x²/2)")
              .plot_function(color='blue', label='f(x)')
              .plot_derivative(color='red', label="f'(x)")
              .plot_tangent_line(x0=1, color='green')
              .plot_tangent_line(x0=-1, color='purple')
              .plot_critical_points()
              .plot_inflection_points()
              .add_legend()
              .save('gaussian_graph.png')
              .show())
    
    print("\nExample 5: Square function f(x) = x²")
    
    def square(x):
        return (x ** 2)
    
    grapher6 = FunctionGrapher(square, x_range=(-5, 10))
    (grapher6.create_plot(title="Square Function: f(x) = x²")
              .plot_function(color='blue', label='f(x)')
              .plot_derivative(color='red', label="f'(x)")
              .plot_asymptotes()
              .set_limits(ylim=(-5, 5))
              .plot_critical_points()
              .plot_inflection_points()
              .add_legend()
              .save('square_graph.png')
              .show())
    
    print("\n" + "="*60)
    print("All graphs have been created and saved!")
    print("="*60)