# EDA Tool Integration Guide

This document provides guidance on integrating GDSII workflows with common EDA tools.

## KLayout Integration

KLayout is a popular open-source layout viewer and editor with Python and Ruby scripting support.

### Installation

```bash
# Ubuntu/Debian
sudo apt-get install klayout

# macOS (Homebrew)
brew install klayout

# Or download from https://www.klayout.de/
```

### Basic Usage

```bash
# Open GDSII file
klayout design.gds

# Load with layer properties
klayout -l layers.lyp design.gds

# Run Ruby script
klayout -b -r script.rb design.gds

# Run Python script
klayout -b -z script.py design.gds

# Export to PNG
klayout -b -r export_png.rb design.gds -o output.png
```

### Python Scripting in KLayout

```python
import pya

# Load layout
app = pya.Application.instance()
mw = app.main_window()
layout_view = mw.current_view()

# Load GDSII
layout_view.load_layout("design.gds", 0)

# Get layout object
layout = layout_view.cellview(0).layout()

# Iterate through cells
for cell in layout.each_cell():
    print(f"Cell: {layout.cell_name(cell)}")

# Access layers
for layer_info in layout_view.each_layer():
    print(f"Layer: {layer_info.layer_index()}")

# Export
layout_view.save_as("output.gds", 0)
```

### DRC Scripts in KLayout

```ruby
# example_drc.drc - KLayout DRC script

# Read input
input("design.gds")

# Define layers
metal1 = input(10, 0)
via1 = input(11, 0)

# Minimum width check
metal1.width(0.5).output("Metal1 width < 0.5um")

# Minimum spacing check
metal1.space(0.5).output("Metal1 spacing < 0.5um")

# Overlap check
metal1.not_overlapping(via1).output("Metal1 not over via1")

# Density check
metal1.area / layout.area > 0.8
```

## Cadence Virtuoso Integration

### Exporting from Virtuoso

```skill
; SKILL script to export GDSII
procedure( exportGDS( libName cellName viewName gdsFile )
    let( (cv dbId)
        cv = dbOpenCellViewByType(libName cellName viewName "maskLayout" "r")
        when( cv
            dbStreamOut(
                cv
                gdsFile
                list( 
                    'streamFile gdsFile
                    'libName libName
                    'outputFormat "GDSII"
                    'layerMapping "/path/to/layer.map"
                )
            )
            dbClose(cv)
            printf("Exported %s to %s\n" cellName gdsFile)
        )
    )
)

; Usage
exportGDS("myLib" "myCell" "layout" "output.gds")
```

### Importing to Virtuoso

```skill
; SKILL script to import GDSII
procedure( importGDS( libName gdsFile @optional (topCell nil) )
    let( (cv)
        dbStreamIn(
            libName
            gdsFile
            list(
                'streamFile gdsFile
                'libName libName
                'topCell topCell
                'layerMapping "/path/to/layer.map"
            )
        )
        printf("Imported %s to library %s\n" gdsFile libName)
    )
)

; Usage
importGDS("myLib" "input.gds")
```

### Layer Mapping File

```
# layer.map - Cadence layer mapping
# GDS_LAYER GDS_DATATYPE CADENCE_LAYER CADENCE_PURPOSE
0 0 M1 drawing
0 1 M1 pin
1 0 M2 drawing
1 1 M2 pin
2 0 VIA1 drawing
```

## Magic Layout Integration

Magic is an open-source VLSI layout tool.

### Installation

```bash
# Ubuntu/Debian
sudo apt-get install magic

# Build from source
git clone https://github.com/RTimothyEdwards/magic.git
cd magic
./configure
make
sudo make install
```

### Tcl Scripting

```tcl
# Load GDSII
gds read design.gds

# Select top cell
load toplevel

# Export to different format
gds write output.gds

# CIF export
cif write output.cif

# Extract netlist
extract all
ext2spice lvs
ext2spice
```

### Python Interface

```python
import magic

# Start Magic
magic.magic()

# Load design
magic.load("design")

# Select cell
magic.select_cell("toplevel")

# Get bounding box
bbox = magic.get_bbox()

# Extract
magic.extract()

# Write GDS
magic.writeall("output.gds")
```

## OpenROAD/OpenLane Integration

OpenROAD is an open-source RTL-to-GDSII flow.

