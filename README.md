# ORIVANTIQ World Quant Brain

A public Streamlit starter app for generating and organizing quantitative Alpha research hypotheses.

## Run locally

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Publish publicly for free

1. Create a GitHub account and a new public repository.
2. Upload `app.py` and `requirements.txt` to the repository root.
3. Open https://share.streamlit.io/
4. Sign in with GitHub, select the repository, branch, and `app.py`.
5. Deploy and share the public Streamlit URL.

## Important limitations

- The app generates educational research candidates, not verified profitable strategies.
- The operator list is a broad reference catalogue, not a guarantee that every operator or signature is supported by every BRAIN dataset/account.
- It does not connect to BRAIN, submit formulas, or run backtests.
- The JSON file is local app storage. Streamlit Community Cloud may not preserve local files reliably across restarts/redeployments. Use a persistent database such as Supabase for a dependable shared public library.
- This starter generates candidates when a visitor clicks Generate. True unattended scheduled generation requires a scheduled job and persistent database.
- Performance metrics must only be entered from actual backtest results.
