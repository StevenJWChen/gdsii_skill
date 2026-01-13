# GDSII Agent Skill

A comprehensive Claude Agent Skill for working with GDSII/OASIS IC layout files.

## Overview

This skill enables Claude to:
- Read and write GDSII/OASIS files (industry-standard IC layout formats)
- Analyze IC layout data (cells, layers, geometries, hierarchy)
- Manipulate and transform layouts programmatically
- Generate reports and visualizations
- Integrate with EDA tools (KLayout, Cadence, Magic, etc.)
- Automate layout workflows

## Installation

1. **Install Python dependencies:**
```bash
pip install gdspy --break-system-packages
# Optional: faster alternative
pip install gdstk --break-system-packages
```

2. **For Claude Code users:**
```bash
# Copy this skill directory to your skills folder
cp -r gdsii-skill ~/.claude/skills/gdsii
```

3. **For API users:**
Upload this skill directory using the Skills API.

## Quick Start

### Example 1: Inspect a GDSII File

Ask Claude:
```
Can you inspect the file design.gds and tell me what cells and layers it contains?
```

### Example 2: Extract a Specific Cell

Ask Claude:
```
Extract the cell named "SRAM_BLOCK" from chip.gds and save it to sram.gds
```

### Example 3: Analyze Layer Density

Ask Claude:
```
Calculate the metal density for layers 10-15 in my layout.gds
```

### Example 4: Generate Custom Layout

Ask Claude:
```
Create a parametric resistor layout with width=5um and length=50um on layer 10
```

## File Structure

```
gdsii-skill/
├── SKILL.md                 # Main skill file (loaded by Claude)
├── README.md                # This file
├── scripts/
│   └── gds_helper.py        # Command-line utility for GDSII operations
└── references/
    ├── gdsii_format.md      # GDSII format specification
    ├── workflows.md         # Common workflow examples
    └── eda_integration.md   # EDA tool integration guide
```

## Capabilities

### Reading and Analysis
- Load GDSII/OASIS files
- Inspect library metadata
- List cells and hierarchy
- Enumerate layers and datatypes
- Calculate bounding boxes
- Compute areas and densities
- Generate reports

### Layout Manipulation
- Extract specific cells
- Extract specific layers
- Remap layer numbers
- Merge multiple files
- Scale designs
- Boolean operations (union, intersection, difference)
- Flatten hierarchy

### Layout Generation
- Create parametric cells
- Generate arrays
- Create custom geometries
- Add text labels
- Define cell references

### Format Conversion
- GDSII ↔ OASIS
- Export to SVG/PNG
- Generate scripts for EDA tools

### Workflow Automation
- Batch processing
- Layer manipulation pipelines
- Design rule checks (basic)
- Mask shop preparation
- Integration with version control

## Command-Line Tool

The included `gds_helper.py` script provides quick GDSII operations:

```bash
# Inspect a file
python scripts/gds_helper.py inspect design.gds

# Extract a cell
python scripts/gds_helper.py extract-cell design.gds MYCELL output.gds

# Extract a layer
python scripts/gds_helper.py extract-layer design.gds 10 0 layer10.gds

# Merge files
python scripts/gds_helper.py merge file1.gds file2.gds -o merged.gds

# Calculate area
python scripts/gds_helper.py area design.gds -l 10
```

## Common Use Cases

### 1. Layout Analysis and Reporting
Generate comprehensive reports about IC layouts including cell hierarchy, layer usage, density calculations, and bounding box information.

### 2. Layer Manipulation
Remap layers for different process nodes, merge layers, split layers based on conditions, or extract specific layers for analysis.

### 3. Design Integration
Merge digital and analog blocks, integrate IP blocks, or combine multiple design files into a single chip layout.

### 4. Parametric Generation
Create parameterized layout generators for resistors, capacitors, inductors, or other custom components.

### 5. Mask Preparation
Prepare layouts for mask shop submission including flattening, text-to-polygon conversion, and alignment mark insertion.

### 6. Design Rule Checking
Perform basic automated checks for width, spacing, density, and other design rules.

## Integration with EDA Tools

### KLayout
```python
# Generate KLayout layer properties
generate_klayout_script('design.gds', 'layers.lyp')
```

### Cadence Virtuoso
Export/import via SKILL scripts (see `references/eda_integration.md`)

### Magic Layout
Use Tcl or Python interfaces

### OpenROAD/OpenLane
Merge with RTL-to-GDS flow outputs

## Reference Documentation

- **SKILL.md**: Main skill documentation with code examples
- **gdsii_format.md**: GDSII file format specification
- **workflows.md**: Complete workflow examples
- **eda_integration.md**: Integration with EDA tools

## Tips for Best Results

1. **Be Specific**: Specify exact cell names, layer numbers, and file paths
2. **Verify Units**: GDSII files can have different database units
3. **Test First**: Try operations on small test files before production data
4. **Validate Output**: Always check generated files in a GDSII viewer
5. **Backup**: Keep backups of original files

## Troubleshooting

**Claude doesn't recognize GDSII commands:**
- Make sure the skill is properly installed
- Try explicitly mentioning "using the GDSII skill"

**Library import errors:**
- Install gdspy: `pip install gdspy --break-system-packages`
- For faster performance, try gdstk: `pip install gdstk --break-system-packages`

**File not found errors:**
- Use absolute paths or verify working directory
- Check file permissions

**Large file performance:**
- Use gdstk instead of gdspy for better performance
- Process layers individually
- Consider flattening only when necessary

## Examples

### Extract and Analyze
```python
# Ask Claude:
"Read design.gds, extract the top-level cell called CHIP_TOP, 
and create a report showing all layers used with their total areas"
```

### Batch Processing
```python
# Ask Claude:
"Process all .gds files in the input/ directory:
1. Remove layer 99
2. Remap layer 1 to layer 10
3. Save results to output/ directory"
```

### Custom Generation
```python
# Ask Claude:
"Create a 10x10 array of resistors with width=5um, length=50um, 
spaced 100um apart, on layers 10 and 11, and save to array.gds"
```

## Contributing

This skill is designed to be extended. To add new capabilities:

1. Add functions to SKILL.md
2. Add workflow examples to workflows.md
3. Update this README with new use cases

## License

This skill is provided as-is for use with Claude. Refer to Anthropic's terms of service.

## Resources

- **gdspy documentation**: https://gdspy.readthedocs.io/
- **gdstk documentation**: https://heitzmann.github.io/gdstk/
- **GDSII specification**: Cadence GDSII Stream Format Manual
- **OASIS specification**: SEMI P39 Standard

## Version History

- **v1.0.0** (2025-01-13): Initial release
  - Complete GDSII/OASIS file manipulation
  - Analysis and reporting tools
  - Layout generation capabilities
  - EDA tool integration
  - Comprehensive documentation

---

**Need Help?** Ask Claude to "use the GDSII skill" to access these capabilities!