### Basic Flow

```python
import openroad as ord

# Initialize design
design = ord.Design("my_design")

# Read LEF/DEF
design.readLef("tech.lef")
design.readDef("design.def")

# Placement
design.global_placement()
design.detailed_placement()

# Routing
design.global_route()
design.detailed_route()

# Write GDSII
design.writeGDS("final.gds")
```

### Using gdspy with OpenROAD Output

```python
import gdspy
import json

def merge_openroad_output(digital_gds, analog_gds, output_gds):
    """Merge digital (OpenROAD) and analog (custom) layouts."""
    
    # Load both designs
    digital_lib = gdspy.GdsLibrary(infile=digital_gds)
    analog_lib = gdspy.GdsLibrary(infile=analog_gds)
    
    # Create merged library
    merged_lib = gdspy.GdsLibrary(name="MERGED_CHIP")
    
    # Create top cell
    top = merged_lib.new_cell("TOP")
    
    # Add digital block
    digital_cell = digital_lib.top_level()[0]
    digital_ref = gdspy.CellReference(
        digital_cell,
        origin=(0, 0)
    )
    top.add(digital_ref)
    
    # Add analog block
    analog_cell = analog_lib.top_level()[0]
    analog_ref = gdspy.CellReference(
        analog_cell,
        origin=(5000, 0)  # Offset analog block
    )
    top.add(analog_ref)
    
    # Copy all cells
    for name, cell in digital_lib.cells.items():
        merged_lib.cells[name] = cell
    
    for name, cell in analog_lib.cells.items():
        # Rename if conflict
        if name in merged_lib.cells:
            name = f"ANALOG_{name}"
        merged_lib.cells[name] = cell
    
    # Write merged design
    merged_lib.write_gds(output_gds)
    print(f"Merged design saved to {output_gds}")

# Usage
merge_openroad_output("digital.gds", "analog.gds", "merged_chip.gds")
```

## PDK Integration

### SKY130 PDK Example

```python
import gdspy
import yaml

def load_sky130_pdk():
    """Load SKY130 PDK layer definitions."""
    
    # SKY130 layer stack
    layers = {
        'nwell': {'gds': (64, 20), 'color': '#FFB6C1'},
        'diff': {'gds': (65, 20), 'color': '#90EE90'},
        'tap': {'gds': (65, 44), 'color': '#FFD700'},
        'nsdm': {'gds': (93, 44), 'color': '#FFA500'},
        'psdm': {'gds': (94, 20), 'color': '#FF69B4'},
        'li1': {'gds': (67, 20), 'color': '#4169E1'},
        'mcon': {'gds': (67, 44), 'color': '#8B4513'},
        'met1': {'gds': (68, 20), 'color': '#1E90FF'},
        'via1': {'gds': (68, 44), 'color': '#696969'},
        'met2': {'gds': (69, 20), 'color': '#00CED1'},
        'via2': {'gds': (69, 44), 'color': '#A9A9A9'},
        'met3': {'gds': (70, 20), 'color': '#48D1CC'},
        'via3': {'gds': (70, 44), 'color': '#D3D3D3'},
        'met4': {'gds': (71, 20), 'color': '#40E0D0'},
        'via4': {'gds': (71, 44), 'color': '#DCDCDC'},
        'met5': {'gds': (72, 20), 'color': '#00FFFF'},
    }
    
    return layers

def create_sky130_component():
    """Create a simple component using SKY130 layers."""
    lib = gdspy.GdsLibrary(name="SKY130_DESIGN")
    cell = lib.new_cell("INVERTER")
    
    layers = load_sky130_pdk()
    
    # NMOS (example simplified)
    nmos = gdspy.Rectangle(
        (0, 0), (10, 5),
        layer=layers['diff']['gds'][0],
        datatype=layers['diff']['gds'][1]
    )
    cell.add(nmos)
    
    # PMOS (in nwell)
    nwell = gdspy.Rectangle(
        (0, 6), (10, 16),
        layer=layers['nwell']['gds'][0],
        datatype=layers['nwell']['gds'][1]
    )
    cell.add(nwell)
    
    pmos = gdspy.Rectangle(
        (0, 11), (10, 16),
        layer=layers['diff']['gds'][0],
        datatype=layers['diff']['gds'][1]
    )
    cell.add(pmos)
    
    # Local interconnect
    li = gdspy.FlexPath(
        [(5, 5), (5, 8), (5, 11)],
        width=0.17,
        layer=layers['li1']['gds'][0],
        datatype=layers['li1']['gds'][1]
    )
    cell.add(li)
    
    lib.write_gds("inverter_sky130.gds")
    return lib
```

