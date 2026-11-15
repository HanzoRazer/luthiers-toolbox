# American Hardwoods: Comprehensive Tonewood Guide

> **Sources:** `wood_species.json` v4.0.0, CIRAD, Web research 2025-2026
> **Generated:** 2026-06-22
> **Purpose:** Complete domestic alternative guide — no imports required

> **ᵉ Estimated Janka (added 2026-11-14).** Values marked ᵉ equal the bulk-import regression `Janka ≈ 0.00355 × density^1.85` (`scripts/bulk_import_wood_species.py`), not a hardness test. They rise smoothly with density, so they cannot rank species of similar density, and they can be far below published measurements for the hardest woods. Treat them as placeholders. See `VERIFICATION_LOG.md` (C-02).

> **FPL GTR-282 values (corrected 2026-11-15, `VERIFICATION_LOG.md` C-11).** For species that FPL GTR-282 (2021) covers, density (at 12% MC), specific gravity (G₁₂), Janka, MOE, MOR and shrinkage in the tables are now FPL values, and sound speed, impedance and E/ρ are recomputed from them. `scripts/check_tonewood_fpl_values.py` lists the species mapped and checks every such cell. Values for other species are unchanged and mostly unsourced.

This document covers **about 70 North American species**, organized by family and application. The earlier figure of "172 American species in the database" could not be traced: `wood_species.json` has no origin field to count by (corrected 2026-11-14, see `VERIFICATION_LOG.md`). Every wood here grows in North America.

---

## Why American Hardwoods Matter

1. **No CITES paperwork** — domestic species have no import restrictions
2. **Shorter supply chains** — lower cost, faster delivery
3. **Sustainability transparency** — US forestry practices are documented
4. **Ecological benefit** — some species (mesquite, black locust, chinaberry) are invasive
5. **Regional character** — "Made in USA" from American wood

---

## Part I: The Juglandaceae Family (Walnut & Hickory)

The walnut family spans the full density range from mahogany-weight to rosewood-weight.

### Black Walnut (*Juglans nigra*)

The benchmark American tonewood for back/sides:

| Property | Value | Comparison |
|----------|:-----:|------------|
| Density | 610 kg/m³ | = Koa |
| Janka | 1,010 lbf | Harder than mahogany |
| MOE | 11.34 GPa | = Mahogany |
| MOR | 90.7 MPa | Good strength |
| Tone | Warm, rich mids | "Mahogany-like" |
| Workability | Excellent | Easy to work |

**Builder consensus:** "Tone falls between Mahogany and Rosewood" — warm fundamentals with some complexity.

### The Hickory Genus (*Carya*)

Hickory spans 672–840 kg/m³ — from walnut-weight to rosewood-weight:

| Species | Density | Janka | MOE | Notes |
|---------|:-------:|:-----:|:---:|-------|
| **Pignut Hickory** | 840 | 2136 | 15.59 | **Rosewood-range**; highest density |
| **Mockernut Hickory** | 806 | 1978 | 15.31 | Rosewood-range |
| **Shagbark Hickory** | 806 | 1888 | 14.90 | Rosewood-range; classic |
| **Shellbark Hickory** | 773 | 1821 | 13.03 | Upper mahogany |
| **Pecan** | 739 | 1821 | 11.93 | Mid-range; *C. illinoinensis* |
| **Bitternut Hickory** | 739 | 713 ᵉ | 12.35 | = Pecan density |
| **Water Hickory** | 694 | 634 ᵉ | 13.93 | Walnut-adjacent |
| **Nutmeg Hickory** | 672 | 609 ᵉ | 11.72 | Lightest hickory |

**CIRAD data:** *Carya sp* from USA measured at D12 0.85 (850 kg/m³) — confirms the denser hickories reach rosewood territory.

**Key insight:** Pignut, Mockernut and Shagbark hickory (806–840) approach Pau Ferro (880) and Jatoba (861) in density (corrected 2026-11-14 and, from FPL GTR-282, 2026-11-15; see `VERIFICATION_LOG.md`). They belong in the rosewood-alternatives discussion.

### Pecan (*Carya illinoinensis*)

Botanically a hickory — and the most *available* one, thanks to orchard cultivation across the South:

