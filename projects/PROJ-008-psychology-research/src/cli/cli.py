#!/usr/bin/env python3
"""
CLI interface for researchers working on the Mindfulness and Social Skills in Children with ASD project.

Provides commands for data collection, analysis, and documentation management.
"""

import argparse
import sys
from pathlib import Path

# Import project services
from src.services.data_collector import DataCollector
from src.services.analysis import AnalysisService
from src.lib.validators import validate_data

VERSION = "1.0.0"
PROJECT_ROOT = Path(__file__).parent.parent.parent


def cmd_validate(args):
    """Validate data files against schema contracts."""
    try:
        data_path = Path(args.file)
        schema_type = args.schema_type
        
        if not data_path.exists():
            print(f"Error: File not found: {data_path}")
            return 1
        
        result = validate_data(data_path, schema_type)
        
        if result["valid"]:
            print(f"✓ Validation passed for {data_path.name}")
            print(f"  Records validated: {result.get('record_count', 0)}")
            return 0
        else:
            print(f"✗ Validation failed for {data_path.name}")
            for error in result.get("errors", []):
                print(f"  - {error}")
            return 1
            
    except Exception as e:
        print(f"Error during validation: {e}")
        return 1


def cmd_import(args):
    """Import raw data into the processed data store."""
    try:
        collector = DataCollector(
            raw_dir=PROJECT_ROOT / "data" / "raw",
            processed_dir=PROJECT_ROOT / "data" / "processed"
        )
        
        result = collector.import_data(args.file, args.format)
        
        if result["success"]:
            print(f"✓ Imported {result['records_imported']} records")
            print(f"  Output: {result['output_path']}")
            return 0
        else:
            print(f"✗ Import failed: {result.get('error', 'Unknown error')}")
            return 1
            
    except Exception as e:
        print(f"Error during import: {e}")
        return 1


def cmd_analyze(args):
    """Run statistical analysis on processed data."""
    try:
        analysis_service = AnalysisService(
            processed_dir=PROJECT_ROOT / "data" / "processed"
        )
        
        analysis_type = args.analysis_type
        output_path = Path(args.output) if args.output else None
        
        result = analysis_service.run_analysis(
            analysis_type=analysis_type,
            timepoints=args.timepoints.split(",") if args.timepoints else None,
            output_path=output_path
        )
        
        if result["success"]:
            print(f"✓ Analysis complete: {analysis_type}")
            print(f"  Results: {result['summary']}")
            if result.get("output_path"):
                print(f"  Output: {result['output_path']}")
            return 0
        else:
            print(f"✗ Analysis failed: {result.get('error', 'Unknown error')}")
            return 1
            
    except Exception as e:
        print(f"Error during analysis: {e}")
        return 1


def cmd_generate_docs(args):
    """Generate IRB-ready documentation."""
    try:
        from src.services.docs import DocumentationService
        
        doc_service = DocumentationService(
            docs_dir=PROJECT_ROOT / "docs"
        )
        
        doc_type = args.doc_type
        output_path = Path(args.output) if args.output else None
        
        result = doc_service.generate_document(
            doc_type=doc_type,
            output_path=output_path
        )
        
        if result["success"]:
            print(f"✓ Generated {doc_type} documentation")
            print(f"  Output: {result['output_path']}")
            return 0
        else:
            print(f"✗ Documentation generation failed: {result.get('error', 'Unknown error')}")
            return 1
            
    except Exception as e:
        print(f"Error during documentation generation: {e}")
        return 1


def cmd_summary(args):
    """Print project summary and status."""
    try:
        print(f"Project: Mindfulness and Social Skills in Children with ASD")
        print(f"Version: {VERSION}")
        print(f"Root: {PROJECT_ROOT}")
        print()
        
        # Check data directories
        raw_dir = PROJECT_ROOT / "data" / "raw"
        processed_dir = PROJECT_ROOT / "data" / "processed"
        
        print("Data Status:")
        if raw_dir.exists():
            raw_count = len(list(raw_dir.glob("*.json"))) + len(list(raw_dir.glob("*.csv")))
            print(f"  Raw records: {raw_count}")
        else:
            print("  Raw data: Not initialized")
        
        if processed_dir.exists():
            processed_count = len(list(processed_dir.glob("*.json"))) + len(list(processed_dir.glob("*.csv")))
            print(f"  Processed records: {processed_count}")
        else:
            print("  Processed data: Not initialized")
        
        print()
        print("Contracts:")
        contracts_dir = PROJECT_ROOT / "contracts"
        if contracts_dir.exists():
            contract_count = len(list(contracts_dir.glob("*.yaml")))
            print(f"  Active contracts: {contract_count}")
        else:
            print("  Contracts: Not initialized")
        
        return 0
        
    except Exception as e:
        print(f"Error generating summary: {e}")
        return 1


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="mindfulness-asd-research",
        description="CLI interface for Mindfulness and Social Skills in Children with ASD research project"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {VERSION}"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Validate command
    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate data files against schema contracts"
    )
    validate_parser.add_argument("file", help="Path to data file to validate")
    validate_parser.add_argument(
        "--schema-type",
        choices=["participant", "assessment", "intervention"],
        required=True,
        help="Type of schema to validate against"
    )
    validate_parser.set_defaults(func=cmd_validate)
    
    # Import command
    import_parser = subparsers.add_parser(
        "import",
        help="Import raw data into processed data store"
    )
    import_parser.add_argument("file", help="Path to raw data file")
    import_parser.add_argument(
        "--format",
        choices=["json", "csv"],
        default="json",
        help="Format of input file (default: json)"
    )
    import_parser.set_defaults(func=cmd_import)
    
    # Analyze command
    analyze_parser = subparsers.add_parser(
        "analyze",
        help="Run statistical analysis on processed data"
    )
    analyze_parser.add_argument(
        "--analysis-type",
        choices=["t-test", "anova", "repeated-measures", "full"],
        required=True,
        help="Type of statistical analysis to run"
    )
    analyze_parser.add_argument(
        "--timepoints",
        help="Comma-separated list of timepoints (e.g., pre,post,followup)"
    )
    analyze_parser.add_argument(
        "--output",
        help="Path to output results file"
    )
    analyze_parser.set_defaults(func=cmd_analyze)
    
    # Generate docs command
    docs_parser = subparsers.add_parser(
        "docs",
        help="Generate IRB-ready documentation"
    )
    docs_parser.add_argument(
        "--doc-type",
        choices=["protocol", "consent-parent", "consent-child", "analysis-plan"],
        required=True,
        help="Type of documentation to generate"
    )
    docs_parser.add_argument(
        "--output",
        help="Path to output documentation file"
    )
    docs_parser.set_defaults(func=cmd_generate_docs)
    
    # Summary command
    summary_parser = subparsers.add_parser(
        "summary",
        help="Print project summary and status"
    )
    summary_parser.set_defaults(func=cmd_summary)
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        return 0
    
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())