## Mask Shop Integration

### Generating Mask Data

```python
import gdspy

def prepare_for_mask_shop(input_gds, output_gds, foundry="TSMC"):
    """
    Prepare GDSII for mask shop submission.
    
    Operations:
    - Flatten hierarchy
    - Remove text elements
    - Validate coordinates
    - Add alignment marks
    - Generate checksum
    """
    lib = gdspy.GdsLibrary(infile=input_gds)
    
    # Flatten all cells
    for cell in lib.top_level():
        cell.flatten()
    
    # Remove text (mask shops prefer text as polygons)
    for cell in lib.cells.values():
        cell.elements = [
            el for el in cell.elements
            if not isinstance(el, gdspy.Text)
        ]
    
    # Add alignment marks
    for cell in lib.top_level():
        add_alignment_marks(cell, foundry)
    
    # Write output
    lib.write_gds(output_gds)
    print(f"Mask-ready file: {output_gds}")
    
    # Generate checksum
    import hashlib
    with open(output_gds, 'rb') as f:
        checksum = hashlib.md5(f.read()).hexdigest()
    
    print(f"MD5 Checksum: {checksum}")
    
    return checksum

def add_alignment_marks(cell, foundry):
    """Add foundry-specific alignment marks."""
    
    # Simple cross mark example
    mark_layer = 0
    mark_size = 100
    mark_width = 10
    
    # Bottom-left corner
    h_line = gdspy.Rectangle(
        (-mark_size, -mark_width/2),
        (mark_size, mark_width/2),
        layer=mark_layer
    )
    v_line = gdspy.Rectangle(
        (-mark_width/2, -mark_size),
        (mark_width/2, mark_size),
        layer=mark_layer
    )
    
    cell.add(h_line)
    cell.add(v_line)
```

## Verification Tool Integration

### Calibre Integration

```python
def generate_calibre_runset(gds_file, rule_deck, output_dir="./calibre_run"):
    """Generate Calibre DRC/LVS runset."""
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    runset = f"""
// Calibre DRC Runset
LAYOUT PATH "{gds_file}"
LAYOUT PRIMARY "TOP"
LAYOUT SYSTEM GDSII

DRC RESULTS DATABASE "{output_dir}/drc.db" ASCII
DRC SUMMARY REPORT "{output_dir}/drc_summary.rpt"

DRC MAXIMUM RESULTS ALL
DRC MAXIMUM VERTEX ALL

VIRTUAL CONNECT COLON YES
VIRTUAL CONNECT REPORT NO

INCLUDE "{rule_deck}"
"""
    
    runset_file = os.path.join(output_dir, "runset.drc")
    with open(runset_file, 'w') as f:
        f.write(runset)
    
    print(f"Calibre runset generated: {runset_file}")
    print(f"Run with: calibre -drc -runset {runset_file}")
    
    return runset_file
```

## Best Practices

1. **Layer Mapping**: Always maintain consistent layer mapping files between tools
2. **Units**: Verify database units match (typically 1nm precision)
3. **Flattening**: Only flatten when required (for mask shop)
4. **Text**: Convert to polygons before final tapeout
5. **Validation**: Cross-check in multiple viewers
6. **Backup**: Version control your GDSII files
7. **Documentation**: Document all conversions and modifications

## Troubleshooting

**Issue**: Layer mismatch between tools
- **Solution**: Create and maintain layer.map file

**Issue**: Coordinate overflow
- **Solution**: Check units and scale factors

**Issue**: Missing cells after import
- **Solution**: Verify hierarchy isn't too deep, flatten if needed

**Issue**: Text not displaying correctly
- **Solution**: Convert text to polygons

## Resources

- **KLayout**: https://www.klayout.de/
- **Magic**: http://opencircuitdesign.com/magic/
- **OpenROAD**: https://theopenroadproject.org/
- **SKY130 PDK**: https://skywater-pdk.readthedocs.io/
- **Calibre**: https://eda.sw.siemens.com/
