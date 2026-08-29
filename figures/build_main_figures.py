from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


INK = "#202735"
MUTED = "#667085"
GRID = "#D9E1EC"
BLUE = "#5479BE"
DARK_BLUE = "#35558E"
WHITE = "#FFFFFF"

FONT_REGULAR = "C:/Windows/Fonts/arial.ttf"
FONT_BOLD = "C:/Windows/Fonts/arialbd.ttf"

PERIODS = ("≤2009", "2010-2014", "2015-2019", "2020 onward")
PERIOD_LABELS = ("≤2009", "2010-14", "2015-19", "2020 onward")
PERIOD_NS = (62, 215, 667, 1045)
TOPICS = tuple(f"C{i}" for i in range(1, 10))
TOPIC_LABELS = {
    "C1": "C1 Disease information/etiology",
    "C2": "C2 Symptoms/diagnosis",
    "C3": "C3 General treatment/surgery",
    "C4": "C4 Anti-VEGF injection",
    "C5": "C5 Nutrition/lifestyle",
    "C6": "C6 Course/prognosis",
    "C7": "C7 Cost/insurance/administration",
    "C8": "C8 Hospital/physician referral",
    "C9": "C9 Other/adverse-interaction",
}


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_BOLD if bold else FONT_REGULAR, size=size)


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def period_for_year(year: int) -> str:
    if year <= 2009:
        return "≤2009"
    if year <= 2014:
        return "2010-2014"
    if year <= 2019:
        return "2015-2019"
    return "2020 onward"


def hex_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[index : index + 2], 16) for index in (0, 2, 4))


def interpolate(start: str, end: str, fraction: float) -> str:
    first = hex_rgb(start)
    second = hex_rgb(end)
    fraction = max(0.0, min(1.0, fraction))
    rgb = tuple(round(a + (b - a) * fraction) for a, b in zip(first, second))
    return "#" + "".join(f"{channel:02X}" for channel in rgb)


def centered(
    draw: ImageDraw.ImageDraw,
    xy: tuple[float, float],
    text: str,
    selected_font: ImageFont.FreeTypeFont,
    fill: str = INK,
) -> None:
    draw.text(xy, text, font=selected_font, fill=fill, anchor="mm")


def save(image: Image.Image, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output, dpi=(300, 300))


def build_figure3(rows: list[dict[str, str]], output: Path) -> None:
    counts = {period: Counter() for period in PERIODS}
    denominators = Counter()
    for row in rows:
        period = period_for_year(int(row["question_year"]))
        denominators[period] += 1
        counts[period][row["primary_topic"]] += 1

    observed_ns = tuple(denominators[period] for period in PERIODS)
    if observed_ns != PERIOD_NS:
        raise ValueError(f"Unexpected period denominators: {observed_ns}")

    image = Image.new("RGB", (1800, 1500), WHITE)
    draw = ImageDraw.Draw(image)
    grid_left, grid_top = 650, 190
    cell_width, cell_height = 250, 112

    for column, (label, denominator) in enumerate(zip(PERIOD_LABELS, PERIOD_NS)):
        x = grid_left + column * cell_width + cell_width / 2
        centered(draw, (x, 112), label, font(31, True))
        centered(draw, (x, 150), f"n={denominator:,}", font(25), MUTED)

    for row_index, topic in enumerate(TOPICS):
        y_top = grid_top + row_index * cell_height
        y_center = y_top + cell_height / 2
        draw.text(
            (grid_left - 28, y_center),
            TOPIC_LABELS[topic],
            font=font(28),
            fill=INK,
            anchor="rm",
        )
        for column, period in enumerate(PERIODS):
            value = counts[period][topic] / denominators[period] * 100
            x_left = grid_left + column * cell_width
            fill = interpolate("#F7F9FC", DARK_BLUE, value / 30)
            draw.rectangle(
                (x_left + 3, y_top + 3, x_left + cell_width - 3, y_top + cell_height - 3),
                fill=fill,
            )
            centered(
                draw,
                (x_left + cell_width / 2, y_center),
                f"{value:.1f}%",
                font(29, value >= 19),
                WHITE if value >= 19 else INK,
            )

    bar_left, bar_right, bar_y = grid_left, grid_left + 500, 1325
    steps = 80
    for step in range(steps):
        x1 = bar_left + (bar_right - bar_left) * step / steps
        x2 = bar_left + (bar_right - bar_left) * (step + 1) / steps
        draw.rectangle(
            (x1, bar_y, x2 + 1, bar_y + 28),
            fill=interpolate("#F7F9FC", DARK_BLUE, step / (steps - 1)),
        )
    draw.text((bar_left, bar_y - 18), "Primary-topic rate (%)", font=font(25), fill=MUTED, anchor="ls")
    draw.text((bar_left, bar_y + 44), "0", font=font(23), fill=MUTED, anchor="ms")
    draw.text((bar_right, bar_y + 44), "30", font=font(23), fill=MUTED, anchor="ms")
    save(image, output)


