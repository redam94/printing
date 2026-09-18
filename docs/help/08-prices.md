---
title: Prices and turnaround
order: 8
summary: The two numbers on every quote (the print price and the design fee), worked examples, what is included, and how long things take.
---

Every quote shows its working, and the price you confirm is the price you pay. A price is two numbers: the **print price**, worked out from the part itself, and a flat **design fee** that depends on how much design is new.

## The print price

| Part of the price | How it is worked out |
|---|---|
| Filament | The weight of the part, calculated from the design: {price.shell} walls plus {price.infill} infill, at the material's price per kilo ({price.pla_kg} PLA, {price.petg_kg} PETG, {price.tpu_kg} TPU, {price.asa_kg} ASA) |
| Printer time | {price.machine_per_h} an hour on the printer, from setup to the last layer |
| Handling | Setup, cleanup and checking against the measurements, at {price.labor_per_h} an hour: {price.setup_min} minutes a job plus about {price.post_min} minutes a part |

Those three, plus a {price.margin} margin, rounded up to the nearest 50 cents, and never less than **{price.min_charge}**. Quantity multiplies the print price only: five of something costs five times the filament and printing, but the design is paid once.

## The design fee

Every design is built from a library of parts that have already been printed and measured (see *Designed from proven parts*), so most requests are a matter of fitting, not inventing. The fee reflects how much is new:

| Case | Fee | When it applies |
|---|---|---|
| Existing design, or your own file | {price.design_none} | A piece from [the work page]({site}) printed as it is, a reprint, or an STL you send us |
| Fitted to your object | {price.design_adapt} | An existing design or the library parts, resized and rearranged around your measurements. Most requests land here |
| Designed from scratch | {price.design_fee} | Nothing on file fits, so it is drawn from your description. One flat fee, however many revisions it takes |

The quote names which case it is. If you think a request was put in the wrong one, say so on the request.

## Worked examples

Priced from real designs, exactly as a request would be today:

{price.examples_table}

[The work page on the site]({site}) lists every published design with its print price, so you can find something similar in size to yours.

## What is included

- Designing the part, and **every revision** until you are happy.
- The 3D model, the measurements and the quote itself.
- Cleanup, checking against the measurements, and a reprint if a print fails or a part comes out flawed.

## What is not

- **Materials we do not stock**, if you need a special colour or a technical filament: quoted separately.
- **Sanding, priming or painting**: hand work, quoted separately.
- **Metal parts**: brass inserts, screws, magnets and bearings are charged at cost when a design needs them.
- **Delivery**: arranged on the request.

## Turnaround

| Stage | Usual time |
|---|---|
| Request to first quote | 2–3 working days |
| A revision | About a day |
| Queue before printing | {price.queue_days} days |
| Printing | 2–4 hours for a palm-sized part; large parts run overnight |

A working day is {price.hours_per_day} hours of machine time. Your quote gives the estimate for your part, counted from the day you confirm. If you have a deadline, put it on the request and it is planned around.

::: tip Nothing is charged until you confirm
A request you cancel costs nothing, however many revisions it went through. The design fee is part of the quote you accept, not a fee for asking.
:::
