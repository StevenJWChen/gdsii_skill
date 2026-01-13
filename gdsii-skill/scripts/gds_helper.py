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

try:
    import matplotlib
    matplotlib.use('Agg')  # Use non-interactive backend
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon as MplPolygon
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


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


def display_gds(input_file, output_image=None, cell_name=None, layers=None, show_bbox=True):
    """Display/visualize GDSII file and save as image."""
    if not MATPLOTLIB_AVAILABLE:
        print("Error: matplotlib not installed. Run: pip install matplotlib --break-system-packages")
        return False

    if USE_GDSPY:
        lib = gdspy.GdsLibrary(infile=input_file)

        # Get cell to display
        if cell_name:
            if cell_name not in lib.cells:
                print(f"Error: Cell '{cell_name}' not found")
                return False
            cell = lib.cells[cell_name]
        else:
            top_cells = lib.top_level()
            if not top_cells:
                print("Error: No top-level cells found")
                return False
            cell = top_cells[0]

        # Get all polygons
        polygons_by_spec = cell.get_polygons(by_spec=True)
    else:
        # Using gdstk
        lib = gdstk.read_gds(input_file)

        # Get cell to display
        if cell_name:
            cell = None
            for c in lib.cells:
                if c.name == cell_name:
                    cell = c
                    break
            if cell is None:
                print(f"Error: Cell '{cell_name}' not found")
                return False
        else:
            if not lib.cells:
                print("Error: No cells found")
                return False
            cell = lib.cells[0]

        # Get all polygons organized by layer
        polygons_by_spec = {}
        for poly in cell.polygons:
            spec = (poly.layer, poly.datatype)
            if spec not in polygons_by_spec:
                polygons_by_spec[spec] = []
            polygons_by_spec[spec].append(poly.points)

    # Create figure
    fig, ax = plt.subplots(figsize=(12, 12))

    # Define color map for layers
    colors = plt.cm.tab20(range(20))
    color_map = {}

    # Plot polygons by layer
    for spec, polys in sorted(polygons_by_spec.items()):
        layer, datatype = spec

        # Skip if layers filter is specified and this layer isn't in it
        if layers is not None and layer not in layers:
            continue

        # Assign color based on layer
        if layer not in color_map:
            color_map[layer] = colors[len(color_map) % len(colors)]
        color = color_map[layer]

        # Plot each polygon
        for poly in polys:
            polygon = MplPolygon(poly, facecolor=color, edgecolor='black',
                               linewidth=0.5, alpha=0.7, label=f'Layer {layer}')
            ax.add_patch(polygon)

    # Get bounding box
    if USE_GDSPY:
        bbox = cell.get_bounding_box()
    else:
        bbox = cell.bounding_box()

    if bbox is not None:
        # Set axis limits with some padding
        padding = max(bbox[1][0] - bbox[0][0], bbox[1][1] - bbox[0][1]) * 0.1
        ax.set_xlim(bbox[0][0] - padding, bbox[1][0] + padding)
        ax.set_ylim(bbox[0][1] - padding, bbox[1][1] + padding)

        # Show bounding box
        if show_bbox:
            ax.plot([bbox[0][0], bbox[1][0], bbox[1][0], bbox[0][0], bbox[0][0]],
                   [bbox[0][1], bbox[0][1], bbox[1][1], bbox[1][1], bbox[0][1]],
                   'r--', linewidth=2, label='Bounding Box')

    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)
    ax.set_xlabel('X (µm)', fontsize=12)
    ax.set_ylabel('Y (µm)', fontsize=12)
    ax.set_title(f'GDSII Layout: {cell.name}', fontsize=14, fontweight='bold')

    # Create legend with unique layers
    handles, labels = ax.get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    ax.legend(by_label.values(), by_label.keys(), loc='best', fontsize=10)

    # Save or show
    if output_image is None:
        output_image = input_file.replace('.gds', '.png')

    plt.tight_layout()
    plt.savefig(output_image, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"✓ Visualization saved to {output_image}")
    print(f"  Cell: {cell.name}")
    if bbox:
        print(f"  Size: {bbox[1][0] - bbox[0][0]:.2f} x {bbox[1][1] - bbox[0][1]:.2f} µm")
    print(f"  Layers: {len(set(spec[0] for spec in polygons_by_spec.keys()))}")

    return True


