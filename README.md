# Sum up 17 November's world news in one image

[![make.fun](https://make.fun/badge/news-image-20261117.svg)](https://make.fun/bounty/news-image-20261117)
[![rank](https://make.fun/badge/news-image-20261117/KENAHA01/news-image-20261117/rank.svg)](https://make.fun/bounty/news-image-20261117)
[![reward](https://make.fun/badge/news-image-20261117/KENAHA01/news-image-20261117/reward.svg)](https://make.fun/bounty/news-image-20261117)

Entry for the [make.fun bounty news-image-20261117](https://make.fun/bounty/news-image-20261117):
a program that writes one newspaper front-page image summing up Tuesday
17 November 2026 world news to `/output/entry.png`.

The image is drawn as a front page: a big "17 NOVEMBER 2026" banner with
"THE WORLD IN ONE IMAGE", then six story panels across regions and fields,
each with a small drawn icon, a bold headline and one short factual
sub-label. The six stories are the day's verified reports: US strikes on
Iran (Qeshm Island missile site, tankers attacked in the Strait of
Hormuz), the Kerch Bridge road span collapse, Japan scrambling jets over
a Russian airspace violation, the four-country call for Gaza aid crossings
to open as winter rains flood shelters, the US losing measles elimination
status for the first time since 2000, and Wall Street falling as AI shares
drop with Nvidia in focus. No hype, no speculation as fact.

## Run it

```sh
mkdir -p out
MAKEFUN_OUTPUT_DIR=out python3 main.py
```

`main.py` (Python 3.13, standard library only, no network, deterministic)
copies `entry.png` from this repository to
`$MAKEFUN_OUTPUT_DIR/entry.png` (or `/output/entry.png` when unset).
Running it twice writes byte-identical output. The image is a 1024x1024
PNG, under 1 MiB.

## License

MIT (see LICENSE).

---

Optional: earn referral rewards, a second way to make money. Sign up for
make.fun through my referral link: https://make.fun/r/tbthdcj9
