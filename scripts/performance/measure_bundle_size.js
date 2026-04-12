#!/usr/bin/env node
/**
 * Bundle size measurement script for Next.js frontend.
 * Measures bundle sizes and generates baseline metrics.
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

class BundleSizeMeasurer {
  constructor() {
    this.frontendDir = path.join(__dirname, '../../frontend');
    this.outputDir = path.join(__dirname, 'baselines');

    // Ensure output directory exists
    if (!fs.existsSync(this.outputDir)) {
      fs.mkdirSync(this.outputDir, { recursive: true });
    }
  }

  /**
   * Build the Next.js application and measure bundle sizes
   */
  async measureBundleSize() {
    console.log('Building Next.js application for bundle size measurement...');

    try {
      // Change to frontend directory and build
      process.chdir(this.frontendDir);

      // Clean previous build
      if (fs.existsSync('.next')) {
        execSync('rm -rf .next', { stdio: 'inherit' });
      }

      // Build the application with linting disabled for performance measurement
      execSync('npx next build --no-lint', { stdio: 'inherit' });

      // Analyze bundle
      const bundleAnalysis = this.analyzeBundleSize();

      // Save baseline
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      const outputFile = path.join(this.outputDir, `bundle_baseline_${timestamp}.json`);

      const baseline = {
        timestamp: new Date().toISOString(),
        ...bundleAnalysis,
        summary: this.calculateSummary(bundleAnalysis),
      };

      fs.writeFileSync(outputFile, JSON.stringify(baseline, null, 2));

      console.log(`\nBundle size baseline saved to: ${outputFile}`);
      this.printSummary(baseline);

      return baseline;
    } catch (error) {
      console.error('Error measuring bundle size:', error.message);
      throw error;
    }
  }

  /**
   * Analyze the built bundle sizes
   */
  analyzeBundleSize() {
    const buildDir = path.join(this.frontendDir, '.next');
    const staticDir = path.join(buildDir, 'static');

    const analysis = {
      pages: {},
      chunks: {},
      assets: {},
      totalSize: 0,
    };

    try {
      // Read build manifest
      const buildManifestPath = path.join(buildDir, 'build-manifest.json');
      if (fs.existsSync(buildManifestPath)) {
        const buildManifest = JSON.parse(fs.readFileSync(buildManifestPath, 'utf8'));
        analysis.buildManifest = buildManifest;
      }

      // Analyze static files
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
   * Calculate summary statistics
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
   * Print summary to console
   */
  printSummary(baseline) {
    console.log('\n=== Bundle Size Baseline Summary ===');
    console.log(`Timestamp: ${baseline.timestamp}`);
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
}

/**
 * Main function
 */
async function main() {
  const measurer = new BundleSizeMeasurer();

  try {
    await measurer.measureBundleSize();
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

module.exports = { BundleSizeMeasurer };