| Property | Value | Notes |
|----------|:-----:|-------|
| Density | 735 kg/m³ | Mid-range *Carya* |
| Janka | 713 lbf | Hard |
| MOE | 11.93 GPa | ≈ Black Walnut / Mahogany |
| MOR | 94.5 MPa | Good strength |
| Tone class | Walnut-to-hickory | Warm with hickory firmness |
| Availability | **Excellent** | Orchard-salvage + lumber trade |

Pecan appears in the hickory table above (it *is* a hickory), but earns its own callout for one practical reason: it is by far the easiest *Carya* to source. Pecan-orchard removals and the pecan lumber trade make it far more available than the wild hickories, at a density (739) that sits neatly between Black Walnut (616) and the rosewood-weight pignut/mockernut/shagbark (806–840) — a warm-but-firm back/sides candidate that is actually easy to buy.

### Butternut (*Juglans cinerea*)

| Property | Value |
|----------|:-----:|
| Density | 426 kg/m³ |
| Character | Lightweight walnut relative |
| Notes | Soft; "white walnut" |

---

## Part II: The Oak Family (Fagaceae)

### White Oak Group

Dense, ring-porous, traditional:

| Species | Density | Janka | MOE | Notes |
|---------|:-------:|:-----:|:---:|-------|
| **White Oak** | 762 | 1,349 | 12.3 | Classic; high tannin |
| **Swamp White Oak** | 806 | 1619 | 14.1 | Wetland species |
| **Chestnut Oak** | 739 | 1124 | 11.00 | Appalachian |
| **Swamp Chestnut Oak** | 750 | 1236 | 12.2 | Southern |
| **Oregon White Oak** | 815 | 863 ᵉ | 7.51 | Pacific Northwest |
| **Live Oak** | **986** | 1,260 ᵉ | 13.7 | **Densest US oak** |

**Live Oak** (*Quercus virginiana*) at 986 kg/m³ is the standout — dense enough for the ebony-range discussion.

### Red Oak Group

Slightly less dense, more porous:

| Species | Density | Janka | MOE | Notes |
|---------|:-------:|:-----:|:---:|-------|
| **Northern Red Oak** | 706 | 1,281 | 12.5 | Most common |
| **Cherrybark Oak** | 762 | 1484 | 15.70 | High MOE |
| **Southern Red Oak** | 661 | 1057 | 10.3 | Lower density |
| **Willow Oak** | 773 | 1461 | 13.1 | Fine-grained |
| **Pin Oak** | 706 | 1506 | — | Urban tree |

**Builder feedback:** "Red oak produces warm bass similar to rosewood, but without Brazilian's overtones or reverb." In this table white oak (762) is denser than northern red oak (706) (corrected 2026-11-14, see `VERIFICATION_LOG.md`).

### Chestnut & Beech

| Species | Density | Janka | MOE | Notes |
|---------|:-------:|:-----:|:---:|-------|
| **American Beech** | 717 | 1,304 | — | Hard; steam-bends well |
| **Sweet Chestnut** (*Castanea sativa*) | 590 | 475 ᵉ | 8.61 | European species, not American chestnut (*C. dentata*); reclaimed "wormy chestnut" is American |

---

## Part III: The Maple Family (Sapindaceae)

### Hard Maple (*Acer saccharum*)

The electric guitar neck standard:

| Property | Value | Notes |
|----------|:-----:|-------|
| Density | 705 kg/m³ | Heavy for mahogany-range |
| Janka | 1,450 lbf | Very hard |
| MOE | 13.49 GPa | Stiff |
| Tone | Bright, transparent | "Fewer overtones than other medium-density woods" |
| Uses | Necks, tops, bodies | Fender standard |

**Figured varieties:** Birdseye, curly/flame, quilted — same species, different growth patterns.

### Soft Maple (*Acer rubrum*)

| Property | Value | Notes |
|----------|:-----:|-------|
| Density | 610 kg/m³ | Lighter than hard maple |
| Janka | 950 lbf | Moderate |
| Tone | Warmer than hard maple | Less "glass" |
| Uses | Bodies, backs | Budget alternative |

### Other Maples

| Species | Density | Janka | Notes |
|---------|:-------:|:-----:|-------|
| **Black Maple** | 638 | 1169 | Between hard/soft |
| **Pacific Maple** | 605 | 497 ᵉ | West Coast bigleaf |
| **Norway Maple** | 645 | 560 ᵉ | Introduced; common |