def crop_gds(input_file, output_file, x_min, y_min, x_max, y_max, cell_name=None):
    """Crop/cut a rectangular region from GDSII file."""
    if USE_GDSPY:
        lib = gdspy.GdsLibrary(infile=input_file)

        # Get source cell
        if cell_name:
            if cell_name not in lib.cells:
                print(f"Error: Cell '{cell_name}' not found")
                return False
            src_cell = lib.cells[cell_name]
        else:
            top_cells = lib.top_level()
            if not top_cells:
                print("Error: No top-level cells found")
                return False
            src_cell = top_cells[0]

        # Create new library and cell
        new_lib = gdspy.GdsLibrary(name=lib.name + '_CROP', unit=lib.unit, precision=lib.precision)
        new_cell = new_lib.new_cell(src_cell.name + '_CROP')

        # Get all polygons
        polygons_by_spec = src_cell.get_polygons(by_spec=True)

        # Crop rectangle
        crop_rect = gdspy.Rectangle((x_min, y_min), (x_max, y_max))

        cropped_count = 0
        for spec, polys in polygons_by_spec.items():
            layer, datatype = spec
            for poly in polys:
                poly_obj = gdspy.Polygon(poly, layer=layer, datatype=datatype)

                # Perform boolean intersection with crop rectangle
                try:
                    result = gdspy.boolean(poly_obj, crop_rect, 'and',
                                          layer=layer, datatype=datatype)
                    if result is not None:
                        new_cell.add(result)
                        cropped_count += 1
                except:
                    # If polygon doesn't intersect, skip it
                    pass

        new_lib.write_gds(output_file)

    else:
        # Using gdstk
        lib = gdstk.read_gds(input_file)

        # Get source cell
        if cell_name:
            src_cell = None
            for c in lib.cells:
                if c.name == cell_name:
                    src_cell = c
                    break
            if src_cell is None:
                print(f"Error: Cell '{cell_name}' not found")
                return False
        else:
            if not lib.cells:
                print("Error: No cells found")
                return False
            src_cell = lib.cells[0]

        # Create new library and cell
        new_lib = gdstk.Library(name=lib.name + '_CROP')
        new_cell = new_lib.new_cell(src_cell.name + '_CROP')

        # Crop rectangle
        crop_rect = gdstk.rectangle((x_min, y_min), (x_max, y_max))

        cropped_count = 0
        for poly in src_cell.polygons:
            # Check if polygon intersects with crop region
            poly_bbox = [[poly.points[:, 0].min(), poly.points[:, 1].min()],
                        [poly.points[:, 0].max(), poly.points[:, 1].max()]]

            # Simple bounding box check first
            if (poly_bbox[1][0] >= x_min and poly_bbox[0][0] <= x_max and
                poly_bbox[1][1] >= y_min and poly_bbox[0][1] <= y_max):

                # Perform boolean intersection
                try:
                    result = gdstk.boolean(poly, crop_rect, 'and',
                                          layer=poly.layer, datatype=poly.datatype)
                    if result:
                        for r in result:
                            new_cell.add(r)
                        cropped_count += 1
                except:
                    pass

        new_lib.write_gds(output_file)

    print(f"✓ Cropped region saved to {output_file}")
    print(f"  Source cell: {src_cell.name}")
    print(f"  Crop region: ({x_min}, {y_min}) to ({x_max}, {y_max})")
    print(f"  Size: {x_max - x_min:.2f} x {y_max - y_min:.2f} µm")
    print(f"  Polygons in cropped region: {cropped_count}")

    return True


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

  # Display/visualize layout
  %(prog)s display design.gds -o layout.png

  # Crop/cut region
  %(prog)s crop design.gds output.gds --bbox 0 0 100 100
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

    # Display command
    display_parser = subparsers.add_parser('display', help='Display/visualize GDSII layout')
    display_parser.add_argument('input', help='Input GDSII file')
    display_parser.add_argument('-o', '--output', help='Output image file (PNG)')
    display_parser.add_argument('-c', '--cell', help='Specific cell name to display')
    display_parser.add_argument('-l', '--layers', type=int, nargs='+', help='Specific layers to display')
    display_parser.add_argument('--no-bbox', action='store_true', help='Do not show bounding box')

    # Crop command
    crop_parser = subparsers.add_parser('crop', help='Crop/cut a rectangular region from layout')
    crop_parser.add_argument('input', help='Input GDSII file')
    crop_parser.add_argument('output', help='Output GDSII file')
    crop_parser.add_argument('--bbox', type=float, nargs=4, required=True,
                           metavar=('X_MIN', 'Y_MIN', 'X_MAX', 'Y_MAX'),
                           help='Bounding box coordinates (x_min y_min x_max y_max)')
    crop_parser.add_argument('-c', '--cell', help='Specific cell name to crop')

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

        elif args.command == 'display':
            display_gds(args.input, args.output, args.cell, args.layers, not args.no_bbox)

        elif args.command == 'crop':
            x_min, y_min, x_max, y_max = args.bbox
            crop_gds(args.input, args.output, x_min, y_min, x_max, y_max, args.cell)

    except Exception as e:
        print(f"\n✗ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
