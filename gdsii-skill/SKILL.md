---
name: gdsii
description: Comprehensive GDSII/OASIS IC layout file manipulation toolkit for reading, writing, analyzing, and converting IC layout files. Use when working with GDSII/GDS2/OASIS files, IC layout design, mask data processing, or EDA workflows involving physical layout manipulation.
---

# GDSII IC Layout Processing Guide

## Overview

This skill provides comprehensive tools for working with GDSII (Graphic Data System) and OASIS files, the industry-standard formats for IC layout data. GDSII files are the final output of the IC design cycle and are used for mask fabrication.

**Key Capabilities:**
- Read and write GDSII/OASIS files
- Extract layout information (cells, layers, geometries)
- Modify and create IC layouts programmatically
- Convert between formats
- Analyze layout data (area calculations, density checks, hierarchy analysis)
- Generate reports and visualizations

**When to Use This Skill:**
- Processing mask data files
- Automating layout tasks
- Extracting design information
- Converting between GDSII and other formats
- Performing layout analysis
- Creating custom layout generators
- Integration with EDA workflows

## Quick Start

### Installation

```bash
# Install gdspy (Python 2.7/3.x compatible)
pip install gdspy --break-system-packages

# OR install gdstk (faster, modern C++/Python library)
pip install gdstk --break-system-packages

# Additional useful tools
pip install numpy matplotlib --break-system-packages
```

### Reading a GDSII File

```python
import gdspy

# Read GDSII file
gdsii = gdspy.GdsLibrary(infile='design.gds')

# Print library information
print(f"Library name: {gdsii.name}")
print(f"Units: {gdsii.unit} (user), {gdsii.precision} (database)")
print(f"Number of cells: {len(gdsii.cells)}")

# List all cells
for cell_name in gdsii.cells:
    print(f"Cell: {cell_name}")
    
# Get top-level cells (cells not referenced by others)
top_cells = gdsii.top_level()
print(f"Top-level cells: {[cell.name for cell in top_cells]}")
```

### Basic Layout Creation

```python
import gdspy

# Create a new library
lib = gdspy.GdsLibrary(name='MYDESIGN', unit=1e-6, precision=1e-9)

# Create a cell
cell = lib.new_cell('TOPLEVEL')

# Add a rectangle on layer 0
rect = gdspy.Rectangle((0, 0), (10, 20), layer=0)
cell.add(rect)

# Add a polygon on layer 1
points = [(0, 0), (5, 0), (5, 10), (3, 10), (3, 5), (0, 5)]
poly = gdspy.Polygon(points, layer=1, datatype=0)
cell.add(poly)

# Add a circle approximation
circle = gdspy.Round((15, 15), 5, layer=2, number_of_points=64)
cell.add(circle)

# Write to file
lib.write_gds('output.gds')
print("GDSII file created: output.gds")
```

## Core Operations

### 1. Reading and Inspecting GDSII Files

#### Extract All Layer Information
```python
import gdspy

def analyze_layers(gds_file):
    """Extract all unique layers and datatypes from GDSII file."""
    lib = gdspy.GdsLibrary(infile=gds_file)
    
    layers = set()
    for cell_name, cell in lib.cells.items():
        for element in cell.elements:
            if hasattr(element, 'layers'):
                # For polygons, paths
                for layer in element.layers:
                    layers.add((layer, element.datatypes[element.layers.index(layer)]))
            elif hasattr(element, 'layer'):
                # For simple elements
                layers.add((element.layer, element.datatype))
    
    # Sort and display
    layers = sorted(list(layers))
    print(f"Total unique layers: {len(layers)}")
    for layer, datatype in layers:
        print(f"  Layer {layer}, Datatype {datatype}")
    
    return layers

# Usage
layers = analyze_layers('design.gds')
```

#### Extract Cell Hierarchy
```python
def print_hierarchy(cell, level=0, visited=None):
    """Print cell hierarchy tree."""
    if visited is None:
        visited = set()
    
    indent = "  " * level
    print(f"{indent}{cell.name}")
    
    if cell.name in visited:
        print(f"{indent}  (already shown)")
        return
    
    visited.add(cell.name)
    
    for ref in cell.references:
        print_hierarchy(ref.ref_cell, level + 1, visited)

# Usage
lib = gdspy.GdsLibrary(infile='design.gds')
top_cells = lib.top_level()
for cell in top_cells:
    print("\nHierarchy:")
    print_hierarchy(cell)
```