---

## Part IV: The Ash Family (Oleaceae)

### Swamp Ash

The Fender body wood:

| Property | Value | Notes |
|----------|:-----:|-------|
| Density | 450–550 kg/m³ | Lighter than northern ash |
| Tone | "Chiming highs, clear midrange, robust low end" | Scooped mids |
| Grain | Open, large pores | Takes finish well |
| Source | Southern wetlands | Lower trunk sections |

### Northern Ash Species

| Species | Density | Janka | MOE | Notes |
|---------|:-------:|:-----:|:---:|-------|
| **White Ash** | 672 | 1,326 | — | Baseball bats; heavier |
| **Green Ash** | 627 | 1191 | 11.40 | Common |
| **Blue Ash** | 650 | 552 ᵉ | 9.66 | Rare |
| **Oregon Ash** | 616 | 1169 | 9.38 | Pacific Northwest |
| **Pumpkin Ash** | 575 | 452 ᵉ | 8.76 | Wetland |
| **Black Ash** | 549 | 854 | — | Basket wood |

**Emerald Ash Borer crisis:** Ash populations are declining across eastern US. Salvage wood is increasingly available.

---

## Part V: The Birch Family (Betulaceae)

| Species | Density | Janka | MOE | Notes |
|---------|:-------:|:-----:|:---:|-------|
| **Sweet Birch** | 728 | 1461 | 14.97 | Black birch; wintergreen scent |
| **Yellow Birch** | 694 | 1,259 | — | Classic cabinet wood |
| **Paper Birch** | 616 | 899 | 10.97 | White bark |
| **Alaska Paper Birch** | 610 | 505 ᵉ | 13.10 | Northern variant |

### American Hornbeam (*Carpinus caroliniana*)

| Property | Value |
|----------|:-----:|
| Density | 785 kg/m³ |
| Janka | 805 lbf |
| MOE | 11.68 GPa |
| Notes | "Musclewood" — very hard for its weight |

---

## Part VI: The Cherry & Rose Family (Rosaceae)

### Black Cherry (*Prunus serotina*)

The American body wood:

| Property | Value | Notes |
|----------|:-----:|-------|
| Density | 560 kg/m³ | Mahogany-weight |
| Janka | 950 lbf | Moderate |
| MOE | 10.24 GPa | Standard |
| Tone | "Warm, sweet mids — between maple and walnut" | |
| Workability | Excellent | Burns with dull tools |
| Finish | Darkens with age | Beautiful patina |

**Builder consensus:** "Tone falls somewhere between maple and walnut—not as 'transparent' as maple, or as 'dark' as walnut."

---

## Part VII: The Legume Family (Fabaceae) — American Members

### Black Locust (*Robinia pseudoacacia*)

| Property | Value | Notes |
|----------|:-----:|-------|
| Density | 770 kg/m³ | Rosewood-range |
| Janka | 777 lbf | Hard |
| MOE | 14.14 GPa | Stiff |
| Tone | "Rosewood-like with high density and low damping" | |
| Durability | Extremely rot-resistant | Fence posts last 50+ years |
| Status | **Invasive** in many areas | Harvest is ecological benefit |

**Builder feedback:** "Black locust works great for backs and sides, with sound very similar to rosewood."

### Honey Locust (*Gleditsia triacanthos*)

| Property | Value |
|----------|:-----:|
| Density | 719 kg/m³ |
| Janka | 1574 lbf |
| MOE | 11.24 GPa |
| Notes | Thorny; less common |

### Honey Mesquite (*Prosopis glandulosa*)

| Property | Value | Notes |
|----------|:-----:|-------|
| Density | 950 kg/m³ | Near-ebony weight |
| Janka | 2,345 lbf | Very hard |
| MOE | 11.58 GPa | Moderate |
| Tone | "Bright, crystalline highs, strong sustain — rosewood-like but more percussive" | |
| Status | **Invasive** | Texas/Southwest |
| Uses | Body, fretboard, bridge, accent | Versatile |

### Texas Ebony (*Ebenopsis ebano*)

| Property | Value | Notes |
|----------|:-----:|-------|
| Density | 965 kg/m³ | Ebony-weight |
| Janka | 1,179 lbf | Moderate for density |
| MOE | 16.54 GPa | **Stiff** |
| Notes | Legume, not true ebony | South Texas native |

