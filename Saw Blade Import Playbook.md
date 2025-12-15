Below is a clean, repo-ready Saw Blade Import Playbook.
This is not code — it’s the operational document you (and future contributors) follow to safely populate the Saw Lab tool library with real blade data without destabilizing RMOS, CAM, or feasibility scoring.

You can drop this directly into docs/Saw_Lab/.

Saw Blade Import Playbook

RMOS / CNC Saw Lab

1. Purpose

This playbook defines the authoritative process for importing real-world saw blade data into the Luthier’s ToolBox Saw Lab in a way that is:

Physically accurate

Auditable

Non-destructive to existing CAM / RMOS logic

Incrementally improvable as better data becomes available

The Saw Blade Library is foundational manufacturing data, not UI decoration.

2. What Counts as “Saw Blade Data”

A blade entry is considered importable only if it includes enough information to support:

Rim speed validation

Tooth engagement / bite-per-tooth calculation

Heat risk estimation

Deflection / lateral load reasoning

Kerf-based material yield planning

Minimum Viable Blade (MVB) Data
Category	Required
Identification	Manufacturer, model, blade type
Geometry	Diameter, kerf, plate thickness
Teeth	Tooth count, hook angle (if available)
Speed	Max RPM (absolute or recommended)
Material	Steel / carbide / hybrid
Use Case	Rip / crosscut / plywood / laminate

If any of these are missing, the blade may still be imported but must be marked data_quality: PARTIAL.

3. Accepted Source Materials
Primary Sources (Preferred)

Manufacturer spec sheets (PDF)

Manufacturer websites

Engineering whitepapers

Direct manufacturer email responses

Secondary Sources (Allowed, flagged)

Distributor listings

Forum posts quoting specs

User-measured data (calipers, tachometer)

Disallowed Sources

Marketing-only blurbs

Amazon listings without specs

AI-generated guesses

4. Import Workflow (Step-by-Step)
Step 1 — Acquire Source Files

Store all raw sources in:

docs/Saw_Lab/sources/
  ├── tenryu/
  ├── kanefusa/
  ├── freud/
  └── misc/


Never discard original PDFs — they are the chain of custody.

Step 2 — Extract Raw Values

From each source, extract:

Blade diameter (mm or inches)

Kerf width

Plate thickness

Tooth count

Max RPM or recommended RPM range

Tooth geometry notes (ATB, FTG, TCG, etc.)

Record ambiguous or missing values explicitly as null.

Step 3 — Normalize Units

Canonical units in JSON:

Length → mm

Speed → RPM

Angles → degrees

Forces → Newtons (if present)

Never store mixed units in the same field.

Step 4 — Populate Blade JSON Entry

Example (simplified):

{
  "blade_id": "tenryu_gold_305_60t",
  "manufacturer": "Tenryu",
  "model": "Gold Series",
  "diameter_mm": 305.0,
  "kerf_mm": 3.2,
  "plate_thickness_mm": 2.2,
  "tooth_count": 60,
  "tooth_geometry": "ATB",
  "max_rpm": 6000,
  "intended_use": ["crosscut", "plywood"],
  "data_quality": "VERIFIED",
  "source_refs": [
    "docs/Saw_Lab/sources/tenryu/gold_series_305mm.pdf"
  ]
}

Step 5 — Assign Data Quality Level
Level	Meaning
VERIFIED	Manufacturer spec confirmed
PARTIAL	Some inferred values
ESTIMATED	User-measured or extrapolated
LEGACY	Old data retained for compatibility

RMOS feasibility scoring must read this flag.

Step 6 — Validate with Import Script

Run the blade library validator:

python scripts/validate_saw_blade_library.py


Validator checks:

Required fields present

Units sane

RPM vs diameter not physically absurd

Kerf > plate thickness

Tooth count reasonable

No silent failures allowed.

Step 7 — Commit Strategy

Each manufacturer batch should be:

One commit

One commit message

One changelog entry

Example:

feat(saw-lab): add Tenryu Gold Series 305mm blades (verified)

5. How RMOS Uses Blade Data

Once imported, blades participate in:

Rim Speed Calculator

Bite Per Tooth Model

Heat Risk Estimator

Kickback Risk Model

Saw Path Planner Yield Math

Importing a blade does not automatically make it “safe” — it makes it analyzable.

6. Common Pitfalls (Avoid These)

❌ Guessing max RPM from YouTube
❌ Copying router-bit RPM limits to saw blades
❌ Omitting plate thickness
❌ Treating marketing names as geometry
❌ Mixing mm/inch values

7. Review & Approval Checklist

Before merging:

 Source PDF stored

 JSON validates cleanly

 Data quality flag set

 No duplicate blade_id

 Changelog updated

8. Future Enhancements (Explicitly Deferred)

Tooth force coefficient tables

Manufacturer-specific correction factors

Blade wear modeling

Acoustic / vibration models

These are Wave-level features, not import blockers.

9. Bottom Line

This playbook ensures:

Saw blades are treated as physics objects, not catalog items

RMOS feasibility remains trustworthy

CAM decisions stay grounded in reality

Future contributors don’t corrupt the library unintentionally

Once this is followed consistently, the Saw Lab becomes a credible manufacturing intelligence system, not just a CAM add-on.