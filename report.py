"""Write report.html: cost split per person for every year, plus interactive monthly charts."""
import json
import urllib.request

import numpy as np
import pandas as pd

import EnergieVerbrauch as ev

WEATHER = "WeatherVienna.csv"  # daily mean temperature, Vienna (Open-Meteo archive)
WEATHER_URL = ("https://archive-api.open-meteo.com/v1/archive?latitude=48.19&longitude=16.35"
               "&daily=temperature_2m_mean&timezone=Europe/Vienna&start_date={}&end_date={}")


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


def load_weather(last_day):
    """Daily temperatures; fetch days missing since the last run, keep the file if offline."""
    w = pd.read_csv(WEATHER, parse_dates=["date"])
    start = w.date.max() + pd.Timedelta(days=1)
    end = min(last_day, pd.Timestamp.today().normalize() - pd.Timedelta(days=1))
    if start <= end:
        try:
            with urllib.request.urlopen(WEATHER_URL.format(start.date(), end.date()), timeout=20) as r:
                d = json.load(r)["daily"]
            new = pd.DataFrame({"date": pd.to_datetime(d["time"]), "temp_mean_c": d["temperature_2m_mean"]}).dropna()
            w = pd.concat([w, new], ignore_index=True)
            w.to_csv(WEATHER, index=False, date_format="%Y-%m-%d")
        except (OSError, ValueError, KeyError) as e:
            print(f"Weather not updated ({e}), using {WEATHER} up to {w.date.max().date()}")
    return w.set_index("date").temp_mean_c


def monthly(df, years, temp):
    """Per calendar month: average kWh per day, people living here, heating degree days."""
    names = {}
    for entries in years:
        for e in entries:
            if e[0] == "Total":
                continue
            here = names.setdefault(e[0], np.zeros(len(df), bool))
            for s, en, *_ in [tuple(e[1:4])] + list(e[4:]):
                here[s:en + 1] = True
    d = pd.DataFrame({
        "el": df.dE_EL_kWh, "gas": df.dE_Gas_kWh,
        "people": np.sum(list(names.values()), axis=0),
        # Austrian heating degree days 20/12: count 20 - T on days below 12 degrees
        "hdd": (20 - temp).where(temp < 12, 0).reindex(df.index),
    }).iloc[1:]  # first day has no difference
    m = d.resample("MS")
    out = pd.DataFrame({"el": m.el.mean(), "gas": m.gas.mean(), "days": m.el.count(),
                        "people": m.people.mean(), "hdd": m.hdd.sum(min_count=1)})
    # Billing years start in October (year 1 = Oct 2022)
    out["year"] = out.index.year - 2021 - (out.index.month < 10)
    out = out[out.year >= 1]
    # Heating gas per degree day: slope of monthly gas (kWh) against monthly degree days, per year.
    # The intercept is hot water and cooking, so it doesn't distort the slope. Full months only.
    full = out[(out.days == out.index.days_in_month) & out.hdd.notna()]
    per_hdd = {y: np.polyfit(g.hdd, g.gas * g.days, 1)[0] for y, g in full.groupby("year") if len(g) >= 6}
    return out, per_hdd


def chart_data(df, years, temp):
    m, per_hdd = monthly(df, years, temp)
    return {
        "months": [{"m": i.strftime("%Y-%m"), "y": int(r.year), "el": round(r.el, 2), "gas": round(r.gas, 2),
                    "days": int(r.days), "people": round(r.people, 2),
                    "hdd": None if pd.isna(r.hdd) else round(r.hdd)} for i, r in m.iterrows()],
        "gasPerHdd": {int(k): round(float(v), 2) for k, v in per_hdd.items()},
    }


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