---

## Part VIII: The Mulberry Family (Moraceae)

### Osage Orange (*Maclura pomifera*)

| Property | Value | Notes |
|----------|:-----:|-------|
| Density | 855 kg/m³ | Rosewood-range |
| Janka | 943 lbf | Hard |
| MOE | 11.64 GPa | Moderate |
| Color | Brilliant yellow → orange | Darkens with UV |
| Durability | Extremely rot-resistant | Bow wood |
| Status | Native hedge tree | Abundant |

### Red Mulberry (*Morus rubra*)

| Property | Value | Notes |
|----------|:-----:|-------|
| Density | 640 kg/m³ | Mahogany-range |
| CIRAD D12 | 0.63–0.64 | Consistent measurements |
| Distribution | Eastern US | Virginia specimens documented |
| Character | Related to Osage Orange | Same family |
| Availability | Common | Native forest tree |

**Note:** Red Mulberry is the main native *Morus*; Texas mulberry (*M. microphylla*) is also native to the Southwest (corrected 2026-11-14, see `VERIFICATION_LOG.md`). White Mulberry (*M. alba*) is Asian-origin but widely naturalized.

---

## Part IX: The Mahogany Family (Meliaceae) — Naturalized

### Chinaberry (*Melia azedarach*)

| Property | Value | Notes |
|----------|:-----:|-------|
| Density | 500 kg/m³ | Lightweight mahogany range |
| CIRAD D12 | 0.41–0.65 | Variable; typical 0.50 |
| Family | **Meliaceae** | Same family as true mahogany |
| Status | **Invasive** | Southern US, thoroughly naturalized |
| Origin | Asia | Introduced as ornamental |
| Character | Lightweight, workable | Untested for lutherie |

**Key insight:** Chinaberry is the most widespread **Meliaceae family member** growing wild in North America (West Indies mahogany, *Swietenia mahagoni*,, is native to south Florida) (corrected 2026-11-14, see `VERIFICATION_LOG.md`) — a domestic mahogany-family tree. Its invasive status means harvesting is ecologically beneficial (same argument as mesquite). D12 range of 0.50 places it lighter than Honduran Mahogany (0.55) but in the same acoustic territory. Unexplored for lutherie.

---

## Part X: Underexplored American Species

### Catalpa (*Catalpa speciosa*)

| Property | Value | Notes |
|----------|:-----:|-------|
| Density | ~420 kg/m³ | Lightweight |
| Character | Clear, bright; pronounced fundamentals | Few overtones |
| Workability | Excellent | Soft, resonant |
| Uses | Back/sides, necks, experimental tops | |
| Availability | Common ornamental | Large trees |

**Builder quote:** "Catalpa has been discussed as a replacement for Honduras Mahogany as a neck wood... very resonant."

### Sassafras (*Sassafras albidum*)

| Property | Value | Notes |
|----------|:-----:|-------|
| Density | ~480 kg/m³ | Light-medium |
| Character | Similar to Catalpa and Swamp Ash | |
| Workability | Excellent | Cuts, machines, sands nicely |
| Notable Use | **Fender Eric Johnson "Virginia" Strat** | |
| Availability | Eastern US | Can be hard to find large pieces |

### Persimmon (*Diospyros virginiana*)

| Property | Value | Notes |
|----------|:-----:|-------|
| Density | 835 kg/m³ | Rosewood-range |
| Janka | 902 lbf | Hard |
| MOE | 13.86 GPa | Good stiffness |
| Family | **Diospyros** — same as ebony | American ebony relative |
| Traditional Use | Golf club heads | Dense, shock-resistant |

**Key insight:** Persimmon is the main **American Diospyros** — a domestic ebony cousin (Texas persimmon, *D. texana*, is also native but grows as a small tree) (corrected 2026-11-14, see `VERIFICATION_LOG.md`).

### Dogwood (*Cornus florida*)

| Property | Value | Notes |
|----------|:-----:|-------|
| Density | 815 kg/m³ | Rosewood-range |
| Janka | 863 lbf | Hard |
| MOE | 13.26 GPa | Good |
| Grain | Very fine | Excellent for detail work |
| Availability | Small trees | Limited blank sizes |

### The Plane Family — Sycamore (*Platanaceae*)

