# Directional Stress Model Backtest

Date: 2026-07-04

## Purpose

This replay validates the current production GFCRI engine after two major model changes:

1. Directional stress scoring:
   - high-is-worse nodes only add pressure when z-score is positive;
   - low-is-worse nodes only add pressure when z-score is negative;
   - two-sided nodes use absolute z-score.
2. Dimension-weighted `SI_CREDIT`:
   - US Corporate Credit
   - EM / Sovereign Credit
   - Europe Credit
   - Bank Funding
   - Default / Downgrade Cycle
   - China Credit
   - AI / Cloud Credit

Command:

```bash
python3 scripts/backtest_current_engine_replay.py all
```

## Replay Summary

| Crisis | Peak event GFCRI | Window peak | Peak month | Pressure level | First warning | First orange | Avg coverage |
|---|---:|---:|---|---|---|---|---:|
| 1987 Black Monday | - | 37.9 | 1988-04 | elevated_pressure | 3m after | - | 4.0 |
| 1992 ERM Crisis | 26.6 | 34.4 | 1993-04 | elevated_pressure | 3m before | - | 5.0 |
| 1994 Global Bond Massacre | 28.4 | 31.8 | 1994-03 | elevated_pressure | 9m before | - | 5.0 |
| 1997 Asian Financial Crisis | 31.5 | 44.5 | 1998-08 | high_transmission_pressure | 12m before | - | 5.0 |
| 2000 Dot-Com Bust | 45.0 | 58.7 | 2001-09 | severe_pre_crisis_pressure | 33m before | 24m before | 6.0 |
| 2010 Eurozone Debt Crisis | 37.1 | 49.0 | 2011-09 | high_transmission_pressure | 22m before | - | 10.0 |
| 2015 China Equity / RMB Shock | 30.9 | 36.6 | 2015-08 | elevated_pressure | 7m before | - | 10.0 |
| 2018 Fed Hikes / Christmas Selloff | 29.9 | 33.2 | 2018-10 | elevated_pressure | 11m before | - | 10.0 |
| 2020 COVID Panic | 57.0 | 57.0 | 2020-03 | severe_pre_crisis_pressure | same month | same month | 10.0 |
| 2022 Aggressive Fed Hikes | 40.5 | 51.8 | 2022-09 | high_transmission_pressure | 8m before | 1m before | 10.0 |

Insufficient replay coverage:

- 1971 Nixon shock
- 1973 oil crisis
- 1980 Volcker tightening

The early historical windows lack enough production-node market data in Yahoo/FRED-compatible form, especially VIX and HSI.

## Interpretation

The directional-stress model is less aggressive than the previous absolute-z-score version. This is expected and desirable:

- Risk-improving anomalies no longer increase pressure.
- False positives from narrowing credit spreads, rising equity markets, or improving ETF prices are reduced.
- The model still detects major modern stress episodes, especially 2000, 2020, and 2022.

Important changes:

- 2020 COVID panic remains orange at the peak month.
- 2022 aggressive rate hikes reaches orange one month before the peak stress month.
- 2000 dot-com stress remains the strongest replay result, with a window peak near 59.
- 2010 Eurozone debt crisis is close to orange but does not cross the 50 threshold in this replay.
- 1997 Asian crisis reaches high yellow but not orange under current production-node coverage.

## Calibrated Alert Thresholds

The directional model uses cleaner but lower scores than the previous absolute-z-score model. The first calibrated threshold set is:

```text
green   < 25
yellow  25-45
orange  45-60
red     >= 60
```

Rationale:

- `45+` captures modern high-pressure windows such as 2000, 2020, and 2022.
- `60+` is reserved for crisis-grade pressure after directional false positives are removed.
- The old `50/75` orange/red thresholds were calibrated on a noisier absolute-z-score model and are too high for the directional model.

## Current Limitations

1. Historical coverage is uneven.
   - Older crises are under-covered by production nodes.
   - The replay should not be used as final validation for 1970s/1980s events.

2. Damage levels in replay output are not yet reliable.
   - Many replay rows show `no_material_damage` because the realized-damage taxonomy uses current-style factor mapping and does not yet ingest event-specific realized damage data during replay.
   - Historical damage labels should come from the damage taxonomy dataset, not from sparse replay node coverage.

3. Credit history still lacks Europe/China/default data for older windows.
   - Newly added FRED and AKShare nodes improve current scoring, but long historical replay needs compatible series and crisis-specific mappings.

4. Thresholds need recalibration.
   - Directional scoring lowers the overall pressure scale.
   - Warning/orange/red thresholds should be recalibrated against the new model rather than inherited from the old absolute-z-score model.

## Required Next Steps

1. Recalibrate pressure thresholds for the directional model.
2. Build crisis-specific replay datasets for 1970s/1980s coverage.
3. Feed historical realized-damage labels directly into replay output.
4. Compare old vs new model precision/recall on:
   - 2000 dot-com bust
   - 2008 global financial crisis
   - 2010 Eurozone debt crisis
   - 2020 COVID panic
   - 2022 rate-hike shock
5. Update the Backtest UI so users understand that directional GFCRI values are lower but cleaner.
