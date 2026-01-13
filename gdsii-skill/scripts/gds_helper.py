#!/usr/bin/env python3
"""
GDSII Helper Script
Common operations for GDSII file manipulation
"""

import argparse
import sys
import json

try:
    import gdspy
    USE_GDSPY = True
except ImportError:
    try:
        import gdstk
        USE_GDSPY = False
        print("Note: Using gdstk (gdspy not available)")
    except ImportError:
        print("Error: Neither gdspy nor gdstk is installed.")
        print("Run: pip install gdstk --break-system-packages")
        sys.exit(1)


def inspect_gds(filename, verbose=False):
    """Inspect GDSII file and print summary."""
    lib = gdspy.GdsLibrary(infile=filename)
    
    print(f"\n{'='*70}")
    print(f"GDSII File: {filename}")
    print(f"{'='*70}")
    print(f"Library Name: {lib.name}")
    print(f"Unit: {lib.unit} (user), {lib.precision} (database)")
    print(f"Total Cells: {len(lib.cells)}")
    
    # Top-level cells
    top_cells = lib.top_level()
    print(f"\nTop-Level Cells ({len(top_cells)}):")
    for cell in top_cells:
        print(f"  • {cell.name}")
    
    # Collect layers
    all_layers = set()
    for cell in lib.cells.values():
        for element in cell.elements:
            if hasattr(element, 'layer'):
                all_layers.add((element.layer, element.datatype))
    
    print(f"\nLayers Used ({len(all_layers)}):")
    for layer, dt in sorted(all_layers):
        print(f"  Layer {layer:3d}, Datatype {dt:2d}")
    
    if verbose:
        print(f"\nDetailed Cell Information:")
        for name, cell in sorted(lib.cells.items()):
            print(f"\n  Cell: {name}")
            print(f"    Elements: {len(cell.elements)}")
            print(f"    References: {len(cell.references)}")
            bbox = cell.get_bounding_box()
            if bbox:
                width = bbox[1][0] - bbox[0][0]
                height = bbox[1][1] - bbox[0][1]
                print(f"    Size: {width:.2f} x {height:.2f}")


def extract_cell(input_file, cell_name, output_file):
    """Extract specific cell and dependencies to new file."""
    lib = gdspy.GdsLibrary(infile=input_file)
    
    if cell_name not in lib.cells:
        print(f"Error: Cell '{cell_name}' not found in {input_file}")
        print("Available cells:")
        for name in lib.cells:
            print(f"  - {name}")
        return False
    
    new_lib = gdspy.GdsLibrary(name=lib.name, unit=lib.unit, precision=lib.precision)
    
    # Collect all dependencies
    cells_to_copy = {cell_name}
    
    def get_deps(cell):
        for ref in cell.references:
            if ref.ref_cell.name not in cells_to_copy:
                cells_to_copy.add(ref.ref_cell.name)
                get_deps(ref.ref_cell)
    
    get_deps(lib.cells[cell_name])
    
    # Copy cells
    for name in cells_to_copy:
        new_lib.cells[name] = lib.cells[name]
    
    new_lib.write_gds(output_file)
    print(f"✓ Extracted {len(cells_to_copy)} cells to {output_file}")
    return True


def extract_layer(input_file, layer, datatype, output_file):
    """Extract specific layer to new file."""
    lib = gdspy.GdsLibrary(infile=input_file)
    new_lib = gdspy.GdsLibrary(name=lib.name, unit=lib.unit, precision=lib.precision)
    
    for cell_name, cell in lib.cells.items():
        new_cell = new_lib.new_cell(cell_name)
        
        for element in cell.elements:
            match = False
            if hasattr(element, 'layer') and element.layer == layer:
                if element.datatype == datatype:
                    match = True
            elif hasattr(element, 'layers') and layer in element.layers:
                idx = element.layers.index(layer)
                if element.datatypes[idx] == datatype:
                    match = True
            
            if match:
                new_cell.add(element)
    
    new_lib.write_gds(output_file)
    print(f"✓ Extracted layer {layer}:{datatype} to {output_file}")


def remap_layers(input_file, mapping_file, output_file):
    """Remap layers according to JSON mapping file."""
    lib = gdspy.GdsLibrary(infile=input_file)
    
    with open(mapping_file, 'r') as f:
        mapping = json.load(f)
    
    # Convert string keys to tuples
    layer_map = {}
    for key, value in mapping.items():
        if ':' in key:
            from_layer, from_dt = map(int, key.split(':'))
        else:
            from_layer, from_dt = int(key), 0
        
        if isinstance(value, list):
            to_layer, to_dt = value
        elif ':' in str(value):
            to_layer, to_dt = map(int, str(value).split(':'))
        else:
            to_layer, to_dt = int(value), 0
        
        layer_map[(from_layer, from_dt)] = (to_layer, to_dt)
    
    # Apply mapping
    for cell in lib.cells.values():
        for element in cell.elements:
            if hasattr(element, 'layer'):
                key = (element.layer, element.datatype)
                if key in layer_map:
                    element.layer, element.datatype = layer_map[key]
    
    lib.write_gds(output_file)
    print(f"✓ Remapped {len(layer_map)} layers, saved to {output_file}")