North American "sycamore" is *Platanus* — the plane family — famous for the ray-fleck "lacewood" figure of quartersawn stock. (Note: British "sycamore" is a *maple*, *Acer pseudoplatanus* — a different, European tree — and is deliberately not grouped here.)

#### American Sycamore (*Platanus occidentalis*)

| Property | Value | Notes |
|----------|:-----:|-------|
| Density | 545 kg/m³ | Mahogany-weight |
| Janka | 410 lbf | Soft–moderate |
| MOE | 9.79 GPa | Lower stiffness |
| MOR | 69.0 MPa | Modest strength |
| Character | Warm, open, airy | Pronounced mids |
| Figure | Quartersawn = "lacewood" ray fleck | Dramatic |
| Availability | Very common | Large trees |

#### London Plane (*Platanus × acerifolia*)

The naturalized street-tree cousin (a *P. occidentalis* × *P. orientalis* hybrid), planted throughout US cities — the trade "lacewood." Not native, but abundant as urban-removal salvage.

| Property | Value | Notes |
|----------|:-----:|-------|
| Density | 560 kg/m³ | Mahogany-weight |
| Janka | 431 lbf | Soft–moderate |
| MOE | 8.9 GPa | Low stiffness |
| MOR | 74.7 MPa | Modest strength |
| Figure | Even more pronounced lacewood | Prized for veneer |
| Availability | Common | Urban salvage |

**Note:** American Sycamore and London Plane are near-identical in the shop — both mahogany-weight, low-stiffness, and defined by that lacewood ray fleck. London Plane's figure is often the showier of the two.

### The Elm Family (*Ulmaceae*)

Elms are defined by **interlocked grain** — the source of their legendary toughness and steam-bending ability (historically chair seats, wheel hubs, and boat keels). That same interlock resists splitting and makes them bend superbly, a genuine advantage for guitar sides. Density spans mahogany-weight to upper-Koa range.

| Species | Density | Janka | MOE | MOR | Notes |
|---------|:-------:|:-----:|:---:|:---:|-------|
| **American Elm** (*U. americana*) | 560 | 832 | 9.24 | 81.0 | Classic; declining (Dutch elm disease) |
| **Red / Slippery Elm** (*U. rubra*) | 594 | 854 | 10.28 | 90.0 | Warmer color |
| **Cedar Elm** (*U. crassifolia*) | 655 | 576 ᵉ | 10.21 | 93.1 | Texas / South-Central |
| **Winged Elm** (*U. alata*) | 675 | 609 ᵉ | 11.38 | 102.1 | Highest-MOE domestic elm |
| **Rock Elm** (*U. thomasii*) | 706 | 749 ᵉ | 10.62 | 102.0 | **Densest US elm**; upper-Koa range |

**Key points:**
- **Steam-bending:** the interlocked grain that resists splitting also bends without cracking — an unusual and useful profile for back/sides.
- **Rock Elm** (706) reaches the upper-mahogany/Koa tier — the densest and toughest of the group.
- **American Elm** is in decline from Dutch elm disease, so much market elm is salvage — the same salvage story as ash (EAB).
- Untested as a tonewood; the toughness-plus-bendability combination is worth trialing.

### The Gum Group — Sweetgum & Tupelo

Two unrelated North American families both called "gum" — and **not** the Australian eucalyptus "gums" (which are excluded from this domestic guide). Both are diffuse-porous, interlocked-grained, mahogany-weight or lighter, abundant, and cheap.

#### Sweetgum (*Liquidambar styraciflua*)

Trade names: "satin walnut," "redgum," "sap gum."

| Property | Value | Notes |
|----------|:-----:|-------|
| Density | 545 kg/m³ | Mahogany-weight |
| Janka | 410 lbf | Soft–moderate |
| MOE | 11.31 GPa | Standard |
| MOR | 86.2 MPa | Moderate |
| Grain | Interlocked | Ribbon figure quartersawn; **prone to warp** |
| Availability | Very common | Abundant SE hardwood |

**Working caveat:** the interlock that gives quartersawn sweetgum its ribbon stripe also makes it warp-prone in drying — the reason it stays underused despite abundance. Stable, quartersawn stock is the way in.

#### Tupelo / Blackgum (*Nyssa*)

