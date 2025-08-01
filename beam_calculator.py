import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import quad
import logging

class BeamCalculator:
    """
    Beam Bending Calculator and Visualizer
    Supports cantilever and simply supported beams with point and distributed loads
    """
    
    def __init__(self, length, young_modulus, moment_inertia, support_type='simply_supported'):
        self.L = length  # Beam length
        self.E = young_modulus  # Young's modulus
        self.I = moment_inertia  # Moment of inertia
        self.EI = self.E * self.I  # Flexural rigidity
        self.support_type = support_type
        
        # Load storage
        self.point_loads = []  # [(magnitude, position)]
        self.distributed_loads = []  # [(magnitude, start_pos, end_pos)]
        
        # Results storage
        self.x_points = None
        self.shear_force = None
        self.bending_moment = None
        self.deflection = None
        self.max_deflection = None
        self.max_moment = None
        self.max_shear = None
        
        logging.info(f"Beam initialized: L={length}, E={young_modulus}, I={moment_inertia}, Support={support_type}")
    
    def add_point_load(self, magnitude, position):
        """Add a point load to the beam"""
        if 0 <= position <= self.L:
            self.point_loads.append((magnitude, position))
            logging.info(f"Added point load: {magnitude}N at {position}m")
        else:
            raise ValueError(f"Point load position {position} is outside beam length {self.L}")
    
    def add_distributed_load(self, magnitude, start_pos, length):
        """Add a uniformly distributed load to the beam"""
        end_pos = start_pos + length
        if 0 <= start_pos <= self.L and 0 <= end_pos <= self.L:
            self.distributed_loads.append((magnitude, start_pos, end_pos))
            logging.info(f"Added distributed load: {magnitude}N/m from {start_pos}m to {end_pos}m")
        else:
            raise ValueError(f"Distributed load extends outside beam length")
    
    def calculate_reactions(self):
        """Calculate support reactions based on equilibrium"""
        if self.support_type == 'cantilever':
            # For cantilever beam, reactions are at the fixed end (x=0)
            return self._calculate_cantilever_reactions()
        elif self.support_type == 'simply_supported':
            # For simply supported beam, reactions are at both ends
            return self._calculate_simply_supported_reactions()
        else:
            raise ValueError(f"Unsupported beam type: {self.support_type}")
    
    def _calculate_cantilever_reactions(self):
        """Calculate reactions for cantilever beam (fixed at x=0)"""
        # Sum of vertical forces
        R_y = 0
        # Sum of moments about fixed end
        M_fixed = 0
        
        # Point loads
        for P, a in self.point_loads:
            R_y += P
            M_fixed += P * a
        
        # Distributed loads
        for w, start, end in self.distributed_loads:
            load_length = end - start
            total_load = w * load_length
            centroid = start + load_length / 2
            R_y += total_load
            M_fixed += total_load * centroid
        
        return {'R_y': R_y, 'M_fixed': M_fixed}
    
    def _calculate_simply_supported_reactions(self):
        """Calculate reactions for simply supported beam"""
        # Sum of moments about left support (x=0) to find right reaction
        moment_sum = 0
        total_vertical_load = 0
        
        # Point loads
        for P, a in self.point_loads:
            moment_sum += P * a
            total_vertical_load += P
        
        # Distributed loads
        for w, start, end in self.distributed_loads:
            load_length = end - start
            total_load = w * load_length
            centroid = start + load_length / 2
            moment_sum += total_load * centroid
            total_vertical_load += total_load
        
        R_B = moment_sum / self.L  # Right reaction
        R_A = total_vertical_load - R_B  # Left reaction
        
        return {'R_A': R_A, 'R_B': R_B}
    
    def calculate_shear_force(self, x):
        """Calculate shear force at position x"""
        if self.support_type == 'cantilever':
            return self._cantilever_shear_force(x)
        else:
            return self._simply_supported_shear_force(x)
    
    def _cantilever_shear_force(self, x):
        """Calculate shear force for cantilever beam"""
        V = 0
        
        # Point loads to the right of section
        for P, a in self.point_loads:
            if a > x:
                V += P
        
        # Distributed loads to the right of section
        for w, start, end in self.distributed_loads:
            if start > x:
                # Entire load to the right
                V += w * (end - start)
            elif end > x > start:
                # Partial load to the right
                V += w * (end - x)
        
        return V
    
    def _simply_supported_shear_force(self, x):
        """Calculate shear force for simply supported beam"""
        reactions = self.calculate_reactions()
        V = reactions['R_A']  # Start with left reaction
        
        # Subtract loads to the left of section
        for P, a in self.point_loads:
            if a <= x:
                V -= P
        
        # Subtract distributed loads to the left of section
        for w, start, end in self.distributed_loads:
            if end <= x:
                # Entire load to the left
                V -= w * (end - start)
            elif start <= x < end:
                # Partial load to the left
                V -= w * (x - start)
        
        return V
    
    def calculate_bending_moment(self, x):
        """Calculate bending moment at position x"""
        if self.support_type == 'cantilever':
            return self._cantilever_bending_moment(x)
        else:
            return self._simply_supported_bending_moment(x)
    
    def _cantilever_bending_moment(self, x):
        """Calculate bending moment for cantilever beam"""
        M = 0
        
        # Point loads to the right of section
        for P, a in self.point_loads:
            if a > x:
                M += P * (a - x)
        
        # Distributed loads to the right of section
        for w, start, end in self.distributed_loads:
            if start > x:
                # Entire load to the right
                load_magnitude = w * (end - start)
                centroid_distance = (start + end) / 2 - x
                M += load_magnitude * centroid_distance
            elif end > x > start:
                # Partial load to the right
                load_magnitude = w * (end - x)
                centroid_distance = (x + end) / 2 - x
                M += load_magnitude * centroid_distance
        
        return M
    
    def _simply_supported_bending_moment(self, x):
        """Calculate bending moment for simply supported beam"""
        reactions = self.calculate_reactions()
        M = reactions['R_A'] * x  # Moment due to left reaction
        
        # Subtract moments due to loads to the left of section
        for P, a in self.point_loads:
            if a <= x:
                M -= P * (x - a)
        
        # Subtract moments due to distributed loads to the left of section
        for w, start, end in self.distributed_loads:
            if end <= x:
                # Entire load to the left
                load_magnitude = w * (end - start)
                centroid_distance = x - (start + end) / 2
                M -= load_magnitude * centroid_distance
            elif start <= x < end:
                # Partial load to the left
                load_magnitude = w * (x - start)
                centroid_distance = (x - start) / 2
                M -= load_magnitude * centroid_distance
        
        return M
    
    def calculate_deflection(self):
        """Calculate deflection using the moment-area method"""
        # This is a simplified implementation
        # In practice, more sophisticated methods would be used
        n_points = 1000
        x = np.linspace(0, self.L, n_points)
        
        # Calculate moments at all points
        moments = np.array([self.calculate_bending_moment(xi) for xi in x])
        
        # Numerical integration for deflection
        # EI * d²y/dx² = M(x)
        # Double integration to get deflection
        
        if self.support_type == 'cantilever':
            # For cantilever: y(0) = 0, dy/dx(0) = 0
            deflection = np.zeros_like(x)
            for i in range(1, len(x)):
                dx = x[i] - x[i-1]
                # Simple numerical integration
                deflection[i] = deflection[i-1] + (moments[i] * dx**2) / (2 * self.EI)
        else:
            # For simply supported: y(0) = 0, y(L) = 0
            # Use more sophisticated integration with boundary conditions
            deflection = self._calculate_simply_supported_deflection(x, moments)
        
        return x, deflection
    
    def _calculate_simply_supported_deflection(self, x, moments):
        """Calculate deflection for simply supported beam using conjugate beam method"""
        # Simplified calculation - in practice, use more accurate methods
        deflection = np.zeros_like(x)
        dx = x[1] - x[0]
        
        # First integration for slope
        slope = np.zeros_like(x)
        for i in range(1, len(x)):
            slope[i] = slope[i-1] + (moments[i] * dx) / self.EI
        
        # Apply boundary condition for simply supported beam
        # Adjust slope to satisfy y(L) = 0
        slope_correction = -slope[-1] / self.L
        slope += slope_correction * x
        
        # Second integration for deflection
        for i in range(1, len(x)):
            deflection[i] = deflection[i-1] + slope[i] * dx
        
        return deflection
    
    def calculate(self):
        """Perform all calculations"""
        # Create x points for analysis
        self.x_points = np.linspace(0, self.L, 1000)
        
        # Calculate shear force
        self.shear_force = np.array([self.calculate_shear_force(x) for x in self.x_points])
        
        # Calculate bending moment
        self.bending_moment = np.array([self.calculate_bending_moment(x) for x in self.x_points])
        
        # Calculate deflection
        x_def, self.deflection = self.calculate_deflection()
        
        # Calculate maximum values
        self.max_deflection = np.max(np.abs(self.deflection))
        self.max_moment = np.max(np.abs(self.bending_moment))
        self.max_shear = np.max(np.abs(self.shear_force))
        
        logging.info(f"Calculations complete: Max deflection={self.max_deflection:.6f}m, Max moment={self.max_moment:.2f}Nm")
    
    def generate_plots(self):
        """Generate all visualization plots"""
        plt.style.use('default')
        plots = {}
        
        # Shear Force Diagram
        fig1, ax1 = plt.subplots(figsize=(10, 6))
        ax1.plot(self.x_points, self.shear_force, 'b-', linewidth=2, label='Shear Force')
        ax1.axhline(y=0, color='k', linestyle='-', alpha=0.3)
        ax1.grid(True, alpha=0.3)
        ax1.set_xlabel('Position along beam (m)')
        ax1.set_ylabel('Shear Force (N)')
        ax1.set_title('Shear Force Diagram (SFD)')
        ax1.legend()
        plots['shear_force'] = fig1
        
        # Bending Moment Diagram
        fig2, ax2 = plt.subplots(figsize=(10, 6))
        ax2.plot(self.x_points, self.bending_moment, 'r-', linewidth=2, label='Bending Moment')
        ax2.axhline(y=0, color='k', linestyle='-', alpha=0.3)
        ax2.grid(True, alpha=0.3)
        ax2.set_xlabel('Position along beam (m)')
        ax2.set_ylabel('Bending Moment (Nm)')
        ax2.set_title('Bending Moment Diagram (BMD)')
        ax2.legend()
        plots['bending_moment'] = fig2
        
        # Deflection Curve
        fig3, ax3 = plt.subplots(figsize=(10, 6))
        ax3.plot(self.x_points[:len(self.deflection)], self.deflection, 'g-', linewidth=2, label='Deflection')
        ax3.axhline(y=0, color='k', linestyle='-', alpha=0.3)
        ax3.grid(True, alpha=0.3)
        ax3.set_xlabel('Position along beam (m)')
        ax3.set_ylabel('Deflection (m)')
        ax3.set_title('Beam Deflection Curve')
        ax3.legend()
        # Exaggerate deflection for visibility
        ax3.set_ylim([np.min(self.deflection) * 1.1, np.max(self.deflection) * 1.1])
        plots['deflection'] = fig3
        
        # Beam diagram with loads
        fig4, ax4 = plt.subplots(figsize=(12, 4))
        self._draw_beam_diagram(ax4)
        plots['beam_diagram'] = fig4
        
        return plots
    
    def _draw_beam_diagram(self, ax):
        """Draw beam diagram with loads and supports"""
        # Draw beam
        ax.plot([0, self.L], [0, 0], 'k-', linewidth=8, label='Beam')
        
        # Draw supports
        if self.support_type == 'cantilever':
            # Fixed support at x=0
            ax.plot([0, 0], [-0.1, 0.1], 'k-', linewidth=6)
            ax.add_patch(plt.Rectangle((-0.05, -0.15), 0.1, 0.3, 
                                     facecolor='gray', edgecolor='black'))
        else:
            # Simply supported
            # Left support
            ax.plot([0, 0], [-0.1, 0], 'k-', linewidth=4)
            ax.plot([-0.05, 0.05], [-0.1, -0.1], 'k-', linewidth=4)
            # Right support  
            ax.plot([self.L, self.L], [-0.1, 0], 'k-', linewidth=4)
            ax.plot([self.L-0.05, self.L+0.05], [-0.1, -0.1], 'k-', linewidth=4)
        
        # Draw point loads
        for P, pos in self.point_loads:
            ax.annotate('', xy=(pos, 0), xytext=(pos, 0.3),
                       arrowprops=dict(arrowstyle='->', color='red', lw=2))
            ax.text(pos, 0.35, f'{P}N', ha='center', va='bottom', color='red', fontweight='bold')
        
        # Draw distributed loads
        for w, start, end in self.distributed_loads:
            x_dist = np.linspace(start, end, 20)
            y_dist = np.full_like(x_dist, 0.2)
            ax.plot(x_dist, y_dist, 'b-', linewidth=3)
            # Draw arrows
            for x in x_dist[::3]:
                ax.annotate('', xy=(x, 0), xytext=(x, 0.2),
                           arrowprops=dict(arrowstyle='->', color='blue', lw=1))
            ax.text((start + end)/2, 0.25, f'{w}N/m', ha='center', va='bottom', color='blue', fontweight='bold')
        
        ax.set_xlim(-self.L*0.1, self.L*1.1)
        ax.set_ylim(-0.2, 0.5)
        ax.set_xlabel('Position (m)')
        ax.set_title('Beam Loading Diagram')
        ax.grid(True, alpha=0.3)
        ax.set_aspect('equal', adjustable='box')
    
    def get_results(self):
        """Return calculation results as dictionary"""
        reactions = self.calculate_reactions()
        
        return {
            'reactions': reactions,
            'max_deflection': self.max_deflection,
            'max_moment': self.max_moment,
            'max_shear': self.max_shear,
            'beam_properties': {
                'length': self.L,
                'young_modulus': self.E,
                'moment_inertia': self.I,
                'flexural_rigidity': self.EI,
                'support_type': self.support_type
            },
            'loads': {
                'point_loads': self.point_loads,
                'distributed_loads': self.distributed_loads
            }
        }
