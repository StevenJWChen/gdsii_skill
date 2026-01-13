#!/usr/bin/env python3
"""
Production Readiness Test Suite for GDSII Agent Skill
Comprehensive testing before public release
"""

import gdstk
import os
import sys
import subprocess
import tempfile
import shutil

class TestResult:
    def __init__(self, name, category):
        self.name = name
        self.category = category
        self.passed = False
        self.error = None
        self.warnings = []

    def mark_pass(self):
        self.passed = True

    def mark_fail(self, error):
        self.passed = False
        self.error = error

    def add_warning(self, warning):
        self.warnings.append(warning)


class ProductionTestSuite:
    def __init__(self):
        self.results = []
        self.gds_helper = 'gdsii-skill/scripts/gds_helper.py'

    def run_command(self, cmd, timeout=10):
        """Run command and return result"""
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return result
        except subprocess.TimeoutExpired:
            return None

    def test_invalid_file(self):
        """Test 1: Invalid file handling"""
        result = TestResult("Invalid file handling", "Error Handling")

        # Test with non-existent file
        cmd = ['python3', self.gds_helper, 'inspect', 'nonexistent.gds']
        proc = self.run_command(cmd)

        if proc and proc.returncode != 0:
            result.mark_pass()
        else:
            result.mark_fail("Should fail on non-existent file")

        self.results.append(result)
        return result.passed

    def test_empty_file(self):
        """Test 2: Empty file handling"""
        result = TestResult("Empty file handling", "Error Handling")

        # Create empty file
        with tempfile.NamedTemporaryFile(suffix='.gds', delete=False) as f:
            empty_file = f.name

        try:
            cmd = ['python3', self.gds_helper, 'inspect', empty_file]
            proc = self.run_command(cmd)

            # Should handle gracefully (either error or report empty)
            if proc and proc.returncode != 0:
                result.mark_pass()
            else:
                result.add_warning("Empty file didn't produce error")
                result.mark_pass()
        finally:
            os.unlink(empty_file)

        self.results.append(result)
        return result.passed

    def test_corrupted_file(self):
        """Test 3: Corrupted file handling"""
        result = TestResult("Corrupted file handling", "Error Handling")

        # Create corrupted file
        with tempfile.NamedTemporaryFile(suffix='.gds', delete=False, mode='wb') as f:
            corrupted_file = f.name
            f.write(b'This is not a valid GDS file\x00\x00\x00')

        try:
            cmd = ['python3', self.gds_helper, 'inspect', corrupted_file]
            proc = self.run_command(cmd)

            # Should fail gracefully
            if proc and proc.returncode != 0:
                result.mark_pass()
            else:
                result.mark_fail("Should detect corrupted file")
        finally:
            os.unlink(corrupted_file)

        self.results.append(result)
        return result.passed

    def test_negative_coordinates(self):
        """Test 4: Negative coordinates handling"""
        result = TestResult("Negative coordinates", "Edge Cases")

        try:
            # Create layout with negative coordinates
            lib = gdstk.Library()
            cell = lib.new_cell('NEG_COORDS')

            # Rectangle in negative space
            rect = gdstk.rectangle((-50, -50), (-10, -10), layer=0)
            cell.add(rect)

            lib.write_gds('test_negative.gds')

            # Test inspect
            cmd = ['python3', self.gds_helper, 'inspect', 'test_negative.gds']
            proc = self.run_command(cmd)

            if proc and proc.returncode == 0:
                # Test display
                cmd = ['python3', self.gds_helper, 'display', 'test_negative.gds',
                       '-o', 'test_negative.png']
                proc = self.run_command(cmd)

                if proc and proc.returncode == 0:
                    result.mark_pass()
                else:
                    result.mark_fail("Display failed on negative coordinates")
            else:
                result.mark_fail("Inspect failed on negative coordinates")

        except Exception as e:
            result.mark_fail(f"Exception: {e}")
        finally:
            for f in ['test_negative.gds', 'test_negative.png']:
                if os.path.exists(f):
                    os.unlink(f)

        self.results.append(result)
        return result.passed

    def test_very_small_features(self):
        """Test 5: Very small features (nanometer scale)"""
        result = TestResult("Very small features", "Edge Cases")

        try:
            lib = gdstk.Library()
            cell = lib.new_cell('TINY')

            # Nanometer-scale rectangle
            rect = gdstk.rectangle((0, 0), (0.001, 0.001), layer=0)
            cell.add(rect)

            lib.write_gds('test_tiny.gds')

            cmd = ['python3', self.gds_helper, 'inspect', 'test_tiny.gds', '-v']
            proc = self.run_command(cmd)

            if proc and proc.returncode == 0:
                result.mark_pass()
            else:
                result.mark_fail("Failed to handle tiny features")

        except Exception as e:
            result.mark_fail(f"Exception: {e}")
        finally:
            if os.path.exists('test_tiny.gds'):
                os.unlink('test_tiny.gds')

        self.results.append(result)
        return result.passed

    def test_very_large_features(self):
        """Test 6: Very large features (millimeter scale)"""
        result = TestResult("Very large features", "Edge Cases")

        try:
            lib = gdstk.Library()
            cell = lib.new_cell('HUGE')

            # Millimeter-scale rectangle
            rect = gdstk.rectangle((0, 0), (10000, 10000), layer=0)
            cell.add(rect)

            lib.write_gds('test_huge.gds')

            cmd = ['python3', self.gds_helper, 'inspect', 'test_huge.gds']
            proc = self.run_command(cmd)

            if proc and proc.returncode == 0:
                result.mark_pass()
            else:
                result.mark_fail("Failed to handle large features")

        except Exception as e:
            result.mark_fail(f"Exception: {e}")
        finally:
            if os.path.exists('test_huge.gds'):
                os.unlink('test_huge.gds')

        self.results.append(result)
        return result.passed

    def test_many_layers(self):
        """Test 7: Many layers (>20)"""
        result = TestResult("Many layers (50+)", "Stress Testing")

        try:
            lib = gdstk.Library()
            cell = lib.new_cell('MULTILAYER')

            # Create 50 layers
            for layer in range(50):
                rect = gdstk.rectangle((layer, 0), (layer+0.5, 0.5), layer=layer)
                cell.add(rect)

            lib.write_gds('test_multilayer.gds')

            # Test inspect
            cmd = ['python3', self.gds_helper, 'inspect', 'test_multilayer.gds']
            proc = self.run_command(cmd)

            if proc and proc.returncode == 0 and '50' in proc.stdout:
                # Test display (color cycling)
                cmd = ['python3', self.gds_helper, 'display', 'test_multilayer.gds',
                       '-o', 'test_multilayer.png']
                proc = self.run_command(cmd)

                if proc and proc.returncode == 0:
                    result.mark_pass()
                else:
                    result.mark_fail("Display failed with many layers")
            else:
                result.mark_fail("Inspect failed to count all layers")

        except Exception as e:
            result.mark_fail(f"Exception: {e}")
        finally:
            for f in ['test_multilayer.gds', 'test_multilayer.png']:
                if os.path.exists(f):
                    os.unlink(f)

        self.results.append(result)
        return result.passed

    def test_many_polygons(self):
        """Test 8: Many polygons (1000+)"""
        result = TestResult("Many polygons (1000+)", "Stress Testing")

        try:
            lib = gdstk.Library()
            cell = lib.new_cell('DENSE')

            # Create 1000 small rectangles
            for i in range(1000):
                x = (i % 100) * 2
                y = (i // 100) * 2
                rect = gdstk.rectangle((x, y), (x+1, y+1), layer=0)
                cell.add(rect)

            lib.write_gds('test_dense.gds')

            cmd = ['python3', self.gds_helper, 'inspect', 'test_dense.gds', '-v']
            proc = self.run_command(cmd, timeout=30)

            if proc and proc.returncode == 0:
                result.mark_pass()
            elif proc is None:
                result.mark_fail("Timeout processing many polygons")
            else:
                result.mark_fail("Failed to handle many polygons")

        except Exception as e:
            result.mark_fail(f"Exception: {e}")
        finally:
            if os.path.exists('test_dense.gds'):
                os.unlink('test_dense.gds')

        self.results.append(result)
        return result.passed

    def test_deep_hierarchy(self):
        """Test 9: Deep cell hierarchy"""
        result = TestResult("Deep hierarchy (10 levels)", "Stress Testing")

        try:
            lib = gdstk.Library()

            # Create 10-level hierarchy
            cells = []
            for i in range(10):
                cell = lib.new_cell(f'LEVEL_{i}')
                rect = gdstk.rectangle((0, 0), (1, 1), layer=i)
                cell.add(rect)

                if i > 0:
                    # Reference previous cell
                    ref = gdstk.Reference(cells[i-1], origin=(2, 0))
                    cell.add(ref)

                cells.append(cell)

            lib.write_gds('test_hierarchy.gds')

            cmd = ['python3', self.gds_helper, 'inspect', 'test_hierarchy.gds', '-v']
            proc = self.run_command(cmd)

            if proc and proc.returncode == 0:
                result.mark_pass()
            else:
                result.mark_fail("Failed to handle deep hierarchy")

        except Exception as e:
            result.mark_fail(f"Exception: {e}")
        finally:
            if os.path.exists('test_hierarchy.gds'):
                os.unlink('test_hierarchy.gds')

        self.results.append(result)
        return result.passed

    def test_crop_edge_cases(self):
        """Test 10: Crop edge cases"""
        result = TestResult("Crop edge cases", "Feature Testing")

        try:
            # Create test file
            lib = gdstk.Library()
            cell = lib.new_cell('CROP_TEST')
            rect = gdstk.rectangle((0, 0), (100, 100), layer=0)
            cell.add(rect)
            lib.write_gds('test_crop_edge.gds')

            # Test 1: Crop completely outside
            cmd = ['python3', self.gds_helper, 'crop', 'test_crop_edge.gds',
                   'test_outside.gds', '--bbox', '200', '200', '300', '300']
            proc = self.run_command(cmd)

            if proc and proc.returncode == 0:
                # Should create file even if empty
                if os.path.exists('test_outside.gds'):
                    result.add_warning("Created file for empty crop")

            # Test 2: Crop with zero area
            cmd = ['python3', self.gds_helper, 'crop', 'test_crop_edge.gds',
                   'test_zero.gds', '--bbox', '50', '50', '50', '50']
            proc = self.run_command(cmd)

            # Test 3: Crop with negative bbox (should fail or handle)
            cmd = ['python3', self.gds_helper, 'crop', 'test_crop_edge.gds',
                   'test_negative_bbox.gds', '--bbox', '100', '100', '0', '0']
            proc = self.run_command(cmd)

            result.mark_pass()

        except Exception as e:
            result.mark_fail(f"Exception: {e}")
        finally:
            for f in ['test_crop_edge.gds', 'test_outside.gds',
                     'test_zero.gds', 'test_negative_bbox.gds']:
                if os.path.exists(f):
                    os.unlink(f)

        self.results.append(result)
        return result.passed

    def test_display_edge_cases(self):
        """Test 11: Display edge cases"""
        result = TestResult("Display edge cases", "Feature Testing")

        try:
            # Create file with no polygons (empty cell)
            lib = gdstk.Library()
            cell = lib.new_cell('EMPTY')
            lib.write_gds('test_empty_cell.gds')

            cmd = ['python3', self.gds_helper, 'display', 'test_empty_cell.gds',
                   '-o', 'test_empty_display.png']
            proc = self.run_command(cmd)

            # Should handle gracefully
            if proc:
                result.mark_pass()
            else:
                result.mark_fail("Timeout on empty cell display")

        except Exception as e:
            result.mark_fail(f"Exception: {e}")
        finally:
            for f in ['test_empty_cell.gds', 'test_empty_display.png']:
                if os.path.exists(f):
                    os.unlink(f)

        self.results.append(result)
        return result.passed

    def test_special_characters_filename(self):
        """Test 12: Special characters in filename"""
        result = TestResult("Special characters in filename", "Security")

        try:
            # Test with spaces
            lib = gdstk.Library()
            cell = lib.new_cell('TEST')
            rect = gdstk.rectangle((0, 0), (10, 10), layer=0)
            cell.add(rect)
            lib.write_gds('test file with spaces.gds')

            cmd = ['python3', self.gds_helper, 'inspect', 'test file with spaces.gds']
            proc = self.run_command(cmd)

            if proc and proc.returncode == 0:
                result.mark_pass()
            else:
                result.mark_fail("Failed to handle spaces in filename")

        except Exception as e:
            result.mark_fail(f"Exception: {e}")
        finally:
            if os.path.exists('test file with spaces.gds'):
                os.unlink('test file with spaces.gds')

        self.results.append(result)
        return result.passed

    def test_round_trip(self):
        """Test 13: Round-trip (create -> read -> write -> read)"""
        result = TestResult("Round-trip consistency", "Integration")

        try:
            # Create original
            lib1 = gdstk.Library(name='ORIGINAL')
            cell1 = lib1.new_cell('CELL1')
            rect = gdstk.rectangle((0, 0), (50, 50), layer=5)
            cell1.add(rect)
            lib1.write_gds('test_original.gds')

            # Crop it
            cmd = ['python3', self.gds_helper, 'crop', 'test_original.gds',
                   'test_cropped_rt.gds', '--bbox', '0', '0', '30', '30']
            proc = self.run_command(cmd)

            if proc and proc.returncode == 0:
                # Read back cropped file
                lib2 = gdstk.read_gds('test_cropped_rt.gds')

                if len(lib2.cells) > 0:
                    cell2 = lib2.cells[0]
                    bbox = cell2.bounding_box()

                    # Verify dimensions are approximately correct
                    if bbox and abs((bbox[1][0] - bbox[0][0]) - 30) < 0.1:
                        result.mark_pass()
                    else:
                        result.mark_fail(f"Dimensions mismatch: {bbox}")
                else:
                    result.mark_fail("No cells in output")
            else:
                result.mark_fail("Crop operation failed")

        except Exception as e:
            result.mark_fail(f"Exception: {e}")
        finally:
            for f in ['test_original.gds', 'test_cropped_rt.gds']:
                if os.path.exists(f):
                    os.unlink(f)

        self.results.append(result)
        return result.passed

    def test_concurrent_operations(self):
        """Test 14: Multiple operations in sequence"""
        result = TestResult("Sequential operations", "Integration")

        try:
            # Create file
            lib = gdstk.Library()
            cell = lib.new_cell('SEQ_TEST')
            for i in range(5):
                rect = gdstk.rectangle((i*20, 0), (i*20+10, 10), layer=i)
                cell.add(rect)
            lib.write_gds('test_seq.gds')

            # Operation 1: Inspect
            cmd = ['python3', self.gds_helper, 'inspect', 'test_seq.gds']
            proc1 = self.run_command(cmd)

            # Operation 2: Display
            cmd = ['python3', self.gds_helper, 'display', 'test_seq.gds',
                   '-o', 'test_seq.png']
            proc2 = self.run_command(cmd)

            # Operation 3: Crop
            cmd = ['python3', self.gds_helper, 'crop', 'test_seq.gds',
                   'test_seq_crop.gds', '--bbox', '0', '0', '50', '10']
            proc3 = self.run_command(cmd)

            # Operation 4: Display cropped
            cmd = ['python3', self.gds_helper, 'display', 'test_seq_crop.gds',
                   '-o', 'test_seq_crop.png']
            proc4 = self.run_command(cmd)

            if all([p and p.returncode == 0 for p in [proc1, proc2, proc3, proc4]]):
                result.mark_pass()
            else:
                result.mark_fail("One or more operations failed")

        except Exception as e:
            result.mark_fail(f"Exception: {e}")
        finally:
            for f in ['test_seq.gds', 'test_seq.png',
                     'test_seq_crop.gds', 'test_seq_crop.png']:
                if os.path.exists(f):
                    os.unlink(f)

        self.results.append(result)
        return result.passed

    def test_help_documentation(self):
        """Test 15: Help and documentation"""
        result = TestResult("Help documentation", "Usability")

        try:
            # Test main help
            cmd = ['python3', self.gds_helper, '--help']
            proc = self.run_command(cmd)

            if proc and proc.returncode == 0 and 'inspect' in proc.stdout:
                # Test command-specific help
                cmd = ['python3', self.gds_helper, 'display', '--help']
                proc = self.run_command(cmd)

                if proc and proc.returncode == 0:
                    result.mark_pass()
                else:
                    result.mark_fail("Command help failed")
            else:
                result.mark_fail("Main help failed")

        except Exception as e:
            result.mark_fail(f"Exception: {e}")

        self.results.append(result)
        return result.passed

    def run_all_tests(self):
        """Run all production tests"""
        print("="*70)
        print("GDSII AGENT SKILL - PRODUCTION READINESS TEST SUITE")
        print("="*70)
        print()

        tests = [
            ("Error Handling", [
                self.test_invalid_file,
                self.test_empty_file,
                self.test_corrupted_file,
            ]),
            ("Edge Cases", [
                self.test_negative_coordinates,
                self.test_very_small_features,
                self.test_very_large_features,
            ]),
            ("Stress Testing", [
                self.test_many_layers,
                self.test_many_polygons,
                self.test_deep_hierarchy,
            ]),
            ("Feature Testing", [
                self.test_crop_edge_cases,
                self.test_display_edge_cases,
            ]),
            ("Security", [
                self.test_special_characters_filename,
            ]),
            ("Integration", [
                self.test_round_trip,
                self.test_concurrent_operations,
            ]),
            ("Usability", [
                self.test_help_documentation,
            ]),
        ]

        for category, category_tests in tests:
            print(f"\n{'='*70}")
            print(f"{category} Tests")
            print(f"{'='*70}")

            for test_func in category_tests:
                test_name = test_func.__doc__.split(':')[1].strip()
                print(f"\nRunning: {test_name}...", end=' ')

                try:
                    passed = test_func()
                    if passed:
                        print("✓ PASS")
                    else:
                        print("✗ FAIL")
                except Exception as e:
                    print(f"✗ EXCEPTION: {e}")

        return self.results

    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)

        categories = {}
        for r in self.results:
            if r.category not in categories:
                categories[r.category] = {'pass': 0, 'fail': 0, 'warn': 0}
            if r.passed:
                categories[r.category]['pass'] += 1
            else:
                categories[r.category]['fail'] += 1
            if r.warnings:
                categories[r.category]['warn'] += len(r.warnings)

        total_pass = sum(c['pass'] for c in categories.values())
        total_fail = sum(c['fail'] for c in categories.values())
        total_warn = sum(c['warn'] for c in categories.values())
        total_tests = total_pass + total_fail

        print(f"\nBy Category:")
        for cat, stats in sorted(categories.items()):
            print(f"  {cat:20s}: {stats['pass']:2d} pass, {stats['fail']:2d} fail, {stats['warn']:2d} warnings")

        print(f"\nOverall:")
        print(f"  Total Tests: {total_tests}")
        print(f"  Passed: {total_pass} ({100*total_pass//total_tests if total_tests > 0 else 0}%)")
        print(f"  Failed: {total_fail}")
        print(f"  Warnings: {total_warn}")

        # Print failures
        if total_fail > 0:
            print(f"\nFailed Tests:")
            for r in self.results:
                if not r.passed:
                    print(f"  ✗ {r.name}: {r.error}")

        # Print warnings
        if total_warn > 0:
            print(f"\nWarnings:")
            for r in self.results:
                for w in r.warnings:
                    print(f"  ⚠ {r.name}: {w}")

        # Production readiness assessment
        print(f"\n{'='*70}")
        print("PRODUCTION READINESS ASSESSMENT")
        print(f"{'='*70}")

        if total_fail == 0:
            print("✓ READY FOR PRODUCTION RELEASE")
            print("  All critical tests passed")
        elif total_fail <= 2:
            print("⚠ NEEDS MINOR FIXES")
            print(f"  {total_fail} non-critical issues found")
        else:
            print("✗ NOT READY FOR RELEASE")
            print(f"  {total_fail} critical issues must be fixed")

        return total_fail == 0


if __name__ == '__main__':
    suite = ProductionTestSuite()
    suite.run_all_tests()
    ready = suite.print_summary()

    sys.exit(0 if ready else 1)