#### Calculate Total Area by Layer
```python
def calculate_layer_areas(gds_file):
    """Calculate total polygon area for each layer."""
    lib = gdspy.GdsLibrary(infile=gds_file)
    
    layer_areas = {}
    
    for cell in lib.top_level():
        # Flatten to get all geometries
        polygons = cell.get_polygons(by_spec=True)
        
        for spec, polys in polygons.items():
            layer, datatype = spec
            if (layer, datatype) not in layer_areas:
                layer_areas[(layer, datatype)] = 0
            
            for poly in polys:
                # Calculate polygon area using shoelace formula
                area = gdspy.polygon_area(poly)
                layer_areas[(layer, datatype)] += abs(area)
    
    # Display results
    print("Layer Areas (in square units):")
    for (layer, datatype), area in sorted(layer_areas.items()):
        print(f"  Layer {layer}, Datatype {datatype}: {area:.2e}")
    
    return layer_areas

# Usage
areas = calculate_layer_areas('design.gds')
```

### 2. Modifying GDSII Files

#### Extract Specific Cell
```python
def extract_cell(input_gds, cell_name, output_gds):
    """Extract a specific cell and its dependencies to new file."""
    lib = gdspy.GdsLibrary(infile=input_gds)
    
    if cell_name not in lib.cells:
        print(f"Error: Cell '{cell_name}' not found")
        return False
    
    # Create new library with only this cell
    new_lib = gdspy.GdsLibrary(name=lib.name, unit=lib.unit, precision=lib.precision)
    
    # Get cell and all its dependencies
    cell = lib.cells[cell_name]
    cells_to_copy = {cell_name}
    
    def get_dependencies(c):
        for ref in c.references:
            if ref.ref_cell.name not in cells_to_copy:
                cells_to_copy.add(ref.ref_cell.name)
                get_dependencies(ref.ref_cell)
    
    get_dependencies(cell)
    
    # Copy cells
    for name in cells_to_copy:
        new_lib.cells[name] = lib.cells[name]
    
    new_lib.write_gds(output_gds)
    print(f"Extracted {len(cells_to_copy)} cells to {output_gds}")
    return True

# Usage
extract_cell('design.gds', 'MYCELL', 'extracted.gds')
```

#### Layer Operations
```python
def change_layer_numbers(input_gds, layer_map, output_gds):
    """Remap layer numbers (e.g., {0: 10, 1: 11} changes layer 0 to 10, layer 1 to 11)."""
    lib = gdspy.GdsLibrary(infile=input_gds)
    
    for cell_name, cell in lib.cells.items():
        for element in cell.elements:
            if hasattr(element, 'layers'):
                # Handle multi-layer elements
                new_layers = []
                for layer in element.layers:
                    new_layers.append(layer_map.get(layer, layer))
                element.layers = new_layers
            elif hasattr(element, 'layer'):
                # Handle single-layer elements
                element.layer = layer_map.get(element.layer, element.layer)
    
    lib.write_gds(output_gds)
    print(f"Layer mapping applied, saved to {output_gds}")

# Usage
layer_map = {0: 100, 1: 101, 2: 102}
change_layer_numbers('input.gds', layer_map, 'remapped.gds')
```

#### Scale Design
```python
def scale_layout(input_gds, scale_factor, output_gds):
    """Scale entire layout by a factor."""
    lib = gdspy.GdsLibrary(infile=input_gds)
    
    for cell_name, cell in lib.cells.items():
        for element in cell.elements:
            if hasattr(element, 'scale'):
                element.scale(scale_factor)
            elif hasattr(element, 'points'):
                element.points *= scale_factor
    
    lib.write_gds(output_gds)
    print(f"Layout scaled by {scale_factor}x, saved to {output_gds}")

# Usage
scale_layout('input.gds', 2.0, 'scaled_2x.gds')
```

### 3. Creating Custom Layouts