def parse_secondary(value: str) -> set[str]:
    return {item.strip() for item in value.split(";") if item.strip()}


def build_figure2(rows: list[dict[str, str]], output: Path) -> None:
    primary = Counter(row["primary_topic"] for row in rows)
    any_mention = Counter()
    for row in rows:
        for topic in {row["primary_topic"], *parse_secondary(row["secondary_topics"])}:
            any_mention[topic] += 1

    image = Image.new("RGB", (1800, 1750), WHITE)
    draw = ImageDraw.Draw(image)

    draw.text((55, 45), "A", font=font(42, True), fill=INK)
    order = sorted(TOPICS, key=lambda topic: primary[topic], reverse=True)
    left, right, top, bottom = 650, 1650, 125, 850
    max_pct = 25
    for tick in range(0, 26, 5):
        x = left + (right - left) * tick / max_pct
        draw.line((x, top - 10, x, bottom), fill=GRID, width=2)
        centered(draw, (x, bottom + 35), f"{tick}%", font(24), MUTED)
    bar_height, row_gap = 54, 78
    for index, topic in enumerate(order):
        value = primary[topic] / len(rows) * 100
        y = top + index * row_gap
        draw.text((left - 24, y + bar_height / 2), TOPIC_LABELS[topic], font=font(27), fill=INK, anchor="rm")
        x_end = left + (right - left) * value / max_pct
        draw.rectangle((left, y, x_end, y + bar_height), fill=BLUE)
        draw.text((x_end + 14, y + bar_height / 2), f"{value:.1f}%  |  n={primary[topic]}", font=font(25, True), fill=INK, anchor="lm")
    centered(draw, ((left + right) / 2, bottom + 92), "Primary-topic rate (%)", font(27), MUTED)

    draw.text((55, 970), "B", font=font(42, True), fill=INK)
    selected = sorted(
        [
            topic
            for topic in TOPICS
            if (any_mention[topic] - primary[topic]) / len(rows) * 100 >= 5
        ],
        key=lambda topic: (any_mention[topic] - primary[topic]),
        reverse=True,
    )
    panel_left, panel_right, panel_top, panel_bottom = 650, 1650, 1070, 1530
    panel_max = 32
    for tick in range(0, 31, 5):
        x = panel_left + (panel_right - panel_left) * tick / panel_max
        draw.line((x, panel_top - 10, x, panel_bottom), fill=GRID, width=2)
        centered(draw, (x, panel_bottom + 35), f"{tick}%", font(24), MUTED)
    draw.ellipse((1120, 1000, 1138, 1018), fill="#A9BCD9")
    draw.text((1148, 1009), "Primary topic", font=font(24), fill=INK, anchor="lm")
    draw.ellipse((1370, 1000, 1388, 1018), fill=DARK_BLUE)
    draw.text((1398, 1009), "Any mention", font=font(24), fill=INK, anchor="lm")
    row_gap = 82
    for index, topic in enumerate(selected):
        primary_value = primary[topic] / len(rows) * 100
        any_value = any_mention[topic] / len(rows) * 100
        y = panel_top + index * row_gap
        draw.text((panel_left - 24, y), TOPIC_LABELS[topic], font=font(27), fill=INK, anchor="rm")
        x_primary = panel_left + (panel_right - panel_left) * primary_value / panel_max
        x_any = panel_left + (panel_right - panel_left) * any_value / panel_max
        draw.line((x_primary, y, x_any, y), fill="#AAB5C5", width=5)
        draw.ellipse((x_primary - 10, y - 10, x_primary + 10, y + 10), fill="#A9BCD9")
        draw.ellipse((x_any - 10, y - 10, x_any + 10, y + 10), fill=DARK_BLUE)
        draw.text((x_primary - 14, y), f"{primary_value:.1f}%", font=font(23), fill=MUTED, anchor="rm")
        draw.text((x_any + 14, y), f"{any_value:.1f}%", font=font(23, True), fill=INK, anchor="lm")
    centered(draw, ((panel_left + panel_right) / 2, panel_bottom + 92), "Rate among all strict AMD threads (%)", font(27), MUTED)
    save(image, output)


