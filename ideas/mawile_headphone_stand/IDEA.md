---
title: Mawile headphone stand
status: parked
kind: part
created: 2026-09-07
updated: 2026-09-07
tags: [headphone stand, pokemon, mawile, figure, form, multi-material]
hardware: []
reuse: [form.blob_outline, form.revolved_body, fasteners.clearance_hole]
gaps: [primitives.tenon_socket]
model:
---

## Problem
A headphone stand shaped like Mawile (the Pokemon with the huge steel jaws on the back of its
head).  The jaws are the point: the headband rests over the upper jaw, the mouth hangs open behind
the head, the cable can loop through the mouth.

## Concept
From the reference photo brief (inspiration/lea7563bfd9.md), borrowing: "oversized black jaw-mane
sweeping upward from the body", "sharp white triangular teeth arranged along jaw edge", "smooth
tapering curve of the jaw from back to front", "compact body-to-jaw size contrast".  Not borrowed:
the face, arms and dress detail (a stylised bell silhouette stands in for them).

Stylised, not a figurine: a yellow bell-dress body with a round head and two black ear flaps on a
blob base; the jaw is a big black horn that leaves the back of the head, arches up and over, and
comes down to rest on the base behind her, wide "mouth" end at the bottom, 5 teeth along the inner
(concave) edge pointing at her back.  The top of the arch is the headband saddle (46 x 30 mm section
there); the mouth end on the base is a second foot, so the loaded stand cannot tip.  The first
concept (crocodile mouth behind the head, rounds 1-3) was wrong and is dropped.

## Constraints
- Saddle: headband width up to 45 mm, ear cups hang either side (+/-X) and must clear the body:
  jaws extend >= 60 mm behind the head; total height ~ 250 so over-ear cups clear the base.
- Base wide enough not to tip with 350 g headphones cantilevered backward: ~110 x 80 mm footprint,
  or weight the base (heat-set nut pocket for a steel plate) if the sketch says it tips.
- Two parts, two colours (body yellow, jaws black), joined by a rectangular tenon + socket with a
  0.3 mm slip fit; both parts print upright without supports.
- Jaws print with the mouth opening UP so the teeth are short overhangs, then rotate 90 deg to mount.

## Reuse map
| need | component | notes |
|---|---|---|
| two-foot base outline | form.blob_outline | three overlapping circles, smoothed |
| body / head silhouette | form.revolved_body | (r, z) profile, spline |
| soft skin (optional) | form.textured | exterior-only, if the plain surface looks too CAD |
| arched jaw (loft along a path) + saddle | freehand in the sketch | candidate for form.lofted_horn if it recurs |
| tenon / socket joint | gap: primitives.tenon_socket | elliptical stub + clearance pocket, twice (head, base) |
| pin holes joining the halves | fasteners.clearance_hole | M3 clearance, filament or screw shank as the pin |

## Gaps
- primitives.tenon_socket: boss + negative pocket pair for plugging two printed parts together.

## Open questions
- Which headphones (band width, cup size) so the saddle and the cup clearance are sized to them?
- Base weighting needed?  Sketch will report the centre of mass.
- Teeth as a third (white) part for the fourth toolhead, or painted in the slicer?

## Log
- 2026-09-07 captured from chat ("headphone stand kind of shaped like Mawile"); first sketch
- 2026-09-07 sketch round 1: through-cut mouth and floating teeth; jaws' hinge end had 1 cm2 of bed
  contact; tenon underside flat; mass behind the feet.
- 2026-09-07 reference photo filed (inspiration/lea7563bfd9.md, Haiku brief): the jaw is a mane
  arching up from the back of the head, not a mouth behind it.  Rounds 1-3 dropped.
- 2026-09-07 sketch round 5: jaw = loft of 10 ellipse sections along a YZ arc from the head root
  (24 x 16) over the apex (46 x 30 at z 250) to the mouth end (70 x 50) standing on the base; split
  on the mid-plane into two halves printed flat face down (no overhang at all), M3 pin holes,
  root tenon into the head and foot tenon into the base (0.3 clearance).  Body 128 x 204 x 197
  (dress + head profile kept <= 45 deg), halves 267 x 150 x 35 each.  ~576 g PLA at 35 % fill;
  with 350 g headphones on the apex the CoM stays inside the footprint.  Waiting on the user.
- 2026-09-07 (superseded) sketch round 3: mouth is a pocket with 8 mm
  cheeks; jaws print mouth-up on a flat 50 mm hinge face with 45 deg flanks; tenon is a trapezoid with
  a 41 deg underside (no support) into a blind socket that opens on the jaws' bed face; rear base lobe
  under the jaws.  Body 140 x 130 x 247, jaws 56 x 88 x 106, ~333 g PLA at 35 % fill.  Combined CoM
  with 350 g headphones at y = -95 sits 28 mm inside the rear edge.  Only remaining overhangs are the
  24 teeth cones (970 mm2), acceptable or make them 45 deg pyramids.  Waiting on: headphone band
  width / cup size, colours (jaws black, body yellow, teeth painted), go-ahead to promote.
- 2026-09-07 parked by the user ("table it for now") after sketch round 5; resume from the Open questions above
