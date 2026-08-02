# ForgeCAD Architecture v0.1

## Vision

ForgeCAD is an open-source fabrication workbench for FreeCAD focused on tube frames, chassis, and welded structures.

The goal is not to create another generic CAD workbench.

The goal is to create software that thinks the way fabricators think.

---

# Core Philosophy

## Fabrication First

Users design structural members—not cylinders and extrusions.

A tube is a structural object with engineering and manufacturing properties.

Its geometry is only one representation of that object.

---

## Multiple Workflows

There is no single "correct" design workflow.

ForgeCAD will support multiple ways to build the same model.

Examples include:

* Sketch → Nodes → Members
* Point-to-Point Member Creation
* Existing Geometry → Members
* Imported Centerlines → Members

Regardless of workflow, every project produces the same internal model.

---

## Single Source of Truth

The ForgeCAD model is the authoritative representation of the project.

FreeCAD geometry is generated from the ForgeCAD model.

The ForgeCAD model is never reconstructed from arbitrary CAD geometry.

---

## Parametric by Default

Every object should regenerate correctly after design changes.

Typical editable parameters include:

* Wheelbase
* Track width
* Chassis width
* Tube profile
* Ride height
* Material

Users should modify parameters rather than redraw geometry.

---

# Core Object Model

## Frame

The top-level project object.

A Frame owns:

* Tube Profiles
* Nodes
* Members
* Joints
* Materials
* Rule Set
* Reference Geometry

---

## TubeProfile

Defines reusable tube cross-sections.

Properties include:

* Shape
* Outside diameter
* Wall thickness
* Material
* Description

Multiple members may reference the same profile.

Changing a profile updates all dependent members unless explicitly overridden.

---

## Node

A connection point in 3D space.

Nodes are normally created automatically.

Users rarely need to manage them directly.

Nodes represent connectivity, not merely coordinates.

---

## Member

A structural element connecting two nodes.

A Member stores:

* Start Node
* End Node
* Tube Profile
* Material
* Manufacturing metadata
* User metadata

Members generate FreeCAD geometry but are not defined by it.

---

## Joint

Defines how one or more members connect.

Examples include:

* Fishmouth
* Miter
* Sleeve
* Weld Gap
* Gusset

A Joint contains fabrication intent.

---

## Material

Defines engineering properties such as:

* Name
* Density
* Yield strength
* Tensile strength
* Finish

---

## Rule Set

A configurable collection of fabrication rules.

Examples:

* Rock Crawler
* Formula SAE
* Baja SAE
* NHRA Drag Racing
* Aircraft
* General Fabrication
* Custom

Rule Sets provide guidance and validation without unnecessarily restricting the designer.

---

# Reference Geometry

Every Frame begins with common fabrication references.

Examples include:

* Vehicle Centerline
* Floor Plane
* Front Axle Centerline
* Rear Axle Centerline
* Firewall Plane
* Datum Origin

Reference Geometry exists independently of structural members.

---

# User Workflows

ForgeCAD should support multiple entry points into the same data model.

## Workflow 1

Choose Tube Profile

↓

Create Base Sketch

↓

Generate Nodes

↓

Generate Members

---

## Workflow 2

Choose Tube Profile

↓

Select Start Point

↓

Select End Point

↓

Create Member

---

## Workflow 3

Import Existing Centerlines

↓

Generate Nodes

↓

Generate Members

---

# Future Capabilities

Planned fabrication tools include:

* Fishmouth Generator
* Miter Generator
* Tube Bender
* Roll Cage Wizard
* X-Brace Generator
* Door Bar Wizard
* Roof Hoop Wizard
* Tube Labeling
* Cut Lists
* Material Reports
* Weight Estimation
* Manufacturing Drawings

---

# Development Principles

* Keep fabrication logic independent of FreeCAD internals.
* Prefer clear object relationships over clever implementations.
* Write automated tests for all core functionality.
* Document major architectural decisions.
* Maintain backward compatibility whenever practical.
* Favor readability over premature optimization.

---

# Long-Term Vision

ForgeCAD should become the open-source standard for parametric tube frame and chassis design.

It should be equally useful for:

* Motorsports
* Off-road vehicles
* Aircraft structures
* Industrial frames
* Robotics
* Experimental fabrication

Every design decision should answer one question:

**"Is this how a fabricator naturally thinks about the problem?"**

If the answer is no, the design should be reconsidered.
