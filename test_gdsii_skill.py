#!/usr/bin/env python3
"""
Test suite for the GDSII Agent Skill
Tests basic GDSII operations using gdstk
"""

import gdstk
import os
import sys
import subprocess

def test_create_simple_gds():
    """Test 1: Create a simple GDSII file"""
    print("\n" + "="*70)
    print("TEST 1: Creating a simple GDSII file")
    print("="*70)

    # Create a library
    lib = gdstk.Library(name='TEST_LIBRARY', unit=1e-6, precision=1e-9)

    # Create a cell
    cell = lib.new_cell('SIMPLE_CELL')

    # Add a rectangle (coordinates in micrometers)
    rect = gdstk.rectangle((0, 0), (10, 20), layer=0, datatype=0)
    cell.add(rect)

    # Add a polygon
    points = [(0, 0), (5, 0), (5, 10), (3, 10), (3, 5), (0, 5)]
    poly = gdstk.Polygon(points, layer=1, datatype=0)
    cell.add(poly)

    # Add a circle
    circle = gdstk.ellipse((15, 15), 5, layer=2, datatype=0)
    cell.add(circle)

    # Write to file
    lib.write_gds('test_simple.gds')

    # Verify file was created
    if os.path.exists('test_simple.gds'):
        size = os.path.getsize('test_simple.gds')
        print(f"✓ Created test_simple.gds ({size} bytes)")
        print(f"  Library: {lib.name}")
        print(f"  Unit: {lib.unit} m")
        print(f"  Precision: {lib.precision} m")
        print(f"  Cells: {len(lib.cells)}")
        return True
    else:
        print("✗ Failed to create file")
        return False


def test_read_and_inspect():
    """Test 2: Read and inspect a GDSII file"""
    print("\n" + "="*70)
    print("TEST 2: Reading and inspecting GDSII file")
    print("="*70)

    if not os.path.exists('test_simple.gds'):
        print("✗ test_simple.gds not found")
        return False

    # Read the file
    lib = gdstk.read_gds('test_simple.gds')

    print(f"Library name: {lib.name}")
    print(f"Number of cells: {len(lib.cells)}")

    # Iterate through cells (cells is a list in gdstk)
    for cell in lib.cells:
        print(f"\nCell: {cell.name}")
        print(f"  Polygons: {len(cell.polygons)}")
        print(f"  Paths: {len(cell.paths)}")
        print(f"  References: {len(cell.references)}")

        # Get bounding box
        bbox = cell.bounding_box()
        if bbox is not None:
            width = bbox[1][0] - bbox[0][0]
            height = bbox[1][1] - bbox[0][1]
            print(f"  Bounding box: ({bbox[0][0]:.2f}, {bbox[0][1]:.2f}) to ({bbox[1][0]:.2f}, {bbox[1][1]:.2f})")
            print(f"  Size: {width:.2f} x {height:.2f} µm")

        # List layers
        layers = set()
        for poly in cell.polygons:
            layers.add((poly.layer, poly.datatype))
        print(f"  Layers used: {sorted(layers)}")

    print("✓ Successfully read and inspected file")
    return True


def test_extract_layer():
    """Test 3: Extract a specific layer"""
    print("\n" + "="*70)
    print("TEST 3: Extracting specific layer")
    print("="*70)

    # Read source file
    src_lib = gdstk.read_gds('test_simple.gds')

    # Create new library for extracted layer
    new_lib = gdstk.Library(name='LAYER_EXTRACT', unit=1e-6, precision=1e-9)
    new_cell = new_lib.new_cell('LAYER_0')

    # Extract layer 0
    target_layer = 0
    for cell in src_lib.cells:
        for poly in cell.polygons:
            if poly.layer == target_layer:
                new_cell.add(poly)

    # Write extracted layer
    new_lib.write_gds('test_layer0.gds')

    if os.path.exists('test_layer0.gds'):
        print(f"✓ Extracted layer {target_layer} to test_layer0.gds")
        print(f"  Polygons extracted: {len(new_cell.polygons)}")
        return True
    else:
        print("✗ Failed to extract layer")
        return False


