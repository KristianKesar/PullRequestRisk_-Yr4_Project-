# make_charts.py - Kristian Kesar, C00296348
#
# makes the charts for the docs + screencast, saves them into docs/images/
# run it after download_data.py and train.py:
#   python scripts/make_charts.py

from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
from sklearn.metrics import precision_recall_curve

from pr_risk.dataset import load_apachejit, load_split, to_xy
from pr_risk.model import load, rule_baseline

matplotlib.use("Agg")   # just save files, dont try to open a window

# colours: blue for clean / the model, orange for buggy / the rule
BLUE = "#2a78d6"
ORANGE = "#eb6834"
GREY = "#8a8985"
TEXT = "#0b0b0b"
MUTED = "#52514e"
BG = "#fcfcfb"

plt.rcParams.update({
    "figure.facecolor": BG, "axes.facecolor": BG, "savefig.facecolor": BG,
    "text.color": TEXT, "axes.labelcolor": MUTED, "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.edgecolor": "#d6d5d0", "axes.spines.top": False, "axes.spines.right": False,
    "font.size": 11,
})

out = Path("docs/images")
out.mkdir(parents=True, exist_ok=True)


# ---- chart 1: buggy vs clean ----------------------------------------
# 3 small charts side by side cause the numbers are on totally different scales
df = load_apachejit("data/raw/apachejit_total.csv")
medians = df.groupby("buggy")[["total_churn", "files_changed", "change_entropy"]].median()

panels = [("total_churn", "Lines changed"), ("files_changed", "Files changed"),
          ("change_entropy", "Spread (entropy)")]
fig, axes = plt.subplots(1, 3, figsize=(10, 3.6))
for ax, (col, title) in zip(axes, panels):
    clean, buggy = medians.loc[0, col], medians.loc[1, col]
    bars = ax.bar(["Clean", "Buggy"], [clean, buggy], color=[BLUE, ORANGE], width=0.55)
    for bar, value in zip(bars, [clean, buggy]):
        label = f"{value:.2f}" if col == "change_entropy" else f"{value:.0f}"
        ax.text(bar.get_x() + bar.get_width() / 2, value, label,
                ha="center", va="bottom", color=TEXT, fontsize=11)
    ax.set_title(title, fontsize=12, color=TEXT)
    ax.set_yticks([])
    ax.spines["left"].set_visible(False)
fig.suptitle("Buggy commits are bigger and more spread out (median, ApacheJIT)",
             fontsize=13, color=TEXT)
fig.tight_layout()
fig.savefig(out / "buggy_vs_clean.png", dpi=150)
plt.close(fig)


# ---- chart 2: model vs the 400 line rule ------------------------------
# the line = every trade-off the model can make between catching bugs (recall)
# and not crying wolf (precision). the dot = where the simple rule lands
_, test_df = load_split("data/raw")
X_test, y_test = to_xy(test_df)
model = load("models/risk_model.joblib")
probs = model.predict_proba(X_test)[:, 1]
precision, recall, _ = precision_recall_curve(y_test, probs)
rule = rule_baseline(X_test, y_test)

fig, ax = plt.subplots(figsize=(7, 5))
ax.plot(recall, precision, color=BLUE, linewidth=2, label="Logistic regression")
ax.axhline(y_test.mean(), color=GREY, linewidth=1.5, linestyle="--",
           label=f"Random guessing ({y_test.mean():.0%})")
ax.scatter([rule["recall"]], [rule["precision"]], s=90, color=ORANGE, zorder=3,
           edgecolor=BG, linewidth=2, label="Rule: over 400 lines")
ax.set_xlabel("Recall (share of buggy changes caught)")
ax.set_ylabel("Precision (share of flagged changes that were buggy)")
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)
ax.grid(color="#ecebe7", linewidth=0.8)
ax.set_axisbelow(True)
ax.legend(frameon=False, loc="upper right")
ax.set_title("Model vs simple rule on 2017-2019 commits", fontsize=13, color=TEXT)
fig.tight_layout()
fig.savefig(out / "model_vs_rule.png", dpi=150)
plt.close(fig)

print("saved docs/images/buggy_vs_clean.png and docs/images/model_vs_rule.png")