| Species | Density | Janka | MOE | MOR | Notes |
|---------|:-------:|:-----:|:---:|:---:|-------|
| **Black Tupelo / Blackgum** (*N. sylvatica*) | 560 | 809 | 8.3 | 66.0 | Fine, uniform texture |
| **Water Tupelo** (*N. aquatica*) | 560 | 877 | 8.7 | 66.0 | Swamp-native; light |

**Character:** *Nyssa* is famous for fine, uniform texture and interlocked grain — tough, hard to split, and a prized carving timber. Low stiffness (MOE ~8–9 GPa) makes it a body/back candidate rather than a top or structural wood. Experimental for lutherie.

---

## Part XI: American Softwoods for Tops

### Sitka Spruce (*Picea sitchensis*)

The acoustic guitar top standard:

| Property | Value |
|----------|:-----:|
| Density | 400–450 kg/m³ |
| MOE | Very high for weight |
| Character | Bright, dynamic, powerful |
| Source | Pacific Northwest, Alaska |

### Engelmann Spruce

| Property | Value |
|----------|:-----:|
| Density | 350–400 kg/m³ |
| Character | Warmer than Sitka; responds to light touch |
| Source | Rocky Mountains |

### Adirondack (Red) Spruce

| Property | Value |
|----------|:-----:|
| Density | 400–450 kg/m³ |
| Character | Powerful; pre-war Martin standard |
| Status | Limited old-growth; plantation coming |

### Western Red Cedar

| Property | Value |
|----------|:-----:|
| Density | 350–380 kg/m³ |
| Character | Warm, immediate; classical standard |
| Source | Pacific Northwest |

### Port Orford Cedar (*Chamaecyparis lawsoniana*)

| Property | Value |
|----------|:-----:|
| Density | 482 kg/m³ |
| Character | Between spruce and cedar |
| Source | Oregon coast |

### Redwood (*Sequoia sempervirens*)

| Property | Value |
|----------|:-----:|
| Density | 400–450 kg/m³ |
| Character | Warm, complex; endangered old-growth |
| Source | Salvage only |

### Bald Cypress (*Taxodium distichum*)

| Property | Value | Notes |
|----------|:-----:|-------|
| Density | 510 kg/m³ | Heavier than spruce |
| Janka | 510 lbf | Soft |
| MOE | 9.93 GPa | Moderate |
| Tone | "Dry, percussive, bright" | Cypress family; flamenco-style use |
| Uses | Back/sides | Not a top wood |
| Rot-resistance | Excellent | Swamp-native |
| Source | Southeastern US swamps | Louisiana, Florida |

**Key insight:** The traditional flamenco back/sides wood is Spanish/Mediterranean cypress (*Cupressus sempervirens*), not Bald Cypress. Bald Cypress is a domestic cypress-family alternative with a similar dry, snappy attack (corrected 2026-11-14, see `VERIFICATION_LOG.md`). It's a conifer (softwood) but used for body work, not tops.

---

## Part XII: Density Tiers & Substitution Guide

### Tier 1: Lightweight (350–500 kg/m³)

*Mahogany substitutes for lightweight builds:*

| Species | Density | Best For |
|---------|:-------:|----------|
| Catalpa | 420 | Back/sides, necks |
| Sassafras | 515 | Bodies, back/sides |
| Butternut | 426 | Lightweight bodies |
| Swamp Ash | 480 | Electric bodies |
| **Chinaberry** | 500 | **Meliaceae family — unexplored** |
| Black Ash | 549 | Lighter alternative |

### Tier 2: Mahogany Range (500–650 kg/m³)

*Direct mahogany substitutes:*

| Species | Density | Best For |
|---------|:-------:|----------|
| **Bald Cypress** | 515 | **Flamenco-style back/sides alternative — dry, percussive** |
| Sweetgum | 582 | Back/sides (warp-prone; use quartersawn) |
| Black Tupelo / Blackgum | 560 | Body, back/sides (experimental) |
| American Sycamore | 549 | Back/sides, experimental tops |
| Water Tupelo | 560 | Body, back/sides (experimental) |
| Black Cherry | 560 | Body, back/sides |
| American Elm | 560 | Back/sides (tough; bends well) |
| London Plane | 560 | Back/sides (naturalized; lacewood figure) |
| Red / Slippery Elm | 594 | Back/sides (tough; bends well) |
| Black Walnut | 616 | Back/sides, bodies |
| Soft Maple | 605 | Bodies |
| **Red Mulberry** | 640 | **Moraceae family — related to Osage Orange** |

