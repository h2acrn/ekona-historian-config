from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import json


REPO_ROOT = Path(__file__).resolve().parents[1]
OI_GATEWAY_DIR = REPO_ROOT / "exports" / "oi-gateway"
TAGS_DIR = REPO_ROOT / "exports" / "tags"
NOTES_DIR = REPO_ROOT / "notes"
SUMMARY_PATH = NOTES_DIR / "latest-compare-summary.md"
ALIASES_PATH = REPO_ROOT / "scripts" / "compare_aliases.json"

@dataclass
class ComparisonResult:
    pair_name: str
    oi_file: str
    tags_file: str
    oi_total_raw: int
    oi_total_parsed: int
    tags_total: int
    common_count: int
    oi_only: list[str]
    tags_only: list[str]
    unparsable_oi_items: list[str]


def normalize_name(value: str) -> str:
    return value.strip().strip('"').strip().lower()


def pretty_sort(values: set[str]) -> list[str]:
    return sorted(values, key=lambda x: x.lower())

def load_alias_config(path: Path) -> dict:
    if not path.exists():
        return {
            "strip_prefixes": [],
            "strip_suffixes": [],
            "explicit_aliases": {}
        }

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


ALIAS_CONFIG = load_alias_config(ALIASES_PATH)


def apply_alias_rules(value: str) -> str:
    v = normalize_name(value)

    explicit_aliases = {
        normalize_name(k): normalize_name(val)
        for k, val in ALIAS_CONFIG.get("explicit_aliases", {}).items()
    }

    if v in explicit_aliases:
        return explicit_aliases[v]

    for prefix in ALIAS_CONFIG.get("strip_prefixes", []):
        prefix_n = normalize_name(prefix)
        if v.startswith(prefix_n):
            v = v[len(prefix_n):]
            break

    for suffix in ALIAS_CONFIG.get("strip_suffixes", []):
        suffix_n = normalize_name(suffix)
        if v.endswith(suffix_n):
            v = v[: -len(suffix_n)]
            break

    return v
def read_tags_file(path: Path) -> set[str]:
    tags: set[str] = set()

    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        for i, row in enumerate(reader):
            if not row:
                continue

            value = row[0].strip().strip('"')
            if not value:
                continue

            if i == 0 and value.lower() == "tag name":
                continue

            tags.add(apply_alias_rules(value))

    return tags


def parse_oi_gen2_or_sfr(item_path: str) -> str | None:
    """
    Examples:
      /ALIAS2/s=Gen2_PCS.AI-2211A         -> AI-2211A
      /ALIAS2/s=SFR PCS.AIT-111           -> AIT-111
      /ALIAS2/s=Gen2_PCS."System.Time"    -> System.Time
      /ALIAS2/s=SFR PCS."Calc.Cdiss"      -> Calc.Cdiss
    """
    match = re.search(r'/ALIAS2/s=(.+)$', item_path, flags=re.IGNORECASE)
    if not match:
        return None

    rhs = match.group(1).strip()

    quoted_match = re.search(r'\."([^"]+)"$', rhs)
    if quoted_match:
        return apply_alias_rules(quoted_match.group(1))

    if "." in rhs:
        return apply_alias_rules(rhs.split(".")[-1])

    return apply_alias_rules(rhs)


def parse_oi_deltav(item_path: str) -> str | None:
    """
    Examples:
      /DA/s=0:20-FI-1115C/AI1/PV.CV      -> 20-FI-1115C
      /DA/s=0:20-ESD/DI1/PV_D.CV         -> 20-ESD
      /DA/s=0:20-HMI-ESD/PV.CV           -> 20-HMI-ESD
    """
    match = re.search(r'/DA/s=0:([^/]+)', item_path, flags=re.IGNORECASE)
    if not match:
        return None

    return apply_alias_rules(match.group(1))


def parse_oi_item(pair_name: str, item_path: str) -> str | None:
    pair_lower = pair_name.lower()

    if "deltav" in pair_lower:
        return parse_oi_deltav(item_path)

    if "gen2_pcs_labview" in pair_lower or "sfr_pcs_labview" in pair_lower:
        return parse_oi_gen2_or_sfr(item_path)

    return None


