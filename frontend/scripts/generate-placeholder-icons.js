#!/usr/bin/env node

/**
 * Generate placeholder PWA icons
 * This creates simple SVG-based PNG icons for development
 * Replace with proper icons before production deployment
 */

const fs = require('fs');
const path = require('path');

const sizes = [72, 96, 128, 144, 152, 192, 384, 512];
const iconsDir = path.join(__dirname, '../public/icons');

// Create icons directory if it doesn't exist
if (!fs.existsSync(iconsDir)) {
  fs.mkdirSync(iconsDir, { recursive: true });
}

// Generate SVG-based placeholder icons
function generatePlaceholderIcon(size) {
  const svg = `<?xml version="1.0" encoding="UTF-8"?>
<svg width="${size}" height="${size}" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#0f172a;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#1e293b;stop-opacity:1" />
    </linearGradient>
  </defs>
  <rect width="${size}" height="${size}" fill="url(#grad)" rx="${size * 0.15}"/>
  <text
    x="50%"
    y="50%"
    font-size="${size * 0.35}"
    fill="#ffffff"
    text-anchor="middle"
    dominant-baseline="middle"
    font-family="Arial, sans-serif"
    font-weight="bold">
    TN
  </text>
  <text
    x="50%"
    y="${size * 0.75}"
    font-size="${size * 0.08}"
    fill="#94a3b8"
    text-anchor="middle"
    dominant-baseline="middle"
    font-family="Arial, sans-serif">
    Tech News
  </text>
</svg>`;

  return svg;
}

// Check if sharp is available for PNG conversion
let sharp;
try {
  sharp = require('sharp');
} catch (error) {
  console.log('⚠️  Sharp not installed. Generating SVG icons only.');
  console.log('   Install sharp for PNG icons: npm install --save-dev sharp');
  sharp = null;
}

async function generateIcons() {
  console.log('🎨 Generating placeholder PWA icons...\n');

  for (const size of sizes) {
    const svg = generatePlaceholderIcon(size);
    const filename = `icon-${size}x${size}`;

    if (sharp) {
      // Generate PNG with sharp
      try {
        await sharp(Buffer.from(svg))
          .resize(size, size)
          .png()
          .toFile(path.join(iconsDir, `${filename}.png`));
        console.log(`✓ Generated ${filename}.png`);
      } catch (error) {
        console.error(`✗ Failed to generate ${filename}.png:`, error.message);
      }
    } else {
      // Fallback: save as SVG
      fs.writeFileSync(path.join(iconsDir, `${filename}.svg`), svg);
      console.log(`✓ Generated ${filename}.svg (SVG fallback)`);
    }
  }

  // Generate additional icons
  if (sharp) {
    const baseSvg = generatePlaceholderIcon(512);

    // Generate favicon
    try {
      await sharp(Buffer.from(baseSvg))
        .resize(32, 32)
        .png()
        .toFile(path.join(__dirname, '../public/favicon.ico'));
      console.log('✓ Generated favicon.ico');
    } catch (error) {
      console.error('✗ Failed to generate favicon.ico:', error.message);
    }

    // Generate apple touch icon
    try {
      await sharp(Buffer.from(baseSvg))
        .resize(180, 180)
        .png()
        .toFile(path.join(iconsDir, 'apple-touch-icon.png'));
      console.log('✓ Generated apple-touch-icon.png');
    } catch (error) {
      console.error('✗ Failed to generate apple-touch-icon.png:', error.message);
    }
  }

  console.log('\n✅ Icon generation complete!');
  console.log('\n📝 Note: These are placeholder icons for development.');
  console.log('   Replace with proper branded icons before production deployment.');
  console.log('\n💡 Tip: Use a tool like https://www.pwabuilder.com/imageGenerator');
  console.log('   to generate professional PWA icons from your logo.');
}

generateIcons().catch((error) => {
  console.error('❌ Icon generation failed:', error);
  process.exit(1);
});
