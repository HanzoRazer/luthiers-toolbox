# Bridge Break Angle — Corrected Geometry Derivation

## The Physical Setup (Cross-Section View)

```
         saddle crown
              ●  ← string bends here
             /|
            / |
           /  |  h = saddle projection above bridge surface
          /   |
         /  θ |
        ●─────┘
   string      bridge surface (top of bridge wood)
   exit        
   point       
   ├─── d ───┤
```

The string runs from the **exit point** at the bridge surface (where it emerges from the slotted pin hole) up and over the **saddle crown**. The break angle θ is formed at the saddle crown between the string and the horizontal plane.

---

## Why v1 Was Wrong

The v1 model used:

```
         saddle crown
              ●
             /|
            / |
           /  |  h_plate = saddle height above bridge PLATE
          /   |
         /    |
        /     |            ┬ bridge thickness
       /      |            │ (6-11 mm of wood)
      /       |            │
     ●────────┘            ┴
  pin center    bridge plate (underside of soundboard)
  ├── d_pin ──┤
```

Two errors:

1. **Height measured from the wrong surface.** The string doesn't originate at the bridge plate — it exits at the bridge **top surface** through a slotted hole. The bridge plate is 6–11 mm lower, inside the guitar body. Measuring from the plate inflates *h* by the full bridge thickness.

2. **Horizontal distance from the wrong point.** The pin hole is **tapered and slotted** toward the saddle. The slot shifts the string's exit point ~1–1.5 mm closer to the saddle than the pin center. Using pin center distance inflates *d*.

These errors partially cancelled (both inflate numerator and denominator), which is why v1 produced plausible-looking angles — but the thresholds derived from this geometry were meaningless.

---

## The Corrected Model

**Given:**

- *d* = horizontal distance from string exit point to saddle crown center (mm)
- *h* = saddle crown height above the bridge **top surface** (mm)

**The right triangle:**

The string path from exit to saddle crown forms the hypotenuse of a right triangle where:

- Opposite side = *h* (vertical: saddle projection above bridge surface)
- Adjacent side = *d* (horizontal: string exit to saddle crown)

**Break angle:**

$$\theta = \arctan\!\left(\frac{h}{d}\right)$$

---

## Accounting for the Slotted Pin Hole

The pin hole has a ramp slot cut toward the saddle to accommodate the string diameter. This moves the effective string exit point closer to the saddle:

$$d = d_{\text{pin center}} - \delta_{\text{slot}}$$

Where δ_slot ≈ 1.0–1.5 mm depending on string gauge and slot geometry.

**Example for a Martin D-28:**

- d_pin center = 5.5 mm
- δ_slot ≈ 1.2 mm
- d = 5.5 − 1.2 = **4.3 mm**

---

## Saddle Projection vs. Protrusion

The saddle sits in a slot routed into the bridge. Only the portion **above the bridge surface** creates break angle:

$$h = h_{\text{blank}} - h_{\text{seated}}$$

Where *h_seated* is the depth of saddle inside the slot (equal to the slot depth cut into the bridge wood, not through the soundboard).

The v1 model called this `saddle_protrusion_mm` but described it as "above the bridge plate" — which is a different surface entirely.

---

## Carruth's Empirical Minimum

Alan Carruth's testing established that the break angle's acoustic contribution is essentially binary:

$$\theta_{\min} \approx 6°$$

- **Below 6°:** The string's downward force on the saddle crown,

$$F_{\perp} = T \cdot \sin(\theta)$$

  where *T* is string tension, becomes insufficient to prevent the string from vibrating **laterally along the saddle crown** rather than purely in the intended plane. This causes buzzing, muting, or inconsistent tone.

- **Above 6°:** F⊥ is sufficient to seat the string firmly. Further increases in θ do not meaningfully change the acoustic coupling. The saddle is already transmitting string energy to the soundboard effectively.

---

## Minimum Projection from the 6° Threshold

Given the minimum angle and a typical exit distance:

$$h_{\min} = d \cdot \tan(6°) = d \times 0.1051$$

For *d* = 4.5 mm (typical):

$$h_{\min} = 4.5 \times 0.1051 \approx 0.47 \text{ mm}$$

But Carruth's practical minimum is **~1.6 mm (1/16")**, which is higher than the pure trig minimum because:

- String gauge variation shifts the effective exit point
- Saddle crown radius means the contact point shifts with action height
- Over time, the saddle wears a groove that lowers effective projection

At 1.6 mm projection and 4.5 mm distance:

$$\theta = \arctan\!\left(\frac{1.6}{4.5}\right) = 19.6°$$

This is well above 6° — the 1/16" rule gives a large safety margin.

---

## What Actually Drives Break Angle

The real equation for break angle in the full system is:

$$\theta = \arctan\!\left(\frac{h_{\text{bridge}} + h_{\text{saddle projection}} - h_{\text{string at pin}}}{d}\right)$$

Where *h_bridge* depends on:

- **Neck angle** α: A steeper neck angle requires a taller bridge to maintain action height, which increases available saddle projection
- **Bridge thickness**: Limits maximum slot depth and therefore maximum projection

This is why Charles noted that neck angle and bridge thickness are **far more influential** on achievable break angle than pin placement. You can move pin holes around all day, but *d* only varies by ~2 mm. The neck angle can swing the required bridge height by 5–10 mm.

---

## v1 → v2 Threshold Comparison

| Parameter | v1 (incorrect) | v2 (corrected) |
|-----------|----------------|----------------|
| Horizontal measurement | Pin center to saddle | String exit to saddle |
| Vertical measurement | Saddle above bridge plate | Saddle above bridge surface |
| Minimum threshold | 18° (fabricated) | **6°** (Carruth empirical) |
| "Optimal" band | 23–31° (fabricated) | **Removed** — no tonal gradient above 6° |
| Ratings | optimal / acceptable / too_shallow / too_steep | **adequate** / too_shallow / too_steep |
| Steep limit | 38° | 38° (mechanical — unchanged) |

---

## Origin Disclosure

The v1 formula and 23–31° "optimal" range were **not from a published lutherie source**. They were AI-synthesized consensus: a blend of forum posts, general engineering trigonometry, and averaged numbers that multiple AI models agreed on. The Martin/Gibson distance measurements are real, but the thresholds were fabricated confidence — numbers that sound authoritative but aren't grounded in empirical testing.

The v2 correction is based on:

1. **Alan Carruth** — break angle testing establishing the ~6° minimum
2. **Charles (luthier)** — geometry correction: measure from bridge surface, account for slotted/tapered pin holes, recognize that neck angle and bridge thickness are the dominant variables
3. **Industry practice** — 1/16" (1.6 mm) minimum saddle projection as a practical rule of thumb