def build_figure4(source_rows: list[dict[str, str]], output: Path) -> None:
    overall = {
        row["subgroup"]: row for row in source_rows if row["period"] == "overall"
    }
    subgroup_order = [
        ("S1_post_injection_AE", "S1 Post-injection adverse events/safety"),
        ("S2_drug_food_interaction", "S2 Drug/food interaction"),
        ("S3_other_ophth_postproc", "S3 Other ophthalmic post-procedure"),
        ("S7_other", "S7 Other miscellaneous"),
        ("S5_lifestyle_protective", "S5 Protective optical devices"),
        ("S4_nonspecific_dx", "S4 Non-AMD/nonspecific diagnosis"),
        ("S6_caregiver_admin", "S6 Family/caregiving/administration"),
    ]

    image = Image.new("RGB", (1800, 1900), WHITE)
    draw = ImageDraw.Draw(image)
    draw.text((60, 45), "A", font=font(42, True), fill=INK)
    left, right, top, bottom = 700, 1650, 130, 865
    max_pct = 70
    for tick in range(0, 71, 10):
        x = left + (right - left) * tick / max_pct
        draw.line((x, top - 12, x, bottom), fill=GRID, width=2)
        centered(draw, (x, bottom + 34), f"{tick}%", font(25), MUTED)
    bar_height, row_gap = 58, 96
    for index, (code, label) in enumerate(subgroup_order):
        row = overall[code]
        count = int(row["count"])
        value = float(row["rate_within_c9_pct"])
        y = top + index * row_gap
        draw.text((left - 25, y + bar_height / 2), label, font=font(28), fill=INK, anchor="rm")
        x_end = left + (right - left) * value / max_pct
        draw.rectangle((left, y, x_end, y + bar_height), fill=DARK_BLUE if index == 0 else BLUE)
        draw.text((x_end + 15, y + bar_height / 2), f"{value:.1f}%  |  n={count}", font=font(27, True), fill=INK, anchor="lm")
    centered(draw, ((left + right) / 2, bottom + 92), "Share of C9-tagged threads (%)", font(28), MUTED)

    draw.text((60, 1025), "B", font=font(42, True), fill=INK)
    source_periods = ("<=2009", "2010-2014", "2015-2019", "2020 onward")
    s1_rows = {
        row["period"]: row
        for row in source_rows
        if row["subgroup"] == "S1_post_injection_AE" and row["period"] != "overall"
    }
    rates = [float(s1_rows[period]["rate_all_threads_pct"]) for period in source_periods]
    counts = [int(s1_rows[period]["count"]) for period in source_periods]
    chart_left, chart_right, chart_top, chart_bottom = 190, 1680, 1120, 1690
    max_rate = 13
    for tick in range(0, 13, 2):
        y = chart_bottom - (chart_bottom - chart_top) * tick / max_rate
        draw.line((chart_left, y, chart_right, y), fill=GRID, width=2)
        draw.text((chart_left - 18, y), f"{tick}%", font=font(25), fill=MUTED, anchor="rm")
    draw.line((chart_left, chart_top, chart_left, chart_bottom), fill="#B7C2D2", width=2)
    draw.line((chart_left, chart_bottom, chart_right, chart_bottom), fill="#B7C2D2", width=2)
    draw.text((chart_left, chart_top - 42), "S1 rate among all strict AMD threads (%)", font=font(27), fill=MUTED, anchor="ls")

    slot = (chart_right - chart_left) / 4
    bar_width = 200
    for index, (rate, count, label, denominator) in enumerate(zip(rates, counts, PERIOD_LABELS, PERIOD_NS)):
        x_center = chart_left + slot * (index + 0.5)
        y_top = chart_bottom - (chart_bottom - chart_top) * rate / max_rate
        draw.rectangle((x_center - bar_width / 2, y_top, x_center + bar_width / 2, chart_bottom), fill=DARK_BLUE)
        centered(draw, (x_center, y_top - 56), f"{rate:.1f}%", font(29, True))
        centered(draw, (x_center, y_top - 22), f"n={count}", font(25), MUTED)
        centered(draw, (x_center, chart_bottom + 42), label, font(28, True))
        centered(draw, (x_center, chart_bottom + 82), f"period n={denominator:,}", font(24), MUTED)
    save(image, output)


