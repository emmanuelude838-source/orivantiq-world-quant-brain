import json
import random
import hashlib
from datetime import date, datetime
from pathlib import Path

import streamlit as st

APP_DIR = Path(__file__).parent
DATA_FILE = APP_DIR / "alpha_library.json"

st.set_page_config(
    page_title="ORIVANTIQ | World Quant Brain",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Educational reference catalogue. Check operator availability and signatures
# against the current BRAIN platform documentation before submission.
OPERATOR_LIBRARY = {
    "Arithmetic": {
        "add": "Adds two or more inputs.",
        "subtract": "Subtracts the second input from the first.",
        "multiply": "Multiplies inputs.",
        "divide": "Divides the first input by the second; guard against zero.",
        "abs": "Absolute value.",
        "log": "Natural logarithm; input must be valid and positive.",
        "sign": "Returns the sign of an input.",
        "power": "Raises an input to a power.",
        "signed_power": "Power transform that preserves the input sign.",
        "max": "Returns the maximum input.",
        "min": "Returns the minimum input.",
    },
    "Cross-sectional": {
        "rank": "Ranks instruments against one another on the current date.",
        "zscore": "Standardizes values across the current cross-section.",
        "normalize": "Normalizes a cross-sectional vector.",
        "scale": "Scales values, subject to platform-specific signature.",
        "quantile": "Maps ranks into a chosen distribution.",
    },
    "Time-series": {
        "ts_rank": "Ranks the current value within its own historical window.",
        "ts_mean": "Rolling arithmetic mean.",
        "ts_sum": "Rolling sum.",
        "ts_std_dev": "Rolling standard deviation.",
        "ts_product": "Rolling product.",
        "ts_median": "Rolling median.",
        "ts_zscore": "Time-series z-score.",
        "ts_min": "Rolling minimum.",
        "ts_max": "Rolling maximum.",
        "ts_argmin": "Position of the minimum in a rolling window.",
        "ts_argmax": "Position of the maximum in a rolling window.",
        "ts_delta": "Difference between current value and lagged value.",
        "ts_delay": "Lagged value.",
        "ts_corr": "Rolling correlation between two series.",
        "ts_covariance": "Rolling covariance.",
        "ts_skewness": "Rolling skewness.",
        "ts_kurtosis": "Rolling kurtosis.",
        "ts_ir": "Rolling information-ratio-style statistic; verify definition.",
        "ts_decay_linear": "Linearly weighted time-series decay.",
    },
    "Group": {
        "group_rank": "Ranks instruments within a specified group.",
        "group_neutralize": "Removes group-level exposure.",
        "group_zscore": "Standardizes values within groups.",
        "group_mean": "Computes group-level mean.",
        "group_scale": "Scales values within groups.",
    },
    "Logical and conditional": {
        "if_else": "Selects a value based on a condition.",
        "and": "Logical AND.",
        "or": "Logical OR.",
        "not": "Logical NOT.",
        "greater": "Compares whether the first value is greater.",
        "less": "Compares whether the first value is smaller.",
    },
    "Vector": {
        "vec_avg": "Average of vector elements.",
        "vec_sum": "Sum of vector elements.",
        "vec_max": "Maximum vector element.",
        "vec_min": "Minimum vector element.",
        "vec_stddev": "Standard deviation of vector elements.",
        "vec_count": "Count of vector elements.",
    },
    "Other / transformation": {
        "trade_when": "Conditional trade/hold expression; verify exact argument semantics.",
        "bucket": "Maps values into buckets.",
        "hump": "Limits changes in an input signal.",
        "winsorize": "Limits extreme values; availability may vary.",
        "pasteurize": "Platform-specific data treatment; verify availability.",
    },
}

# Templates are research hypotheses, not guaranteed-valid submissions.
# Some expressions require data fields, group classifications, or operators
# that may differ by dataset and account.
FAMILIES = {
    "Momentum": [
        ("rank(ts_delta(close, {w}))", "Tests whether recent price change predicts subsequent relative returns."),
        ("rank(ts_mean(returns, {w}))", "Tests persistence in recent returns."),
        ("rank(ts_rank(close, {w}))", "Tests whether price is high within its own recent history."),
    ],
    "Mean Reversion": [
        ("-rank(ts_zscore(close, {w}))", "Tests whether unusually high or low price levels tend to revert."),
        ("-rank(ts_delta(close, {w}))", "Tests reversal after recent price movement."),
        ("rank(ts_mean(close, {w}) - close)", "Tests deviation from a rolling price mean."),
    ],
    "Volume": [
        ("rank(volume / (ts_mean(volume, {w}) + 0.001))", "Tests unusual trading activity relative to its rolling baseline."),
        ("rank(ts_delta(volume, {w}))", "Tests changes in trading activity."),
    ],
    "Volatility": [
        ("-rank(ts_std_dev(returns, {w}))", "Tests whether lower recent realized volatility is associated with future relative performance."),
        ("rank(ts_skewness(returns, {w}))", "Explores whether return-distribution asymmetry contains information."),
    ],
    "Price Action": [
        ("rank((close - low) / (high - low + 0.001))", "Tests the close location within the daily high-low range."),
        ("rank((close - open) / (abs(open) + 0.001))", "Tests normalized intraday price movement."),
    ],
    "Correlation": [
        ("rank(ts_corr(returns, volume, {w}))", "Tests the relationship between returns and trading activity."),
        ("rank(ts_corr(close, vwap, {w}))", "Tests co-movement between close and VWAP."),
    ],
    "Statistical": [
        ("rank(ts_ir(returns, {w}))", "Explores consistency of returns over a rolling window; verify operator definition."),
        ("rank(ts_kurtosis(returns, {w}))", "Explores changes in tail behaviour."),
        ("rank(ts_median(returns, {w}))", "Uses rolling median returns as a robust signal candidate."),
    ],
    "Liquidity": [
        ("rank(volume / (abs(returns) + 0.001))", "Explores trading activity relative to absolute price movement; proxy only."),
        ("rank(ts_mean(volume, {w}))", "Tests persistence in average trading activity."),
    ],
    "Hybrid": [
        ("rank(ts_mean(returns, {w})) - rank(ts_std_dev(returns, {w}))", "Combines return persistence and realized volatility."),
        ("rank(ts_corr(returns, volume, {w})) * rank(ts_delta(close, {w2}))", "Combines price momentum with return-volume association."),
        ("rank(ts_zscore(close, {w})) * -rank(ts_std_dev(returns, {w2}))", "Combines relative price extension with volatility."),
    ],
}

DEFAULT_SETTINGS = {
    "Instrument type": "Equities",
    "Region": "USA",
    "Universe": "TOP3000",
    "Delay": 1,
    "Decay": 5,
    "Neutralization": "Industry",
    "Truncation": 0.08,
    "Pasteurization": "Verify on platform",
    "Test status": "Not backtested",
    "Sharpe": None,
    "Fitness": None,
    "Turnover": None,
}

def load_library():
    if DATA_FILE.exists():
        try:
            return json.loads(DATA_FILE.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []

def save_library(items):
    DATA_FILE.write_text(json.dumps(items, indent=2), encoding="utf-8")

def make_alpha(family=None):
    family = family or random.choice(list(FAMILIES))
    template, rationale = random.choice(FAMILIES[family])
    w = random.choice([5, 10, 15, 20, 30, 40, 60])
    w2 = random.choice([5, 10, 20, 30, 60])
    expression = template.format(w=w, w2=w2)
    digest = hashlib.sha256(expression.encode()).hexdigest()[:10].upper()
    return {
        "id": f"ORV-{digest}",
        "name": f"{family} Alpha {digest[:5]}",
        "family": family,
        "expression": expression,
        "rationale": rationale,
        "operators": sorted({
            op for group in OPERATOR_LIBRARY.values()
            for op in group
            if op + "(" in expression
        }),
        "settings": DEFAULT_SETTINGS.copy(),
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "validation": "Research candidate — not validated or backtested",
    }

def unique_alpha(items, family=None, attempts=100):
    existing = {x.get("expression") for x in items}
    for _ in range(attempts):
        candidate = make_alpha(family)
        if candidate["expression"] not in existing:
            return candidate
    return None

library = load_library()

st.markdown("""
<style>
.stApp { background: #071426; color: #F4F7FB; }
section[data-testid="stSidebar"] { background: #0B1D33; }
h1, h2, h3 { color: #E8C76A !important; }
div[data-testid="stMetric"] { background: #10243D; padding: 14px; border-radius: 12px; }
div.stButton > button { border-radius: 10px; font-weight: 700; }
.small-note { color: #B8C5D6; font-size: 0.9rem; }
</style>
""", unsafe_allow_html=True)

st.title("🧠 ORIVANTIQ WORLD QUANT BRAIN")
st.caption("Public quantitative research idea laboratory | Build Skills. Create Opportunities. Shape Your Future.")
st.warning(
    "Educational research tool. Generated formulas are hypotheses, not investment advice "
    "or verified profitable strategies. Check operator signatures, data fields and settings "
    "against the current WorldQuant BRAIN documentation before use."
)

page = st.sidebar.radio(
    "Explore",
    ["Dashboard", "Generate Alphas", "Alpha Library", "Operator Dictionary", "Settings Guide", "About"]
)

if page == "Dashboard":
    c1, c2, c3 = st.columns(3)
    c1.metric("Saved research candidates", len(library))
    c2.metric("Alpha families", len(FAMILIES))
    c3.metric("Operator reference entries", sum(len(v) for v in OPERATOR_LIBRARY.values()))
    st.subheader("Research families")
    st.write(" • ".join(FAMILIES.keys()))
    st.subheader("How it works")
    st.markdown("""
    1. Generate a candidate from a research family.
    2. Inspect its expression, rationale and operators.
    3. Review the proposed settings.
    4. Validate syntax and data availability on the target platform.
    5. Backtest before recording any performance metrics.
    """)

elif page == "Generate Alphas":
    st.subheader("Generate new research candidates")
    family_choice = st.selectbox("Alpha family", ["Any family"] + list(FAMILIES))
    count = st.number_input("Number of candidates", min_value=1, max_value=50, value=10)
    if st.button("Generate candidates", type="primary"):
        made = []
        for _ in range(int(count)):
            item = unique_alpha(library + made, None if family_choice == "Any family" else family_choice)
            if item:
                made.append(item)
        library.extend(made)
        save_library(library)
        st.session_state["latest_batch"] = made
        st.success(f"Created {len(made)} unique research candidates.")
    for item in st.session_state.get("latest_batch", []):
        with st.expander(f'{item["name"]} — {item["family"]}', expanded=False):
            st.code(item["expression"])
            st.write(item["rationale"])
            st.write("Operators:", ", ".join(item["operators"]) or "None detected")
            st.json(item["settings"])
            st.caption(item["validation"])
            st.download_button(
                "Download JSON",
                json.dumps(item, indent=2),
                file_name=f'{item["id"]}.json',
                mime="application/json",
                key=f'dl_{item["id"]}'
            )

elif page == "Alpha Library":
    st.subheader("Public research library")
    search = st.text_input("Search by name, formula, or family")
    chosen = [
        x for x in reversed(library)
        if search.lower() in (x.get("name", "") + x.get("expression", "") + x.get("family", "")).lower()
    ]
    if not chosen:
        st.info("No matching saved candidates yet. Generate some in the Generate Alphas section.")
    for item in chosen:
        with st.expander(f'{item["name"]} — {item["family"]} — {item["created_at"][:10]}'):
            st.code(item["expression"])
            st.write(item["rationale"])
            st.write("Operators:", ", ".join(item["operators"]))
            st.json(item["settings"])
            st.caption(item["validation"])

elif page == "Operator Dictionary":
    st.subheader("Operator reference catalogue")
    st.caption("Reference list for research and learning. This is not a guarantee of current platform support.")
    for category, operators in OPERATOR_LIBRARY.items():
        with st.expander(f"{category} ({len(operators)})"):
            for op, description in operators.items():
                st.markdown(f"**`{op}`** — {description}")

elif page == "Settings Guide":
    st.subheader("Alpha simulation settings")
    st.markdown("""
    - **Region:** Market region selected in the simulation environment.
    - **Universe:** Eligible instrument universe; availability depends on region/data.
    - **Delay:** Execution/data delay setting; commonly distinguishes same-day vs next-day assumptions.
    - **Decay:** Smooths or slows changes in portfolio weights according to platform behaviour.
    - **Neutralization:** Controls exposure removal, such as market, sector or industry.
    - **Truncation:** Limits the influence of extreme weights.
    - **Pasteurization:** Platform-specific handling of data outliers/missing values; verify current meaning.

    These are editable research defaults only. They are not recommendations and must be selected
    according to the platform, dataset, instrument universe and research objective.
    """)
    st.info("No Sharpe, Fitness, Returns or Turnover values are fabricated. Add them only from real backtest results.")

elif page == "About":
    st.subheader("About ORIVANTIQ World Quant Brain")
    st.write("""
    ORIVANTIQ is a public educational quantitative research idea laboratory.
    It helps users explore formula structures, operator families and simulation settings.
    It does not connect to WorldQuant BRAIN, submit Alphas, or run verified backtests.
    """)
    st.markdown("**Important deployment note:** Streamlit Community Cloud storage can be ephemeral. For a reliable public shared library, connect a persistent database (for example, Supabase) before treating saved entries as permanent.")

st.divider()
st.caption("ORIVANTIQ | Research responsibly. Validate before submission.")