#### Parametric Cell Generator
```python
def create_resistor(width, length, layer=10, datatype=0):
    """Create a simple resistor layout."""
    cell = gdspy.Cell('RESISTOR')
    
    # Main resistor body
    body = gdspy.Rectangle(
        (0, -width/2), 
        (length, width/2), 
        layer=layer, 
        datatype=datatype
    )
    cell.add(body)
    
    # Contact pads
    contact_size = width * 1.5
    pad_layer = layer + 1
    
    # Left contact
    left_contact = gdspy.Rectangle(
        (-contact_size, -contact_size/2),
        (0, contact_size/2),
        layer=pad_layer
    )
    cell.add(left_contact)
    
    # Right contact
    right_contact = gdspy.Rectangle(
        (length, -contact_size/2),
        (length + contact_size, contact_size/2),
        layer=pad_layer
    )
    cell.add(right_contact)
    
    return cell

# Usage
lib = gdspy.GdsLibrary()
resistor = create_resistor(width=5, length=50)
lib.add(resistor)
lib.write_gds('resistor.gds')
```

#### Array Generator
```python
def create_array(base_cell, rows, cols, spacing_x, spacing_y, array_name='ARRAY'):
    """Create a regular array of cells."""
    array_cell = gdspy.Cell(array_name)
    
    for row in range(rows):
        for col in range(cols):
            x = col * spacing_x
            y = row * spacing_y
            ref = gdspy.CellReference(base_cell, origin=(x, y))
            array_cell.add(ref)
    
    return array_cell

# Usage
lib = gdspy.GdsLibrary(infile='unit_cell.gds')
unit_cell = lib.cells['UNIT']
array = create_array(unit_cell, rows=10, cols=10, spacing_x=100, spacing_y=100)
lib.add(array)
lib.write_gds('array.gds')
```

### 4. Format Conversion

#### GDSII to OASIS
```python
# Using gdspy (OASIS support)
def gds_to_oasis(gds_file, oasis_file):
    """Convert GDSII to OASIS format."""
    lib = gdspy.GdsLibrary(infile=gds_file)
    lib.write_gds(oasis_file, binary_cells=True)  # OASIS uses binary
    print(f"Converted {gds_file} to {oasis_file}")

# Usage
gds_to_oasis('design.gds', 'design.oas')
```

#### Export to SVG/PNG
```python
def gds_to_svg(gds_file, svg_file, cell_name=None):
    """Export GDSII layout to SVG."""
    lib = gdspy.GdsLibrary(infile=gds_file)
    
    if cell_name:
        cell = lib.cells[cell_name]
    else:
        cell = lib.top_level()[0]
    
    cell.write_svg(svg_file, background='#FFFFFF')
    print(f"Exported {cell.name} to {svg_file}")

# Usage
gds_to_svg('design.gds', 'layout.svg')
```

## Advanced Features

### Boolean Operations
```python
def boolean_operations_example():
    """Demonstrate boolean operations on polygons."""
    # Create two overlapping rectangles
    rect1 = gdspy.Rectangle((0, 0), (20, 20))
    rect2 = gdspy.Rectangle((10, 10), (30, 30))
    
    # Union (OR)
    union = gdspy.boolean(rect1, rect2, 'or', layer=1)
    
    # Intersection (AND)
    intersection = gdspy.boolean(rect1, rect2, 'and', layer=2)
    
    # Difference (NOT)
    difference = gdspy.boolean(rect1, rect2, 'not', layer=3)
    
    # XOR
    xor = gdspy.boolean(rect1, rect2, 'xor', layer=4)
    
    # Create library and save
    lib = gdspy.GdsLibrary()
    cell = lib.new_cell('BOOLEAN_OPS')
    cell.add(union)
    cell.add(intersection)
    cell.add(difference)
    cell.add(xor)
    
    lib.write_gds('boolean_ops.gds')
    return cell
```

### Design Rule Checking (Basic)
```python
def check_minimum_spacing(gds_file, layer, min_spacing):
    """Basic check for minimum spacing violations on a layer."""
    lib = gdspy.GdsLibrary(infile=gds_file)
    
    violations = []
    
    for cell in lib.top_level():
        polygons = cell.get_polygons()
        layer_polys = [p for spec, polys in polygons.items() 
                       if spec[0] == layer for p in polys]
        
        # Check spacing between all polygon pairs
        for i in range(len(layer_polys)):
            for j in range(i + 1, len(layer_polys)):
                # Calculate minimum distance (simplified)
                # In production, use more robust algorithms
                pass  # Implementation would go here
    
    return violations
```

