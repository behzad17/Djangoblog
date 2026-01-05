# Vazir Font Files

This directory contains local Vazir font files to replace the broken CDN.

## Current Status

✅ **Vazir-Bold.woff2** - Downloaded successfully (43KB)
✅ **Vazir-Medium.woff2** - Downloaded successfully (43KB)
⚠️ **Vazir.woff2** - Not available from CDN sources (Medium used as fallback)

## Manual Download (Optional)

If you need the regular weight (400) Vazir font file, you can:

1. Download from: https://github.com/rastikerdar/vazir-font
2. Extract `Vazir.woff2` from the dist folder
3. Place it in this directory: `static/fonts/vazir/Vazir.woff2`

The CSS will automatically use it once the file is present. Until then, Medium weight (500) will be used as a fallback for regular weight (400).

## Font Weights Available

- **400 (Regular)**: Uses Medium as fallback until Vazir.woff2 is added
- **500 (Medium)**: ✅ Available
- **700 (Bold)**: ✅ Available