CHART_CSS = """
/* Years: one blue ramp, oldest faint (--y1) to newest strongest (--y5) */
:root { --y1:#86b6ef; --y2:#5598e7; --y3:#2a78d6; --y4:#1c5cab; --y5:#0d366b; --gas:#2a78d6; --el:#eb6834; --band:rgba(120,113,108,.12); }
@media (prefers-color-scheme: dark) { :root { --y1:#184f95; --y2:#256abf; --y3:#3987e5; --y4:#6da7ec; --y5:#b7d3f6; --gas:#3987e5; --el:#d95926; --band:rgba(168,162,158,.14); } }
.toggle { display:flex; gap:6px; margin:4px 0 0; }
.toggle button { font:inherit; padding:4px 14px; border-radius:99px; border:1px solid var(--line); background:var(--card); color:var(--fg); cursor:pointer; }
.toggle button[aria-pressed=true] { background:var(--fg); color:var(--bg); border-color:var(--fg); }
.chart { position:relative; height:300px; margin-top:8px; }
.note { color:var(--muted); font-size:.85rem; margin:8px 0 0; }
"""

# Chart.js reads the monthly data embedded by main(); no cost logic here.
CHART_JS = """
const D = JSON.parse(document.getElementById('data').textContent);
const css = n => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
const MONTHS = ['Oct','Nov','Dec','Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep'];
const years = [...new Set(D.months.map(m => m.y))];
const last = years[years.length - 1];
const color = y => css('--y' + Math.max(1, 5 - (last - y)));  // newest year darkest, older years fade
const label = y => 'Year ' + y;
const slot = m => (Number(m.m.slice(5)) + 2) % 12;  // October = 0
const partial = m => m.days < new Date(+m.m.slice(0, 4), +m.m.slice(5), 0).getDate();
let energy = 'gas';

Chart.defaults.font.family = 'system-ui, sans-serif';
Chart.defaults.color = css('--muted');
Chart.defaults.borderColor = css('--line');
Chart.defaults.plugins.legend.labels.boxHeight = 2;
const base = { responsive: true, maintainAspectRatio: false, interaction: { mode: 'index', intersect: false } };

function yearLines(valueFn, unit) {
  return years.map(y => {
    const pts = Array(12).fill(null);
    D.months.filter(m => m.y === y).forEach(m => pts[slot(m)] = valueFn(m, y));
    return { label: label(y), data: pts, borderColor: color(y), backgroundColor: color(y),
             borderWidth: y === last ? 3 : 2, pointRadius: y === last ? 3 : 0, pointHoverRadius: 5, tension: .3, spanGaps: false };
  });
}

const season = new Chart(document.getElementById('season'), { type: 'line', data: { labels: MONTHS, datasets: [] },
  options: { ...base, scales: { y: { beginAtZero: true, title: { display: true, text: 'kWh per day' } } },
    plugins: { tooltip: { callbacks: { label: c => `${c.dataset.label}: ${c.parsed.y.toFixed(1)} kWh/day` } } } } });

const cumulative = new Chart(document.getElementById('cumulative'), { type: 'line', data: { labels: MONTHS, datasets: [] },
  options: { ...base, scales: { y: { beginAtZero: true, title: { display: true, text: 'kWh since October' } } },
    plugins: { tooltip: { callbacks: { label: c => `${c.dataset.label}: ${Math.round(c.parsed.y).toLocaleString()} kWh` } } } } });

// Shade months with three people living in the flat
const bands = { id: 'bands', beforeDatasetsDraw(chart) {
  const { ctx, chartArea: a, scales: { x } } = chart, w = x.getPixelForValue(1) - x.getPixelForValue(0);
  ctx.save(); ctx.fillStyle = css('--band');
  D.months.forEach((m, i) => { if (m.people > 2.5) ctx.fillRect(x.getPixelForValue(i) - w / 2, a.top, w, a.bottom - a.top); });
  ctx.restore();
} };
const history = new Chart(document.getElementById('history'), { type: 'bar', plugins: [bands],
  data: { labels: D.months.map(m => m.m), datasets: [{ data: [], borderRadius: 4, borderSkipped: 'start', categoryPercentage: .85 }] },
  options: { ...base, plugins: { legend: { display: false }, tooltip: { callbacks: {
      title: c => c[0].label, label: c => { const m = D.months[c.dataIndex];
        return [`${c.parsed.y.toFixed(1)} kWh/day`, `${(c.parsed.y / m.people).toFixed(1)} kWh/day per person (${m.people.toFixed(1)} people)`]
          .concat(partial(m) ? [`partial month: ${m.days} days`] : []); } } } },
    scales: { x: { grid: { display: false }, ticks: { callback: (v, i) => D.months[i].m.endsWith('-01') ? D.months[i].m.slice(0, 4) : '', autoSkip: false, maxRotation: 0 } },
              y: { beginAtZero: true, title: { display: true, text: 'kWh per day' } } } } });

new Chart(document.getElementById('perhdd'), { type: 'bar',
  data: { labels: Object.keys(D.gasPerHdd).map(label), datasets: [{ data: Object.values(D.gasPerHdd),
    backgroundColor: Object.keys(D.gasPerHdd).map(y => color(+y)), borderRadius: 4, borderSkipped: 'start', maxBarThickness: 64 }] },
  options: { ...base, plugins: { legend: { display: false },
      tooltip: { callbacks: { label: c => `${c.parsed.y.toFixed(2)} kWh gas per degree day` } } },
    scales: { x: { grid: { display: false } }, y: { beginAtZero: true, title: { display: true, text: 'kWh per degree day' } } } } });

function render() {
  const k = energy;
  season.data.datasets = yearLines(m => m[k]);
  cumulative.data.datasets = yearLines((m, y) => D.months.filter(n => n.y === y && n.m <= m.m).reduce((s, n) => s + n[k] * n.days, 0));
  history.data.datasets[0].data = D.months.map(m => m[k]);
  history.data.datasets[0].backgroundColor = css(k === 'gas' ? '--gas' : '--el');
  [season, cumulative, history].forEach(c => c.update());
  document.querySelectorAll('.toggle button').forEach(b => b.setAttribute('aria-pressed', b.dataset.k === k));
}
document.querySelectorAll('.toggle button').forEach(b => b.onclick = () => { energy = b.dataset.k; render(); });
render();
"""