def test_create_parametric_cell():
    """Test 4: Create a parametric resistor cell"""
    print("\n" + "="*70)
    print("TEST 4: Creating parametric resistor")
    print("="*70)

    def create_resistor(width, length, layer=10):
        """Create a simple resistor layout"""
        cell = gdstk.Cell('RESISTOR')

        # Main resistor body
        body = gdstk.rectangle((0, -width/2), (length, width/2), layer=layer, datatype=0)
        cell.add(body)

        # Contact pads
        contact_size = width * 1.5
        pad_layer = layer + 1

        # Left contact
        left_pad = gdstk.rectangle(
            (-contact_size, -contact_size/2),
            (0, contact_size/2),
            layer=pad_layer,
            datatype=0
        )
        cell.add(left_pad)

        # Right contact
        right_pad = gdstk.rectangle(
            (length, -contact_size/2),
            (length + contact_size, contact_size/2),
            layer=pad_layer,
            datatype=0
        )
        cell.add(right_pad)

        return cell

    # Create library and resistor
    lib = gdstk.Library()
    resistor = create_resistor(width=5, length=50)
    lib.add(resistor)

    # Write to file
    lib.write_gds('test_resistor.gds')

    if os.path.exists('test_resistor.gds'):
        bbox = resistor.bounding_box()
        width = bbox[1][0] - bbox[0][0]
        height = bbox[1][1] - bbox[0][1]
        print(f"✓ Created parametric resistor")
        print(f"  Cell name: {resistor.name}")
        print(f"  Polygons: {len(resistor.polygons)}")
        print(f"  Size: {width:.2f} x {height:.2f} µm")
        return True
    else:
        print("✗ Failed to create resistor")
        return False


def test_area_calculation():
    """Test 5: Calculate polygon areas"""
    print("\n" + "="*70)
    print("TEST 5: Calculating polygon areas")
    print("="*70)

    lib = gdstk.read_gds('test_simple.gds')

    layer_areas = {}

    for cell in lib.cells:
        for poly in cell.polygons:
            layer = poly.layer
            area = poly.area()

            if layer not in layer_areas:
                layer_areas[layer] = 0
            layer_areas[layer] += area

    print("Layer areas (µm²):")
    for layer in sorted(layer_areas.keys()):
        print(f"  Layer {layer:2d}: {layer_areas[layer]:.2f} µm²")

    print("✓ Area calculation complete")
    return True


def test_merge_files():
    """Test 6: Merge multiple GDSII files"""
    print("\n" + "="*70)
    print("TEST 6: Merging GDSII files")
    print("="*70)

    # Create a new library for merged content
    merged_lib = gdstk.Library(name='MERGED')
    top_cell = merged_lib.new_cell('TOP')

    files_to_merge = ['test_simple.gds', 'test_resistor.gds']
    x_offset = 0
    spacing = 100  # 100 µm spacing

    for gds_file in files_to_merge:
        if not os.path.exists(gds_file):
            print(f"  Skipping {gds_file} (not found)")
            continue

        # Read file
        temp_lib = gdstk.read_gds(gds_file)

        # Get first cell (assuming it's the main cell)
        if len(temp_lib.cells) == 0:
            continue

        cell = temp_lib.cells[0]

        # Add to merged library
        merged_lib.add(cell)

        # Create reference with offset
        ref = gdstk.Reference(cell, origin=(x_offset, 0))
        top_cell.add(ref)

        # Update offset
        bbox = cell.bounding_box()
        if bbox is not None:
            x_offset += (bbox[1][0] - bbox[0][0]) + spacing

        print(f"  Added {gds_file} (offset: {x_offset - spacing:.0f} µm)")

    # Write merged file
    merged_lib.write_gds('test_merged.gds')

    if os.path.exists('test_merged.gds'):
        print(f"✓ Merged {len(files_to_merge)} files")
        print(f"  Total cells in merged file: {len(merged_lib.cells)}")
        return True
    else:
        print("✗ Failed to merge files")
        return False


def test_display_gds():
    """Test 7: Test display/visualization feature"""
    print("\n" + "="*70)
    print("TEST 7: Testing display/visualization feature")
    print("="*70)

    if not os.path.exists('test_simple.gds'):
        print("✗ test_simple.gds not found")
        return False

    # Test display using the gds_helper.py script
    import subprocess
    result = subprocess.run([
        'python3', 'gdsii-skill/scripts/gds_helper.py',
        'display', 'test_simple.gds',
        '-o', 'test_display_output.png'
    ], capture_output=True, text=True)

    if result.returncode != 0:
        print(f"✗ Display command failed: {result.stderr}")
        return False

    if os.path.exists('test_display_output.png'):
        size = os.path.getsize('test_display_output.png')
        print(f"✓ Display feature working")
        print(f"  Created test_display_output.png ({size} bytes)")
        return True
    else:
        print("✗ Display output file not created")
        return False


