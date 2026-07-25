# AI Portfolio Analyst

A local, research-only dashboard for a small portfolio. It combines Yahoo Finance
market data, recent news, and Gemini-generated stock research. It does **not**
place trades or provide personalized investment advice.

## What it does

- Displays current quotes, allocation, and interactive price charts.
- Generates cautious stock research from recent headlines and a one-month price
  snapshot.
- Retains article sources with each saved analysis so claims can be checked.
- Creates one immutable end-of-session report for each completed NYSE trading day.
- Produces a deterministic portfolio briefing for concentration and attention flags.

## Run locally

1. Create and activate the virtual environment if it does not already exist:

   ```powershell
   py -3.13 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

2. Install dependencies:

   ```powershell
   pip install -r requirements.txt
   ```

3. Add a `.env` file in the project root:

   ```text
   AI_PROVIDER=gemini
   GEMINI_MODEL=gemini-3.6-flash
   GEMINI_API_KEY=your_key_here
   ```

4. Update `portfolio.json` with the holdings you want to research, then run:

   ```powershell
   .\.venv\Scripts\streamlit.exe run streamlit_app.py --server.port 8502
   ```

## Daily reports

`run_end_of_day.cmd` runs the end-of-session job once. The configured Windows
scheduled task invokes it periodically; it safely exits before market close, on
non-trading days, and after a report has already been saved for that session.

Each report uses the data available when it runs. Prices and news may be delayed
or incomplete, so treat all output as research context—not a trading instruction.

## Public demo deployment

The repository includes a safe `demo` mode for a public Streamlit deployment.
It uses `demo_portfolio.json`, hides local analysis history, and disables
AI-generated analysis so visitors cannot consume your Gemini API quota.

Set this deployment secret/environment variable:

```text
APP_MODE=demo
```

Do not add your `.env`, local SQLite database, or personal `portfolio.json`
data to a public repository. The deployed demo does not run the Windows
end-of-day scheduler; keep that job on the local version unless you later add
a separate hosted scheduler.

## Checks

Run the test suite with:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```
