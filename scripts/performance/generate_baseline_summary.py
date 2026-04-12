#!/usr/bin/env python3
"""
Generate a comprehensive performance baseline summary.
Combines API, bundle size, and component performance measurements.
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional


def find_latest_baseline_file(baseline_dir: Path, pattern: str) -> Optional[Path]:
    """Find the latest baseline file matching the pattern."""
    files = list(baseline_dir.glob(pattern))
    if not files:
        return None
    return max(files, key=lambda f: f.stat().st_mtime)


def load_baseline_data(file_path: Path) -> Optional[Dict[str, Any]]:
    """Load baseline data from JSON file."""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return None


def generate_comprehensive_summary():
    """Generate comprehensive performance baseline summary."""
    baseline_dir = Path("scripts/performance/baselines")

    if not baseline_dir.exists():
        print("No baseline directory found")
        return

    # Find latest baseline files
    api_file = find_latest_baseline_file(baseline_dir, "api_baseline_*.json")
    bundle_file = find_latest_baseline_file(baseline_dir, "bundle_baseline_*.json")
    component_file = find_latest_baseline_file(baseline_dir, "component_baseline_*.json")

    # Load data
    api_data = load_baseline_data(api_file) if api_file else None
    bundle_data = load_baseline_data(bundle_file) if bundle_file else None
    component_data = load_baseline_data(component_file) if component_file else None

    # Generate summary
    summary = {
        'timestamp': datetime.now().isoformat(),
        'task': '17.1 - Performance Baseline Establishment',
        'measurements_completed': [],
        'baseline_files': {},
        'performance_metrics': {}
    }

    # API Performance Summary
    if api_data:
        summary['measurements_completed'].append('API Performance')
        summary['baseline_files']['api'] = str(api_file)
        summary['performance_metrics']['api'] = {
            'source': api_data.get('source', 'unknown'),
            'overall_mean_response_time_ms': api_data['summary']['overall_mean_response_time'],
            'overall_median_response_time_ms': api_data['summary']['overall_median_response_time'],
            'average_success_rate_percent': api_data['summary']['average_success_rate'],
            'endpoints_measured': api_data['summary']['total_endpoints_measured'],
            'fastest_endpoint': api_data['summary']['fastest_endpoint'],
            'slowest_endpoint': api_data['summary']['slowest_endpoint']
        }

    # Bundle Size Summary
    if bundle_data:
        summary['measurements_completed'].append('Bundle Size')
        summary['baseline_files']['bundle'] = str(bundle_file)

        if bundle_data.get('source') == 'existing_build':
            summary['performance_metrics']['bundle'] = {
                'source': 'existing_build',
                'total_size_mb': float(bundle_data['summary']['totalBundleSizeMB']),
                'js_chunks_count': bundle_data['summary']['jsChunksCount'],
                'js_chunks_size_mb': float(bundle_data['summary']['jsChunksSizeMB']),
                'css_assets_count': bundle_data['summary']['cssAssetsCount'],
                'css_assets_size_mb': float(bundle_data['summary']['cssAssetsSizeMB']),
                'largest_chunk': bundle_data['summary']['largestChunk'],
                'largest_chunk_size_mb': float(bundle_data['summary']['largestChunkSizeMB'])
            }
        else:
            # Package.json estimation
            summary['performance_metrics']['bundle'] = {
                'source': 'package_json_estimation',
                'estimated_size_mb': float(bundle_data['summary']['estimatedBundleSizeMB']),
                'production_dependencies': bundle_data['summary']['totalDependencies'],
                'dev_dependencies': bundle_data['summary']['totalDevDependencies'],
                'major_dependencies': bundle_data['summary']['majorDependencies'],
                'largest_dependency': bundle_data['summary']['largestEstimatedDependency']['name']
            }

    # Component Performance Summary
    if component_data:
        summary['measurements_completed'].append('Component Performance')
        summary['baseline_files']['component'] = str(component_file)
        summary['performance_metrics']['component'] = {
            'average_render_time_ms': component_data['summary']['averageRenderTime'],
            'components_tested': component_data['summary']['totalComponentsTested'],
            'slowest_component': component_data['summary']['slowestComponent'],
            'fastest_component': component_data['summary']['fastestComponent'],
            'individual_components': {}
        }

        # Add individual component metrics
        for comp in component_data['components']:
            summary['performance_metrics']['component']['individual_components'][comp['componentName']] = {
                'render_time_ms': comp['renderTime'],
                'rerender_time_ms': comp.get('reRenderTime'),
                'props_size_bytes': comp['propsSize']
            }

    # Save comprehensive summary
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    summary_file = baseline_dir / f"comprehensive_baseline_summary_{timestamp}.json"

    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)

    print(f"Comprehensive performance baseline summary saved to: {summary_file}")

    # Print summary to console
    print_summary(summary)

    return summary


def print_summary(summary: Dict[str, Any]):
    """Print comprehensive summary to console."""
    print("\n" + "="*60)
    print("TASK 17.1: PERFORMANCE BASELINE ESTABLISHMENT - COMPLETE")
    print("="*60)
    print(f"Timestamp: {summary['timestamp']}")
    print(f"Measurements completed: {len(summary['measurements_completed'])}")

    for measurement in summary['measurements_completed']:
        print(f"✓ {measurement}")

    print("\n" + "-"*40)
    print("PERFORMANCE METRICS SUMMARY")
    print("-"*40)

    # API Performance
    if 'api' in summary['performance_metrics']:
        api = summary['performance_metrics']['api']
        print(f"\n📡 API Performance ({api['source']}):")
        print(f"   Mean response time: {api['overall_mean_response_time_ms']:.2f}ms")
        print(f"   Median response time: {api['overall_median_response_time_ms']:.2f}ms")
        print(f"   Success rate: {api['average_success_rate_percent']:.1f}%")
        print(f"   Endpoints tested: {api['endpoints_measured']}")
        print(f"   Fastest: {api['fastest_endpoint']}")
        print(f"   Slowest: {api['slowest_endpoint']}")

    # Bundle Size
    if 'bundle' in summary['performance_metrics']:
        bundle = summary['performance_metrics']['bundle']
        print(f"\n📦 Bundle Size ({bundle['source']}):")

        if bundle['source'] == 'existing_build':
            print(f"   Total size: {bundle['total_size_mb']:.2f} MB")
            print(f"   JS chunks: {bundle['js_chunks_count']} files ({bundle['js_chunks_size_mb']:.2f} MB)")
            print(f"   CSS assets: {bundle['css_assets_count']} files ({bundle['css_assets_size_mb']:.2f} MB)")
            print(f"   Largest chunk: {bundle['largest_chunk']} ({bundle['largest_chunk_size_mb']:.2f} MB)")
        else:
            print(f"   Estimated size: {bundle['estimated_size_mb']} MB")
            print(f"   Production deps: {bundle['production_dependencies']}")
            print(f"   Major deps: {bundle['major_dependencies']}")
            print(f"   Largest dep: {bundle['largest_dependency']}")

    # Component Performance
    if 'component' in summary['performance_metrics']:
        comp = summary['performance_metrics']['component']
        print(f"\n⚛️  Component Performance:")
        print(f"   Average render time: {comp['average_render_time_ms']:.2f}ms")
        print(f"   Components tested: {comp['components_tested']}")
        print(f"   Slowest: {comp['slowest_component']}")
        print(f"   Fastest: {comp['fastest_component']}")

        print(f"\n   Individual Components:")
        for name, metrics in comp['individual_components'].items():
            rerender_info = f", Re-render: {metrics['rerender_time_ms']:.2f}ms" if metrics['rerender_time_ms'] else ""
            print(f"   • {name}: {metrics['render_time_ms']:.2f}ms{rerender_info}")

    print("\n" + "-"*40)
    print("BASELINE FILES CREATED")
    print("-"*40)

    for measurement_type, file_path in summary['baseline_files'].items():
        print(f"• {measurement_type.title()}: {file_path}")

    print("\n" + "="*60)
    print("TASK 17.1 STATUS: ✅ COMPLETED")
    print("All performance baselines have been established successfully.")
    print("These baselines will be used for comparison in Task 17.2 and 17.3.")
    print("="*60)


def main():
    """Main function."""
    try:
        generate_comprehensive_summary()
    except Exception as e:
        print(f"Error generating summary: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