### Density Calculation
```python
def calculate_density(gds_file, layer, window_size=(100, 100)):
    """Calculate pattern density for a given layer."""
    lib = gdspy.GdsLibrary(infile=gds_file)
    
    for cell in lib.top_level():
        bbox = cell.get_bounding_box()
        if bbox is None:
            continue
        
        polygons = cell.get_polygons(by_spec=True)
        layer_polys = polygons.get((layer, 0), [])
        
        if not layer_polys:
            print(f"No polygons found on layer {layer}")
            continue
        
        # Calculate total area
        total_area = sum(abs(gdspy.polygon_area(p)) for p in layer_polys)
        
        # Layout area
        layout_width = bbox[1][0] - bbox[0][0]
        layout_height = bbox[1][1] - bbox[0][1]
        layout_area = layout_width * layout_height
        
        density = (total_area / layout_area) * 100 if layout_area > 0 else 0
        
        print(f"Layer {layer} density: {density:.2f}%")
        print(f"  Total polygon area: {total_area:.2e}")
        print(f"  Layout area: {layout_area:.2e}")
        
        return density
```

## Command-Line Tools

### Using KLayout (if installed)
```bash
# Convert GDSII to OASIS
klayout -b -r script.rb input.gds -o output.oas

# Export to PNG
klayout -b -r export.rb input.gds -o layout.png

# Run DRC script
klayout -b -r drc.drc input.gds
```

### Using gdstk (faster alternative)
```python
import gdstk

# Read GDSII
library = gdstk.read_gds('design.gds')

# Create new cell
cell = gdstk.Cell('NEWCELL')

# Add rectangle
rect = gdstk.rectangle((0, 0), (10, 20), layer=0)
cell.add(rect)

# Add to library and write
library.add(cell)
library.write_gds('output.gds')
```

## Common Workflows

### Workflow 1: Extract and Analyze Specific Layer
```python
def extract_layer(gds_file, layer, datatype=0, output_file='layer_extract.gds'):
    """Extract all geometries from a specific layer."""
    lib = gdspy.GdsLibrary(infile=gds_file)
    new_lib = gdspy.GdsLibrary(name=lib.name, unit=lib.unit, precision=lib.precision)
    
    for cell_name, cell in lib.cells.items():
        new_cell = new_lib.new_cell(cell_name)
        
        for element in cell.elements:
            if hasattr(element, 'layer') and element.layer == layer:
                if element.datatype == datatype:
                    new_cell.add(element)
            elif hasattr(element, 'layers') and layer in element.layers:
                idx = element.layers.index(layer)
                if element.datatypes[idx] == datatype:
                    new_cell.add(element)
    
    new_lib.write_gds(output_file)
    print(f"Layer {layer}:{datatype} extracted to {output_file}")
```

### Workflow 2: Merge Multiple GDS Files
```python
def merge_gds_files(gds_files, output_file, spacing=1000):
    """Merge multiple GDS files side by side."""
    lib = gdspy.GdsLibrary()
    top_cell = lib.new_cell('MERGED')
    
    x_offset = 0
    
    for gds_file in gds_files:
        temp_lib = gdspy.GdsLibrary(infile=gds_file)
        
        # Get top-level cell
        top_cells = temp_lib.top_level()
        if not top_cells:
            continue
        
        cell = top_cells[0]
        
        # Add as reference with offset
        ref = gdspy.CellReference(cell, origin=(x_offset, 0))
        top_cell.add(ref)
        
        # Copy cell to new library
        lib.cells[cell.name] = cell
        
        # Update offset
        bbox = cell.get_bounding_box()
        if bbox:
            x_offset += (bbox[1][0] - bbox[0][0]) + spacing
    
    lib.write_gds(output_file)
    print(f"Merged {len(gds_files)} files to {output_file}")
```

