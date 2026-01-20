from src.reporting.pdf_generator import SafetyReportGenerator
import logging
import sys
import os

# Setup logging to stdout
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

def debug_report(upload_id):
    print(f"Attempting to generate report for {upload_id}...")
    try:
        gen = SafetyReportGenerator()
        out = f"data/reports/{upload_id}_safety_report.pdf"
        success = gen.generate(upload_id, out)
        if success:
            print("SUCCESS: Report generated.")
        else:
            print("FAILURE: Generator returned False.")
    except Exception as e:
        print(f"CRITICAL EXCEPTION: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Use the known successful video upload ID
    upload_id = "c2b05d03-bb5b-4604-9426-9d70ebd0a923"
    debug_report(upload_id)
    
    # Check fallback existence
    if os.path.exists("safety_report.pdf"):
        print("\nFALLBACK WARNING: 'safety_report.pdf' exists in root. This explains identical output.")
    else:
        print("\nFallback 'safety_report.pdf' NOT found.")