def merge_files(input_files, output_file, spacing=1000):
    """Merge multiple GDSII files."""
    lib = gdspy.GdsLibrary()
    top_cell = lib.new_cell('MERGED')
    
    x_offset = 0
    
    for input_file in input_files:
        temp_lib = gdspy.GdsLibrary(infile=input_file)
        top_cells = temp_lib.top_level()
        
        if not top_cells:
            print(f"Warning: No top-level cells in {input_file}, skipping")
            continue
        
        cell = top_cells[0]
        
        # Rename if conflict
        original_name = cell.name
        counter = 1
        while cell.name in lib.cells:
            cell.name = f"{original_name}_{counter}"
            counter += 1
        
        # Add reference
        ref = gdspy.CellReference(cell, origin=(x_offset, 0))
        top_cell.add(ref)
        
        # Copy cell
        lib.cells[cell.name] = cell
        
        # Update offset
        bbox = cell.get_bounding_box()
        if bbox:
            x_offset += (bbox[1][0] - bbox[0][0]) + spacing
    
    lib.write_gds(output_file)
    print(f"✓ Merged {len(input_files)} files to {output_file}")


def calculate_area(input_file, layer=None, datatype=0):
    """Calculate total area by layer."""
    lib = gdspy.GdsLibrary(infile=input_file)
    
    layer_areas = {}
    
    for cell in lib.top_level():
        polygons = cell.get_polygons(by_spec=True)
        
        for spec, polys in polygons.items():
            if layer is not None and spec[0] != layer:
                continue
            if spec[1] != datatype:
                continue
            
            if spec not in layer_areas:
                layer_areas[spec] = 0
            
            for poly in polys:
                area = abs(gdspy.polygon_area(poly))
                layer_areas[spec] += area
    
    print("\nLayer Areas:")
    for (l, dt), area in sorted(layer_areas.items()):
        print(f"  Layer {l:3d}, Datatype {dt:2d}: {area:.3e} square units")


def main():
    parser = argparse.ArgumentParser(
        description='GDSII Helper Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Inspect a GDSII file
  %(prog)s inspect design.gds
  
  # Extract specific cell
  %(prog)s extract-cell design.gds MYCELL output.gds
  
  # Extract layer
  %(prog)s extract-layer design.gds 10 0 layer10.gds
  
  # Remap layers
  %(prog)s remap design.gds mapping.json remapped.gds
  
  # Merge files
  %(prog)s merge file1.gds file2.gds file3.gds -o merged.gds
  
  # Calculate area
  %(prog)s area design.gds -l 10
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Inspect command
    inspect_parser = subparsers.add_parser('inspect', help='Inspect GDSII file')
    inspect_parser.add_argument('input', help='Input GDSII file')
    inspect_parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    
    # Extract cell command
    extract_parser = subparsers.add_parser('extract-cell', help='Extract specific cell')
    extract_parser.add_argument('input', help='Input GDSII file')
    extract_parser.add_argument('cell', help='Cell name to extract')
    extract_parser.add_argument('output', help='Output GDSII file')
    
    # Extract layer command
    layer_parser = subparsers.add_parser('extract-layer', help='Extract specific layer')
    layer_parser.add_argument('input', help='Input GDSII file')
    layer_parser.add_argument('layer', type=int, help='Layer number')
    layer_parser.add_argument('datatype', type=int, help='Datatype number')
    layer_parser.add_argument('output', help='Output GDSII file')
    
    # Remap command
    remap_parser = subparsers.add_parser('remap', help='Remap layers')
    remap_parser.add_argument('input', help='Input GDSII file')
    remap_parser.add_argument('mapping', help='JSON mapping file')
    remap_parser.add_argument('output', help='Output GDSII file')
    
    # Merge command
    merge_parser = subparsers.add_parser('merge', help='Merge multiple files')
    merge_parser.add_argument('inputs', nargs='+', help='Input GDSII files')
    merge_parser.add_argument('-o', '--output', required=True, help='Output GDSII file')
    merge_parser.add_argument('-s', '--spacing', type=float, default=1000, help='Spacing between designs')
    
    # Area command
    area_parser = subparsers.add_parser('area', help='Calculate area by layer')
    area_parser.add_argument('input', help='Input GDSII file')
    area_parser.add_argument('-l', '--layer', type=int, help='Specific layer (optional)')
    area_parser.add_argument('-d', '--datatype', type=int, default=0, help='Datatype (default: 0)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        if args.command == 'inspect':
            inspect_gds(args.input, args.verbose)
        
        elif args.command == 'extract-cell':
            extract_cell(args.input, args.cell, args.output)
        
        elif args.command == 'extract-layer':
            extract_layer(args.input, args.layer, args.datatype, args.output)
        
        elif args.command == 'remap':
            remap_layers(args.input, args.mapping, args.output)
        
        elif args.command == 'merge':
            merge_files(args.inputs, args.output, args.spacing)
        
        elif args.command == 'area':
            calculate_area(args.input, args.layer, args.datatype)
    
    except Exception as e:
        print(f"\n✗ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
