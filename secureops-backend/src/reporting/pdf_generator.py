from pathlib import Path
import logging
from fpdf import FPDF
from src.db.session import get_db_session
from src.db.models import SiteMetrics, SafetyViolation, ProximityEvent

logger = logging.getLogger(__name__)

class SafetyReportGenerator:
    """Generates PDF safety reports from database metrics."""
    
    def generate(self, upload_id: str, output_path: str):
        try:
            with get_db_session() as session:
                metrics = session.query(SiteMetrics).filter(SiteMetrics.upload_id == upload_id).first()
                violations = session.query(SafetyViolation).filter(SafetyViolation.upload_id == upload_id).all()
                proximities = session.query(ProximityEvent).filter(ProximityEvent.upload_id == upload_id).all()
                
                if not metrics:
                    logger.error(f"No metrics found for {upload_id}")
                    return False

                pdf = FPDF()
                pdf.add_page()
                
                # --- Header ---
                pdf.set_font('Arial', 'B', 16)
                pdf.cell(0, 10, 'SecureOps Safety Compliance Report', 0, 1, 'C')
                pdf.ln(10)
                
                # --- Executive Summary ---
                pdf.set_font('Arial', 'B', 14)
                pdf.cell(0, 10, 'Executive Summary', 0, 1)
                pdf.set_font('Arial', '', 12)
                
                # Calculate Risk Score (Reverse of Accuracy)
                risk_score = max(0.0, 100.0 - metrics.accuracy)
                
                summary_data = [
                    f"Upload ID: {upload_id}",
                    f"Date: {metrics.created_at.strftime('%Y-%m-%d %H:%M:%S')}",
                    f"Pipeline Status: {metrics.pipeline_status}",
                    f"Total Violations: {metrics.ppe_violations + metrics.zone_violations + metrics.proximity_violations}",
                    f"Compliance Rate: {metrics.accuracy:.1f}%",
                    f"Bounded Risk Score: {risk_score:.1f} / 100.0"
                ]
                
                for line in summary_data:
                    pdf.cell(0, 8, line, 0, 1)
                pdf.ln(5)

                # --- Detailed Breakdown ---
                pdf.set_font('Arial', 'B', 14)
                pdf.cell(0, 10, 'Violation Breakdown', 0, 1)
                
                # Table Header
                pdf.set_font('Arial', 'B', 11)
                pdf.cell(40, 10, 'Type', 1)
                pdf.cell(30, 10, 'Severity', 1)
                pdf.cell(120, 10, 'Details', 1)
                pdf.ln()
                
                pdf.set_font('Arial', '', 10)
                
                # Helper to add row with optional image
                def add_violation_entry(v_type, sev, det, img_rel_path=None):
                    # Text Row
                    pdf.cell(40, 8, v_type, 1)
                    pdf.cell(30, 8, sev, 1)
                    pdf.cell(120, 8, str(det)[:60], 1)
                    pdf.ln()
                    
                    # Image Row (if exists)
                    if img_rel_path:
                        # Resolve absolute path. img_rel_path is like 'violations/...'
                        # We stored it relative to 'storage' in FrameAnnotator?
                        # FrameAnnotator: return str(out_path.relative_to(self.base_dir.parent)) -> "violations/..."
                        # base_dir.parent is "storage".
                        # So full path is "storage/" + img_rel_path
                        full_path = Path("storage") / img_rel_path
                        
                        if full_path.exists():
                            try:
                                # Add image (max width 100, height auto)
                                # x=15 to indent slightly
                                x = pdf.get_x()
                                y = pdf.get_y()
                                # Calculate available width, maybe 80mm wide?
                                pdf.image(str(full_path), x=x+20, w=80)
                                # Move cursor down. FPDF image doesn't automatically move cursor? 
                                # It does if not using x/y? "If x and y are not specified, the current position is used."
                                # But we want to indent.
                                # Let's just put it below.
                                pdf.ln(2) # Spacing
                                # pdf.image() updates y? Let's assume w=80 creates ~45mm height (16:9).
                                # We need to move cursor past the image.
                                # FPDF's .image() doesn't return height used.
                                # Standard approach: 
                                # pdf.image(..., h=45) -> explicitly set height or calculate.
                                # Let's assume aspect ratio 16:9. 80mm width -> 45mm height.
                                pdf.ln(45 + 5) 
                            except Exception as e:
                                logger.warning(f"Failed to embed image {full_path}: {e}")

                # PPE
                for v in violations:
                    if v.violation_type != 'zone_intrusion':
                        add_violation_entry('PPE', v.severity, v.description, v.image_path)
                
                # Zone
                for v in violations:
                    if v.violation_type == 'zone_intrusion':
                        add_violation_entry('ZONE', v.severity, v.description, v.image_path)
                
                # Proximity
                for p in proximities:
                     add_violation_entry('PROXIMITY', p.risk_level, f"{p.machine_type} proximity (dist: {p.distance_px:.1f})", p.image_path)
                
                # Save
                Path(output_path).parent.mkdir(parents=True, exist_ok=True)
                pdf.output(output_path)
                logger.info(f"Report generated: {output_path}")
                return True
            
        except Exception as e:
            logger.error(f"Failed to generate report: {e}")
            return False