### Workflow 3: Generate Report
```python
def generate_gds_report(gds_file, output_txt='report.txt'):
    """Generate comprehensive report about GDSII file."""
    lib = gdspy.GdsLibrary(infile=gds_file)
    
    with open(output_txt, 'w') as f:
        f.write(f"GDSII File Report: {gds_file}\n")
        f.write("=" * 60 + "\n\n")
        
        f.write(f"Library Name: {lib.name}\n")
        f.write(f"Unit: {lib.unit}\n")
        f.write(f"Precision: {lib.precision}\n")
        f.write(f"Total Cells: {len(lib.cells)}\n\n")
        
        # Top-level cells
        top_cells = lib.top_level()
        f.write(f"Top-Level Cells ({len(top_cells)}):\n")
        for cell in top_cells:
            f.write(f"  - {cell.name}\n")
        f.write("\n")
        
        # Layer summary
        all_layers = set()
        for cell in lib.cells.values():
            for element in cell.elements:
                if hasattr(element, 'layer'):
                    all_layers.add((element.layer, element.datatype))
        
        f.write(f"Layers Used ({len(all_layers)}):\n")
        for layer, datatype in sorted(all_layers):
            f.write(f"  Layer {layer}, Datatype {datatype}\n")
        f.write("\n")
        
        # Cell details
        f.write("Cell Details:\n")
        for name, cell in sorted(lib.cells.items()):
            f.write(f"\n  Cell: {name}\n")
            f.write(f"    Elements: {len(cell.elements)}\n")
            f.write(f"    References: {len(cell.references)}\n")
            
            bbox = cell.get_bounding_box()
            if bbox:
                width = bbox[1][0] - bbox[0][0]
                height = bbox[1][1] - bbox[0][1]
                f.write(f"    Bounding Box: ({bbox[0][0]:.2f}, {bbox[0][1]:.2f}) to ({bbox[1][0]:.2f}, {bbox[1][1]:.2f})\n")
                f.write(f"    Size: {width:.2f} x {height:.2f}\n")
    
    print(f"Report generated: {output_txt}")
```

## Best Practices

1. **Always Check Units and Precision**: GDSII files can have different database units. Always check `lib.unit` and `lib.precision`.

2. **Handle Large Files Carefully**: For very large GDSII files, consider processing in chunks or using streaming methods.

3. **Preserve Hierarchy**: When modifying designs, maintain cell hierarchy to keep file size manageable.

4. **Layer Naming**: Use consistent layer numbering schemes. Document your layer stack.

5. **Validation**: Always validate output files with a GDSII viewer (like KLayout) after programmatic generation.

6. **Backup**: Keep backups before modifying original GDS files.

## Troubleshooting

**Issue: File won't open**
- Check file format (GDS vs OASIS)
- Verify file isn't corrupted
- Check if file uses features not supported by library

**Issue: Missing geometries after conversion**
- Check layer numbers in source and destination
- Verify precision and units match
- Check if elements are outside the visible area

**Issue: Performance problems**
- Use gdstk instead of gdspy for large files
- Flatten hierarchy if needed
- Process layers individually

## Reference

For more advanced features:
- **gdspy documentation**: https://gdspy.readthedocs.io/
- **gdstk documentation**: https://heitzmann.github.io/gdstk/
- **GDSII format specification**: See `references/gdsii_format.md`
- **Common workflows**: See `references/workflows.md`
- **EDA tool integration**: See `references/eda_integration.md`

## Quick Reference Table

| Task | Library | Code |
|------|---------|------|
| Read GDS | gdspy | `lib = gdspy.GdsLibrary(infile='file.gds')` |
| Write GDS | gdspy | `lib.write_gds('output.gds')` |
| Create cell | gdspy | `cell = lib.new_cell('NAME')` |
| Add rectangle | gdspy | `cell.add(gdspy.Rectangle((x1,y1), (x2,y2), layer=n))` |
| Boolean ops | gdspy | `gdspy.boolean(poly1, poly2, 'or', layer=n)` |
| Flatten | gdspy | `cell.flatten()` |
| Get area | gdspy | `gdspy.polygon_area(polygon)` |
| Extract layers | gdspy | `cell.get_polygons(by_spec=True)` |