### Tier 3: Upper Mahogany / Koa Range (650–800 kg/m³)

*Koa/premium mahogany substitutes:*

| Species | Density | Best For |
|---------|:-------:|----------|
| Cedar Elm | 655 | Back/sides (tough; bends well) |
| Winged Elm | 675 | Back/sides (highest-MOE elm) |
| Hard Maple | 706 | Necks, tops |
| Pecan | 739 | Back/sides |
| Rock Elm | 706 | Back/sides (densest US elm) |
| White Oak | 762 | Back/sides |
| Black Locust | 773 | Back/sides (rosewood-like) |
| Shagbark Hickory | 806 | Back/sides |

### Tier 4: Rosewood Range (800–1,000 kg/m³)

*Rosewood substitutes:*

| Species | Density | Best For |
|---------|:-------:|----------|
| Pignut Hickory | 840 | Back/sides |
| Persimmon | 835 | Fretboard, bridge |
| Dogwood | 815 | Fretboard (small blanks) |
| Osage Orange | 855 | Bridge, accent |
| Honey Mesquite | 950 | Body, fretboard, bridge |
| Texas Ebony | 965 | Fretboard, bridge |
| Live Oak | 986 | Fretboard, bridge |

### Tier 5: Ebony Range (1,000+ kg/m³ — no domestic species reaches it; the nearest are 950–986)

*Ebony substitutes:*

| Species | Density | Best For |
|---------|:-------:|----------|
| Live Oak | 986 | Fretboard, bridge |
| Texas Ebony | 965 | Fretboard, bridge |
| Honey Mesquite | 950 | Near-ebony applications |

---

## Part XIII: The "Texas Trio" — Best Domestic Dense Options

Three Texas/Southwest species cover 950–986 kg/m³:

| Species | Density | Janka | MOE | Status |
|---------|:-------:|:-----:|:---:|--------|
| **Honey Mesquite** | 950 | 2,345 | 11.58 | Invasive — harvest beneficial |
| **Texas Ebony** | 965 | 1,179 ᵉ | 16.54 | Native; not restricted |
| **Live Oak** | 986 | 1,260 ᵉ | 13.7 | Abundant SE US |

**Combined range:** These three span the entire rosewood-to-ebony bridge zone with zero import issues.

---

## Part XIV: Stiffness Champions (Highest MOE)

For bridges and structural applications:

| Species | MOE (GPa) | Density | Notes |
|---------|:---------:|:-------:|-------|
| **Texas Ebony** | 16.54 | 965 | Stiffest American hardwood |
| **Cherrybark Oak** | 15.70 | 762 | High MOE oak |
| **Pignut Hickory** | 15.59 | 840 | Dense hickory |
| **Mockernut Hickory** | 15.31 | 806 | Dense hickory |
| **White Oak** | 12.3 | 762 | Classic |
| **Sweet Birch** | 14.97 | 728 | Wintergreen birch |
| **Shagbark Hickory** | 14.90 | 806 | Classic hickory |
| **Black Locust** | 14.14 | 773 | Rosewood-like |
| **Water Hickory** | 13.93 | 694 | Lighter hickory |
| **Persimmon** | 13.86 | 835 | American ebony cousin |

---

## Part XV: Regional Availability

### Eastern US

Most abundant selection:
- All oaks (white, red, live)
- All hickories and pecan
- Black walnut, butternut
- Cherry, beech, birch
- Ash (declining due to EAB)
- Elm (American, red, winged, rock — declining, Dutch elm disease)
- Sweetgum, tupelo/blackgum
- Persimmon, dogwood
- Black locust, honey locust
- Sassafras, catalpa
- American sycamore

### Pacific Northwest

- Oregon white oak
- Oregon ash
- Pacific maple
- All softwoods (Sitka, Engelmann, cedar, redwood)

### Texas/Southwest

- Honey mesquite (invasive)
- Texas ebony
- Live oak
- Osage orange
- Cedar elm

### Rocky Mountains

- Engelmann spruce
- Various pines

---

## Part XVI: Sustainability Notes

### Invasive Species (Harvest = Ecological Benefit)

