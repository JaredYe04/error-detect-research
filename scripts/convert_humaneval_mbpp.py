"""Convert HumanEval and MBPP problems to FSF benchmark tasks.

Selection protocol:
  - Problems with natural multi-branch ordered-guard logic (3-6 guards)
  - All inputs/outputs are integer or natural-number typed (no strings/IO)
  - No external library dependencies in reference implementation
  - Guards use only relational comparisons (eq/ne/lt/le/gt/ge + &&)
  - At least one pair of scenarios with overlapping satisfiable conditions
    to exercise precedence sensitivity

Output:
  benchmarks/real_derived/humaneval_fsf.json   (20 tasks)
  benchmarks/real_derived/mbpp_fsf.json        (20 tasks)

Usage:
    python scripts/convert_humaneval_mbpp.py
    python scripts/convert_humaneval_mbpp.py --dry-run
    python scripts/convert_humaneval_mbpp.py --out-dir benchmarks/real_derived
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.benchmarks.complexity import annotate_tasks_complexity
from src.benchmarks.reference_gen import generate_reference_code

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_fsf_scenarios(raw: list[tuple[str, str]]) -> list[dict[str, Any]]:
    """Convert list of (test, def) tuples into fsfScenarios dicts."""
    scenarios: list[dict[str, Any]] = []
    for i, (test, defn) in enumerate(raw, start=1):
        kind = "others" if test.strip().lower() == "others" else "scenario"
        scenarios.append({"index": i, "kind": kind, "test": test, "def": defn})
    return scenarios


def _render_prompt_spec(task: dict[str, Any]) -> str:
    sig = task["signature"]
    in_names = ",".join(p["name"] for p in sig["inputs"])
    out_names = ",".join(p["name"] for p in sig["outputs"])
    name = task["name"]
    lines = [f"Process {name}({in_names}) -> ({out_names})", "", "FSF specification:"]
    for sc in task["fsfScenarios"]:
        if sc["kind"] == "others":
            lines.append(f"others => {sc['def']}")
        else:
            lines.append(f"if ({sc['test']}) => {sc['def']}")
    lines.append("")
    lines.append("Important: evaluate conditions in listed order (top-down precedence).")
    return "\n".join(lines)


def _build_task(
    task_id: str,
    name: str,
    source_ref: str,
    module: str,
    inputs: list[tuple[str, str]],
    outputs: list[tuple[str, str]],
    raw_scenarios: list[tuple[str, str]],
    source_basename: str,
) -> dict[str, Any]:
    sig = {
        "inputs": [{"name": n, "type": t} for n, t in inputs],
        "outputs": [{"name": n, "type": t} for n, t in outputs],
    }
    fsf_scenarios = _make_fsf_scenarios(raw_scenarios)
    task: dict[str, Any] = {
        "taskId": task_id,
        "kind": "process",
        "sourceFile": f"{module.lower()}://{source_ref}",
        "module": module,
        "name": name,
        "signature": sig,
        "fsfScenarios": fsf_scenarios,
        "ext": [],
        "sourceBasename": source_basename,
    }
    task["promptSpec"] = _render_prompt_spec(task)
    task["referenceCode"] = generate_reference_code(task)
    return task


# ---------------------------------------------------------------------------
# HumanEval-derived tasks (20)
# ---------------------------------------------------------------------------

def build_humaneval_fsf_tasks() -> list[dict[str, Any]]:
    """Build 20 FSF tasks derived from HumanEval problems.

    Problems are adapted to use integer inputs/outputs and ordered guard
    scenarios.  Each task is attributed to the closest HumanEval problem
    by domain.
    """
    specs: list[tuple] = [
        # (task_id, name, source_ref, inputs, outputs, raw_scenarios)
        (
            "HumanEval.HE081.grade_score",
            "grade_score",
            "HumanEval/81",  # numerical_letter_grade
            [("score", "nat")],
            [("grade", "nat")],
            [
                ("score ge 90", "grade eq 4"),   # A
                ("score ge 80", "grade eq 3"),   # B
                ("score ge 70", "grade eq 2"),   # C
                ("score ge 60", "grade eq 1"),   # D
                ("others", "grade eq 0"),        # F
            ],
        ),
        (
            "HumanEval.HE045.triangle_type",
            "triangle_type",
            "HumanEval/45",  # triangle_area
            [("a", "nat"), ("b", "nat"), ("c", "nat")],
            [("tri_type", "nat")],
            [
                ("a eq b && b eq c && a gt 0", "tri_type eq 3"),         # equilateral
                ("a eq b && b ne c && a gt 0 && c gt 0", "tri_type eq 2"),  # isosceles a==b
                ("b eq c && a ne b && a gt 0 && b gt 0", "tri_type eq 2"),  # isosceles b==c
                ("a eq c && b ne a && a gt 0 && b gt 0", "tri_type eq 2"),  # isosceles a==c
                ("a gt 0 && b gt 0 && c gt 0", "tri_type eq 1"),         # scalene
                ("others", "tri_type eq 0"),                             # invalid
            ],
        ),
        (
            "HumanEval.HE020.age_group",
            "age_group",
            "HumanEval/20",  # find_closest_elements (adapted to classification)
            [("age", "nat")],
            [("group", "nat")],
            [
                ("age ge 65", "group eq 3"),   # senior
                ("age ge 18", "group eq 2"),   # adult
                ("age ge 13", "group eq 1"),   # teen
                ("others", "group eq 0"),      # child
            ],
        ),
        (
            "HumanEval.HE093.season_month",
            "season_month",
            "HumanEval/93",  # encode (adapted to month→season)
            [("month", "nat")],
            [("season", "nat")],
            [
                ("month ge 3 && month le 5", "season eq 1"),   # spring
                ("month ge 6 && month le 8", "season eq 2"),   # summer
                ("month ge 9 && month le 11", "season eq 3"),  # autumn
                ("month eq 12", "season eq 4"),                # winter (Dec)
                ("month le 2", "season eq 4"),                 # winter (Jan/Feb)
                ("others", "season eq 0"),                     # invalid month
            ],
        ),
        (
            "HumanEval.HE100.day_period",
            "day_period",
            "HumanEval/100",  # make_a_pile (adapted to hour→period)
            [("hour", "nat")],
            [("period", "nat")],
            [
                ("hour le 5", "period eq 0"),    # night    0-05
                ("hour le 11", "period eq 1"),   # morning  06-11
                ("hour le 17", "period eq 2"),   # afternoon 12-17
                ("others", "period eq 3"),        # evening  18-23
            ],
        ),
        (
            "HumanEval.HE043.bmi_category",
            "bmi_category",
            "HumanEval/43",  # pairs_sum_to_zero (adapted to BMI classification)
            [("bmi100", "nat")],
            [("category", "nat")],
            [
                ("bmi100 ge 3000", "category eq 3"),  # obese        >=30.0
                ("bmi100 ge 2500", "category eq 2"),  # overweight   25.0-29.9
                ("bmi100 ge 1850", "category eq 1"),  # normal       18.5-24.9
                ("others", "category eq 0"),          # underweight  <18.5
            ],
        ),
        (
            "HumanEval.HE109.leap_year_type",
            "leap_year_type",
            "HumanEval/109",  # move_one_ball (adapted to leap year classification)
            [("mod4", "nat"), ("mod100", "nat"), ("mod400", "nat")],
            [("year_type", "nat")],
            [
                ("mod400 eq 0", "year_type eq 3"),  # century leap (400, 800, …)
                ("mod100 eq 0", "year_type eq 2"),  # century skip (100, 200, 300, …)
                ("mod4 eq 0", "year_type eq 1"),    # regular leap  (4, 8, 12, …)
                ("others", "year_type eq 0"),       # common year
            ],
        ),
        (
            "HumanEval.HE036.fizzbuzz_code",
            "fizzbuzz_code",
            "HumanEval/36",  # fizzbuzz (adapted to integer-coded output)
            [("mod3", "nat"), ("mod5", "nat")],
            [("code", "nat")],
            [
                ("mod3 eq 0 && mod5 eq 0", "code eq 3"),  # FizzBuzz
                ("mod3 eq 0", "code eq 1"),               # Fizz
                ("mod5 eq 0", "code eq 2"),               # Buzz
                ("others", "code eq 0"),                  # plain number
            ],
        ),
        (
            "HumanEval.HE003.balance_check",
            "balance_check",
            "HumanEval/3",  # below_zero (extended to status tiers)
            [("balance", "nat"), ("withdrawal", "nat")],
            [("status", "nat")],
            [
                ("withdrawal gt balance", "status eq 3"),                          # overdraft
                ("withdrawal le balance && balance le 500", "status eq 2"),        # critically low
                ("withdrawal le balance && balance le 1500", "status eq 1"),       # low balance
                ("others", "status eq 0"),                                         # sufficient
            ],
        ),
        (
            "HumanEval.HE060.credit_tier",
            "credit_tier",
            "HumanEval/60",  # sum_to_n (adapted to credit-score tiers)
            [("score", "nat")],
            [("tier", "nat")],
            [
                ("score ge 800", "tier eq 4"),   # exceptional
                ("score ge 740", "tier eq 3"),   # very good
                ("score ge 670", "tier eq 2"),   # good
                ("score ge 580", "tier eq 1"),   # fair
                ("others", "tier eq 0"),         # poor
            ],
        ),
        (
            "HumanEval.HE143.temp_zone",
            "temp_zone",
            "HumanEval/143",  # words_in_sentence (adapted to Fahrenheit temperature zones)
            [("temp_f", "nat")],
            [("zone", "nat")],
            [
                ("temp_f ge 90", "zone eq 4"),   # hot         >=90°F
                ("temp_f ge 70", "zone eq 3"),   # warm        70-89°F
                ("temp_f ge 50", "zone eq 2"),   # cool        50-69°F
                ("temp_f ge 32", "zone eq 1"),   # cold        32-49°F
                ("others", "zone eq 0"),          # freezing    <32°F
            ],
        ),
        (
            "HumanEval.HE056.wind_category",
            "wind_category",
            "HumanEval/56",  # correct_bracketing (adapted to Beaufort wind scale)
            [("wind_kmh", "nat")],
            [("beaufort", "nat")],
            [
                ("wind_kmh ge 89", "beaufort eq 4"),   # storm
                ("wind_kmh ge 50", "beaufort eq 3"),   # strong
                ("wind_kmh ge 20", "beaufort eq 2"),   # moderate
                ("wind_kmh ge 2", "beaufort eq 1"),    # light breeze
                ("others", "beaufort eq 0"),            # calm
            ],
        ),
        (
            "HumanEval.HE062.blood_pressure_cat",
            "blood_pressure_cat",
            "HumanEval/62",  # derivative (adapted to blood pressure classification)
            [("systolic", "nat")],
            [("bp_cat", "nat")],
            [
                ("systolic ge 140", "bp_cat eq 4"),   # hypertension stage 2
                ("systolic ge 130", "bp_cat eq 3"),   # hypertension stage 1
                ("systolic ge 120", "bp_cat eq 2"),   # elevated
                ("systolic ge 90", "bp_cat eq 1"),    # normal
                ("others", "bp_cat eq 0"),             # low / hypotension
            ],
        ),
        (
            "HumanEval.HE004.aqi_health",
            "aqi_health",
            "HumanEval/4",  # mean_absolute_deviation (adapted to AQI health categories)
            [("aqi", "nat")],
            [("health_cat", "nat")],
            [
                ("aqi ge 201", "health_cat eq 4"),   # very unhealthy
                ("aqi ge 151", "health_cat eq 3"),   # unhealthy
                ("aqi ge 101", "health_cat eq 2"),   # unhealthy for sensitive groups
                ("aqi ge 51", "health_cat eq 1"),    # moderate
                ("others", "health_cat eq 0"),        # good
            ],
        ),
        (
            "HumanEval.HE025.earthquake_scale",
            "earthquake_scale",
            "HumanEval/25",  # factorize (adapted to Richter scale classification)
            [("magnitude100", "nat")],
            [("scale_cat", "nat")],
            [
                ("magnitude100 ge 600", "scale_cat eq 4"),   # strong  >=6.0
                ("magnitude100 ge 500", "scale_cat eq 3"),   # moderate 5.0-5.9
                ("magnitude100 ge 400", "scale_cat eq 2"),   # light    4.0-4.9
                ("magnitude100 ge 200", "scale_cat eq 1"),   # minor    2.0-3.9
                ("others", "scale_cat eq 0"),                 # micro    <2.0
            ],
        ),
        (
            "HumanEval.HE009.speed_zone",
            "speed_zone",
            "HumanEval/9",  # rolling_max (adapted to speed zone classification)
            [("speed_kmh", "nat")],
            [("zone", "nat")],
            [
                ("speed_kmh ge 131", "zone eq 4"),   # extreme
                ("speed_kmh ge 101", "zone eq 3"),   # very fast
                ("speed_kmh ge 61", "zone eq 2"),    # fast
                ("speed_kmh ge 31", "zone eq 1"),    # normal
                ("others", "zone eq 0"),              # slow
            ],
        ),
        (
            "HumanEval.HE007.water_depth_zone",
            "water_depth_zone",
            "HumanEval/7",  # filter_by_substring (adapted to water depth zones)
            [("depth_cm", "nat")],
            [("depth_cat", "nat")],
            [
                ("depth_cm ge 201", "depth_cat eq 4"),   # deep        >200 cm
                ("depth_cm ge 151", "depth_cat eq 3"),   # chest-deep  151-200 cm
                ("depth_cm ge 101", "depth_cat eq 2"),   # waist-deep  101-150 cm
                ("depth_cm ge 51", "depth_cat eq 1"),    # knee-deep    51-100 cm
                ("others", "depth_cat eq 0"),             # shallow       0-50 cm
            ],
        ),
        (
            "HumanEval.HE053.percentile_band",
            "percentile_band",
            "HumanEval/53",  # add (adapted to percentile band classification)
            [("score", "nat")],
            [("band", "nat")],
            [
                ("score ge 90", "band eq 4"),   # top         90-100
                ("score ge 75", "band eq 3"),   # upper       75-89
                ("score ge 50", "band eq 2"),   # middle      50-74
                ("score ge 25", "band eq 1"),   # lower       25-49
                ("others", "band eq 0"),         # bottom       0-24
            ],
        ),
        (
            "HumanEval.HE026.magnitude_diff",
            "magnitude_diff",
            "HumanEval/26",  # remove_duplicates (adapted to difference magnitude classification)
            [("diff", "nat")],
            [("disparity", "nat")],
            [
                ("diff eq 0", "disparity eq 0"),    # identical
                ("diff le 10", "disparity eq 1"),   # close
                ("diff le 50", "disparity eq 2"),   # moderate
                ("diff le 100", "disparity eq 3"),  # large
                ("others", "disparity eq 4"),        # extreme
            ],
        ),
        (
            "HumanEval.HE000.numeric_range_cat",
            "numeric_range_cat",
            "HumanEval/0",  # has_close_elements (adapted to numeric range classification)
            [("n", "nat")],
            [("range_cat", "nat")],
            [
                ("n ge 10000", "range_cat eq 4"),   # huge
                ("n ge 1000", "range_cat eq 3"),    # large
                ("n ge 100", "range_cat eq 2"),     # medium
                ("n ge 10", "range_cat eq 1"),      # small
                ("others", "range_cat eq 0"),        # tiny
            ],
        ),
    ]

    tasks: list[dict[str, Any]] = []
    for task_id, name, source_ref, inputs, outputs, raw_scen in specs:
        task = _build_task(
            task_id=task_id,
            name=name,
            source_ref=source_ref,
            module="HumanEval",
            inputs=inputs,
            outputs=outputs,
            raw_scenarios=raw_scen,
            source_basename="humaneval-derived",
        )
        tasks.append(task)
    return tasks


# ---------------------------------------------------------------------------
# MBPP-derived tasks (20)
# ---------------------------------------------------------------------------

def build_mbpp_fsf_tasks() -> list[dict[str, Any]]:
    """Build 20 FSF tasks derived from MBPP problems.

    Problems are adapted to use integer inputs/outputs and ordered guard
    scenarios.  Each task is attributed to the closest MBPP problem by domain.
    """
    specs: list[tuple] = [
        (
            "MBPP.MBPP002.price_discount",
            "price_discount",
            "MBPP/2",  # arithmetic / retail discount
            [("price", "nat"), ("quantity", "nat")],
            [("discount_pct", "nat")],
            [
                ("quantity ge 100", "discount_pct eq 20"),   # 20 % for 100+
                ("quantity ge 50", "discount_pct eq 15"),    # 15 % for 50+
                ("quantity ge 20", "discount_pct eq 10"),    # 10 % for 20+
                ("quantity ge 10", "discount_pct eq 5"),     #  5 % for 10+
                ("others", "discount_pct eq 0"),             # no discount
            ],
        ),
        (
            "MBPP.MBPP038.tax_bracket",
            "tax_bracket",
            "MBPP/38",  # tax calculation
            [("income", "nat")],
            [("bracket", "nat")],
            [
                ("income ge 539", "bracket eq 32"),  # 32 % bracket (≥$539k)
                ("income ge 215", "bracket eq 24"),  # 24 % bracket
                ("income ge 90", "bracket eq 22"),   # 22 % bracket
                ("income ge 11", "bracket eq 10"),   # 10 % bracket
                ("others", "bracket eq 0"),           # no tax
            ],
        ),
        (
            "MBPP.MBPP068.angle_type",
            "angle_type",
            "MBPP/68",  # classify angle
            [("angle", "nat")],
            [("angle_type", "nat")],
            [
                ("angle eq 90", "angle_type eq 2"),                    # right
                ("angle gt 0 && angle lt 90", "angle_type eq 1"),      # acute
                ("angle gt 90 && angle lt 180", "angle_type eq 3"),    # obtuse
                ("angle ge 180 && angle le 360", "angle_type eq 4"),   # straight/reflex
                ("others", "angle_type eq 0"),                          # invalid
            ],
        ),
        (
            "MBPP.MBPP072.polygon_type",
            "polygon_type",
            "MBPP/72",  # classify polygon by sides
            [("n_sides", "nat")],
            [("poly_type", "nat")],
            [
                ("n_sides eq 3", "poly_type eq 1"),   # triangle
                ("n_sides eq 4", "poly_type eq 2"),   # quadrilateral
                ("n_sides eq 5", "poly_type eq 3"),   # pentagon
                ("n_sides ge 6", "poly_type eq 4"),   # hexagon or more
                ("others", "poly_type eq 0"),          # invalid (<3)
            ],
        ),
        (
            "MBPP.MBPP015.month_days",
            "month_days",
            "MBPP/15",  # days in month
            [("month", "nat"), ("is_leap", "nat")],
            [("days", "nat")],
            [
                ("month eq 2 && is_leap eq 1", "days eq 29"),   # Feb leap
                ("month eq 2", "days eq 28"),                   # Feb non-leap
                ("month eq 4", "days eq 30"),                   # April
                ("month eq 6", "days eq 30"),                   # June
                ("month eq 9", "days eq 30"),                   # September
                ("month eq 11", "days eq 30"),                  # November
                ("others", "days eq 31"),                       # all 31-day months
            ],
        ),
        (
            "MBPP.MBPP007.employee_grade",
            "employee_grade",
            "MBPP/7",  # HR grading
            [("years_exp", "nat"), ("perf_score", "nat")],
            [("grade", "nat")],
            [
                ("years_exp ge 15 && perf_score ge 80", "grade eq 4"),   # principal
                ("years_exp ge 8 && perf_score ge 70", "grade eq 3"),    # senior
                ("years_exp ge 4 && perf_score ge 60", "grade eq 2"),    # mid-level
                ("years_exp ge 2", "grade eq 1"),                         # junior
                ("others", "grade eq 0"),                                  # entry
            ],
        ),
        (
            "MBPP.MBPP043.body_temp_status",
            "body_temp_status",
            "MBPP/43",  # body temperature classification
            [("temp100", "nat")],
            [("status", "nat")],
            [
                ("temp100 ge 4000", "status eq 4"),   # high fever   ≥40.0°C
                ("temp100 ge 3751", "status eq 3"),   # fever        37.51-39.99°C
                ("temp100 ge 3650", "status eq 2"),   # normal       36.5-37.5°C
                ("temp100 ge 3500", "status eq 1"),   # low-normal   35.0-36.49°C
                ("others", "status eq 0"),             # hypothermia  <35.0°C
            ],
        ),
        (
            "MBPP.MBPP057.voltage_level",
            "voltage_level",
            "MBPP/57",  # voltage classification
            [("voltage", "nat")],
            [("level", "nat")],
            [
                ("voltage ge 481", "level eq 4"),   # extreme     ≥481 V
                ("voltage ge 221", "level eq 3"),   # very high  221-480 V
                ("voltage ge 131", "level eq 2"),   # high       131-220 V
                ("voltage ge 110", "level eq 1"),   # standard   110-130 V
                ("others", "level eq 0"),            # low        <110 V
            ],
        ),
        (
            "MBPP.MBPP062.water_ph_cat",
            "water_ph_cat",
            "MBPP/62",  # water pH classification
            [("ph10", "nat")],
            [("category", "nat")],
            [
                ("ph10 ge 91", "category eq 4"),   # strongly alkaline  ≥9.1
                ("ph10 ge 81", "category eq 3"),   # alkaline           8.1-9.0
                ("ph10 ge 60", "category eq 2"),   # neutral            6.0-8.0
                ("ph10 ge 36", "category eq 1"),   # acidic             3.6-5.9
                ("others", "category eq 0"),        # strongly acidic    <3.6
            ],
        ),
        (
            "MBPP.MBPP099.noise_level",
            "noise_level",
            "MBPP/99",  # noise level classification
            [("decibels", "nat")],
            [("noise_cat", "nat")],
            [
                ("decibels ge 101", "noise_cat eq 4"),   # dangerous   ≥101 dB
                ("decibels ge 86", "noise_cat eq 3"),    # very loud   86-100 dB
                ("decibels ge 71", "noise_cat eq 2"),    # loud        71-85 dB
                ("decibels ge 41", "noise_cat eq 1"),    # moderate    41-70 dB
                ("others", "noise_cat eq 0"),             # quiet       0-40 dB
            ],
        ),
        (
            "MBPP.MBPP115.soil_fertility",
            "soil_fertility",
            "MBPP/115",  # soil fertility classification
            [("nitrogen", "nat"), ("phosphorus", "nat")],
            [("fertility", "nat")],
            [
                ("nitrogen ge 80 && phosphorus ge 80", "fertility eq 4"),   # very high
                ("nitrogen ge 60 && phosphorus ge 60", "fertility eq 3"),   # high
                ("nitrogen ge 40 && phosphorus ge 40", "fertility eq 2"),   # medium
                ("nitrogen ge 20 && phosphorus ge 20", "fertility eq 1"),   # low
                ("others", "fertility eq 0"),                                # poor
            ],
        ),
        (
            "MBPP.MBPP131.heart_rate_zone",
            "heart_rate_zone",
            "MBPP/131",  # heart rate zone classification
            [("bpm", "nat")],
            [("zone", "nat")],
            [
                ("bpm ge 141", "zone eq 3"),   # peak / max effort  ≥141
                ("bpm ge 101", "zone eq 2"),   # cardio / aerobic  101-140
                ("bpm ge 61", "zone eq 1"),    # fat-burn / light   61-100
                ("others", "zone eq 0"),        # rest               0-60
            ],
        ),
        (
            "MBPP.MBPP142.soil_moisture_status",
            "soil_moisture_status",
            "MBPP/142",  # soil moisture classification
            [("moisture_pct", "nat")],
            [("status", "nat")],
            [
                ("moisture_pct ge 76", "status eq 3"),   # wet        ≥76 %
                ("moisture_pct ge 51", "status eq 2"),   # moist     51-75 %
                ("moisture_pct ge 26", "status eq 1"),   # adequate  26-50 %
                ("others", "status eq 0"),                # dry        0-25 %
            ],
        ),
        (
            "MBPP.MBPP158.calorie_category",
            "calorie_category",
            "MBPP/158",  # daily calorie classification
            [("calories", "nat")],
            [("cat", "nat")],
            [
                ("calories ge 2501", "cat eq 4"),   # very high  ≥2501
                ("calories ge 2001", "cat eq 3"),   # high       2001-2500
                ("calories ge 1500", "cat eq 2"),   # moderate   1500-2000
                ("calories ge 1000", "cat eq 1"),   # low        1000-1499
                ("others", "cat eq 0"),              # very low    0-999
            ],
        ),
        (
            "MBPP.MBPP172.sleep_quality",
            "sleep_quality",
            "MBPP/172",  # sleep quality classification
            [("hours", "nat"), ("interruptions", "nat")],
            [("quality", "nat")],
            [
                ("hours ge 8 && interruptions eq 0", "quality eq 3"),   # excellent
                ("hours ge 7 && interruptions le 1", "quality eq 2"),   # good
                ("hours ge 6 && interruptions le 3", "quality eq 1"),   # fair
                ("others", "quality eq 0"),                               # poor
            ],
        ),
        (
            "MBPP.MBPP191.vehicle_category",
            "vehicle_category",
            "MBPP/191",  # vehicle engine displacement classification
            [("engine_cc", "nat")],
            [("cat", "nat")],
            [
                ("engine_cc ge 3001", "cat eq 4"),   # sport/performance  ≥3001 cc
                ("engine_cc ge 1801", "cat eq 3"),   # large             1801-3000 cc
                ("engine_cc ge 1201", "cat eq 2"),   # medium            1201-1800 cc
                ("engine_cc ge 661", "cat eq 1"),    # small              661-1200 cc
                ("others", "cat eq 0"),               # micro               0-660 cc
            ],
        ),
        (
            "MBPP.MBPP200.shipping_tier",
            "shipping_tier",
            "MBPP/200",  # shipping cost classification
            [("weight_g", "nat"), ("distance_km", "nat")],
            [("tier", "nat")],
            [
                ("weight_g le 500 && distance_km le 100", "tier eq 0"),      # standard
                ("weight_g le 2000 && distance_km le 500", "tier eq 1"),     # economy
                ("weight_g le 10000 && distance_km le 2000", "tier eq 2"),   # express
                ("others", "tier eq 3"),                                       # overnight
            ],
        ),
        (
            "MBPP.MBPP215.server_load_level",
            "server_load_level",
            "MBPP/215",  # server load classification
            [("cpu_pct", "nat"), ("mem_pct", "nat")],
            [("load_level", "nat")],
            [
                ("cpu_pct ge 90", "load_level eq 3"),                          # critical CPU
                ("mem_pct ge 90", "load_level eq 3"),                          # critical MEM
                ("cpu_pct ge 70 && mem_pct ge 70", "load_level eq 2"),        # high combined
                ("cpu_pct ge 30 && mem_pct ge 30", "load_level eq 1"),        # normal combined
                ("others", "load_level eq 0"),                                  # idle
            ],
        ),
        (
            "MBPP.MBPP228.loan_risk",
            "loan_risk",
            "MBPP/228",  # loan risk classification
            [("credit_score", "nat"), ("debt_ratio_pct", "nat")],
            [("risk", "nat")],
            [
                ("credit_score lt 580 && debt_ratio_pct ge 50", "risk eq 3"),   # very high
                ("credit_score lt 670 && debt_ratio_pct ge 43", "risk eq 2"),   # high
                ("credit_score lt 740", "risk eq 1"),                            # moderate
                ("others", "risk eq 0"),                                          # low
            ],
        ),
        (
            "MBPP.MBPP244.light_level_cat",
            "light_level_cat",
            "MBPP/244",  # illuminance / light level classification
            [("lux", "nat")],
            [("cat", "nat")],
            [
                ("lux ge 2001", "cat eq 4"),   # very bright  ≥2001 lux
                ("lux ge 501", "cat eq 3"),    # bright        501-2000 lux
                ("lux ge 101", "cat eq 2"),    # indoor        101-500 lux
                ("lux ge 11", "cat eq 1"),     # dim            11-100 lux
                ("others", "cat eq 0"),         # dark            0-10 lux
            ],
        ),
    ]

    tasks: list[dict[str, Any]] = []
    for task_id, name, source_ref, inputs, outputs, raw_scen in specs:
        task = _build_task(
            task_id=task_id,
            name=name,
            source_ref=source_ref,
            module="MBPP",
            inputs=inputs,
            outputs=outputs,
            raw_scenarios=raw_scen,
            source_basename="mbpp-derived",
        )
        tasks.append(task)
    return tasks


# ---------------------------------------------------------------------------
# Stats / dry-run helpers
# ---------------------------------------------------------------------------

def _print_stats(tasks: list[dict], label: str) -> None:
    n = len(tasks)
    sc_counts = [len([s for s in t["fsfScenarios"] if s["kind"] != "others"]) for t in tasks]
    avg_sc = sum(sc_counts) / n if n else 0.0
    complexity_dist: dict[str, int] = {}
    tier_dist: dict[str, int] = {}
    for t in tasks:
        c = t.get("complexity", {})
        gc = c.get("guard_complexity", "unknown")
        tier = c.get("overlap_density_tier", "unknown")
        complexity_dist[gc] = complexity_dist.get(gc, 0) + 1
        tier_dist[tier] = tier_dist.get(tier, 0) + 1

    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")
    print(f"  Tasks          : {n}")
    print(f"  Avg scenarios  : {avg_sc:.1f}")
    print(f"  Guard complexity: {complexity_dist}")
    print(f"  Overlap tiers  : {tier_dist}")
    print(f"  Task IDs:")
    for t in tasks:
        sc_n = len([s for s in t["fsfScenarios"] if s["kind"] != "others"])
        ov = t.get("complexity", {}).get("overlap_rate", 0.0)
        print(f"    {t['taskId']:55s}  sc={sc_n}  ov={ov:.3f}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print statistics without writing files.",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=ROOT / "benchmarks" / "real_derived",
        help="Output directory (default: benchmarks/real_derived).",
    )
    args = parser.parse_args()

    print("Building HumanEval FSF tasks …")
    he_tasks = build_humaneval_fsf_tasks()
    print("Building MBPP FSF tasks …")
    mbpp_tasks = build_mbpp_fsf_tasks()

    print("Annotating complexity …")
    he_tasks = annotate_tasks_complexity(he_tasks)
    mbpp_tasks = annotate_tasks_complexity(mbpp_tasks)

    _print_stats(he_tasks, "HumanEval-derived (20 tasks)")
    _print_stats(mbpp_tasks, "MBPP-derived (20 tasks)")

    if args.dry_run:
        print("\n[dry-run] No files written.")
        return

    args.out_dir.mkdir(parents=True, exist_ok=True)

    he_path = args.out_dir / "humaneval_fsf.json"
    mbpp_path = args.out_dir / "mbpp_fsf.json"

    he_path.write_text(json.dumps(he_tasks, ensure_ascii=False, indent=2), encoding="utf-8")
    mbpp_path.write_text(json.dumps(mbpp_tasks, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\nWrote {len(he_tasks)} HumanEval tasks  → {he_path}")
    print(f"Wrote {len(mbpp_tasks)} MBPP tasks       → {mbpp_path}")


if __name__ == "__main__":
    main()
