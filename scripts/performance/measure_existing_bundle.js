#!/usr/bin/env node
/**
 * Alternative bundle size measurement script that analyzes existing build artifacts.
 * This script measures bundle sizes from existing .next directory if available.
 */

const fs = require('fs');
const path = require('path');

class ExistingBundleMeasurer {
  constructor() {
    this.frontendDir = path.join(__dirname, '../../frontend');
    this.outputDir = path.join(__dirname, 'baselines');

    // Ensure output directory exists
    if (!fs.existsSync(this.outputDir)) {
      fs.mkdirSync(this.outputDir, { recursive: true });
    }
  }

  /**
   * Analyze existing bundle if available
   */
  measureExistingBundle() {
    console.log('Analyzing existing Next.js build artifacts...');

    const buildDir = path.join(this.frontendDir, '.next');

    if (!fs.existsSync(buildDir)) {
      console.log('No existing build found. Creating baseline with package.json analysis...');
      return this.analyzePackageJson();
    }

    try {
      const bundleAnalysis = this.analyzeBundleSize(buildDir);

      // Save baseline
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      const outputFile = path.join(this.outputDir, `bundle_baseline_${timestamp}.json`);

      const baseline = {
        timestamp: new Date().toISOString(),
        source: 'existing_build',
        ...bundleAnalysis,
        summary: this.calculateSummary(bundleAnalysis),
      };

      fs.writeFileSync(outputFile, JSON.stringify(baseline, null, 2));

      console.log(`\nBundle size baseline saved to: ${outputFile}`);
      this.printSummary(baseline);

      return baseline;
    } catch (error) {
      console.error('Error analyzing existing bundle:', error.message);
      console.log('Falling back to package.json analysis...');
      return this.analyzePackageJson();
    }
  }

  /**
   * Analyze the built bundle sizes from existing build
   */
  analyzeBundleSize(buildDir) {
    const analysis = {
      pages: {},
      chunks: {},
      assets: {},
      totalSize: 0,
    };

    try {
      // Read build manifest if available
      const buildManifestPath = path.join(buildDir, 'build-manifest.json');
      if (fs.existsSync(buildManifestPath)) {
        const buildManifest = JSON.parse(fs.readFileSync(buildManifestPath, 'utf8'));
        analysis.buildManifest = buildManifest;
      }

      // Analyze static files
      const staticDir = path.join(buildDir, 'static');
      if (fs.existsSync(staticDir)) {
        this.analyzeDirectory(staticDir, analysis, 'static');
      }

      // Analyze server files
      const serverDir = path.join(buildDir, 'server');
      if (fs.existsSync(serverDir)) {
        this.analyzeDirectory(serverDir, analysis, 'server');
      }
    } catch (error) {
      console.warn('Warning: Could not fully analyze bundle structure:', error.message);
    }

    return analysis;
  }

  /**
   * Analyze package.json for dependency size estimation
   */
  analyzePackageJson() {
    console.log('Analyzing package.json for dependency size estimation...');

    const packageJsonPath = path.join(this.frontendDir, 'package.json');

    if (!fs.existsSync(packageJsonPath)) {
      throw new Error('package.json not found');
    }

    const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
    const dependencies = packageJson.dependencies || {};
    const devDependencies = packageJson.devDependencies || {};

    // Estimate bundle size based on dependencies
    const majorDependencies = {
      next: 'Next.js Framework',
      react: 'React Library',
      'react-dom': 'React DOM',
      '@tanstack/react-query': 'React Query',
      axios: 'HTTP Client',
      '@radix-ui/react-avatar': 'Radix UI Components',
      tailwindcss: 'Tailwind CSS',
      'lucide-react': 'Lucide Icons',
    };

    const analysis = {
      source: 'package_json_estimation',
      dependencies: {
        production: Object.keys(dependencies).length,
        development: Object.keys(devDependencies).length,
        major: Object.keys(dependencies).filter((dep) => majorDependencies[dep]).length,
      },
      majorDependencies: Object.keys(dependencies)
        .filter((dep) => majorDependencies[dep])
        .map((dep) => ({ name: dep, description: majorDependencies[dep] })),
      estimatedBundleSize: this.estimateBundleSize(dependencies),
      totalSize: 0, // Will be calculated in summary
    };

    // Save baseline
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const outputFile = path.join(this.outputDir, `bundle_baseline_${timestamp}.json`);

    const baseline = {
      timestamp: new Date().toISOString(),
      source: 'package_json_estimation',
      ...analysis,
      summary: this.calculatePackageJsonSummary(analysis),
    };

    fs.writeFileSync(outputFile, JSON.stringify(baseline, null, 2));

    console.log(`\nBundle size baseline (estimated) saved to: ${outputFile}`);
    this.printPackageJsonSummary(baseline);

    return baseline;
  }

