import pandas as pd

df = pd.read_csv("wild_grid_analysis/results/cropland_watersheds.csv")

HA_TO_ACRES = 2.47105

def area_summary(subset, label):
    print(f"  {label}: {len(subset):,}")
    print(f"    Total watershed area:  {subset['area_total_ha'].sum():>12,.0f} ha  /  {subset['area_total_ha'].sum()*HA_TO_ACRES:>14,.0f} acres")
    print(f"    Total cropland area:   {subset['area_cropland_ha'].sum():>12,.0f} ha  /  {subset['area_cropland_ha'].sum()*HA_TO_ACRES:>14,.0f} acres")
    print(f"    Total perennial area:  {subset['area_perennial_ha'].sum():>12,.0f} ha  /  {subset['area_perennial_ha'].sum()*HA_TO_ACRES:>14,.0f} acres")

# 1. Watersheds with <20% perennial cover
low_peren = df[df["pct_perennial"] < 20]
print("=== 1. Watersheds with <20% perennial cover ===")
print(f"  Count: {len(low_peren):,} of {len(df):,} total ({len(low_peren)/len(df)*100:.1f}%)")
print()
area_summary(df, "All qualifying watersheds (>=25% cropland)")
area_summary(low_peren, "Watersheds with <20% perennial cover")

# 2. By state — expand multi-state rows so each state gets credit
print("\n=== 2. States with most watersheds <20% perennial cover ===")
state_rows = low_peren.copy()
state_rows["state"] = state_rows["state"].str.split(",")
state_rows = state_rows.explode("state")
state_rows["state"] = state_rows["state"].str.strip()
by_state = state_rows.groupby("state").size().sort_values(ascending=False)

total_by_state = df.copy()
total_by_state["state"] = total_by_state["state"].str.split(",")
total_by_state = total_by_state.explode("state")
total_by_state["state"] = total_by_state["state"].str.strip()
total_counts = total_by_state.groupby("state").size()

pct_by_state = (by_state / total_counts * 100).round(1)
summary = pd.DataFrame({"low_peren_count": by_state, "total_count": total_counts, "pct_low_peren": pct_by_state}).dropna()
summary = summary.sort_values("low_peren_count", ascending=False)
print(summary.head(20).to_string())

# 3. Narrowed to >50% cropland
print("\n=== 3. Watersheds with >50% cropland ===")
high_crop = df[df["pct_cropland"] > 50]
high_crop_low_peren = high_crop[high_crop["pct_perennial"] < 20]
print(f"  Count: {len(high_crop):,} of {len(df):,} total ({len(high_crop)/len(df)*100:.1f}%)")
print()
area_summary(high_crop, "All watersheds with >50% cropland")
print()
print(f"  Of those, with <20% perennial: {len(high_crop_low_peren):,} ({len(high_crop_low_peren)/len(high_crop)*100:.1f}%)")
print()
area_summary(high_crop_low_peren, "Watersheds with >50% cropland AND <20% perennial")

# 4. Acres needed to bring all <20% perennial watersheds up to 20% threshold
print("\n=== 4. Acres needed to reach 20% perennial cover ===")

def acres_to_20pct(subset, label):
    deficit_ha = (subset["area_total_ha"] * 0.20 - subset["area_perennial_ha"]).clip(lower=0)
    total_deficit_ha = deficit_ha.sum()
    print(f"  {label}:")
    print(f"    {total_deficit_ha:>14,.0f} ha  /  {total_deficit_ha * HA_TO_ACRES:>14,.0f} acres")

acres_to_20pct(low_peren, "Group 1: >=25% cropland, <20% perennial (9,872 watersheds)")
acres_to_20pct(high_crop_low_peren, "Group 2: >50% cropland, <20% perennial (8,729 watersheds)")
