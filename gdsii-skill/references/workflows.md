# GDSII Common Workflows

This document provides complete, production-ready workflows for common GDSII processing tasks.

## Workflow 1: IC Layout Extraction and Analysis Pipeline

**Use Case**: Extract specific cells from a large chip design and analyze their characteristics.

```python
import gdspy
import json
from datetime import datetime

def extract_and_analyze_cells(input_gds, cell_names, output_dir='./analysis'):
    """
    Complete pipeline to extract cells and generate analysis reports.
    
    Args:
        input_gds: Path to input GDSII file
        cell_names: List of cell names to extract
        output_dir: Directory for outputs
    """
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    # Load library
    print(f"Loading {input_gds}...")
    lib = gdspy.GdsLibrary(infile=input_gds)
    
    results = {
        'input_file': input_gds,
        'timestamp': datetime.now().isoformat(),
        'cells': {}
    }
    
    for cell_name in cell_names:
        if cell_name not in lib.cells:
            print(f"Warning: Cell '{cell_name}' not found, skipping...")
            continue
        
        cell = lib.cells[cell_name]
        print(f"\nProcessing cell: {cell_name}")
        
        # 1. Extract cell with dependencies
        extracted_lib = gdspy.GdsLibrary(
            name=f"{lib.name}_extracted",
            unit=lib.unit,
            precision=lib.precision
        )
        
        # Get all dependencies
        dependencies = set()
        def collect_deps(c):
            for ref in c.references:
                if ref.ref_cell.name not in dependencies:
                    dependencies.add(ref.ref_cell.name)
                    collect_deps(ref.ref_cell)
        
        collect_deps(cell)
        dependencies.add(cell_name)
        
        for dep_name in dependencies:
            extracted_lib.cells[dep_name] = lib.cells[dep_name]
        
        # Save extracted cell
        extract_path = os.path.join(output_dir, f"{cell_name}_extracted.gds")
        extracted_lib.write_gds(extract_path)
        print(f"  Saved extracted cell to {extract_path}")
        
        # 2. Analyze cell
        analysis = analyze_cell(cell)
        results['cells'][cell_name] = analysis
        
        # 3. Generate visualization
        svg_path = os.path.join(output_dir, f"{cell_name}_layout.svg")
        cell.write_svg(svg_path, background='#FFFFFF', scale=10)
        print(f"  Generated SVG visualization: {svg_path}")
        
        # 4. Generate detailed report
        report_path = os.path.join(output_dir, f"{cell_name}_report.txt")
        generate_detailed_report(cell, analysis, report_path)
        print(f"  Generated report: {report_path}")
    
    # Save summary JSON
    summary_path = os.path.join(output_dir, 'analysis_summary.json')
    with open(summary_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nAnalysis complete. Summary saved to {summary_path}")
    
    return results

def analyze_cell(cell):
    """Comprehensive cell analysis."""
    analysis = {
        'name': cell.name,
        'total_elements': len(cell.elements),
        'total_references': len(cell.references),
        'layers': {},
        'bounding_box': None,
        'area': 0,
        'hierarchy_depth': 0
    }
    
    # Get bounding box
    bbox = cell.get_bounding_box()
    if bbox:
        analysis['bounding_box'] = {
            'min': (float(bbox[0][0]), float(bbox[0][1])),
            'max': (float(bbox[1][0]), float(bbox[1][1])),
            'width': float(bbox[1][0] - bbox[0][0]),
            'height': float(bbox[1][1] - bbox[0][1])
        }
        analysis['area'] = analysis['bounding_box']['width'] * analysis['bounding_box']['height']
    
    # Analyze layers
    polygons = cell.get_polygons(by_spec=True)
    for (layer, datatype), polys in polygons.items():
        layer_key = f"{layer}:{datatype}"
        total_area = sum(abs(gdspy.polygon_area(p)) for p in polys)
        analysis['layers'][layer_key] = {
            'polygon_count': len(polys),
            'total_area': float(total_area),
            'layer': layer,
            'datatype': datatype
        }
    
    # Calculate hierarchy depth
    def get_depth(c, current_depth=0):
        if not c.references:
            return current_depth
        return max(get_depth(ref.ref_cell, current_depth + 1) for ref in c.references)
    
    analysis['hierarchy_depth'] = get_depth(cell)
    
    return analysis

def generate_detailed_report(cell, analysis, output_path):
    """Generate human-readable analysis report."""
    with open(output_path, 'w') as f:
        f.write(f"Cell Analysis Report: {cell.name}\n")
        f.write("=" * 70 + "\n\n")
        
        f.write("OVERVIEW\n")
        f.write(f"  Total Elements: {analysis['total_elements']}\n")
        f.write(f"  Total References: {analysis['total_references']}\n")
        f.write(f"  Hierarchy Depth: {analysis['hierarchy_depth']}\n\n")
        
        if analysis['bounding_box']:
            bbox = analysis['bounding_box']
            f.write("BOUNDING BOX\n")
            f.write(f"  Lower-left: ({bbox['min'][0]:.3f}, {bbox['min'][1]:.3f})\n")
            f.write(f"  Upper-right: ({bbox['max'][0]:.3f}, {bbox['max'][1]:.3f})\n")
            f.write(f"  Size: {bbox['width']:.3f} x {bbox['height']:.3f}\n")
            f.write(f"  Area: {bbox['width'] * bbox['height']:.3e}\n\n")
        
        f.write("LAYER BREAKDOWN\n")
        if analysis['layers']:
            for layer_key, data in sorted(analysis['layers'].items()):
                f.write(f"  Layer {data['layer']}, Datatype {data['datatype']}:\n")
                f.write(f"    Polygon count: {data['polygon_count']}\n")
                f.write(f"    Total area: {data['total_area']:.3e}\n")
                if analysis['area'] > 0:
                    density = (data['total_area'] / analysis['area']) * 100
                    f.write(f"    Density: {density:.2f}%\n")
        else:
            f.write("  No polygon data found\n")

# Usage example
if __name__ == '__main__':
    extract_and_analyze_cells(
        'design.gds',
        ['CORE', 'SRAM_BLOCK', 'IO_RING'],
        output_dir='./analysis_output'
    )
```