def build_figure5(output: Path) -> None:
    labels = [
        "Supplement recommendation",
        "Surgery/laser mention",
        "Injection mention",
        "External link/blog",
        "Traditional-medicine mention",
        "Hospital/clinic referral",
        "Examination/clinic-visit recommendation",
        "Cure/vision-recovery claim",
    ]
    counts = [827, 634, 610, 577, 504, 425, 417, 168]
    values = [count / 1989 * 100 for count in counts]

    image = Image.new("RGB", (1800, 1200), WHITE)
    draw = ImageDraw.Draw(image)
    left, right, top, bottom = 670, 1650, 90, 1025
    max_pct = 46
    for tick in range(0, 46, 5):
        x = left + (right - left) * tick / max_pct
        draw.line((x, top - 10, x, bottom), fill=GRID, width=2)
        centered(draw, (x, bottom + 35), f"{tick}%", font(24), MUTED)
    bar_height, row_gap = 64, 112
    for index, (label, count, value) in enumerate(zip(labels, counts, values)):
        y = top + index * row_gap
        draw.text((left - 25, y + bar_height / 2), label, font=font(28), fill=INK, anchor="rm")
        x_end = left + (right - left) * value / max_pct
        draw.rectangle((left, y, x_end, y + bar_height), fill=BLUE)
        draw.text((x_end + 15, y + bar_height / 2), f"{value:.1f}%  |  n={count}", font=font(27, True), fill=INK, anchor="lm")
    centered(draw, ((left + right) / 2, bottom + 95), "Threads with keyword-detected signal (%)", font(28), MUTED)
    save(image, output)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--c9-source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    rows = load_csv(args.corpus)
    if len(rows) != 1989:
        raise ValueError(f"Expected 1,989 rows, found {len(rows)}")
    source_rows = load_csv(args.c9_source)
    build_figure2(rows, args.output / "Figure2.png")
    build_figure3(rows, args.output / "Figure3.png")
    build_figure4(source_rows, args.output / "Figure4.png")
    build_figure5(args.output / "Figure5.png")


if __name__ == "__main__":
    main()