  /**
   * Estimate bundle size based on dependencies
   */
  estimateBundleSize(dependencies) {
    // Rough estimates based on common bundle sizes (in KB)
    const sizeEstimates = {
      next: 500,
      react: 45,
      'react-dom': 130,
      '@tanstack/react-query': 40,
      axios: 15,
      '@radix-ui/react-avatar': 10,
      '@radix-ui/react-checkbox': 8,
      '@radix-ui/react-dialog': 12,
      '@radix-ui/react-dropdown-menu': 15,
      tailwindcss: 50, // After purging
      'lucide-react': 25,
      clsx: 2,
      'date-fns': 20,
      zod: 12,
    };

    let estimatedSize = 0;
    const breakdown = {};

    Object.keys(dependencies).forEach((dep) => {
      const size = sizeEstimates[dep] || 5; // Default 5KB for unknown deps
      estimatedSize += size;
      breakdown[dep] = size;
    });

    return {
      totalKB: estimatedSize,
      totalMB: (estimatedSize / 1024).toFixed(2),
      breakdown,
    };
  }

  /**
   * Recursively analyze directory for file sizes
   */
  analyzeDirectory(dir, analysis, category) {
    try {
      const files = fs.readdirSync(dir, { withFileTypes: true });

      for (const file of files) {
        const filePath = path.join(dir, file.name);

        if (file.isDirectory()) {
          this.analyzeDirectory(filePath, analysis, category);
        } else {
          const stats = fs.statSync(filePath);
          const size = stats.size;
          const relativePath = path.relative(this.frontendDir, filePath);

          // Categorize files
          if (file.name.endsWith('.js')) {
            if (!analysis.chunks[category]) analysis.chunks[category] = {};
            analysis.chunks[category][relativePath] = size;
          } else if (file.name.endsWith('.css')) {
            if (!analysis.assets[category]) analysis.assets[category] = {};
            analysis.assets[category][relativePath] = size;
          } else if (file.name.endsWith('.html')) {
            if (!analysis.pages[category]) analysis.pages[category] = {};
            analysis.pages[category][relativePath] = size;
          }

          analysis.totalSize += size;
        }
      }
    } catch (error) {
      console.warn(`Warning: Could not analyze directory ${dir}:`, error.message);
    }
  }

  /**
   * Calculate summary statistics for existing build
   */
  calculateSummary(analysis) {
    const summary = {
      totalBundleSize: analysis.totalSize,
      totalBundleSizeMB: (analysis.totalSize / (1024 * 1024)).toFixed(2),
      jsChunksCount: 0,
      jsChunksSize: 0,
      cssAssetsCount: 0,
      cssAssetsSize: 0,
      htmlPagesCount: 0,
      htmlPagesSize: 0,
      largestChunk: null,
      largestChunkSize: 0,
    };

    // Count JS chunks
    Object.values(analysis.chunks).forEach((category) => {
      Object.entries(category).forEach(([file, size]) => {
        summary.jsChunksCount++;
        summary.jsChunksSize += size;

        if (size > summary.largestChunkSize) {
          summary.largestChunk = file;
          summary.largestChunkSize = size;
        }
      });
    });

    // Count CSS assets
    Object.values(analysis.assets).forEach((category) => {
      Object.entries(category).forEach(([file, size]) => {
        summary.cssAssetsCount++;
        summary.cssAssetsSize += size;
      });
    });

    // Count HTML pages
    Object.values(analysis.pages).forEach((category) => {
      Object.entries(category).forEach(([file, size]) => {
        summary.htmlPagesCount++;
        summary.htmlPagesSize += size;
      });
    });

    // Convert sizes to readable format
    summary.jsChunksSizeMB = (summary.jsChunksSize / (1024 * 1024)).toFixed(2);
    summary.cssAssetsSizeMB = (summary.cssAssetsSize / (1024 * 1024)).toFixed(2);
    summary.htmlPagesSizeMB = (summary.htmlPagesSize / (1024 * 1024)).toFixed(2);
    summary.largestChunkSizeMB = (summary.largestChunkSize / (1024 * 1024)).toFixed(2);

    return summary;
  }