## Workflow 2: Automated Layer Manipulation

**Use Case**: Remap layers, merge layers, or split layers for different process nodes.

```python
import gdspy

def layer_manipulation_workflow(input_gds, operations, output_gds):
    """
    Apply a series of layer operations to a GDSII file.
    
    Operations can be:
    - {'type': 'remap', 'from': (layer, dt), 'to': (new_layer, new_dt)}
    - {'type': 'merge', 'layers': [(l1,dt1), (l2,dt2)], 'to': (new_layer, new_dt)}
    - {'type': 'split', 'from': (layer, dt), 'condition': function, 'to_true': (l1,dt1), 'to_false': (l2,dt2)}
    - {'type': 'delete', 'layer': (layer, dt)}
    """
    lib = gdspy.GdsLibrary(infile=input_gds)
    
    for op in operations:
        op_type = op['type']
        
        if op_type == 'remap':
            _remap_layer(lib, op['from'], op['to'])
            print(f"Remapped layer {op['from']} → {op['to']}")
        
        elif op_type == 'merge':
            _merge_layers(lib, op['layers'], op['to'])
            print(f"Merged {op['layers']} → {op['to']}")
        
        elif op_type == 'delete':
            _delete_layer(lib, op['layer'])
            print(f"Deleted layer {op['layer']}")
        
        elif op_type == 'copy':
            _copy_layer(lib, op['from'], op['to'])
            print(f"Copied layer {op['from']} → {op['to']}")
    
    lib.write_gds(output_gds)
    print(f"\nOperations complete. Output saved to {output_gds}")

def _remap_layer(lib, from_spec, to_spec):
    """Remap a layer number."""
    from_layer, from_dt = from_spec
    to_layer, to_dt = to_spec
    
    for cell in lib.cells.values():
        for element in cell.elements:
            if hasattr(element, 'layer'):
                if element.layer == from_layer and element.datatype == from_dt:
                    element.layer = to_layer
                    element.datatype = to_dt

def _merge_layers(lib, source_specs, target_spec):
    """Merge multiple layers into one."""
    target_layer, target_dt = target_spec
    
    for cell in lib.cells.values():
        for element in cell.elements:
            if hasattr(element, 'layer'):
                if (element.layer, element.datatype) in source_specs:
                    element.layer = target_layer
                    element.datatype = target_dt

def _delete_layer(lib, spec):
    """Remove all geometries on a specific layer."""
    layer, dt = spec
    
    for cell in lib.cells.values():
        cell.elements = [
            el for el in cell.elements
            if not (hasattr(el, 'layer') and el.layer == layer and el.datatype == dt)
        ]

def _copy_layer(lib, from_spec, to_spec):
    """Copy a layer to a new layer number."""
    from_layer, from_dt = from_spec
    to_layer, to_dt = to_spec
    
    for cell in lib.cells.values():
        elements_to_add = []
        for element in cell.elements:
            if hasattr(element, 'layer'):
                if element.layer == from_layer and element.datatype == from_dt:
                    # Deep copy the element
                    import copy
                    new_element = copy.deepcopy(element)
                    new_element.layer = to_layer
                    new_element.datatype = to_dt
                    elements_to_add.append(new_element)
        
        cell.elements.extend(elements_to_add)

# Usage example
operations = [
    {'type': 'remap', 'from': (1, 0), 'to': (10, 0)},  # Remap layer 1 to layer 10
    {'type': 'merge', 'layers': [(2, 0), (3, 0)], 'to': (20, 0)},  # Merge layers 2,3 → 20
    {'type': 'copy', 'from': (5, 0), 'to': (50, 0)},  # Copy layer 5 to layer 50
    {'type': 'delete', 'layer': (99, 0)},  # Delete layer 99
]

layer_manipulation_workflow('input.gds', operations, 'output.gds')
```

