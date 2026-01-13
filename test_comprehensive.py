#!/usr/bin/env python3
"""
Comprehensive Test Suite - All Features and Documentation
"""

import gdstk
import os
import sys
import subprocess
import time

def run_cmd(cmd):
    """Run command and return result"""
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result

print("="*70)
print("COMPREHENSIVE FEATURE TEST SUITE")
print("="*70)

# Test counter
tests_passed = 0
tests_failed = 0
tests_run = 0

def test(name):
    global tests_run
    tests_run += 1
    print(f"\n[{tests_run}] {name}...", end=' ')

def passed():
    global tests_passed
    tests_passed += 1
    print("✓ PASS")

def failed(msg):
    global tests_failed
    tests_failed += 1
    print(f"✗ FAIL: {msg}")

# Create test files if needed
if not os.path.exists('test_simple.gds'):
    lib = gdstk.Library()
    cell = lib.new_cell('SIMPLE')
    rect = gdstk.rectangle((0, 0), (20, 20), layer=0)
    cell.add(rect)
    lib.write_gds('test_simple.gds')

# =============================================================================
# Test all inspect command variations
# =============================================================================

test("inspect: Basic inspection")
result = run_cmd(['python3', 'gdsii-skill/scripts/gds_helper.py', 'inspect', 'test_simple.gds'])
if result.returncode == 0 and 'SIMPLE' in result.stdout:
    passed()
else:
    failed(f"Return code: {result.returncode}")

test("inspect: Verbose mode")
result = run_cmd(['python3', 'gdsii-skill/scripts/gds_helper.py', 'inspect', 'test_simple.gds', '-v'])
if result.returncode == 0 and 'Polygons' in result.stdout:
    passed()
else:
    failed("Verbose output missing")

test("inspect: Non-existent file (error handling)")
result = run_cmd(['python3', 'gdsii-skill/scripts/gds_helper.py', 'inspect', 'nonexistent.gds'])
if result.returncode != 0:
    passed()
else:
    failed("Should fail on non-existent file")

# =============================================================================
# Test all display command variations
# =============================================================================

test("display: Basic display")
result = run_cmd(['python3', 'gdsii-skill/scripts/gds_helper.py', 'display', 'test_simple.gds', '-o', 'test_display_basic.png'])
if result.returncode == 0 and os.path.exists('test_display_basic.png'):
    passed()
    os.unlink('test_display_basic.png')
else:
    failed("Display failed")

test("display: Without bounding box")
result = run_cmd(['python3', 'gdsii-skill/scripts/gds_helper.py', 'display', 'test_simple.gds', '-o', 'test_nobbox.png', '--no-bbox'])
if result.returncode == 0:
    passed()
    if os.path.exists('test_nobbox.png'):
        os.unlink('test_nobbox.png')
else:
    failed("No-bbox option failed")

test("display: Specific layers filter")
# Create multi-layer file
lib = gdstk.Library()
cell = lib.new_cell('MULTI')
for layer in range(5):
    rect = gdstk.rectangle((layer*5, 0), (layer*5+4, 4), layer=layer)
    cell.add(rect)
lib.write_gds('test_multi.gds')

result = run_cmd(['python3', 'gdsii-skill/scripts/gds_helper.py', 'display', 'test_multi.gds', '-l', '0', '1', '-o', 'test_filtered.png'])
if result.returncode == 0:
    passed()
    if os.path.exists('test_filtered.png'):
        os.unlink('test_filtered.png')
else:
    failed("Layer filter failed")

os.unlink('test_multi.gds')

# =============================================================================
# Test all crop command variations
# =============================================================================

test("crop: Basic crop operation")
result = run_cmd(['python3', 'gdsii-skill/scripts/gds_helper.py', 'crop', 'test_simple.gds', 'test_crop_basic.gds', '--bbox', '0', '0', '10', '10'])
if result.returncode == 0 and os.path.exists('test_crop_basic.gds'):
    passed()
    os.unlink('test_crop_basic.gds')
else:
    failed("Basic crop failed")

test("crop: Crop with specific cell")
# Create file with multiple cells
lib = gdstk.Library()
cell1 = lib.new_cell('CELL1')
cell2 = lib.new_cell('CELL2')
rect1 = gdstk.rectangle((0, 0), (50, 50), layer=0)
rect2 = gdstk.rectangle((0, 0), (30, 30), layer=1)
cell1.add(rect1)
cell2.add(rect2)
lib.write_gds('test_multicell.gds')

result = run_cmd(['python3', 'gdsii-skill/scripts/gds_helper.py', 'crop', 'test_multicell.gds', 'test_crop_cell.gds', '--bbox', '0', '0', '20', '20', '-c', 'CELL1'])
if result.returncode == 0:
    passed()
    if os.path.exists('test_crop_cell.gds'):
        os.unlink('test_crop_cell.gds')
else:
    failed("Cell-specific crop failed")

os.unlink('test_multicell.gds')

test("crop: Fractional coordinates")
result = run_cmd(['python3', 'gdsii-skill/scripts/gds_helper.py', 'crop', 'test_simple.gds', 'test_crop_frac.gds', '--bbox', '0.5', '0.5', '10.5', '10.5'])
if result.returncode == 0:
    passed()
    if os.path.exists('test_crop_frac.gds'):
        os.unlink('test_crop_frac.gds')
else:
    failed("Fractional coordinates failed")

# =============================================================================
# Test performance with realistic data
# =============================================================================

test("Performance: 100 polygons")
lib = gdstk.Library()
cell = lib.new_cell('PERF100')
for i in range(100):
    x, y = i % 10 * 10, i // 10 * 10
    rect = gdstk.rectangle((x, y), (x+8, y+8), layer=0)
    cell.add(rect)
