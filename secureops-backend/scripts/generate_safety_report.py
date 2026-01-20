#!/usr/bin/env python3
import sys
import os
import argparse
# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.reporting.pdf_generator import SafetyReportGenerator

def main():
    parser = argparse.ArgumentParser(description="Generate Safety Report PDF")
    parser.add_argument("--upload_id", required=True, help="Upload ID to report on")
    parser.add_argument("--output", default=None, help="Output path (default: data/reports/<id>_safety_report.pdf)")
    
    args = parser.parse_args()
    
    output_path = args.output
    if not output_path:
        output_path = f"data/reports/{args.upload_id}_safety_report.pdf"
        
    generator = SafetyReportGenerator()
    success = generator.generate(args.upload_id, output_path)
    
    if success:
        print(f"Successfully generated report: {output_path}")
        sys.exit(0)
    else:
        print(f"Failed to generate report for {args.upload_id}")
        sys.exit(1)

if __name__ == "__main__":
    main()
