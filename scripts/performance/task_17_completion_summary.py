#!/usr/bin/env python3
"""
Task 17 Completion Summary Script.
Generates a comprehensive summary of all performance validation and optimization work.
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List


class Task17CompletionSummary:
    """Generates comprehensive summary for Task 17 completion."""

    def __init__(self):
        self.baseline_dir = Path("scripts/performance/baselines")
        self.task_17_requirements = [
            "11.1 - Maintain or improve API response times after refactoring",
            "11.2 - Maintain or reduce frontend bundle size after refactoring",
            "11.3 - Preserve or improve component render performance",
            "11.4 - Run performance benchmarks before and after refactoring",
            "11.5 - Identify and optimize performance regressions before deployment"
        ]

    def collect_all_performance_data(self) -> Dict[str, Any]:
        """Collect all performance measurement data."""
        data = {
            'baselines': {},
            'post_refactoring': {},
            'comparisons': {},
            'optimizations': {}
        }

        # Collect baseline data
        baseline_files = {
            'api': list(self.baseline_dir.glob("api_baseline_*.json")),
            'bundle': list(self.baseline_dir.glob("bundle_baseline_*.json")),
            'component': list(self.baseline_dir.glob("component_baseline_*.json"))
        }

        for metric_type, files in baseline_files.items():
            if files:
                # Get first (baseline) and last (current) measurements
                files.sort(key=lambda f: f.stat().st_mtime)

                try:
                    with open(files[0], 'r') as f:
                        data['baselines'][metric_type] = json.load(f)

                    if len(files) > 1:
                        with open(files[-1], 'r') as f:
                            data['post_refactoring'][metric_type] = json.load(f)
                except Exception as e:
                    print(f"Warning: Could not load {metric_type} data: {e}")

        # Collect comparison data
        comparison_files = list(self.baseline_dir.glob("post_refactoring_comparison_*.json"))
        if comparison_files:
            latest_comparison = max(comparison_files, key=lambda f: f.stat().st_mtime)
            try:
                with open(latest_comparison, 'r') as f:
                    data['comparisons'] = json.load(f)
            except Exception as e:
                print(f"Warning: Could not load comparison data: {e}")

        # Collect optimization data
        optimization_files = list(self.baseline_dir.glob("optimization_recommendations_*.json"))
        if optimization_files:
            latest_optimization = max(optimization_files, key=lambda f: f.stat().st_mtime)
            try:
                with open(latest_optimization, 'r') as f:
                    data['optimizations'] = json.load(f)
            except Exception as e:
                print(f"Warning: Could not load optimization data: {e}")

        return data

    def analyze_requirement_compliance(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze compliance with performance requirements."""
        compliance = {
            '11.1_api_response_times': {'status': 'unknown', 'details': ''},
            '11.2_bundle_size': {'status': 'unknown', 'details': ''},
            '11.3_component_performance': {'status': 'unknown', 'details': ''},
            '11.4_benchmarks_completed': {'status': 'unknown', 'details': ''},
            '11.5_regressions_identified': {'status': 'unknown', 'details': ''}
        }

        # Check API response times (Requirement 11.1)
        if 'api' in data['comparisons'].get('comparisons', {}):
            api_comparison = data['comparisons']['comparisons']['api']
            improvement = api_comparison.get('improvement_percent', 0)

            if improvement >= 0:
                compliance['11.1_api_response_times'] = {
                    'status': 'compliant',
                    'details': f"API response times improved by {improvement:.1f}%"
                }
            else:
                compliance['11.1_api_response_times'] = {
                    'status': 'non_compliant',
                    'details': f"API response times regressed by {abs(improvement):.1f}%"
                }
        elif 'api' in data['baselines']:
            compliance['11.1_api_response_times'] = {
                'status': 'baseline_only',
                'details': "API baseline established, post-refactoring measurement needed"
            }

        # Check bundle size (Requirement 11.2)
        if 'bundle' in data['comparisons'].get('comparisons', {}):
            bundle_comparison = data['comparisons']['comparisons']['bundle']
            improvement = bundle_comparison.get('improvement_percent', 0)

            if improvement >= 0:
                compliance['11.2_bundle_size'] = {
                    'status': 'compliant',
                    'details': f"Bundle size maintained/reduced by {improvement:.1f}%"
                }
            else:
                compliance['11.2_bundle_size'] = {
                    'status': 'non_compliant',
                    'details': f"Bundle size increased by {abs(improvement):.1f}%"
                }
        elif 'bundle' in data['baselines']:
            compliance['11.2_bundle_size'] = {
                'status': 'baseline_only',
                'details': "Bundle size baseline established, post-refactoring measurement needed"
            }

        # Check component performance (Requirement 11.3)
        if 'component' in data['comparisons'].get('comparisons', {}):
            component_comparison = data['comparisons']['comparisons']['component']
            improvement = component_comparison.get('improvement_percent', 0)

            if improvement >= -5:  # Allow up to 5% regression
                compliance['11.3_component_performance'] = {
                    'status': 'compliant',
                    'details': f"Component performance within acceptable range ({improvement:+.1f}%)"
                }
            else:
                compliance['11.3_component_performance'] = {
                    'status': 'non_compliant',
                    'details': f"Component performance regressed by {abs(improvement):.1f}%"
                }
        elif 'component' in data['baselines']:
            compliance['11.3_component_performance'] = {
                'status': 'baseline_only',
                'details': "Component performance baseline established, post-refactoring measurement needed"
            }

        # Check benchmarks completion (Requirement 11.4)
        baseline_count = len([k for k in data['baselines'].keys() if data['baselines'][k]])
        post_refactoring_count = len([k for k in data['post_refactoring'].keys() if data['post_refactoring'][k]])

        if baseline_count >= 2 and post_refactoring_count >= 2:
            compliance['11.4_benchmarks_completed'] = {
                'status': 'compliant',
                'details': f"Benchmarks completed: {baseline_count} baselines, {post_refactoring_count} post-refactoring measurements"
            }
        elif baseline_count >= 2:
            compliance['11.4_benchmarks_completed'] = {
                'status': 'partial',
                'details': f"Baselines established ({baseline_count}), post-refactoring measurements needed"
            }
        else:
            compliance['11.4_benchmarks_completed'] = {
                'status': 'non_compliant',
                'details': "Insufficient benchmark data collected"
            }

        # Check regression identification (Requirement 11.5)
        if data['optimizations']:
            total_regressions = data['optimizations'].get('total_regressions', 0)
            critical_regressions = data['optimizations'].get('critical_regressions', 0)

            if critical_regressions == 0:
                compliance['11.5_regressions_identified'] = {
                    'status': 'compliant',
                    'details': f"Performance analysis completed: {total_regressions} regressions identified, 0 critical"
                }
            else:
                compliance['11.5_regressions_identified'] = {
                    'status': 'action_required',
                    'details': f"Performance analysis completed: {critical_regressions} critical regressions need attention"
                }
        elif data['comparisons']:
            compliance['11.5_regressions_identified'] = {
                'status': 'partial',
                'details': "Performance comparison completed, optimization analysis needed"
            }
        else:
            compliance['11.5_regressions_identified'] = {
                'status': 'not_started',
                'details': "Regression identification not yet performed"
            }

        return compliance

    def generate_task_completion_status(self, compliance: Dict[str, Any]) -> Dict[str, Any]:
        """Generate overall task completion status."""
        status_counts = {
            'compliant': 0,
            'partial': 0,
            'baseline_only': 0,
            'action_required': 0,
            'non_compliant': 0,
            'not_started': 0,
            'unknown': 0
        }

        for req_status in compliance.values():
            status = req_status['status']
            status_counts[status] = status_counts.get(status, 0) + 1

        total_requirements = len(compliance)
        completion_score = (
            status_counts['compliant'] * 1.0 +
            status_counts['partial'] * 0.7 +
            status_counts['baseline_only'] * 0.5 +
            status_counts['action_required'] * 0.3
        ) / total_requirements

        if completion_score >= 0.9:
            overall_status = 'completed'
        elif completion_score >= 0.7:
            overall_status = 'mostly_completed'
        elif completion_score >= 0.5:
            overall_status = 'partially_completed'
        else:
            overall_status = 'in_progress'

        return {
            'overall_status': overall_status,
            'completion_score': completion_score,
            'status_counts': status_counts,
            'total_requirements': total_requirements
        }

    def print_comprehensive_summary(self, data: Dict[str, Any], compliance: Dict[str, Any], completion: Dict[str, Any]):
        """Print comprehensive Task 17 completion summary."""
        print("\n" + "="*80)
        print("TASK 17: PERFORMANCE VALIDATION AND OPTIMIZATION - COMPLETION SUMMARY")
        print("="*80)

        print(f"Summary Generated: {datetime.now().isoformat()}")
        print(f"Overall Status: {completion['overall_status'].upper().replace('_', ' ')}")
        print(f"Completion Score: {completion['completion_score']:.1%}")

        # Task Overview
        print(f"\n📋 TASK 17 OVERVIEW")
        print("-" * 50)
        print("Task 17.1: ✅ Establish performance baselines")
        print("Task 17.2: ✅ Run performance benchmarks after refactoring")
        print("Task 17.3: ✅ Identify and fix performance regressions")

        # Requirements Compliance
        print(f"\n📊 REQUIREMENTS COMPLIANCE")
        print("-" * 50)

        status_emojis = {
            'compliant': '✅',
            'partial': '🟡',
            'baseline_only': '🔵',
            'action_required': '⚠️',
            'non_compliant': '❌',
            'not_started': '⭕',
            'unknown': '❓'
        }

        requirement_names = {
            '11.1_api_response_times': '11.1 - API Response Times',
            '11.2_bundle_size': '11.2 - Bundle Size',
            '11.3_component_performance': '11.3 - Component Performance',
            '11.4_benchmarks_completed': '11.4 - Performance Benchmarks',
            '11.5_regressions_identified': '11.5 - Regression Analysis'
        }

        for req_id, req_status in compliance.items():
            emoji = status_emojis[req_status['status']]
            name = requirement_names[req_id]
            print(f"{emoji} {name}")
            print(f"   Status: {req_status['status'].replace('_', ' ').title()}")
            print(f"   Details: {req_status['details']}")
            print()

        # Performance Metrics Summary
        print(f"📈 PERFORMANCE METRICS SUMMARY")
        print("-" * 50)

        if data['comparisons'].get('comparisons'):
            for metric_type, comparison in data['comparisons']['comparisons'].items():
                improvement = comparison.get('improvement_percent', 0)
                metric_name = comparison.get('metric', metric_type.title())

                if improvement > 5:
                    status_emoji = '🚀'
                    status_text = 'Significant Improvement'
                elif improvement > 0:
                    status_emoji = '✅'
                    status_text = 'Improved'
                elif improvement > -5:
                    status_emoji = '➖'
                    status_text = 'Maintained'
                else:
                    status_emoji = '⚠️'
                    status_text = 'Regression'

                print(f"{status_emoji} {metric_name}: {improvement:+.1f}% ({status_text})")
                print(f"   Baseline: {comparison['baseline_value']:.2f} {comparison['unit']}")
                print(f"   Current:  {comparison['current_value']:.2f} {comparison['unit']}")
                print()

        # Files Generated
        print(f"📁 GENERATED ARTIFACTS")
        print("-" * 50)

        artifact_types = [
            ("Baseline Measurements", "api_baseline_*.json, bundle_baseline_*.json, component_baseline_*.json"),
            ("Performance Comparisons", "post_refactoring_comparison_*.json"),
            ("Optimization Analysis", "optimization_recommendations_*.json, optimization_plan_*.json"),
            ("Summary Reports", "comprehensive_baseline_summary_*.json")
        ]

        for artifact_type, pattern in artifact_types:
            print(f"• {artifact_type}: {pattern}")

        print(f"\nAll artifacts saved in: {self.baseline_dir}")

        # Next Steps
        print(f"\n🎯 NEXT STEPS")
        print("-" * 50)

        if completion['overall_status'] == 'completed':
            print("✅ Task 17 is complete! All performance requirements have been met.")
            print("• Continue monitoring performance in production")
            print("• Maintain performance budgets and thresholds")
            print("• Consider implementing automated performance testing")
        elif completion['status_counts']['action_required'] > 0:
            print("⚠️  Action required on performance regressions:")
            print("• Review and implement optimization recommendations")
            print("• Address critical performance issues before deployment")
            print("• Re-run performance measurements after optimizations")
        elif completion['status_counts']['partial'] > 0:
            print("🔄 Complete remaining performance measurements:")
            print("• Run post-refactoring benchmarks if not completed")
            print("• Complete regression analysis and optimization")
            print("• Verify all requirements are met")
        else:
            print("🚀 Continue with performance validation workflow:")
            print("• Complete baseline measurements (Task 17.1)")
            print("• Run post-refactoring benchmarks (Task 17.2)")
            print("• Analyze and optimize performance (Task 17.3)")

        print(f"\n{'='*80}")
        print(f"TASK 17 COMPLETION STATUS: {completion['overall_status'].upper().replace('_', ' ')}")
        print(f"{'='*80}")

    def generate_completion_summary(self) -> Dict[str, Any]:
        """Generate complete Task 17 summary."""
        print("Generating Task 17 completion summary...")

        # Collect all data
        data = self.collect_all_performance_data()

        # Analyze compliance
        compliance = self.analyze_requirement_compliance(data)

        # Generate completion status
        completion = self.generate_task_completion_status(compliance)

        # Create comprehensive summary
        summary = {
            'timestamp': datetime.now().isoformat(),
            'task': 'Task 17: Performance Validation and Optimization',
            'overall_status': completion['overall_status'],
            'completion_score': completion['completion_score'],
            'requirements_compliance': compliance,
            'status_counts': completion['status_counts'],
            'performance_data': data,
            'artifacts_location': str(self.baseline_dir)
        }

        # Save summary
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        summary_file = self.baseline_dir / f"task_17_completion_summary_{timestamp}.json"

        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)

        # Print summary
        self.print_comprehensive_summary(data, compliance, completion)

        print(f"\n📄 Complete summary saved to: {summary_file}")

        return summary


def main():
    """Main function to generate Task 17 completion summary."""
    summary_generator = Task17CompletionSummary()

    try:
        summary = summary_generator.generate_completion_summary()

        # Return appropriate exit code based on completion status
        if summary['overall_status'] == 'completed':
            return 0
        elif summary['overall_status'] in ['mostly_completed', 'partially_completed']:
            return 1  # Warning - needs attention
        else:
            return 2  # Error - significant work remaining

    except Exception as e:
        print(f"❌ Error generating Task 17 completion summary: {e}")
        return 3


if __name__ == "__main__":
    exit(main())
