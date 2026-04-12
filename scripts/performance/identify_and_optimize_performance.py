#!/usr/bin/env python3
"""
Performance regression identification and optimization script.
Analyzes performance data, identifies regressions, and provides optimization recommendations.
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional


class PerformanceOptimizer:
    """Identifies performance regressions and provides optimization recommendations."""

    def __init__(self):
        self.baseline_dir = Path("scripts/performance/baselines")
        self.optimization_threshold = 5.0  # 5% regression threshold

    def find_latest_comparison(self) -> Optional[Path]:
        """Find the latest performance comparison file."""
        comparison_files = list(self.baseline_dir.glob("post_refactoring_comparison_*.json"))
        if not comparison_files:
            return None
        return max(comparison_files, key=lambda f: f.stat().st_mtime)

    def load_comparison_data(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Load comparison data from JSON file."""
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
            return None

    def identify_regressions(self, comparison_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify performance regressions that need attention."""
        regressions = []

        for metric_type, comparison in comparison_data.get('comparisons', {}).items():
            improvement_percent = comparison.get('improvement_percent', 0)

            # Negative improvement means regression
            if improvement_percent < -self.optimization_threshold:
                regressions.append({
                    'metric_type': metric_type,
                    'metric_name': comparison['metric'],
                    'regression_percent': abs(improvement_percent),
                    'baseline_value': comparison['baseline_value'],
                    'current_value': comparison['current_value'],
                    'unit': comparison['unit'],
                    'severity': self.classify_regression_severity(abs(improvement_percent))
                })

        return regressions

    def classify_regression_severity(self, regression_percent: float) -> str:
        """Classify regression severity based on percentage."""
        if regression_percent >= 50:
            return 'critical'
        elif regression_percent >= 25:
            return 'high'
        elif regression_percent >= 10:
            return 'medium'
        else:
            return 'low'

    def generate_optimization_recommendations(self, regressions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate optimization recommendations for identified regressions."""
        recommendations = {
            'timestamp': datetime.now().isoformat(),
            'total_regressions': len(regressions),
            'critical_regressions': len([r for r in regressions if r['severity'] == 'critical']),
            'recommendations': []
        }

        for regression in regressions:
            metric_type = regression['metric_type']

            if metric_type == 'api':
                rec = self.generate_api_optimization_recommendations(regression)
            elif metric_type == 'bundle':
                rec = self.generate_bundle_optimization_recommendations(regression)
            elif metric_type == 'component':
                rec = self.generate_component_optimization_recommendations(regression)
            else:
                rec = self.generate_generic_optimization_recommendations(regression)

            recommendations['recommendations'].append(rec)

        return recommendations

    def generate_api_optimization_recommendations(self, regression: Dict[str, Any]) -> Dict[str, Any]:
        """Generate API performance optimization recommendations."""
        severity = regression['severity']
        regression_percent = regression['regression_percent']

        recommendations = []

        if severity in ['critical', 'high']:
            recommendations.extend([
                "Implement database query optimization and indexing",
                "Add Redis caching for frequently accessed data",
                "Optimize database connection pooling",
                "Review and optimize slow database queries",
                "Consider implementing API response caching"
            ])

        if severity in ['critical', 'high', 'medium']:
            recommendations.extend([
                "Profile API endpoints to identify bottlenecks",
                "Implement request/response compression",
                "Optimize serialization/deserialization logic",
                "Review third-party API call efficiency",
                "Consider implementing pagination for large datasets"
            ])

        recommendations.extend([
            "Monitor API performance with APM tools",
            "Implement circuit breakers for external dependencies",
            "Review error handling performance impact"
        ])

        return {
            'metric': regression['metric_name'],
            'severity': severity,
            'regression_percent': regression_percent,
            'priority': 'high' if severity in ['critical', 'high'] else 'medium',
            'recommendations': recommendations,
            'estimated_effort': 'high' if severity == 'critical' else 'medium'
        }

    def generate_bundle_optimization_recommendations(self, regression: Dict[str, Any]) -> Dict[str, Any]:
        """Generate bundle size optimization recommendations."""
        severity = regression['severity']
        regression_percent = regression['regression_percent']

        recommendations = []

        if severity in ['critical', 'high']:
            recommendations.extend([
                "Implement code splitting and lazy loading",
                "Remove unused dependencies and dead code",
                "Optimize large dependencies (consider alternatives)",
                "Implement tree shaking for unused exports",
                "Use dynamic imports for non-critical features"
            ])

        if severity in ['critical', 'high', 'medium']:
            recommendations.extend([
                "Analyze bundle composition with webpack-bundle-analyzer",
                "Optimize images and static assets",
                "Implement proper chunk splitting strategy",
                "Review and optimize CSS bundle size",
                "Consider using CDN for large dependencies"
            ])

        recommendations.extend([
            "Enable gzip/brotli compression",
            "Implement service worker for caching",
            "Monitor bundle size in CI/CD pipeline"
        ])

        return {
            'metric': regression['metric_name'],
            'severity': severity,
            'regression_percent': regression_percent,
            'priority': 'high' if severity in ['critical', 'high'] else 'medium',
            'recommendations': recommendations,
            'estimated_effort': 'medium'
        }

    def generate_component_optimization_recommendations(self, regression: Dict[str, Any]) -> Dict[str, Any]:
        """Generate component performance optimization recommendations."""
        severity = regression['severity']
        regression_percent = regression['regression_percent']

        recommendations = []

        if severity in ['critical', 'high']:
            recommendations.extend([
                "Implement React.memo for expensive components",
                "Optimize component re-render patterns",
                "Use useMemo and useCallback for expensive computations",
                "Implement virtualization for large lists",
                "Review and optimize component prop drilling"
            ])

        if severity in ['critical', 'high', 'medium']:
            recommendations.extend([
                "Profile components with React DevTools Profiler",
                "Optimize state management to reduce re-renders",
                "Implement proper key props for list items",
                "Review component lifecycle and effect dependencies",
                "Consider component lazy loading"
            ])

        recommendations.extend([
            "Monitor component performance with React DevTools",
            "Implement performance budgets for components",
            "Use React Concurrent Features where appropriate"
        ])

        return {
            'metric': regression['metric_name'],
            'severity': severity,
            'regression_percent': regression_percent,
            'priority': 'medium' if severity in ['critical', 'high'] else 'low',
            'recommendations': recommendations,
            'estimated_effort': 'medium'
        }

    def generate_generic_optimization_recommendations(self, regression: Dict[str, Any]) -> Dict[str, Any]:
        """Generate generic optimization recommendations."""
        return {
            'metric': regression['metric_name'],
            'severity': regression['severity'],
            'regression_percent': regression['regression_percent'],
            'priority': 'medium',
            'recommendations': [
                "Profile the specific metric to identify bottlenecks",
                "Review recent changes that might impact performance",
                "Implement monitoring and alerting for this metric",
                "Consider performance testing in CI/CD pipeline"
            ],
            'estimated_effort': 'medium'
        }

    def create_optimization_plan(self, recommendations: Dict[str, Any]) -> Dict[str, Any]:
        """Create a prioritized optimization plan."""
        plan = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_recommendations': len(recommendations['recommendations']),
                'high_priority': len([r for r in recommendations['recommendations'] if r['priority'] == 'high']),
                'medium_priority': len([r for r in recommendations['recommendations'] if r['priority'] == 'medium']),
                'low_priority': len([r for r in recommendations['recommendations'] if r['priority'] == 'low'])
            },
            'phases': {
                'immediate': [],
                'short_term': [],
                'long_term': []
            }
        }

        # Categorize recommendations by priority and effort
        for rec in recommendations['recommendations']:
            if rec['priority'] == 'high' and rec['severity'] in ['critical', 'high']:
                plan['phases']['immediate'].append(rec)
            elif rec['priority'] in ['high', 'medium']:
                plan['phases']['short_term'].append(rec)
            else:
                plan['phases']['long_term'].append(rec)

        return plan

    def print_optimization_report(self, regressions: List[Dict[str, Any]],
                                recommendations: Dict[str, Any],
                                plan: Dict[str, Any]):
        """Print comprehensive optimization report."""
        print("\n" + "="*70)
        print("TASK 17.3: PERFORMANCE REGRESSION ANALYSIS & OPTIMIZATION")
        print("="*70)

        print(f"Analysis Timestamp: {recommendations['timestamp']}")
        print(f"Regression Threshold: {self.optimization_threshold}%")

        # Regression Summary
        print(f"\n📊 REGRESSION SUMMARY")
        print(f"   Total Regressions Found: {recommendations['total_regressions']}")
        print(f"   Critical Regressions: {recommendations['critical_regressions']}")

        if not regressions:
            print("   ✅ No significant performance regressions detected!")
            print("   🎉 All performance metrics are within acceptable thresholds.")
            return

        # Detailed Regression Analysis
        print(f"\n🔍 DETAILED REGRESSION ANALYSIS")
        print("-" * 50)

        for i, regression in enumerate(regressions, 1):
            severity_emoji = {
                'critical': '🔴',
                'high': '🟠',
                'medium': '🟡',
                'low': '🟢'
            }

            print(f"\n{i}. {regression['metric_name']} {severity_emoji[regression['severity']]}")
            print(f"   Regression: {regression['regression_percent']:.1f}% ({regression['severity']} severity)")
            print(f"   Baseline: {regression['baseline_value']:.2f} {regression['unit']}")
            print(f"   Current:  {regression['current_value']:.2f} {regression['unit']}")

        # Optimization Recommendations
        print(f"\n💡 OPTIMIZATION RECOMMENDATIONS")
        print("-" * 50)

        for i, rec in enumerate(recommendations['recommendations'], 1):
            priority_emoji = {'high': '🔥', 'medium': '⚡', 'low': '💡'}

            print(f"\n{i}. {rec['metric']} {priority_emoji[rec['priority']]}")
            print(f"   Priority: {rec['priority'].upper()} | Effort: {rec['estimated_effort'].upper()}")
            print(f"   Recommendations:")

            for j, recommendation in enumerate(rec['recommendations'][:5], 1):  # Show top 5
                print(f"   {j}. {recommendation}")

            if len(rec['recommendations']) > 5:
                print(f"   ... and {len(rec['recommendations']) - 5} more recommendations")

        # Optimization Plan
        print(f"\n📋 OPTIMIZATION IMPLEMENTATION PLAN")
        print("-" * 50)

        phases = [
            ('IMMEDIATE (Critical Issues)', plan['phases']['immediate']),
            ('SHORT-TERM (1-2 Sprints)', plan['phases']['short_term']),
            ('LONG-TERM (Future Releases)', plan['phases']['long_term'])
        ]

        for phase_name, phase_items in phases:
            if phase_items:
                print(f"\n🎯 {phase_name}:")
                for item in phase_items:
                    print(f"   • {item['metric']} ({item['regression_percent']:.1f}% regression)")
            else:
                print(f"\n✅ {phase_name}: No items")

        # Summary and Next Steps
        print(f"\n📈 NEXT STEPS")
        print("-" * 50)

        if plan['summary']['high_priority'] > 0:
            print("1. 🔥 Address high-priority regressions immediately")
            print("2. 📊 Set up performance monitoring and alerting")
            print("3. 🧪 Implement performance testing in CI/CD")
            print("4. 📝 Create performance budget guidelines")
        else:
            print("1. ✅ Continue monitoring performance metrics")
            print("2. 📊 Maintain current performance standards")
            print("3. 🔍 Consider proactive optimizations")

        print(f"\n{'='*70}")
        print("TASK 17.3 STATUS: ✅ COMPLETED")
        print("Performance analysis and optimization recommendations generated.")
        print(f"{'='*70}")

    def run_optimization_analysis(self) -> Dict[str, Any]:
        """Run complete performance optimization analysis."""
        print("Starting performance regression analysis and optimization...")

        # Find latest comparison data
        comparison_file = self.find_latest_comparison()
        if not comparison_file:
            print("❌ No performance comparison data found. Run Task 17.2 first.")
            return {'success': False, 'error': 'No comparison data'}

        # Load comparison data
        comparison_data = self.load_comparison_data(comparison_file)
        if not comparison_data:
            print("❌ Failed to load comparison data")
            return {'success': False, 'error': 'Failed to load data'}

        # Identify regressions
        regressions = self.identify_regressions(comparison_data)

        # Generate recommendations
        recommendations = self.generate_optimization_recommendations(regressions)

        # Create optimization plan
        plan = self.create_optimization_plan(recommendations)

        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save recommendations
        recommendations_file = self.baseline_dir / f"optimization_recommendations_{timestamp}.json"
        with open(recommendations_file, 'w') as f:
            json.dump(recommendations, f, indent=2)

        # Save optimization plan
        plan_file = self.baseline_dir / f"optimization_plan_{timestamp}.json"
        with open(plan_file, 'w') as f:
            json.dump(plan, f, indent=2)

        # Print report
        self.print_optimization_report(regressions, recommendations, plan)

        print(f"\n📁 Files Generated:")
        print(f"   • Recommendations: {recommendations_file}")
        print(f"   • Optimization Plan: {plan_file}")

        return {
            'success': True,
            'regressions_found': len(regressions),
            'critical_regressions': len([r for r in regressions if r['severity'] == 'critical']),
            'recommendations_file': str(recommendations_file),
            'plan_file': str(plan_file),
            'regressions': regressions,
            'recommendations': recommendations,
            'plan': plan
        }


def main():
    """Main function to run performance optimization analysis."""
    optimizer = PerformanceOptimizer()

    try:
        results = optimizer.run_optimization_analysis()

        if not results['success']:
            print(f"❌ Optimization analysis failed: {results.get('error', 'Unknown error')}")
            return 1

        # Determine success based on findings
        if results['critical_regressions'] > 0:
            print(f"\n⚠️  ATTENTION REQUIRED: {results['critical_regressions']} critical performance regressions found!")
            return 2  # Warning exit code
        elif results['regressions_found'] > 0:
            print(f"\n📊 Performance analysis complete: {results['regressions_found']} regressions identified with optimization recommendations.")
            return 0
        else:
            print(f"\n✅ Excellent! No significant performance regressions detected.")
            return 0

    except Exception as e:
        print(f"❌ Error running optimization analysis: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