def test_crop_gds():
    """Test 8: Test crop/cut feature"""
    print("\n" + "="*70)
    print("TEST 8: Testing crop/cut feature")
    print("="*70)

    if not os.path.exists('test_simple.gds'):
        print("✗ test_simple.gds not found")
        return False

    # Test crop using the gds_helper.py script
    import subprocess
    result = subprocess.run([
        'python3', 'gdsii-skill/scripts/gds_helper.py',
        'crop', 'test_simple.gds', 'test_crop_output.gds',
        '--bbox', '5', '5', '15', '15'
    ], capture_output=True, text=True)

    if result.returncode != 0:
        print(f"✗ Crop command failed: {result.stderr}")
        return False

    if not os.path.exists('test_crop_output.gds'):
        print("✗ Crop output file not created")
        return False

    # Verify the cropped file
    lib = gdstk.read_gds('test_crop_output.gds')

    if len(lib.cells) == 0:
        print("✗ No cells in cropped file")
        return False

    cell = lib.cells[0]
    bbox = cell.bounding_box()

    print(f"✓ Crop feature working")
    print(f"  Created test_crop_output.gds")
    print(f"  Cell name: {cell.name}")
    if bbox:
        print(f"  Cropped size: {bbox[1][0] - bbox[0][0]:.2f} x {bbox[1][1] - bbox[0][1]:.2f} µm")
    print(f"  Polygons: {len(cell.polygons)}")

    return True


def test_skill_structure():
    """Test 9: Verify skill file structure"""
    print("\n" + "="*70)
    print("TEST 9: Verifying skill structure")
    print("="*70)

    skill_dir = "gdsii-skill"
    required_files = [
        "SKILL.md",
        "README.md",
        "scripts/gds_helper.py",
        "references/gdsii_format.md",
        "references/workflows.md",
        "references/eda_integration.md"
    ]

    all_present = True
    for file in required_files:
        path = os.path.join(skill_dir, file)
        if os.path.exists(path):
            size = os.path.getsize(path)
            print(f"  ✓ {file} ({size} bytes)")
        else:
            print(f"  ✗ {file} (missing)")
            all_present = False

    # Check SKILL.md metadata
    skill_md = os.path.join(skill_dir, "SKILL.md")
    if os.path.exists(skill_md):
        with open(skill_md, 'r') as f:
            content = f.read()
            if 'name: gdsii' in content:
                print("  ✓ SKILL.md has correct name metadata")
            else:
                print("  ✗ SKILL.md missing or incorrect name metadata")
                all_present = False

            if 'description:' in content:
                print("  ✓ SKILL.md has description metadata")
            else:
                print("  ✗ SKILL.md missing description metadata")
                all_present = False

    if all_present:
        print("✓ All required files present")
        return True
    else:
        print("✗ Some required files missing")
        return False


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("GDSII AGENT SKILL TEST SUITE")
    print("="*70)
    print("Testing GDSII/IC layout manipulation capabilities")
    print(f"Using library: gdstk")

    tests = [
        ("Create simple GDSII file", test_create_simple_gds),
        ("Read and inspect GDSII", test_read_and_inspect),
        ("Extract specific layer", test_extract_layer),
        ("Create parametric cell", test_create_parametric_cell),
        ("Calculate areas", test_area_calculation),
        ("Merge GDSII files", test_merge_files),
        ("Display/visualize GDS", test_display_gds),
        ("Crop/cut GDS region", test_crop_gds),
        ("Verify skill structure", test_skill_structure),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))

    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nResults: {passed}/{total} tests passed ({100*passed//total}%)")

    # Cleanup
    print("\n" + "="*70)
    print("Test files created:")
    print("="*70)
    test_files = [
        'test_simple.gds',
        'test_layer0.gds',
        'test_resistor.gds',
        'test_merged.gds',
        'test_display_output.png',
        'test_crop_output.gds'
    ]

    for file in test_files:
        if os.path.exists(file):
            size = os.path.getsize(file)
            print(f"  {file} ({size} bytes)")

    print("\n✓ Test suite complete!")

    return 0 if passed == total else 1


if __name__ == '__main__':
    sys.exit(main())