def read_oi_gateway_file(path: Path, pair_name: str) -> tuple[set[str], int, list[str]]:
    parsed_items: set[str] = set()
    unparsable: list[str] = []
    raw_count = 0

    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        for row in reader:
            if not row:
                continue

            raw_value = row[0].strip().strip('"')
            if not raw_value:
                continue

            raw_count += 1
            parsed = parse_oi_item(pair_name, raw_value)

            if parsed:
                parsed_items.add(parsed)
            else:
                unparsable.append(raw_value)

    return parsed_items, raw_count, unparsable


def get_pair_key_from_filename(filename: str) -> str:
    name = filename.removesuffix(".csv")
    name = re.sub(r"^(oi_gateway__|tags__)", "", name, flags=re.IGNORECASE)
    return name.lower()


def pair_files(oi_dir: Path, tags_dir: Path) -> tuple[list[tuple[str, Path, Path]], list[str], list[str]]:
    oi_files = {get_pair_key_from_filename(p.name): p for p in oi_dir.glob("*.csv")}
    tag_files = {get_pair_key_from_filename(p.name): p for p in tags_dir.glob("*.csv")}

    common_keys = sorted(set(oi_files) & set(tag_files))
    pairs = [(key, oi_files[key], tag_files[key]) for key in common_keys]

    oi_only_files = sorted(p.name for key, p in oi_files.items() if key not in tag_files)
    tag_only_files = sorted(p.name for key, p in tag_files.items() if key not in oi_files)

    return pairs, oi_only_files, tag_only_files


def compare_pair(pair_name: str, oi_csv: Path, tags_csv: Path) -> ComparisonResult:
    oi_items, oi_total_raw, unparsable = read_oi_gateway_file(oi_csv, pair_name)
    tags = read_tags_file(tags_csv)

    oi_only = pretty_sort(oi_items - tags)
    tags_only = pretty_sort(tags - oi_items)
    common_count = len(oi_items & tags)

    return ComparisonResult(
        pair_name=pair_name,
        oi_file=oi_csv.name,
        tags_file=tags_csv.name,
        oi_total_raw=oi_total_raw,
        oi_total_parsed=len(oi_items),
        tags_total=len(tags),
        common_count=common_count,
        oi_only=oi_only,
        tags_only=tags_only,
        unparsable_oi_items=unparsable,
    )


def print_result(result: ComparisonResult) -> None:
    print("=" * 80)
    print(f"Comparison: {result.pair_name}")
    print(f"  OI file:              {result.oi_file}")
    print(f"  Tags file:            {result.tags_file}")
    print(f"  OI raw rows:          {result.oi_total_raw}")
    print(f"  OI parsed unique:     {result.oi_total_parsed}")
    print(f"  Tags unique:          {result.tags_total}")
    print(f"  Common:               {result.common_count}")
    print(f"  OI only:              {len(result.oi_only)}")
    print(f"  Tags only:            {len(result.tags_only)}")
    print(f"  Unparsable OI rows:   {len(result.unparsable_oi_items)}")
    print()

    if result.oi_only:
        print("Available in OI Gateway but missing from Tags:")
        for item in result.oi_only:
            print(f"  - {item}")
        print()

    if result.tags_only:
        print("Present in Tags but missing from OI Gateway:")
        for item in result.tags_only:
            print(f"  - {item}")
        print()

    if result.unparsable_oi_items:
        print("Unparsable OI Gateway rows:")
        for item in result.unparsable_oi_items[:20]:
            print(f"  - {item}")
        if len(result.unparsable_oi_items) > 20:
            print(f"  ... and {len(result.unparsable_oi_items) - 20} more")
        print()

    if not result.oi_only and not result.tags_only and not result.unparsable_oi_items:
        print("No mismatches found.")
        print()