def main():
    df, year_ends, results = ev.compute()
    _, years_def = ev.define_years(df)
    data = json.dumps(chart_data(df, years_def, load_weather(df.index[-1])))

    years = "".join(year_section(i, c, df) for i, c in reversed(list(enumerate(results, start=1))))
    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Energy Costs</title><style>{CSS}{CHART_CSS}</style></head>
<body><main>
<h1>Energy costs per person</h1>
<p class="sub">Meter readings up to {day(df, len(df) - 1)}. Fixed costs (base prices, metering) are split by days present, consumption costs by kWh.
Each person's kWh is their share (half, a third) of what the flat used while they lived here.
When a room was empty for a while, the people's kWh add up to less than the total, but the euros are still spread over everyone so the full bill is paid.</p>
{years}
<section><h2>All years</h2>{summary(results, df)}</section>
<section>
  <h2>Consumption by month</h2>
  <p class="sub">Monthly averages. Readings are taken every week or two, so single days in between are interpolated and not shown.</p>
  <div class="toggle" role="group" aria-label="Energy"><button data-k="gas">Gas</button><button data-k="el">Electricity</button></div>
  <h3>Season by year</h3><div class="chart"><canvas id="season" role="img" aria-label="Average kWh per day for each month, one line per year"></canvas></div>
  <h3>Total so far this year</h3><div class="chart"><canvas id="cumulative" role="img" aria-label="Cumulative kWh since October, one line per year"></canvas></div>
  <h3>All months</h3><div class="chart"><canvas id="history" role="img" aria-label="Average kWh per day for every month since October 2022"></canvas></div>
  <p class="note">Shaded months: three people living in the flat. Hover a bar for kWh per person.</p>
</section>
<section>
  <h2>Gas adjusted for weather</h2>
  <p class="sub">Heating gas per heating degree day (Vienna, 20/12 method): how much gas the flat needs for each degree it is colder outside.
  A colder winter raises the gas bill but not this number. Lower is better. Years with fewer than six full months are left out.</p>
  <div class="chart"><canvas id="perhdd" role="img" aria-label="kWh of gas per heating degree day for each year"></canvas></div>
</section>
</main>
<script id="data" type="application/json">{data}</script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<script>{CHART_JS}</script>
</body></html>"""
    with open("report.html", "w") as f:
        f.write(page)
    print("Wrote report.html")


if __name__ == "__main__":
    main()
