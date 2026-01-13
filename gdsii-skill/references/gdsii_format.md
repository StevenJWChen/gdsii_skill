# GDSII Format Specification Reference

## Overview

GDSII (Graphic Data System version II) is a binary file format for representing IC layout data. Originally developed by Calma in the 1970s, it remains the de facto standard for mask data exchange.

## File Structure

GDSII files are organized as a sequence of records. Each record has:
- **Length** (2 bytes): Total length of record in bytes
- **Record Type** (1 byte): Identifies the record purpose
- **Data Type** (1 byte): Specifies how to interpret data
- **Data** (variable): The actual content

### Record Types

| Record Type | Hex | Name | Description |
|-------------|-----|------|-------------|
| 0x00 | 00 | HEADER | File version number |
| 0x01 | 01 | BGNLIB | Beginning of library |
| 0x02 | 02 | LIBNAME | Library name (up to 44 chars) |
| 0x03 | 03 | UNITS | Database and user units |
| 0x04 | 04 | ENDLIB | End of library |
| 0x05 | 05 | BGNSTR | Beginning of structure (cell) |
| 0x06 | 06 | STRNAME | Structure name |
| 0x07 | 07 | ENDSTR | End of structure |
| 0x08 | 08 | BOUNDARY | Polygon boundary |
| 0x09 | 09 | PATH | Path element |
| 0x0A | 0A | SREF | Structure reference (instance) |
| 0x0B | 0B | AREF | Array reference |
| 0x0C | 0C | TEXT | Text element |
| 0x0D | 0D | LAYER | Layer number |
| 0x0E | 0E | DATATYPE | Datatype number |
| 0x0F | 0F | WIDTH | Path width |
| 0x10 | 10 | XY | Coordinates array |
| 0x11 | 11 | ENDEL | End of element |
| 0x12 | 12 | SNAME | Structure reference name |
| 0x13 | 13 | COLROW | Array columns and rows |
| 0x1A | 1A | TEXTTYPE | Text type |
| 0x1B | 1B | PRESENTATION | Text presentation |
| 0x1C | 1C | STRING | Text string |
| 0x1D | 1D | STRANS | Transformation flags |
| 0x1E | 1E | MAG | Magnification factor |
| 0x1F | 1F | ANGLE | Rotation angle |
| 0x2D | 2D | BOX | Box element |
| 0x2E | 2E | BOXTYPE | Box type |

## Data Types

| Code | Type | Description |
|------|------|-------------|
| 0 | No Data | Record contains no data |
| 1 | Bit Array | 2-byte bit flags |
| 2 | 2-byte Integer | Signed 16-bit integer |
| 3 | 4-byte Integer | Signed 32-bit integer |
| 4 | 4-byte Real | Not used |
| 5 | 8-byte Real | Floating point (special format) |
| 6 | ASCII String | Text data |

## Units

GDSII files define two units:
- **Database Unit**: The size of one database unit in meters
- **User Unit**: The size of one user unit in database units

Common configurations:
- **Micron precision**: database unit = 1e-9 (nanometer), user unit = 1e-6 (micron)
- **Nanometer precision**: database unit = 1e-10, user unit = 1e-9

Example:
```
User Unit (microns) = 0.001  (1 micron)
Database Unit (meters) = 1e-9  (1 nanometer)
→ 1 user unit = 1000 database units = 1 micron = 1000 nm
```

## Layer and Datatype

- **Layer Number**: 0-255 (sometimes extended to 0-65535)
- **Datatype**: 0-255, used to distinguish different polygon types on same layer
  - Common usage: 0 = drawing, 1 = pin, 2 = text, etc.

## Coordinate System

- Coordinates are stored as 32-bit signed integers
- Range: -2,147,483,648 to 2,147,483,647 database units
- Origin (0,0) is typically at lower-left
- Coordinates are always in database units

## Element Types

### BOUNDARY (Polygon)

Closed polygon with 4 to 8191 vertices.

Structure:
```
BOUNDARY
LAYER <layer_number>
DATATYPE <datatype_number>
XY <x1> <y1> <x2> <y2> ... <xn> <yn> <x1> <y1>  (closed)
ENDEL
```

### PATH

A path with width, can be open or closed.

Structure:
```
PATH
LAYER <layer_number>
DATATYPE <datatype_number>
WIDTH <width_in_db_units>
XY <x1> <y1> <x2> <y2> ... <xn> <yn>
ENDEL
```

Path types:
- 0: Square end (flush)
- 1: Round end
- 2: Square end (extends width/2 beyond endpoint)

### SREF (Cell Reference)

Reference to another structure (cell instance).

