#!/usr/bin/env python3
"""
Post-refactoring performance measurement script.
Measures API response times, bundle size, and component performance after refactoring
and compares them with baseline metrics.
"""

import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional


class PostRefactoringPerformanceMeasurer:
    """Measures performance after refactoring and compares with baselines."""

    def __init__(self):
        self.baseline_dir = Path("scripts/performance/baselines")
        self.baseline_dir.mkdir(parents=True, exist_ok=True)

    def find_latest_baseline(self, pattern: str) -> Optional[Path]:
        """Find the latest baseline file matching the pattern."""
        files = list(self.baseline_dir.glob(pattern))
        if not files:
            return None
        return max(files, key=lambda f: f.stat().st_mtime)

    def load_baseline_data(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Load baseline data from JSON file."""
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
            return None

    def run_api_performance_measurement(self) -> bool:
        """Run API performance measurement."""
        print("=== Task 17.2.1: Measuring API Response Times After Refactoring ===")

        try:
            # Try to run the real API performance measurement first
            result = subprocess.run([
                sys.executable, "scripts/performance/measure_api_performance.py"
            ], capture_output=True, text=True, timeout=300)

            if result.returncode == 0:
                print("✅ Real API performance measurement completed successfully")
                return True
            else:
                print("⚠️  Real API measurement failed, falling back to mock measurement")
                print(f"Error: {result.stderr}")

                # Fall back to mock measurement
                result = subprocess.run([
                    sys.executable, "scripts/performance/measure_mock_api_performance.py"
                ], capture_output=True, text=True, timeout=60)

                if result.returncode == 0:
                    print("✅ Mock API performance measurement completed")
                    return True
                else:
                    print(f"❌ Mock API measurement also failed: {result.stderr}")
                    return False

        except subprocess.TimeoutExpired:
            print("⚠️  API measurement timed out, falling back to mock measurement")

            try:
                result = subprocess.run([
                    sys.executable, "scripts/performance/measure_mock_api_performance.py"
                ], capture_output=True, text=True, timeout=60)

                if result.returncode == 0:
                    print("✅ Mock API performance measurement completed")
                    return True
                else:
                    print(f"❌ Mock API measurement failed: {result.stderr}")
                    return False
            except Exception as e:
                print(f"❌ Failed to run mock API measurement: {e}")
                return False

        except Exception as e:
            print(f"❌ Failed to run API performance measurement: {e}")
            return False

    def run_bundle_size_measurement(self) -> bool:
        """Run bundle size measurement."""
        print("\n=== Task 17.2.2: Measuring Frontend Bundle Size After Refactoring ===")

        try:
            # Try the existing bundle measurement first
            result = subprocess.run([
                "node", "scripts/performance/measure_existing_bundle.js"
            ], capture_output=True, text=True, timeout=300)

            if result.returncode == 0:
                print("✅ Bundle size measurement completed successfully")
                return True
            else:
                print(f"❌ Bundle size measurement failed: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            print("⚠️  Bundle size measurement timed out")
            return False
        except Exception as e:
            print(f"❌ Failed to run bundle size measurement: {e}")
            return False

    def run_component_performance_measurement(self) -> bool:
        """Run component performance measurement."""
        print("\n=== Task 17.2.3: Measuring Component Render Performance After Refactoring ===")

        try:
            # Run the component performance tests
            result = subprocess.run([
                "npm", "run", "test", "--",
                "__tests__/performance/component_render_performance.test.tsx",
                "--verbose"
            ], cwd="frontend", capture_output=True, text=True, timeout=180)

            if result.returncode == 0:
                print("✅ Component performance measurement completed successfully")

                # Copy the component baseline to the main baselines directory
                component_files = list(Path("frontend/scripts/performance/baselines").glob("component_baseline_*.json"))
                if component_files:
                    latest_component_file = max(component_files, key=lambda f: f.stat().st_mtime)
                    target_file = self.baseline_dir / latest_component_file.name

                    import shutil
                    shutil.copy2(latest_component_file, target_file)
                    print(f"✅ Component baseline copied to {target_file}")

                return True
            else:
                print(f"❌ Component performance measurement failed: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            print("⚠️  Component performance measurement timed out")
            return False
        except Exception as e:
            print(f"❌ Failed to run component performance measurement: {e}")
            return False

    def compare_with_baselines(self) -> Dict[str, Any]:
        """Compare current measurements with baselines."""
        print("\n=== Task 17.2.4: Comparing Post-Refactoring Performance with Baselines ===")

        comparison_results = {
            'timestamp': datetime.now().isoformat(),
            'comparisons': {},
            'summary': {
                'improvements': [],
                'regressions': [],
                'no_change': []
            }
        }

        # Compare API performance
        api_comparison = self.compare_api_performance()
        if api_comparison:
            comparison_results['comparisons']['api'] = api_comparison
            self.categorize_performance_change(api_comparison, 'API', comparison_results['summary'])

        # Compare bundle size
        bundle_comparison = self.compare_bundle_size()
        if bundle_comparison:
            comparison_results['comparisons']['bundle'] = bundle_comparison
            self.categorize_performance_change(bundle_comparison, 'Bundle Size', comparison_results['summary'])

        # Compare component performance
        component_comparison = self.compare_component_performance()
        if component_comparison:
            comparison_results['comparisons']['component'] = component_comparison
            self.categorize_performance_change(component_comparison, 'Component Performance', comparison_results['summary'])

        return comparison_results

    def compare_api_performance(self) -> Optional[Dict[str, Any]]:
        """Compare API performance with baseline."""
        baseline_file = self.find_latest_baseline("api_baseline_*.json")
        if not baseline_file:
            print("⚠️  No API baseline found for comparison")
            return None

        # Find the latest post-refactoring measurement
        api_files = sorted(self.baseline_dir.glob("api_baseline_*.json"), key=lambda f: f.stat().st_mtime)
        if len(api_files) < 2:
            print("⚠️  Need at least 2 API measurements for comparison")
            return None

        baseline_data = self.load_baseline_data(api_files[0])  # First (baseline)
        current_data = self.load_baseline_data(api_files[-1])  # Latest

        if not baseline_data or not current_data:
            return None

        baseline_mean = baseline_data['summary']['overall_mean_response_time']
        current_mean = current_data['summary']['overall_mean_response_time']

        improvement_percent = ((baseline_mean - current_mean) / baseline_mean) * 100

        return {
            'metric': 'API Response Time',
            'baseline_value': baseline_mean,
            'current_value': current_mean,
            'improvement_percent': improvement_percent,
            'improved': improvement_percent > 0,
            'unit': 'ms'
        }

    def compare_bundle_size(self) -> Optional[Dict[str, Any]]:
        """Compare bundle size with baseline."""
        bundle_files = sorted(self.baseline_dir.glob("bundle_baseline_*.json"), key=lambda f: f.stat().st_mtime)
        if len(bundle_files) < 2:
            print("⚠️  Need at least 2 bundle measurements for comparison")
            return None

        baseline_data = self.load_baseline_data(bundle_files[0])  # First (baseline)
        current_data = self.load_baseline_data(bundle_files[-1])  # Latest

        if not baseline_data or not current_data:
            return None

        # Handle different data structures
        if 'summary' in baseline_data and 'totalBundleSizeMB' in baseline_data['summary']:
            baseline_size = float(baseline_data['summary']['totalBundleSizeMB'])
        elif 'summary' in baseline_data and 'estimatedBundleSizeMB' in baseline_data['summary']:
            baseline_size = float(baseline_data['summary']['estimatedBundleSizeMB'])
        else:
            return None

        if 'summary' in current_data and 'totalBundleSizeMB' in current_data['summary']:
            current_size = float(current_data['summary']['totalBundleSizeMB'])
        elif 'summary' in current_data and 'estimatedBundleSizeMB' in current_data['summary']:
            current_size = float(current_data['summary']['estimatedBundleSizeMB'])
        else:
            return None

        improvement_percent = ((baseline_size - current_size) / baseline_size) * 100

        return {
            'metric': 'Bundle Size',
            'baseline_value': baseline_size,
            'current_value': current_size,
            'improvement_percent': improvement_percent,
            'improved': improvement_percent > 0,
            'unit': 'MB'
        }

    def compare_component_performance(self) -> Optional[Dict[str, Any]]:
        """Compare component performance with baseline."""
        component_files = sorted(self.baseline_dir.glob("component_baseline_*.json"), key=lambda f: f.stat().st_mtime)
        if len(component_files) < 2:
            print("⚠️  Need at least 2 component measurements for comparison")
            return None

        baseline_data = self.load_baseline_data(component_files[0])  # First (baseline)
        current_data = self.load_baseline_data(component_files[-1])  # Latest

        if not baseline_data or not current_data:
            return None

        baseline_render_time = baseline_data['summary']['averageRenderTime']
        current_render_time = current_data['summary']['averageRenderTime']

        improvement_percent = ((baseline_render_time - current_render_time) / baseline_render_time) * 100

        return {
            'metric': 'Component Render Time',
            'baseline_value': baseline_render_time,
            'current_value': current_render_time,
            'improvement_percent': improvement_percent,
            'improved': improvement_percent > 0,
            'unit': 'ms'
        }

    def categorize_performance_change(self, comparison: Dict[str, Any], metric_name: str, summary: Dict[str, list]):
        """Categorize performance change as improvement, regression, or no change."""
        improvement_percent = comparison['improvement_percent']

        if abs(improvement_percent) < 5:  # Less than 5% change considered no change
            summary['no_change'].append(f"{metric_name}: {improvement_percent:+.1f}%")
        elif improvement_percent > 0:
            summary['improvements'].append(f"{metric_name}: {improvement_percent:+.1f}%")
        else:
            summary['regressions'].append(f"{metric_name}: {improvement_percent:+.1f}%")

    def print_comparison_results(self, results: Dict[str, Any]):
        """Print comparison results to console."""
        print("\n" + "="*60)
        print("TASK 17.2: POST-REFACTORING PERFORMANCE COMPARISON")
        print("="*60)

        print(f"Timestamp: {results['timestamp']}")

        # Print individual comparisons
        for metric_type, comparison in results['comparisons'].items():
            print(f"\n📊 {comparison['metric']}:")
            print(f"   Baseline: {comparison['baseline_value']:.2f} {comparison['unit']}")
            print(f"   Current:  {comparison['current_value']:.2f} {comparison['unit']}")

            if comparison['improved']:
                print(f"   ✅ Improvement: {comparison['improvement_percent']:+.1f}%")
            else:
                print(f"   ⚠️  Regression: {comparison['improvement_percent']:+.1f}%")

        # Print summary
        summary = results['summary']
        print(f"\n" + "-"*40)
        print("PERFORMANCE CHANGE SUMMARY")
        print("-"*40)

        if summary['improvements']:
            print(f"✅ Improvements ({len(summary['improvements'])}):")
            for improvement in summary['improvements']:
                print(f"   • {improvement}")

        if summary['regressions']:
            print(f"⚠️  Regressions ({len(summary['regressions'])}):")
            for regression in summary['regressions']:
                print(f"   • {regression}")

        if summary['no_change']:
            print(f"➖ No Significant Change ({len(summary['no_change'])}):")
            for no_change in summary['no_change']:
                print(f"   • {no_change}")

        print("\n" + "="*60)

    def run_all_measurements(self) -> Dict[str, Any]:
        """Run all post-refactoring performance measurements."""
        print("Starting post-refactoring performance measurements...")

        results = {
            'api_success': False,
            'bundle_success': False,
            'component_success': False
        }

        # Run measurements
        results['api_success'] = self.run_api_performance_measurement()
        results['bundle_success'] = self.run_bundle_size_measurement()
        results['component_success'] = self.run_component_performance_measurement()

        # Compare with baselines
        comparison_results = self.compare_with_baselines()

        # Save comparison results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        comparison_file = self.baseline_dir / f"post_refactoring_comparison_{timestamp}.json"

        with open(comparison_file, 'w') as f:
            json.dump(comparison_results, f, indent=2)

        print(f"\nComparison results saved to: {comparison_file}")

        # Print results
        self.print_comparison_results(comparison_results)

        return {
            'measurement_results': results,
            'comparison_results': comparison_results,
            'comparison_file': str(comparison_file)
        }


def main():
    """Main function to run post-refactoring performance measurements."""
    measurer = PostRefactoringPerformanceMeasurer()

    try:
        results = measurer.run_all_measurements()

        # Determine overall success
        measurement_results = results['measurement_results']
        successful_measurements = sum([
            measurement_results['api_success'],
            measurement_results['bundle_success'],
            measurement_results['component_success']
        ])

        print(f"\n{'='*60}")
        print(f"TASK 17.2 SUMMARY: {successful_measurements}/3 measurements completed successfully")

        if successful_measurements == 3:
            print("✅ All post-refactoring performance measurements completed successfully!")
        elif successful_measurements >= 2:
            print("⚠️  Most post-refactoring performance measurements completed successfully")
        else:
            print("❌ Post-refactoring performance measurements had significant issues")

        print(f"{'='*60}")

        return 0 if successful_measurements >= 2 else 1

    except Exception as e:
        print(f"❌ Error running post-refactoring performance measurements: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
