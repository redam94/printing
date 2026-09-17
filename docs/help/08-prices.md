---
title: Prices and turnaround
order: 8
summary: Exactly how a price is built, what it includes, and how long things take.
---

Every quote shows its working, and the price you confirm is the price you pay.

## How a price is built

| Part of the price | How it is worked out |
|---|---|
| Filament | The weight of the part, calculated from the design: {price.shell} walls plus {price.infill} infill, at the material's price per kilo |
| Printer time | {price.machine_per_h} an hour of printing, plus {price.setup_min} minutes of setup |
| Handling | Cleaning up and checking, about {price.post_min} minutes a part, at {price.labor_per_h} an hour |
| Design | {price.design_fee} per request — the modelling, and every revision you ask for |
| Minimum | {price.min_charge} per order |

Totals include a {price.margin} margin and are rounded to the nearest 50 cents. Quantities are priced per part: ten of something costs ten times the filament and printing, but the design fee is paid once.

## What that works out to

Most small holders, clips and brackets land between {price.min_charge} and $40. A full enclosure or a large decorative piece is usually $30–$80. [The work page on the site]({site}) lists real designs with their real prices, so you can find something similar in size to yours.

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