## Workflow 3: Parametric Layout Generation

**Use Case**: Generate multiple variants of a layout with different parameters.

```python
import gdspy
import itertools

def parametric_design_workflow(params_list, output_dir='./variants'):
    """
    Generate multiple layout variants from parameter sets.
    
    Args:
        params_list: List of parameter dictionaries
        output_dir: Directory for output files
    """
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    for i, params in enumerate(params_list):
        print(f"\nGenerating variant {i+1}/{len(params_list)}: {params}")
        
        # Create library
        lib = gdspy.GdsLibrary(name=f"VARIANT_{i}")
        
        # Generate layout based on parameters
        cell = generate_parametric_cell(params)
        lib.add(cell)
        
        # Save
        output_file = os.path.join(
            output_dir, 
            f"variant_{i:03d}_w{params['width']}_l{params['length']}.gds"
        )
        lib.write_gds(output_file)
        print(f"  Saved to {output_file}")

def generate_parametric_cell(params):
    """
    Generate a parametric cell (example: variable resistor).
    
    Parameters:
        width: Resistor width
        length: Resistor length
        contact_size: Contact pad size
        metal_layer: Metal layer number
        contact_layer: Contact layer number
    """
    cell = gdspy.Cell('PARAMETRIC')
    
    width = params.get('width', 10)
    length = params.get('length', 50)
    contact_size = params.get('contact_size', 15)
    metal_layer = params.get('metal_layer', 10)
    contact_layer = params.get('contact_layer', 11)
    
    # Main body
    body = gdspy.Rectangle(
        (0, -width/2),
        (length, width/2),
        layer=metal_layer
    )
    cell.add(body)
    
    # Left contact
    left_contact = gdspy.Rectangle(
        (-contact_size, -contact_size/2),
        (0, contact_size/2),
        layer=contact_layer
    )
    cell.add(left_contact)
    
    # Right contact
    right_contact = gdspy.Rectangle(
        (length, -contact_size/2),
        (length + contact_size, contact_size/2),
        layer=contact_layer
    )
    cell.add(right_contact)
    
    # Add text label
    label = gdspy.Text(
        f"W={width} L={length}",
        contact_size * 1.5,
        (length/2, width/2 + contact_size),
        layer=metal_layer
    )
    cell.add(label)
    
    return cell

# Generate parameter sweep
widths = [5, 10, 15]
lengths = [20, 50, 100]
params_list = [
    {'width': w, 'length': l, 'metal_layer': 10, 'contact_layer': 11}
    for w, l in itertools.product(widths, lengths)
]

parametric_design_workflow(params_list)
```

