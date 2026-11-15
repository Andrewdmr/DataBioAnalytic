"""
build_network.py

Pre-processing step for the application (run it once).

It reads the raw STRING and Open Targets files from datos_originales/,
builds ONE protein network for the three biological pathways of the team
and writes two small CSV files to datos_app/ that the GUI loads in less
than a second:

    datos_app/nodes.csv   one row per protein
    datos_app/edges.csv   one row per interaction (undirected, no duplicates)

Differences with the TB1 scripts (on purpose):
  1. Open Targets is used with a real threshold on globalScore, so the
     filter actually removes proteins (in TB1 it removed almost nothing).
  2. The network keeps the interactions between neighbours too (induced
     subgraph), not only the interactions that touch a seed gene. In TB1
     every non seed protein was only linked to seeds (star shape).
  3. No random step: the same input always gives the same output.

Usage (from the repository root or from scripts/):
    python scripts/build_network.py
    python scripts/build_network.py --min-score 700 --ot-min 0.05
    python scripts/build_network.py --star      (TB1 behaviour, seed edges only)
"""

import argparse
import os
import sys
import time

import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE_DIR, "datos_originales")
OUT_DIR = os.path.join(BASE_DIR, "datos_app")

INFO_FILE = os.path.join(RAW_DIR, "9606.protein.info.v12.0.txt.gz")
LINKS_FILE = os.path.join(RAW_DIR, "9606.protein.links.v12.0.txt.gz")
OT_FILE = os.path.join(RAW_DIR, "opentargets_cancer_mama.tsv")

# Seed genes of each team member (same lists as the TB1 scripts and README)
PATHWAYS = {
    "reparacion_adn": ["BRCA1", "BRCA2", "PALB2", "RAD51", "ATM",
                       "CHEK2", "BARD1", "BRIP1", "TP53"],
    "senalizacion_hormonal": ["ESR1", "ESR2", "PGR", "ERBB2", "EGFR",
                              "ERBB3", "ERBB4", "AR", "FOXA1", "GATA3"],
    "ciclo_celular": ["CDK4", "CDK6", "CCND1", "MYC", "PIK3CA",
                      "AKT1", "PTEN", "MDM2", "BCL2", "BAX"],
}

DEFAULT_MIN_SCORE = 700   # STRING combined_score, same as TB1 (> 700)
DEFAULT_OT_MIN = 0.05     # Open Targets globalScore threshold (see README of datos_app)


def find_file(path):
    """Accept both the .gz file and the uncompressed .txt file."""
    if os.path.exists(path):
        return path
    if path.endswith(".gz") and os.path.exists(path[:-3]):
        return path[:-3]
    sys.exit(f"File not found: {path}")


def load_protein_info():
    info = pd.read_csv(find_file(INFO_FILE), sep="\t")
    info.columns = [c.lstrip("#") for c in info.columns]
    return info[["string_protein_id", "preferred_name"]]


def load_links(min_score):
    """Read STRING links by chunks and keep only high confidence pairs.

    STRING lists every pair twice (A B and B A). We keep only protein1 < protein2
    so each undirected interaction appears once.
    """
    parts = []
    for chunk in pd.read_csv(find_file(LINKS_FILE), sep=r"\s+", chunksize=2_000_000):
        chunk = chunk[(chunk["combined_score"] > min_score)
                      & (chunk["protein1"] < chunk["protein2"])]
        parts.append(chunk)
    return pd.concat(parts, ignore_index=True)


def load_open_targets():
    ot = pd.read_csv(find_file(OT_FILE), sep="\t", usecols=["symbol", "globalScore"])
    ot["symbol"] = ot["symbol"].astype(str).str.upper()
    return dict(zip(ot["symbol"], ot["globalScore"]))


def build(min_score, ot_min, star_only):
    t0 = time.time()
    print("Reading protein info...")
    info = load_protein_info()
    id_to_name = dict(zip(info["string_protein_id"], info["preferred_name"]))
    name_to_id = {v: k for k, v in id_to_name.items()}

    print(f"Reading STRING links (combined_score > {min_score})...")
    links = load_links(min_score)
    print(f"  {len(links):,} high confidence interactions in the whole human network")

    print("Reading Open Targets associations...")
    ot_score = load_open_targets()

    # 1. Seeds of each pathway, mapped to STRING ids
    seeds = {}
    for pathway, genes in PATHWAYS.items():
        found = {name_to_id[g] for g in genes if g in name_to_id}
        missing = [g for g in genes if g not in name_to_id]
        if missing:
            print(f"  WARNING {pathway}: seeds not found in STRING: {missing}")
        seeds[pathway] = found
    all_seeds = set().union(*seeds.values())

    # 2. Expansion: every protein linked to a seed, then Open Targets filter.
    #    Seeds are always kept, even if their globalScore is low.
    node_pathways = {}
    for pathway, seed_ids in seeds.items():
        touching = links[links["protein1"].isin(seed_ids) | links["protein2"].isin(seed_ids)]
        candidates = set(touching["protein1"]) | set(touching["protein2"]) | seed_ids
        kept = {p for p in candidates
                if p in seed_ids or ot_score.get(id_to_name[p].upper(), -1.0) >= ot_min}
        print(f"  {pathway}: {len(candidates)} proteins before Open Targets, "
              f"{len(kept)} after (globalScore >= {ot_min})")
        for p in kept:
            node_pathways.setdefault(p, set()).add(pathway)

    nodes = set(node_pathways)

    # 3. Edges between kept proteins.
    #    star_only=True reproduces TB1 (at least one end must be a seed).
    edges = links[links["protein1"].isin(nodes) & links["protein2"].isin(nodes)]
    if star_only:
        edges = edges[edges["protein1"].isin(all_seeds) | edges["protein2"].isin(all_seeds)]

    # 4. Write the output files
    os.makedirs(OUT_DIR, exist_ok=True)
    order = list(PATHWAYS)
    node_rows = []
    for p in sorted(nodes, key=lambda x: id_to_name[x]):
        name = id_to_name[p]
        node_rows.append({
            "string_id": p,
            "name": name,
            "pathways": ";".join(w for w in order if w in node_pathways[p]),
            "seed_of": ";".join(w for w in order if p in seeds[w]),
            "ot_score": round(ot_score.get(name.upper(), 0.0), 4),
        })
    pd.DataFrame(node_rows).to_csv(os.path.join(OUT_DIR, "nodes.csv"), index=False)

    edge_df = pd.DataFrame({
        "source": edges["protein1"].map(id_to_name),
        "target": edges["protein2"].map(id_to_name),
        "confidence": edges["combined_score"] / 1000.0,
    }).sort_values(["source", "target"])
    edge_df.to_csv(os.path.join(OUT_DIR, "edges.csv"), index=False)

    print("\nResult")
    print(f"  proteins (nodes):     {len(nodes):,}")
    print(f"  interactions (edges): {len(edge_df):,}")
    print(f"  files written in {OUT_DIR}")
    print(f"  done in {time.time() - t0:.1f} s")


def main():
    parser = argparse.ArgumentParser(description="Build the protein network used by the app")
    parser.add_argument("--min-score", type=int, default=DEFAULT_MIN_SCORE,
                        help="STRING combined_score threshold (default 700)")
    parser.add_argument("--ot-min", type=float, default=DEFAULT_OT_MIN,
                        help="Open Targets globalScore threshold (default 0.05)")
    parser.add_argument("--star", action="store_true",
                        help="keep only edges that touch a seed (TB1 behaviour)")
    args = parser.parse_args()
    build(args.min_score, args.ot_min, args.star)


if __name__ == "__main__":
    main()