def write_summary(
    summary_path: Path,
    results: list[ComparisonResult],
    oi_only_files: list[str],
    tag_only_files: list[str],
) -> None:
    summary_path.parent.mkdir(parents=True, exist_ok=True)

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    total_oi_only = sum(len(r.oi_only) for r in results)
    total_tags_only = sum(len(r.tags_only) for r in results)
    total_unparsable = sum(len(r.unparsable_oi_items) for r in results)

    lines: list[str] = []
    lines.append("# Latest Compare Summary")
    lines.append("")
    lines.append(f"Generated: {now}")
    lines.append("")
    lines.append("## Overview")
    lines.append("")
    lines.append(f"- Compared file pairs: {len(results)}")
    lines.append(f"- Total points available in OI Gateway but missing from Tags: {total_oi_only}")
    lines.append(f"- Total points present in Tags but missing from OI Gateway: {total_tags_only}")
    lines.append(f"- Total unparsable OI Gateway rows: {total_unparsable}")
    lines.append("")

    if oi_only_files:
        lines.append("## Files only in `exports/oi-gateway`")
        lines.append("")
        for name in oi_only_files:
            lines.append(f"- {name}")
        lines.append("")

    if tag_only_files:
        lines.append("## Files only in `exports/tags`")
        lines.append("")
        for name in tag_only_files:
            lines.append(f"- {name}")
        lines.append("")

    for result in results:
        lines.append(f"## {result.pair_name}")
        lines.append("")
        lines.append(f"- OI file: `{result.oi_file}`")
        lines.append(f"- Tags file: `{result.tags_file}`")
        lines.append(f"- OI raw rows: {result.oi_total_raw}")
        lines.append(f"- OI parsed unique: {result.oi_total_parsed}")
        lines.append(f"- Tags unique: {result.tags_total}")
        lines.append(f"- Common: {result.common_count}")
        lines.append(f"- OI only: {len(result.oi_only)}")
        lines.append(f"- Tags only: {len(result.tags_only)}")
        lines.append(f"- Unparsable OI rows: {len(result.unparsable_oi_items)}")
        lines.append("")

        if result.oi_only:
            lines.append("### Available in OI Gateway but missing from Tags")
            lines.append("")
            for item in result.oi_only:
                lines.append(f"- `{item}`")
            lines.append("")

        if result.tags_only:
            lines.append("### Present in Tags but missing from OI Gateway")
            lines.append("")
            for item in result.tags_only:
                lines.append(f"- `{item}`")
            lines.append("")

        if result.unparsable_oi_items:
            lines.append("### Unparsable OI Gateway rows")
            lines.append("")
            for item in result.unparsable_oi_items[:50]:
                lines.append(f"- `{item}`")
            if len(result.unparsable_oi_items) > 50:
                lines.append(f"- ... and {len(result.unparsable_oi_items) - 50} more")
            lines.append("")

        if not result.oi_only and not result.tags_only and not result.unparsable_oi_items:
            lines.append("No mismatches found.")
            lines.append("")

    summary_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> None:
    if not OI_GATEWAY_DIR.exists():
        raise FileNotFoundError(f"Missing directory: {OI_GATEWAY_DIR}")
    if not TAGS_DIR.exists():
        raise FileNotFoundError(f"Missing directory: {TAGS_DIR}")

    pairs, oi_only_files, tag_only_files = pair_files(OI_GATEWAY_DIR, TAGS_DIR)

    if oi_only_files:
        print("Files only in oi-gateway:")
        for name in oi_only_files:
            print(f"  - {name}")
        print()

    if tag_only_files:
        print("Files only in tags:")
        for name in tag_only_files:
            print(f"  - {name}")
        print()

    if not pairs:
        print("No matching file pairs found.")
        write_summary(SUMMARY_PATH, [], oi_only_files, tag_only_files)
        print(f"Summary written to: {SUMMARY_PATH}")
        return

    results: list[ComparisonResult] = []



    for pair_name, oi_csv, tags_csv in pairs:
        result = compare_pair(pair_name, oi_csv, tags_csv)
        if result.tags_total <= 1:
            print(f"WARNING: suspiciously low tag count in {result.tags_file}: {result.tags_total}")
        results.append(result)
        print_result(result)

    write_summary(SUMMARY_PATH, results, oi_only_files, tag_only_files)
    print(f"Summary written to: {SUMMARY_PATH}")


if __name__ == "__main__":
    main()