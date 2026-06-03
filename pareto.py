"""
パレート図自動生成スクリプト
pandas + matplotlib だけで動きます（Python 3.10+）
"""
import logging
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path

logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)

matplotlib.rcParams["font.family"] = [
    "Meiryo", "Yu Gothic", "MS Gothic",   # Windows
    "Hiragino Sans", "AppleGothic",         # macOS
    "Noto Sans CJK JP", "IPAGothic",        # Linux
    "DejaVu Sans",                           # ASCII フォールバック
]

# ── 設定（ここだけ書き換えてください） ──────────────
CSV_PATH     = Path(__file__).parent / "defects.csv"  # 入力ファイルパス（CSV または Excel）
ITEM_COLUMN  = "不良種別"       # 分類軸の列名
COUNT_COLUMN = "件数"           # 件数列（生データなら None に変更）
THRESHOLD    = 80              # しきい値（%）
OUTPUT_DIR   = Path(__file__).parent / "output"
# ──────────────────────────────────────────────────


def load_data(path, item_col, count_col):
    p = Path(path)
    if p.suffix in {".xlsx", ".xls"}:
        df = pd.read_excel(p)
    else:
        df = pd.read_csv(p, encoding="utf-8-sig")

    if item_col not in df.columns:
        raise ValueError(f"列 '{item_col}' が見つかりません: {list(df.columns)}")

    if count_col is None:
        return df[item_col].value_counts()
    else:
        s = df.groupby(item_col)[count_col].sum().sort_values(ascending=False)
        s.name = item_col  # 分類軸の名前を保持（count列名に上書きされるのを防ぐ）
        return s


def plot_pareto(series, threshold, output_dir):
    out = Path(output_dir)
    out.mkdir(exist_ok=True)
    save_path = out / f"pareto_{series.name or 'chart'}.png"

    total = series.sum()
    cumulative_pct = series.cumsum() / total * 100

    fig, ax1 = plt.subplots(figsize=(10, 6))

    # 棒グラフ（左軸：件数）
    ax1.bar(series.index, series.values,
            color="#3B82F6", edgecolor="white", linewidth=0.5)
    ax1.set_xlabel(series.name or "項目", fontsize=12)
    ax1.set_ylabel("件数", fontsize=12, color="#3B82F6")
    ax1.tick_params(axis="y", labelcolor="#3B82F6")
    ax1.tick_params(axis="x", rotation=30)

    # 折れ線グラフ（右軸：累積%）
    ax2 = ax1.twinx()
    ax2.plot(series.index, cumulative_pct.values,
             color="#EF4444", marker="o", linewidth=2, markersize=6, label="累積%")
    ax2.set_ylabel("累積 (%)", fontsize=12, color="#EF4444")
    ax2.tick_params(axis="y", labelcolor="#EF4444")
    ax2.set_ylim(0, 110)

    # しきい値の水平線
    ax2.axhline(threshold, color="#10B981", linestyle="--",
                linewidth=1.5, label=f"しきい値 {threshold}%")

    # しきい値を超える最初のアイテムに垂直補助線
    over = cumulative_pct[cumulative_pct >= threshold]
    if not over.empty:
        x_pos = list(series.index).index(over.index[0])
        ax2.axvline(x_pos, color="#10B981", linestyle=":", linewidth=1.0)

    ax2.legend(loc="center right", fontsize=10)
    ax1.set_title(f"パレート図 — {series.name or '不良種別'}", fontsize=14, pad=12)
    ax1.grid(axis="y", alpha=0.3)

    plt.tight_layout()
    plt.savefig(save_path, dpi=150)
    plt.close()
    return save_path


series = load_data(CSV_PATH, ITEM_COLUMN, COUNT_COLUMN)
print(f"\n集計結果（降順）:\n{series.to_string()}")
print(f"合計: {series.sum()} 件")

saved = plot_pareto(series, THRESHOLD, OUTPUT_DIR)
print(f"\n[OK] 保存しました: {saved}")
