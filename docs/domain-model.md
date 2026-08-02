# ForgeCAD Domain Model

## Purpose

ForgeCAD is a fabrication-first modeling system for tube frames, chassis, and welded structures.

The goal of the domain model is to represent fabrication intent independently of CAD geometry.

Geometry is generated from the model—not the other way around.

---

# Design Principles

## Fabrication First

Every object represents something a fabricator understands.

Examples:

- Tube
- Material
- Joint
- Frame

Not:

- Cylinder
- Sweep
- Boolean Cut

---

## Single Source of Truth

The ForgeCAD domain model is authoritative.

FreeCAD geometry is generated from it.

Geometry is never used as the source of fabrication information.

---

## Multiple Design Workflows

ForgeCAD supports multiple ways to create the same model.

Examples include:

- Sketch → Members
- Point → Point
- Imported Centerlines
- Existing Geometry

All workflows produce the same domain objects.

---

## Parametric by Default

Every object should support regeneration after design changes.

---

# Core Objects

## Project

Represents the entire design.

Responsibilities

- Frames
- Libraries
- Materials
- Rule Sets
- User Preferences

Does NOT

- Generate geometry
- Perform fabrication operations

---

## Frame

Represents one welded structure.

Examples

- Chassis
- Roll Cage
- Bumper
- Roof Rack

Responsibilities

- Own Members
- Own Nodes
- Own Joints
- Own Reference Geometry

Does NOT

- Know about FreeCAD objects

---

## Point

Represents a mathematical location.

Responsibilities

- X
- Y
- Z

Does NOT

- Know about fabrication
- Know about members
- Know about geometry

---

## Node

Represents a structural connection.

Responsibilities

- Reference one Point
- Provide a unique connection location

Does NOT

- Store geometry
- Generate joints
- Own members

---

## TubeProfile

Represents reusable cross-section geometry.

Responsibilities

- Shape
- Outside Diameter
- Wall Thickness

Does NOT

- Know material
- Know member length
- Know geometry generation

---

## Material

Represents engineering properties.

Responsibilities

- Name
- Density
- Yield Strength
- Ultimate Strength
- Elastic Modulus

Does NOT

- Know geometry
- Know members

---

## Member

Represents one structural element.

Responsibilities

- Start Node
- End Node
- Tube Profile
- Material

Does NOT

- Generate geometry
- Perform cuts
- Perform welding operations

---

## Joint

Represents a fabrication connection.

Examples

- Fishmouth
- Miter
- Sleeve
- Gusset

Does NOT

- Own members

---

## Geometry Service

Responsible for generating CAD geometry.

Input

Domain objects.

Output

FreeCAD/OpenCascade geometry.

---

## Rule Set

Represents fabrication knowledge.

Examples

- Rock Crawler
- Formula SAE
- NHRA
- Aircraft

Rules should warn the user rather than unnecessarily restrict them.

---

# Development Rules

Every class should have one responsibility.

Every feature should have unit tests.

Every public object should be documented.

Business logic must remain independent of FreeCAD.

The domain model must remain understandable to fabricators.