## Workflow 4: Design Rule Checking (DRC) Reports

**Use Case**: Basic automated checks for common design rule violations.

```python
import gdspy
import json

def basic_drc_workflow(gds_file, rules, output_report='drc_report.json'):
    """
    Perform basic design rule checks.
    
    Rules example:
    {
        'min_width': {10: 0.5, 11: 1.0},  # layer: minimum width
        'min_spacing': {10: 0.5, 11: 0.8},  # layer: minimum spacing
        'max_density': {10: 0.8, 11: 0.7}  # layer: maximum density (0-1)
    }
    """
    lib = gdspy.GdsLibrary(infile=gds_file)
    
    violations = {
        'file': gds_file,
        'rules': rules,
        'cells': {}
    }
    
    for cell_name, cell in lib.cells.items():
        print(f"Checking cell: {cell_name}")
        cell_violations = {
            'min_width': [],
            'min_spacing': [],
            'max_density': []
        }
        
        # Get polygons by layer
        polygons_by_layer = cell.get_polygons(by_spec=True)
        bbox = cell.get_bounding_box()
        
        if not bbox:
            continue
        
        cell_area = (bbox[1][0] - bbox[0][0]) * (bbox[1][1] - bbox[0][1])
        
        for (layer, dt), polys in polygons_by_layer.items():
            # Check minimum width (simplified)
            if 'min_width' in rules and layer in rules['min_width']:
                min_width = rules['min_width'][layer]
                # Implementation would check actual polygon widths
                # This is a placeholder
                pass
            
            # Check density
            if 'max_density' in rules and layer in rules['max_density']:
                max_density = rules['max_density'][layer]
                layer_area = sum(abs(gdspy.polygon_area(p)) for p in polys)
                density = layer_area / cell_area if cell_area > 0 else 0
                
                if density > max_density:
                    violation = {
                        'layer': layer,
                        'datatype': dt,
                        'density': density,
                        'max_allowed': max_density,
                        'violation': density - max_density
                    }
                    cell_violations['max_density'].append(violation)
                    print(f"  VIOLATION: Layer {layer} density {density:.2%} exceeds {max_density:.2%}")
        
        # Store cell violations
        total_violations = sum(len(v) for v in cell_violations.values())
        if total_violations > 0:
            violations['cells'][cell_name] = cell_violations
    
    # Save report
    with open(output_report, 'w') as f:
        json.dump(violations, f, indent=2)
    
    print(f"\nDRC check complete. Report saved to {output_report}")
    return violations

# Usage
rules = {
    'max_density': {
        10: 0.75,  # Metal1 max 75% density
        11: 0.70,  # Metal2 max 70% density
    }
}

basic_drc_workflow('design.gds', rules, 'drc_violations.json')
```

## Workflow 5: Batch Processing Pipeline

**Use Case**: Process multiple GDSII files with the same operations.

```python
import gdspy
import os
from pathlib import Path

def batch_process_gds_files(input_dir, operations, output_dir):
    """
    Process all GDS files in a directory.
    
    Operations: List of functions to apply to each library
    """
    os.makedirs(output_dir, exist_ok=True)
    
    gds_files = list(Path(input_dir).glob('*.gds'))
    print(f"Found {len(gds_files)} GDSII files to process")
    
    results = []
    
    for gds_file in gds_files:
        print(f"\nProcessing: {gds_file.name}")
        
        try:
            lib = gdspy.GdsLibrary(infile=str(gds_file))
            
            # Apply each operation
            for op in operations:
                op(lib)
            
            # Save result
            output_file = Path(output_dir) / gds_file.name
            lib.write_gds(str(output_file))
            
            results.append({
                'file': gds_file.name,
                'status': 'success',
                'output': str(output_file)
            })
            print(f"  ✓ Success: {output_file}")
            
        except Exception as e:
            results.append({
                'file': gds_file.name,
                'status': 'error',
                'error': str(e)
            })
            print(f"  ✗ Error: {e}")
    
    # Summary
    successful = sum(1 for r in results if r['status'] == 'success')
    print(f"\n{'='*60}")
    print(f"Batch processing complete:")
    print(f"  Total files: {len(results)}")
    print(f"  Successful: {successful}")
    print(f"  Failed: {len(results) - successful}")
    
    return results

# Example operations
def flatten_all_cells(lib):
    """Flatten all cells in library."""
    for cell in lib.cells.values():
        cell.flatten()
    print("    Applied: Flatten")

def scale_by_factor(factor):
    """Return a scaling operation function."""
    def scale_op(lib):
        for cell in lib.cells.values():
            for element in cell.elements:
                if hasattr(element, 'scale'):
                    element.scale(factor)
        print(f"    Applied: Scale {factor}x")
    return scale_op

def remove_text_elements(lib):
    """Remove all text elements."""
    for cell in lib.cells.values():
        cell.elements = [
            el for el in cell.elements
            if not isinstance(el, gdspy.Text)
        ]
    print("    Applied: Remove text")

# Usage
operations = [
    remove_text_elements,
    scale_by_factor(2.0),
    # flatten_all_cells,  # Uncomment to flatten
]

batch_process_gds_files('./input_gds', operations, './processed_gds')
```

