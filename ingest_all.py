"""
Imprint Master Ingestion Script
Runs all ingestion pipelines and sends email summary.
"""

import subprocess
import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from imprint_utils import send_ingestion_summary_email


def run_pipeline(name, script):
    """Run an ingestion pipeline."""
    print()
    print("=" * 60)
    print(f"Running {name} Ingestion")
    print("=" * 60)

    script_path = os.path.join(os.path.dirname(__file__), script)
    result = subprocess.run([sys.executable, script_path])

    return result.returncode == 0


def main():
    print("=" * 60)
    print("IMPRINT MASTER INGESTION")
    print("=" * 60)
    print()
    print("Pipelines to run:")
    print("  1. Email (Gmail Imprint label)")
    print("  2. Bookmark (Safari Imprint folder)")
    print("  3. PDF (Google Drive Imprint folder)")
    print("  4. Vision (Google Drive Imprint/Vision folder)")
    print()

    results = {}

    # Run each pipeline
    results['Email'] = run_pipeline('Email', 'ingest_email.py')
    results['Bookmark'] = run_pipeline('Bookmark', 'ingest_bookmark.py')
    results['PDF'] = run_pipeline('PDF', 'ingest_pdf.py')
    results['Vision'] = run_pipeline('Vision', 'ingest_vision.py')

    # Summary
    print()
    print("=" * 60)
    print("INGESTION SUMMARY")
    print("=" * 60)
    for name, success in results.items():
        status = "✓" if success else "✗"
        print(f"  {status} {name}")

    # Send email notification
    print()
    print("Sending summary email...")
    send_ingestion_summary_email()

    print()
    print("Done!")


if __name__ == '__main__':
    main()
