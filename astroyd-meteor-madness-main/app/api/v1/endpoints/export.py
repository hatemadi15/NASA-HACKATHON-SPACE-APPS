"""
Export endpoints for simulation data
"""

from fastapi import APIRouter, HTTPException, Depends, Response
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Optional
import os
import logging
from datetime import datetime

from app.core.database import get_db
from app.core.models import Simulation, SimulationExport, User
from app.core.auth import get_current_user
from app.core.export import simulation_exporter

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/simulation/{simulation_id}/export/pdf")
async def export_simulation_pdf(
    simulation_id: str,
    include_trajectory: bool = True,
    include_zones: bool = True,
    include_mitigation: bool = True,
    custom_title: Optional[str] = None,
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export simulation to PDF report"""
    try:
        # Get simulation
        simulation = db.query(Simulation).filter(
            Simulation.simulation_id == simulation_id
        ).first()
        
        if not simulation:
            raise HTTPException(status_code=404, detail="Simulation not found")
        
        # Check permissions (user must own simulation or be admin)
        if current_user and not current_user.is_admin:
            if simulation.user_id != current_user.id:
                raise HTTPException(status_code=403, detail="Access denied")
        
        # Prepare simulation data
        simulation_data = {
            "simulation_id": simulation.simulation_id,
            "asteroid": simulation.asteroid_data,
            "impact_location": simulation.impact_location,
            "impact_result": simulation.impact_result,
            "damage_assessment": simulation.damage_assessment,
            "trajectory_data": simulation.trajectory_data if include_trajectory else None,
            "impact_zones": simulation.impact_zones if include_zones else None,
            "mitigation_result": simulation.mitigation_result if include_mitigation else None,
            "warnings": simulation.warnings,
            "simulation_metadata": simulation.simulation_metadata
        }
        
        # Generate PDF
        filename = f"simulation_{simulation_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        filepath = simulation_exporter.export_to_pdf(simulation_data, filename)
        
        # Record export
        export_record = SimulationExport(
            simulation_id=simulation.id,
            user_id=current_user.id if current_user else None,
            export_type="pdf",
            file_path=filepath,
            file_size=os.path.getsize(filepath),
            export_format="A4",
            include_trajectory=include_trajectory,
            include_zones=include_zones,
            include_mitigation=include_mitigation,
            custom_title=custom_title,
            expires_at=datetime.utcnow() + timedelta(days=30)  # 30 day retention
        )
        
        db.add(export_record)
        db.commit()
        
        # Return file
        return FileResponse(
            path=filepath,
            filename=filename,
            media_type="application/pdf"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF export failed: {e}")
        raise HTTPException(status_code=500, detail="Export failed")

@router.post("/simulation/{simulation_id}/export/json")
async def export_simulation_json(
    simulation_id: str,
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export simulation to JSON file"""
    try:
        # Get simulation
        simulation = db.query(Simulation).filter(
            Simulation.simulation_id == simulation_id
        ).first()
        
        if not simulation:
            raise HTTPException(status_code=404, detail="Simulation not found")
        
        # Check permissions
        if current_user and not current_user.is_admin:
            if simulation.user_id != current_user.id:
                raise HTTPException(status_code=403, detail="Access denied")
        
        # Prepare simulation data
        simulation_data = {
            "simulation_id": simulation.simulation_id,
            "asteroid": simulation.asteroid_data,
            "impact_location": simulation.impact_location,
            "simulation_request": simulation.simulation_request,
            "impact_result": simulation.impact_result,
            "damage_assessment": simulation.damage_assessment,
            "trajectory_data": simulation.trajectory_data,
            "impact_zones": simulation.impact_zones,
            "mitigation_result": simulation.mitigation_result,
            "warnings": simulation.warnings,
            "simulation_metadata": simulation.simulation_metadata,
            "created_at": simulation.created_at.isoformat(),
            "updated_at": simulation.updated_at.isoformat() if simulation.updated_at else None
        }
        
        # Generate JSON file
        filename = f"simulation_{simulation_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = simulation_exporter.export_to_json(simulation_data, filename)
        
        # Record export
        export_record = SimulationExport(
            simulation_id=simulation.id,
            user_id=current_user.id if current_user else None,
            export_type="json",
            file_path=filepath,
            file_size=os.path.getsize(filepath),
            export_format="JSON"
        )
        
        db.add(export_record)
        db.commit()
        
        # Return file
        return FileResponse(
            path=filepath,
            filename=filename,
            media_type="application/json"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"JSON export failed: {e}")
        raise HTTPException(status_code=500, detail="Export failed")

@router.post("/simulation/{simulation_id}/export/csv")
async def export_simulation_csv(
    simulation_id: str,
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export simulation summary to CSV"""
    try:
        # Get simulation
        simulation = db.query(Simulation).filter(
            Simulation.simulation_id == simulation_id
        ).first()
        
        if not simulation:
            raise HTTPException(status_code=404, detail="Simulation not found")
        
        # Check permissions
        if current_user and not current_user.is_admin:
            if simulation.user_id != current_user.id:
                raise HTTPException(status_code=403, detail="Access denied")
        
        # Prepare simulation data
        simulation_data = {
            "simulation_id": simulation.simulation_id,
            "asteroid": simulation.asteroid_data,
            "impact_location": simulation.impact_location,
            "impact_result": simulation.impact_result,
            "damage_assessment": simulation.damage_assessment
        }
        
        # Generate CSV file
        filename = f"simulation_{simulation_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        filepath = simulation_exporter.export_to_csv(simulation_data, filename)
        
        # Record export
        export_record = SimulationExport(
            simulation_id=simulation.id,
            user_id=current_user.id if current_user else None,
            export_type="csv",
            file_path=filepath,
            file_size=os.path.getsize(filepath),
            export_format="CSV"
        )
        
        db.add(export_record)
        db.commit()
        
        # Return file
        return FileResponse(
            path=filepath,
            filename=filename,
            media_type="text/csv"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"CSV export failed: {e}")
        raise HTTPException(status_code=500, detail="Export failed")

@router.post("/simulation/{simulation_id}/export/image")
async def export_simulation_image(
    simulation_id: str,
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export simulation visualization image"""
    try:
        # Get simulation
        simulation = db.query(Simulation).filter(
            Simulation.simulation_id == simulation_id
        ).first()
        
        if not simulation:
            raise HTTPException(status_code=404, detail="Simulation not found")
        
        # Check permissions
        if current_user and not current_user.is_admin:
            if simulation.user_id != current_user.id:
                raise HTTPException(status_code=403, detail="Access denied")
        
        # Prepare simulation data
        simulation_data = {
            "simulation_id": simulation.simulation_id,
            "impact_location": simulation.impact_location,
            "impact_result": simulation.impact_result
        }
        
        # Generate image
        filename = f"simulation_{simulation_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        filepath = simulation_exporter.create_impact_visualization(simulation_data, filename)
        
        # Record export
        export_record = SimulationExport(
            simulation_id=simulation.id,
            user_id=current_user.id if current_user else None,
            export_type="image",
            file_path=filepath,
            file_size=os.path.getsize(filepath),
            export_format="PNG"
        )
        
        db.add(export_record)
        db.commit()
        
        # Return file
        return FileResponse(
            path=filepath,
            filename=filename,
            media_type="image/png"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Image export failed: {e}")
        raise HTTPException(status_code=500, detail="Export failed")

@router.get("/exports")
async def list_user_exports(
    skip: int = 0,
    limit: int = 50,
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List user's export history"""
    try:
        if not current_user:
            raise HTTPException(status_code=401, detail="Authentication required")
        
        exports = db.query(SimulationExport).filter(
            SimulationExport.user_id == current_user.id
        ).offset(skip).limit(limit).all()
        
        return {
            "exports": [
                {
                    "id": export.id,
                    "simulation_id": export.simulation.simulation_id,
                    "export_type": export.export_type,
                    "export_format": export.export_format,
                    "file_size": export.file_size,
                    "created_at": export.created_at.isoformat(),
                    "expires_at": export.expires_at.isoformat() if export.expires_at else None
                }
                for export in exports
            ],
            "total": len(exports)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list exports: {e}")
        raise HTTPException(status_code=500, detail="Failed to list exports")

@router.delete("/exports/{export_id}")
async def delete_export(
    export_id: int,
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete an export file"""
    try:
        if not current_user:
            raise HTTPException(status_code=401, detail="Authentication required")
        
        # Get export record
        export = db.query(SimulationExport).filter(
            SimulationExport.id == export_id,
            SimulationExport.user_id == current_user.id
        ).first()
        
        if not export:
            raise HTTPException(status_code=404, detail="Export not found")
        
        # Delete file if it exists
        if os.path.exists(export.file_path):
            os.remove(export.file_path)
        
        # Delete database record
        db.delete(export)
        db.commit()
        
        return {"message": "Export deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete export: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete export")