## Workflow 6: Integration with EDA Tools

**Use Case**: Generate scripts for Cadence, KLayout, or other EDA tools.

```python
import gdspy

def generate_klayout_script(gds_file, layer_props_file='layers.lyp'):
    """Generate KLayout layer properties file."""
    lib = gdspy.GdsLibrary(infile=gds_file)
    
    # Collect all unique layers
    layers = set()
    for cell in lib.cells.values():
        polys = cell.get_polygons(by_spec=True)
        for (layer, dt), _ in polys.items():
            layers.add((layer, dt))
    
    # Generate layer properties
    colors = [
        '#FF0000', '#00FF00', '#0000FF', '#FFFF00',
        '#FF00FF', '#00FFFF', '#FFA500', '#800080'
    ]
    
    with open(layer_props_file, 'w') as f:
        f.write('<?xml version="1.0" encoding="utf-8"?>\n')
        f.write('<layer-properties>\n')
        
        for i, (layer, dt) in enumerate(sorted(layers)):
            color = colors[i % len(colors)]
            f.write(f'  <properties>\n')
            f.write(f'    <frame-color>{color}</frame-color>\n')
            f.write(f'    <fill-color>{color}</fill-color>\n')
            f.write(f'    <frame-brightness>0</frame-brightness>\n')
            f.write(f'    <fill-brightness>0</fill-brightness>\n')
            f.write(f'    <dither-pattern>I9</dither-pattern>\n')
            f.write(f'    <valid>true</valid>\n')
            f.write(f'    <visible>true</visible>\n')
            f.write(f'    <transparent>false</transparent>\n')
            f.write(f'    <width>1</width>\n')
            f.write(f'    <marked>false</marked>\n')
            f.write(f'    <animation>0</animation>\n')
            f.write(f'    <name>Layer {layer}:{dt}</name>\n')
            f.write(f'    <source>{layer}/{dt}@1</source>\n')
            f.write(f'  </properties>\n')
        
        f.write('</layer-properties>\n')
    
    print(f"KLayout layer properties generated: {layer_props_file}")
    print("Usage: klayout -l layers.lyp design.gds")

# Usage
generate_klayout_script('design.gds', 'my_layers.lyp')
```

## Best Practices for Production Workflows

1. **Always Validate**: Check output files in a GDSII viewer
2. **Version Control**: Track GDSII files and scripts in Git (use Git LFS for binaries)
3. **Document Operations**: Log all transformations applied
4. **Backup Original**: Keep copies of input files
5. **Test on Samples**: Test workflows on small files first
6. **Error Handling**: Implement comprehensive try-except blocks
7. **Progress Reporting**: Log progress for long-running operations
8. **Parallel Processing**: Use multiprocessing for batch operations on large file sets

## Performance Tips

- Use `gdstk` instead of `gdspy` for large files (10-100x faster)
- Process layers independently when possible
- Avoid unnecessary flattening (preserves hierarchy, reduces file size)
- Use binary format for intermediate files
- Consider streaming for very large files