  /**
   * Calculate summary for package.json analysis
   */
  calculatePackageJsonSummary(analysis) {
    return {
      source: 'package_json_estimation',
      totalDependencies: analysis.dependencies.production,
      totalDevDependencies: analysis.dependencies.development,
      majorDependencies: analysis.dependencies.major,
      estimatedBundleSizeKB: analysis.estimatedBundleSize.totalKB,
      estimatedBundleSizeMB: analysis.estimatedBundleSize.totalMB,
      largestEstimatedDependency: this.getLargestDependency(analysis.estimatedBundleSize.breakdown),
    };
  }

  /**
   * Get largest dependency from breakdown
   */
  getLargestDependency(breakdown) {
    let largest = { name: 'none', size: 0 };

    Object.entries(breakdown).forEach(([name, size]) => {
      if (size > largest.size) {
        largest = { name, size };
      }
    });

    return largest;
  }

  /**
   * Print summary to console for existing build
   */
  printSummary(baseline) {
    console.log('\n=== Bundle Size Baseline Summary ===');
    console.log(`Timestamp: ${baseline.timestamp}`);
    console.log(`Source: ${baseline.source}`);
    console.log(`Total bundle size: ${baseline.summary.totalBundleSizeMB} MB`);
    console.log(
      `JS chunks: ${baseline.summary.jsChunksCount} files (${baseline.summary.jsChunksSizeMB} MB)`
    );
    console.log(
      `CSS assets: ${baseline.summary.cssAssetsCount} files (${baseline.summary.cssAssetsSizeMB} MB)`
    );
    console.log(
      `HTML pages: ${baseline.summary.htmlPagesCount} files (${baseline.summary.htmlPagesSizeMB} MB)`
    );

    if (baseline.summary.largestChunk) {
      console.log(
        `Largest chunk: ${baseline.summary.largestChunk} (${baseline.summary.largestChunkSizeMB} MB)`
      );
    }
  }

  /**
   * Print summary for package.json analysis
   */
  printPackageJsonSummary(baseline) {
    console.log('\n=== Bundle Size Baseline Summary (Estimated) ===');
    console.log(`Timestamp: ${baseline.timestamp}`);
    console.log(`Source: ${baseline.source}`);
    console.log(`Production dependencies: ${baseline.summary.totalDependencies}`);
    console.log(`Development dependencies: ${baseline.summary.totalDevDependencies}`);
    console.log(`Major dependencies: ${baseline.summary.majorDependencies}`);
    console.log(`Estimated bundle size: ${baseline.summary.estimatedBundleSizeMB} MB`);
    console.log(
      `Largest estimated dependency: ${baseline.summary.largestEstimatedDependency.name} (${baseline.summary.largestEstimatedDependency.size} KB)`
    );

    console.log('\n=== Major Dependencies ===');
    baseline.majorDependencies.forEach((dep) => {
      console.log(`- ${dep.name}: ${dep.description}`);
    });
  }
}

/**
 * Main function
 */
async function main() {
  const measurer = new ExistingBundleMeasurer();

  try {
    await measurer.measureExistingBundle();
    console.log('\nBundle size measurement completed successfully!');
  } catch (error) {
    console.error('Bundle size measurement failed:', error.message);
    process.exit(1);
  }
}

// Run if called directly
if (require.main === module) {
  main();
}

module.exports = { ExistingBundleMeasurer };
