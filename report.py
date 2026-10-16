"""Write report.html: cost split per person for every year, plus the plots."""
import base64
import io

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

import EnergieVerbrauch as ev


def img(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=110, bbox_inches="tight")
    plt.close(fig)
    return f'<img alt="" src="data:image/png;base64,{base64.b64encode(buf.getvalue()).decode()}">'


def day(df, i):
    return df.index[i].strftime("%d.%m.%Y")


def year_section(i, c, df):
    table = pd.DataFrame({
        "Person": c["Name"],
        "From": [day(df, s) for s in c["start"]],
        "To": [day(df, e) for e in c["end"]],
        "Electricity kWh": c["EL"],
        "Gas kWh": c["GAS"],
        "Electricity EUR": c["EUR_EL"],
        "Gas EUR": c["EUR_GAS"],
        "To pay EUR": [a + b for a, b in zip(c["EUR_EL"], c["EUR_GAS"])],
    })
    badge = (f'<span class="badge">Estimate, Year {c["bill_year"]} prices, no bill yet</span>'
             if c["estimate"] else '<span class="badge bill">From bill</span>')
    return f"""
<section>
  <h2>Year {i} {badge}</h2>
  <p class="sub">{day(df, c["start"][-1])} to {day(df, c["end"][-1])}</p>
  {table.to_html(index=False, float_format="{:,.2f}".format, border=0, escape=True)}
</section>"""


def summary(results, df):
    table = pd.DataFrame({
        "Year": [f"Year {i}" for i in range(1, len(results) + 1)],
        "From": [day(df, c["start"][-1]) for c in results],
        "To": [day(df, c["end"][-1]) for c in results],
        "Electricity kWh": [c["EL"][-1] for c in results],
        "Gas kWh": [c["GAS"][-1] for c in results],
        "Electricity EUR": [c["EUR_EL"][-1] for c in results],
        "Gas EUR": [c["EUR_GAS"][-1] for c in results],
        "Total EUR": [c["EUR_EL"][-1] + c["EUR_GAS"][-1] for c in results],
        "Source": ["Estimate" if c["estimate"] else "Bill" for c in results],
    })
    return table.to_html(index=False, float_format="{:,.2f}".format, border=0)


CSS = """
:root { --bg:#fafaf9; --fg:#1c1917; --muted:#78716c; --card:#fff; --line:#e7e5e4; --accent:#b45309; --ok:#15803d; }
@media (prefers-color-scheme: dark) { :root { --bg:#1c1917; --fg:#f5f5f4; --muted:#a8a29e; --card:#292524; --line:#44403c; --accent:#f59e0b; --ok:#4ade80; } }
body { margin:0; padding:24px 16px; background:var(--bg); color:var(--fg); font:15px/1.5 system-ui, sans-serif; }
main { max-width:960px; margin:0 auto; }
h1 { margin:0 0 4px; } .sub { color:var(--muted); margin:0 0 12px; }
section { background:var(--card); border:1px solid var(--line); border-radius:10px; padding:16px 20px; margin:16px 0; overflow-x:auto; }
h2 { margin:0; font-size:1.2rem; display:flex; gap:10px; align-items:center; flex-wrap:wrap; }
.badge { font-size:.75rem; font-weight:500; color:var(--accent); border:1px solid currentColor; border-radius:99px; padding:1px 8px; }
.badge.bill { color:var(--ok); }
table { border-collapse:collapse; width:100%; font-variant-numeric:tabular-nums; }
th, td { padding:6px 10px; border-bottom:1px solid var(--line); text-align:right; white-space:nowrap; }
th:first-child, td:first-child { text-align:left; }
th { color:var(--muted); font-weight:500; font-size:.85rem; }
tbody tr:last-child td { font-weight:600; border-bottom:none; }
td:nth-last-child(1) { font-weight:600; }
img { max-width:100%; height:auto; background:#fff; border-radius:6px; }
"""


def main():
    df, year_ends, results = ev.compute()

    ev.plot_rolling_year(df, year_ends, mode="ma")
    plot_ma = img(plt.gcf())
    ev.plot_rolling_year(df, year_ends, mode="cumulative")
    plot_cum = img(plt.gcf())
    ev.plot_timeline(df)
    plot_timeline = img(plt.gcf())

    years = "".join(year_section(i, c, df) for i, c in reversed(list(enumerate(results, start=1))))
    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Energy Costs</title><style>{CSS}</style></head>
<body><main>
<h1>Energy costs per person</h1>
<p class="sub">Meter readings up to {day(df, len(df) - 1)}. Fixed costs (base prices, metering) are split by days present, consumption costs by kWh.
Each person's kWh is their share (half, a third) of what the flat used while they lived here.
When a room was empty for a while, the people's kWh add up to less than the total, but the euros are still spread over everyone so the full bill is paid.</p>
{years}
<section><h2>All years</h2>{summary(results, df)}</section>
<section><h2>Daily consumption</h2>{plot_timeline}</section>
<section><h2>Year comparison</h2>{plot_ma}{plot_cum}</section>
</main></body></html>"""
    with open("report.html", "w") as f:
        f.write(page)
    print("Wrote report.html")


if __name__ == "__main__":
    main()