| Species | Status |
|---------|--------|
| **Honey Mesquite** | Invasive in TX, NM, AZ |
| **Black Locust** | Invasive outside native range |
| **Chinaberry** | Invasive in southern US |
| **Osage Orange** | Naturalized; abundant |

### Abundant Native Species

| Species | Availability |
|---------|-------------|
| White/Red Oak | Very common |
| Hard/Soft Maple | Very common |
| Black Walnut | Common |
| Black Cherry | Common |
| Hickory/Pecan | Common in range |
| American Sycamore | Very common |

### Limited/Declining

| Species | Status |
|---------|--------|
| Ash species | Emerald Ash Borer crisis |
| American Elm | Dutch elm disease (salvage common) |
| American Chestnut | Blight-decimated |
| Old-growth softwoods | Limited |

---

## Summary

**About 70 North American species** covered. Key findings:

1. **Juglandaceae family** (walnut + hickory) spans 430–840 kg/m³ — from lightweight to rosewood-range
2. **Pignut/Mockernut/Shagbark hickory** at 806–840 kg/m³ belong in rosewood discussions
3. **Persimmon** is the main American *Diospyros* — a domestic ebony cousin
4. **Chinaberry** is the most widespread wild **Meliaceae** (mahogany family) — invasive, unexplored for lutherie
5. **Red Mulberry** and **Osage Orange** are both Moraceae — same family, similar potential
6. **Black Locust** is "rosewood-like with high density and low damping" — and invasive
7. **The Texas Trio** (Mesquite, Texas Ebony, Live Oak) covers 950–986 kg/m³
8. **Catalpa and Sassafras** are proven mahogany alternatives
9. **Bald Cypress** is a domestic alternative to the traditional flamenco cypress (*Cupressus sempervirens*) — dry, percussive, snappy
10. **American Sycamore** (and its naturalized cousin **London Plane**) offer dramatic lacewood figure at mahogany weight
11. **Texas Ebony** has the highest MOE (16.54 GPa) of any American hardwood
12. **Pecan** is the most *available* hickory (orchard salvage) — warm, firm, mid-density (739)
13. **Elm** (Ulmaceae) pairs unusual toughness with excellent steam-bending; **Rock Elm** (706) is the densest, reaching the upper-mahogany/Koa tier
14. **Sweetgum** and **Tupelo/Blackgum** — the true North American "gums" (not eucalyptus) — are abundant, cheap, mahogany-weight, and underexplored

No imports required. Every wood here grows in North America.

---

## Sources

### Web Research
- [UMGF: Alternative Acoustic Guitar Tonewoods of USA & Canada](https://umgf.com/alternative-acoustic-guitar-tonewoods-of-usa-canad-t152994.html)
- [UMGF: Catalpa One-Wood Guitar Project](https://umgf.com/catalpa-a-one-wood-guitar-project-t103292.html)
- [UMGF: Black Locust as Fretboard and Bridge Wood](https://umgf.com/black-locust-as-a-fretboard-and-bridge-wood-t107550.html)
- [UMGF: All North American Woods Guitar](https://umgf.com/all-north-american-woods-guitar-t221557.html)
- [TDPRI: Swamp White Oak as Tonewood](https://www.tdpri.com/threads/swamp-white-oak-as-a-tonewood.366011/)
- [Acoustic Guitar Forum: Red vs White Oak](https://www.acousticguitarforum.com/forums/showthread.php?t=448137)
- [UMGF: Cherry as Tonewood](https://umgf.com/tell-me-about-cherry-as-a-tonewood-for-acoustic-gu-t135871.html)
- [Exotic Wood Zone: Swamp Ash Overview](https://exoticwoodzone.com/pages/swamp-ash)
- [Guitar Player: Tonewood Tutorial](https://www.guitarplayer.com/gear/tonewood-tutorial-everything-you-need-to-know-about-tonewoods)
- [Taylor Guitars: Body Woods](https://www.taylorguitars.com/guitars/acoustic/features/woods/body-woods)
- [RC Tonewoods: Catalpa](https://www.rctonewoods.com/RCT_Store/product-category/back-side-domestic/catalpa/)
- [American Specialty Hardwoods](https://americanspecialtyhardwoods.com/)

### Database Sources
- `wood_species.json` v4.0.0
- CIRAD Wood Density Database (North American entries)
