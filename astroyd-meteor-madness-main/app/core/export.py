"""
File export utilities for simulations
"""

import os
import json
import csv
from datetime import datetime
from typing import Dict, Any, List, Optional
from io import BytesIO
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.backends.backend_agg import FigureCanvasAgg
import numpy as np
from PIL import Image as PILImage
import logging

logger = logging.getLogger(__name__)

class SimulationExporter:
    """Export simulation results to various formats"""
    
    def __init__(self, output_dir: str = "exports"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def export_to_pdf(self, simulation_data: Dict[str, Any], filename: str = None) -> str:
        """Export simulation to PDF report"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"simulation_report_{timestamp}.pdf"
        
        filepath = os.path.join(self.output_dir, filename)
        
        # Create PDF document
        doc = SimpleDocTemplate(filepath, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        )
        story.append(Paragraph("NASA Meteor Impact Simulation Report", title_style))
        story.append(Spacer(1, 20))
        
        # Simulation metadata
        metadata = simulation_data.get('simulation_metadata', {})
        story.append(Paragraph(f"<b>Simulation ID:</b> {simulation_data.get('simulation_id', 'N/A')}", styles['Normal']))
        story.append(Paragraph(f"<b>Generated:</b> {metadata.get('timestamp', 'N/A')}", styles['Normal']))
        story.append(Paragraph(f"<b>Version:</b> {metadata.get('version', 'N/A')}", styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Asteroid data
        asteroid = simulation_data.get('asteroid', {})
        story.append(Paragraph("<b>Asteroid Parameters</b>", styles['Heading2']))
        asteroid_data = [
            ['Parameter', 'Value', 'Unit'],
            ['Mass', f"{asteroid.get('mass', 0):,.0f}", 'kg'],
            ['Diameter', f"{asteroid.get('diameter', 0):,.1f}", 'm'],
            ['Velocity', f"{asteroid.get('velocity', 0):,.0f}", 'm/s'],
            ['Impact Angle', f"{asteroid.get('impact_angle', 0):.1f}", 'degrees'],
            ['Composition', asteroid.get('composition', 'Unknown'), ''],
            ['Kinetic Energy', f"{asteroid.get('kinetic_energy_megatons', 0):.2f}", 'megatons TNT']
        ]
        
        asteroid_table = Table(asteroid_data)
        asteroid_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(asteroid_table)
        story.append(Spacer(1, 20))
        
        # Impact location
        location = simulation_data.get('impact_location', {})
        story.append(Paragraph("<b>Impact Location</b>", styles['Heading2']))
        location_data = [
            ['Parameter', 'Value'],
            ['Latitude', f"{location.get('latitude', 0):.4f}°"],
            ['Longitude', f"{location.get('longitude', 0):.4f}°"],
            ['Elevation', f"{location.get('elevation', 0):.1f} m"],
            ['Terrain Type', location.get('terrain_type', 'Unknown')],
            ['Population Density', f"{location.get('population_density', 0):.1f} people/km²"]
        ]
        
        location_table = Table(location_data)
        location_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(location_table)
        story.append(Spacer(1, 20))
        
        # Impact results
        impact_result = simulation_data.get('impact_result', {})
        story.append(Paragraph("<b>Impact Results</b>", styles['Heading2']))
        impact_data = [
            ['Parameter', 'Value', 'Unit'],
            ['Crater Diameter', f"{impact_result.get('crater_diameter', 0):,.1f}", 'm'],
            ['Crater Depth', f"{impact_result.get('crater_depth', 0):,.1f}", 'm'],
            ['Blast Radius', f"{impact_result.get('blast_radius', 0):,.1f}", 'm'],
            ['Thermal Radius', f"{impact_result.get('thermal_radius', 0):,.1f}", 'm'],
            ['Seismic Magnitude', f"{impact_result.get('seismic_magnitude', 0):.1f}", 'Richter'],
            ['Evacuation Radius', f"{impact_result.get('evacuation_radius', 0):,.1f}", 'm'],
            ['Affected Area', f"{impact_result.get('affected_area', 0):,.1f}", 'km²']
        ]
        
        if impact_result.get('tsunami_height'):
            impact_data.append(['Tsunami Height', f"{impact_result.get('tsunami_height', 0):.1f}", 'm'])
        
        impact_table = Table(impact_data)
        impact_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(impact_table)
        story.append(Spacer(1, 20))
        
        # Damage assessment
        damage = simulation_data.get('damage_assessment', {})
        story.append(Paragraph("<b>Damage Assessment</b>", styles['Heading2']))
        damage_data = [
            ['Parameter', 'Value'],
            ['Estimated Casualties', f"{damage.get('estimated_casualties', 0):,}"],
            ['Injured Count', f"{damage.get('injured_count', 0):,}"],
            ['Displaced Count', f"{damage.get('displaced_count', 0):,}"],
            ['Buildings Destroyed', f"{damage.get('buildings_destroyed', 0):,}"],
            ['Total Economic Cost', f"${damage.get('total_economic_cost', 0):,.0f}"],
            ['Recovery Time', f"{damage.get('recovery_time_years', 0):.1f} years"]
        ]
        
        damage_table = Table(damage_data)
        damage_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(damage_table)
        
        # Warnings
        warnings = simulation_data.get('warnings', [])
        if warnings:
            story.append(Spacer(1, 20))
            story.append(Paragraph("<b>System Warnings</b>", styles['Heading2']))
            for warning in warnings:
                story.append(Paragraph(f"• {warning.get('level', '').upper()}: {warning.get('message', '')}", styles['Normal']))
        
        # Build PDF
        doc.build(story)
        
        return filepath
    
    def export_to_json(self, simulation_data: Dict[str, Any], filename: str = None) -> str:
        """Export simulation to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"simulation_data_{timestamp}.json"
        
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w') as f:
            json.dump(simulation_data, f, indent=2, default=str)
        
        return filepath
    
    def export_to_csv(self, simulation_data: Dict[str, Any], filename: str = None) -> str:
        """Export simulation summary to CSV"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"simulation_summary_{timestamp}.csv"
        
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Headers
            writer.writerow(['Parameter', 'Value', 'Unit'])
            
            # Asteroid data
            asteroid = simulation_data.get('asteroid', {})
            writer.writerow(['Asteroid Mass', asteroid.get('mass', 0), 'kg'])
            writer.writerow(['Asteroid Diameter', asteroid.get('diameter', 0), 'm'])
            writer.writerow(['Asteroid Velocity', asteroid.get('velocity', 0), 'm/s'])
            writer.writerow(['Kinetic Energy', asteroid.get('kinetic_energy_megatons', 0), 'megatons TNT'])
            
            # Impact results
            impact_result = simulation_data.get('impact_result', {})
            writer.writerow(['Crater Diameter', impact_result.get('crater_diameter', 0), 'm'])
            writer.writerow(['Blast Radius', impact_result.get('blast_radius', 0), 'm'])
            writer.writerow(['Affected Area', impact_result.get('affected_area', 0), 'km²'])
            
            # Damage assessment
            damage = simulation_data.get('damage_assessment', {})
            writer.writerow(['Estimated Casualties', damage.get('estimated_casualties', 0), 'people'])
            writer.writerow(['Total Economic Cost', damage.get('total_economic_cost', 0), 'USD'])
        
        return filepath
    
    def create_impact_visualization(self, simulation_data: Dict[str, Any], filename: str = None) -> str:
        """Create impact zone visualization image"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"impact_visualization_{timestamp}.png"
        
        filepath = os.path.join(self.output_dir, filename)
        
        # Create figure
        fig, ax = plt.subplots(1, 1, figsize=(10, 10))
        
        # Get impact data
        impact_result = simulation_data.get('impact_result', {})
        location = simulation_data.get('impact_location', {})
        
        # Impact point
        impact_lat = location.get('latitude', 0)
        impact_lon = location.get('longitude', 0)
        
        # Zone radii (convert to degrees for visualization)
        crater_radius = impact_result.get('crater_diameter', 0) / 2 / 111000  # Rough conversion
        blast_radius = impact_result.get('blast_radius', 0) / 111000
        thermal_radius = impact_result.get('thermal_radius', 0) / 111000
        evacuation_radius = impact_result.get('evacuation_radius', 0) / 111000
        
        # Draw zones
        zones = [
            (evacuation_radius, 'red', 'Evacuation Zone', 0.1),
            (thermal_radius, 'orange', 'Thermal Zone', 0.2),
            (blast_radius, 'yellow', 'Blast Zone', 0.3),
            (crater_radius, 'black', 'Crater', 0.5)
        ]
        
        for radius, color, label, alpha in zones:
            if radius > 0:
                circle = patches.Circle((impact_lon, impact_lat), radius, 
                                       color=color, alpha=alpha, label=label)
                ax.add_patch(circle)
        
        # Set plot properties
        ax.set_xlim(impact_lon - evacuation_radius * 1.5, impact_lon + evacuation_radius * 1.5)
        ax.set_ylim(impact_lat - evacuation_radius * 1.5, impact_lat + evacuation_radius * 1.5)
        ax.set_xlabel('Longitude')
        ax.set_ylabel('Latitude')
        ax.set_title('Impact Zone Visualization')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # Mark impact point
        ax.plot(impact_lon, impact_lat, 'ro', markersize=10, label='Impact Point')
        
        # Save figure
        plt.tight_layout()
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()
        
        return filepath

# Global exporter instance
simulation_exporter = SimulationExporter()