lib.write_gds('test_perf100.gds')

start = time.time()
result = run_cmd(['python3', 'gdsii-skill/scripts/gds_helper.py', 'inspect', 'test_perf100.gds'])
elapsed = time.time() - start

if result.returncode == 0 and elapsed < 2.0:  # Should complete in < 2 seconds
    passed()
else:
    failed(f"Too slow: {elapsed:.2f}s")

os.unlink('test_perf100.gds')

test("Performance: Display with 20 layers")
lib = gdstk.Library()
cell = lib.new_cell('PERF_DISPLAY')
for layer in range(20):
    for i in range(10):
        rect = gdstk.rectangle((layer*5+i*0.5, 0), (layer*5+i*0.5+0.4, 10), layer=layer)
        cell.add(rect)
lib.write_gds('test_perf_display.gds')

start = time.time()
result = run_cmd(['python3', 'gdsii-skill/scripts/gds_helper.py', 'display', 'test_perf_display.gds', '-o', 'test_perf.png'])
elapsed = time.time() - start

if result.returncode == 0 and elapsed < 5.0:  # Should complete in < 5 seconds
    passed()
    if os.path.exists('test_perf.png'):
        os.unlink('test_perf.png')
else:
    failed(f"Display too slow: {elapsed:.2f}s")

os.unlink('test_perf_display.gds')

# =============================================================================
# Test file compatibility (read back what we wrote)
# =============================================================================

test("Compatibility: Write and read back")
# Create complex file
lib1 = gdstk.Library(name='COMPAT_TEST')
cell = lib1.new_cell('COMPLEX')
rect = gdstk.rectangle((0, 0), (100, 100), layer=0, datatype=0)
circle = gdstk.ellipse((50, 50), 25, layer=1, datatype=0)
poly = gdstk.Polygon([(10, 10), (30, 10), (30, 30), (10, 30)], layer=2, datatype=1)
cell.add(rect, circle, poly)
lib1.write_gds('test_compat.gds')

# Crop it
result = run_cmd(['python3', 'gdsii-skill/scripts/gds_helper.py', 'crop', 'test_compat.gds', 'test_compat_crop.gds', '--bbox', '20', '20', '80', '80'])

# Read back
lib2 = gdstk.read_gds('test_compat_crop.gds')
if len(lib2.cells) > 0:
    cell2 = lib2.cells[0]
    if len(cell2.polygons) > 0:
        passed()
    else:
        failed("No polygons in cropped file")
else:
    failed("No cells in cropped file")

os.unlink('test_compat.gds')
os.unlink('test_compat_crop.gds')

# =============================================================================
# Test command-line option parsing
# =============================================================================

test("CLI: Help displays")
result = run_cmd(['python3', 'gdsii-skill/scripts/gds_helper.py', '--help'])
if result.returncode == 0 and 'GDSII Helper Tool' in result.stdout:
    passed()
else:
    failed("Help not displaying correctly")

test("CLI: No arguments shows help")
result = run_cmd(['python3', 'gdsii-skill/scripts/gds_helper.py'])
if result.returncode == 0:
    passed()
else:
    failed("No arguments should show help")

test("CLI: Invalid command")
result = run_cmd(['python3', 'gdsii-skill/scripts/gds_helper.py', 'invalid_command'])
if result.returncode != 0 or 'invalid choice' in result.stderr.lower():
    passed()
else:
    failed("Should reject invalid command")

# =============================================================================
# Test output format and quality
# =============================================================================

test("Output: Inspect includes all required info")
result = run_cmd(['python3', 'gdsii-skill/scripts/gds_helper.py', 'inspect', 'test_simple.gds'])
required_fields = ['Library Name', 'Unit', 'Total Cells', 'Layers Used']
if all(field in result.stdout for field in required_fields):
    passed()
else:
    failed("Missing required fields in output")

test("Output: Display creates valid PNG")
result = run_cmd(['python3', 'gdsii-skill/scripts/gds_helper.py', 'display', 'test_simple.gds', '-o', 'test_valid_png.png'])
if os.path.exists('test_valid_png.png'):
    # Check if it's a valid PNG (starts with PNG signature)
    with open('test_valid_png.png', 'rb') as f:
        header = f.read(8)
        if header[:4] == b'\x89PNG':
            passed()
        else:
            failed("Invalid PNG file")
    os.unlink('test_valid_png.png')
else:
    failed("PNG not created")

test("Output: Crop produces valid GDS")
result = run_cmd(['python3', 'gdsii-skill/scripts/gds_helper.py', 'crop', 'test_simple.gds', 'test_valid_crop.gds', '--bbox', '0', '0', '15', '15'])
if os.path.exists('test_valid_crop.gds'):
    try:
        # Try to read it back
        lib = gdstk.read_gds('test_valid_crop.gds')
        if len(lib.cells) > 0:
            passed()
        else:
            failed("Cropped GDS has no cells")
    except:
        failed("Cropped GDS is not valid")
    os.unlink('test_valid_crop.gds')
else:
    failed("Crop didn't create output")

# =============================================================================
# Summary
# =============================================================================

print("\n" + "="*70)
print("COMPREHENSIVE TEST SUMMARY")
print("="*70)
print(f"Tests Run: {tests_run}")
print(f"Passed: {tests_passed} ({100*tests_passed//tests_run if tests_run > 0 else 0}%)")
print(f"Failed: {tests_failed}")

if tests_failed == 0:
    print("\n✓ ALL COMPREHENSIVE TESTS PASSED")
    print("  Ready for public release")
else:
    print(f"\n✗ {tests_failed} TESTS FAILED")
    print("  Review failures before release")

sys.exit(0 if tests_failed == 0 else 1)