Structure:
```
SREF
SNAME <referenced_structure_name>
STRANS <reflection_flags>  (optional)
MAG <magnification>  (optional)
ANGLE <rotation_angle>  (optional)
XY <x> <y>  (insertion point)
ENDEL
```

STRANS flags (bit 15 = reflection about X-axis before rotation):
- 0x0000: No transformation
- 0x8000: Reflect about X-axis

### AREF (Array Reference)

Array of cell instances.

Structure:
```
AREF
SNAME <referenced_structure_name>
STRANS <reflection_flags>  (optional)
MAG <magnification>  (optional)
ANGLE <rotation_angle>  (optional)
COLROW <columns> <rows>
XY <x1> <y1> <x2> <y2> <x3> <y3>
   where: (x1,y1) = origin
          (x2,y2) = end of first row
          (x3,y3) = end of first column
ENDEL
```

### TEXT

Text annotation.

Structure:
```
TEXT
LAYER <layer_number>
TEXTTYPE <text_type>
PRESENTATION <flags>  (optional)
STRANS <transformation>  (optional)
MAG <magnification>  (optional)
ANGLE <rotation>  (optional)
XY <x> <y>
STRING <text_string>
ENDEL
```

## Library Structure

A complete GDSII file structure:

```
HEADER <version>
BGNLIB <modification_time> <access_time>
LIBNAME <library_name>
UNITS <database_unit> <user_unit>

  BGNSTR <creation_time> <modification_time>
  STRNAME <structure_name>
    [Elements: BOUNDARY, PATH, SREF, AREF, TEXT, etc.]
  ENDSTR

  [More structures...]

ENDLIB
```

## Practical Limits

| Property | GDS Version 3 | GDS Version 7 |
|----------|---------------|---------------|
| Max polygon vertices | 200 | 8191 |
| Max layer number | 63 | 255 (extended: 65535) |
| Max structure name | 32 chars | 32 chars |
| Max library name | 44 chars | 44 chars |
| Coordinate range | ±2^31 | ±2^31 |

## Common Issues

### 1. Large Polygons
Polygons with >200 vertices must be split for GDS version 3 compatibility.

### 2. Text Rendering
Text elements don't specify fonts, so rendering varies between tools. Best practice: Convert text to polygons for critical labels.

### 3. Coordinate Overflow
Calculations can cause coordinates to exceed 32-bit integer limits. Always check bounds.

### 4. Layer Mapping
Different tools may use different layer number schemes. Always document your layer mapping.

## Best Practices

1. **Use Version 7 Format**: Supports more vertices per polygon
2. **Document Layer Stack**: Maintain a layer table
3. **Limit Precision**: Don't use more precision than needed (increases file size)
4. **Validate Before Tapeout**: Use commercial verification tools
5. **Maintain Hierarchy**: Don't flatten unnecessarily
6. **Use Standard Names**: Follow naming conventions (uppercase, no spaces)
7. **Check Units**: Always verify unit definitions match expectations

## OASIS Format

OASIS (Open Artwork System Interchange Standard) is the modern successor to GDSII:

**Advantages:**
- Smaller file sizes (10-100x compression)
- Faster read/write
- Better support for repetition
- Native support for properties

**Compatibility:**
- Most modern EDA tools support both
- GDSII remains more universal
- Conversion between formats is generally lossless

## Reading Resources

- **GDSII Format Spec**: Cadence GDSII Stream Format Manual
- **OASIS Spec**: SEMI P39 Standard
- **Tool Docs**: KLayout, Cadence, Synopsys documentation
- **Python Libraries**: gdspy, gdstk documentation

## Example: Minimal GDSII File in Hex

```
Header + Library beginning:
00 06 00 02 00 03       HEADER (version 3)
00 1C 01 02 00 00 00 00 ...  BGNLIB (timestamp)
00 0A 02 06 4D 59 4C 49 42  LIBNAME "MYLIB"
00 14 03 05 3E 41 89 37 ... UNITS (1e-9, 1e-6)

Structure:
00 1C 05 02 00 00 00 00 ... BGNSTR (timestamp)
00 0A 06 06 43 45 4C 4C    STRNAME "CELL"

Polygon:
00 04 08 00              BOUNDARY
00 06 0D 02 00 00        LAYER 0
00 06 0E 02 00 00        DATATYPE 0
00 2C 10 03 00 00 00 00  XY (coordinates)
  00 00 00 00 00 00 27 10
  00 00 27 10 00 00 27 10
  00 00 00 00 00 00 00 00
00 04 11 00              ENDEL

00 04 07 00              ENDSTR
00 04 04 00              ENDLIB
```

This represents a simple library with one cell containing one rectangle.
