"""Streamlit dashboard for the AI Portfolio Analyst."""

import html

import altair as alt
import pandas as pd
import streamlit as st

from config import get_app_mode
from modules.ai import AIError, summarize_news
from modules.briefing import build_portfolio_direction_feedback
from modules.database import (
    get_daily_report_dates,
    get_daily_trading_report,
    get_portfolio_value_history,
    get_saved_analysis_tickers,
    get_stock_research_history,
    initialize_database,
)
from modules.market import (
    MarketDataError,
    MarketQuote,
    get_market_context,
    get_price_history,
    get_stock_quote,
)
from modules.news import NewsError, get_stock_news
from modules.portfolio import (
    PortfolioError,
    import_positions_csv,
    load_portfolio,
    save_portfolio,
)
from modules.report import ReportError, build_portfolio_overview


st.set_page_config(
    page_title="AI Portfolio Analyst",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)


@st.cache_data(ttl=60, show_spinner=False)
def load_live_quote(ticker: str) -> MarketQuote:
    """Cache a live quote briefly to avoid duplicate Yahoo requests."""

    return get_stock_quote(ticker)


@st.cache_data(ttl=900, show_spinner=False)
def load_price_history(ticker: str, period: str) -> pd.DataFrame:
    """Cache chart data long enough for normal dashboard interaction."""

    return get_price_history(ticker, period)


@st.cache_data(ttl=300, show_spinner=False)
def load_recent_news(ticker: str, limit: int) -> list[dict[str, str]]:
    """Cache recent articles so unrelated interactions keep the same inputs."""

    return get_stock_news(ticker, limit)


@st.cache_data(ttl=300, show_spinner=False)
def load_analysis_context(ticker: str) -> dict[str, float | str]:
    """Cache the price snapshot supplied to the AI for one analysis session."""

    return get_market_context(ticker)


def apply_dashboard_style() -> None:
    """Apply a consistent, restrained visual treatment to the dashboard."""

    st.markdown(
        """
        <style>
            :root {
                --ink: #10213c;
                --muted: #697a96;
                --line: #e5ebf3;
                --canvas: #f8fafc;
                --card: #ffffff;
                --blue: #2563eb;
                --blue-soft: #eff6ff;
            }
            .stApp { background: var(--canvas); color: var(--ink); }
            .block-container {
                max-width: 1160px;
                padding-top: 3.25rem;
                padding-bottom: 4rem;
                padding-left: 2.5rem;
                padding-right: 2.5rem;
            }
            h1, h2, h3, p, li { color: var(--ink); }
            h1 { font-weight: 720; letter-spacing: -0.045em; }
            .portfolio-eyebrow {
                color: var(--blue);
                font-size: 0.7rem;
                font-weight: 800;
                letter-spacing: 0.13em;
                margin-bottom: 0.25rem;
            }
            .portfolio-subtitle {
                color: var(--muted);
                font-size: 1.02rem;
                margin-top: -0.35rem;
                margin-bottom: 2rem;
            }
            [data-testid="stMetric"] {
                background: var(--card);
                border: 1px solid var(--line);
                border-radius: 1rem;
                box-shadow: 0 8px 24px rgba(15, 23, 42, 0.045);
                padding: 1rem 1.15rem;
            }
            [data-testid="stMetricLabel"] {
                color: var(--muted);
                font-size: 0.72rem;
                font-weight: 700;
                letter-spacing: 0.08em;
                text-transform: uppercase;
            }
            [data-testid="stMetricValue"] {
                color: var(--ink);
                font-weight: 650;
            }
            [data-testid="stExpander"] {
                background: var(--card);
                border: 1px solid var(--line);
                border-radius: 0.9rem;
                margin-bottom: 0.65rem;
            }
            .analysis-eyebrow {
                color: var(--blue);
                font-size: 0.72rem;
                font-weight: 800;
                letter-spacing: 0.13em;
                margin-bottom: 0.1rem;
            }
            .analysis-summary {
                background: var(--blue-soft);
                border: 1px solid #dbeafe;
                border-left: 4px solid var(--blue);
                border-radius: 0.85rem;
                color: #1e3a5f;
                font-size: 1rem;
                line-height: 1.6;
                margin: 0.65rem 0 1rem;
                padding: 1.1rem 1.2rem;
            }
            .analysis-heading {
                color: var(--ink);
                font-size: 1.45rem;
                font-weight: 700;
                letter-spacing: -0.03em;
                margin-bottom: 0.25rem;
            }
            .ticker-heading {
                color: var(--ink);
                font-size: 1.32rem;
                font-weight: 700;
                letter-spacing: -0.025em;
                margin: 0.2rem 0 0.2rem 0.55rem;
            }
            .ticker-subtitle {
                color: var(--muted);
                font-size: 0.88rem;
                margin: 0 0 1rem 0.55rem;
            }
            [data-testid="stVegaLiteChart"] {
                background: var(--card);
                border: 1px solid var(--line);
                border-radius: 1rem;
                box-shadow: 0 8px 24px rgba(15, 23, 42, 0.045);
                overflow: hidden;
                padding: 0.35rem;
            }
            [data-testid="stButton"] > button {
                background: #dbeafe;
                border: 1px solid #93c5fd;
                border-radius: 0.65rem;
                box-shadow: 0 4px 12px rgba(37, 99, 235, 0.12);
                color: #1d4ed8;
                font-weight: 700;
            }
            [data-testid="stButton"] > button:hover {
                background: #bfdbfe;
                border-color: #60a5fa;
                box-shadow: 0 7px 18px rgba(37, 99, 235, 0.26);
                color: #1e40af;
            }
            div[data-baseweb="tab-list"] {
                gap: 1.2rem;
                border-bottom: 1px solid var(--line);
            }
            button[data-baseweb="tab"] {
                color: var(--muted);
                font-weight: 700;
                padding: 0.7rem 0.1rem;
            }
            button[data-baseweb="tab"][aria-selected="true"] { color: var(--blue); }
            [data-testid="stCaptionContainer"] p { color: var(--muted); }
            [data-testid="stDivider"] { border-color: var(--line); }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_page_heading(eyebrow: str, title: str, subtitle: str) -> None:
    """Render a consistent page heading."""

    st.markdown(f'<div class="portfolio-eyebrow">{eyebrow}</div>', unsafe_allow_html=True)
    st.title(title)
    st.markdown(f'<div class="portfolio-subtitle">{subtitle}</div>', unsafe_allow_html=True)


def render_portfolio(demo_mode: bool = False) -> None:
    """Render live holdings, news, and AI analysis controls."""

    render_page_heading(
        "PORTFOLIO RESEARCH",
        "AI Portfolio Analyst",
        "Live market data, financial news, and AI-assisted research.",
    )

    try:
        holdings = load_portfolio(
            "demo_portfolio.json" if demo_mode else "portfolio.json"
        )
    except PortfolioError as error:
        st.error(f"Could not load portfolio: {error}")
        return

    if not holdings:
        st.info("No holdings found.")
        return

    st.caption("Data source: Yahoo Finance via yfinance. Prices may be delayed.")
    if demo_mode:
        st.info(
            "Demo Mode uses sample holdings. Live AI requests and the local "
            "end-of-day archive are disabled in the public demo."
        )

    quotes: dict[str, MarketQuote] = {}
    quote_errors: dict[str, str] = {}

    for holding in holdings:
        ticker = holding["ticker"]

        try:
            quotes[ticker] = load_live_quote(ticker)
        except MarketDataError as error:
            quote_errors[ticker] = str(error)

    try:
        overview = build_portfolio_overview(holdings, quotes)
    except ReportError as error:
        st.warning(f"Portfolio overview unavailable: {error}")
    else:
        st.markdown("### Portfolio Overview")

        total_column, largest_column, concentration_column = st.columns(3)
        largest_position = overview["largest_position"]

        with total_column:
            st.metric("Total market value", f"${overview['total_value']:,.2f}")

        with largest_column:
            st.metric("Largest position", largest_position["ticker"])

        with concentration_column:
            st.metric(
                "Largest allocation",
                f"{largest_position['allocation']:.1%}",
            )

        allocation_data = pd.DataFrame(overview["positions"])
        allocation_chart = (
            alt.Chart(allocation_data)
            .mark_arc(innerRadius=65)
            .encode(
                theta=alt.Theta("market_value:Q", title="Market value"),
                color=alt.Color("ticker:N", title="Ticker"),
                tooltip=[
                    alt.Tooltip("ticker:N", title="Ticker"),
                    alt.Tooltip("market_value:Q", title="Market value", format="$.2f"),
                    alt.Tooltip("allocation:Q", title="Allocation", format=".1%"),
                ],
            )
            .properties(height=260, title="Portfolio allocation")
        )
        st.altair_chart(allocation_chart, use_container_width=True)

        st.markdown("### Portfolio Direction")
        if st.button("Generate portfolio direction feedback", key="portfolio-direction"):
            try:
                market_contexts = {
                    holding["ticker"]: load_analysis_context(holding["ticker"])
                    for holding in holdings
                }
                live_analyses = [
                    analysis
                    for holding in holdings
                    if (
                        analysis := st.session_state.get(
                            f"analysis-{holding['ticker']}"
                        )
                    ) is not None
                ]
                st.session_state["portfolio-direction-feedback"] = (
                    build_portfolio_direction_feedback(
                        overview,
                        market_contexts,
                        live_analyses,
                    )
                )
            except (MarketDataError, ValueError) as error:
                st.warning(f"Portfolio direction feedback is unavailable: {error}")

        direction_feedback = st.session_state.get("portfolio-direction-feedback")
        if direction_feedback is not None:
            st.info(direction_feedback.summary)
            direction_column, change_column, coverage_column = st.columns(3)

            with direction_column:
                st.metric("One-month direction", direction_feedback.direction.title())

            with change_column:
                st.metric(
                    "Weighted one-month change",
                    f"{direction_feedback.weighted_one_month_change:+.2%}",
                )

            with coverage_column:
                st.metric(
                    "Research coverage",
                    (
                        f"{direction_feedback.research_coverage}/"
                        f"{direction_feedback.total_positions}"
                    ),
                )

            for point in direction_feedback.key_points:
                st.write(f"â€¢ {point}")

    for holding in holdings:
        ticker = holding["ticker"]
        shares = holding["shares"]

        st.divider()
        st.markdown(f'<div class="ticker-heading">{ticker}</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="ticker-subtitle">Live quote, price history, recent news, and research analysis</div>',
            unsafe_allow_html=True,
        )

        price_column, shares_column = st.columns(2)

        with shares_column:
            st.metric("Shares", shares)

        quote = quotes.get(ticker)
        if quote:
            with price_column:
                st.metric(
                    "Current price",
                    f"${quote['price']:.2f}",
                )
        else:
            with price_column:
                st.metric("Current price", "Unavailable")

            st.warning(f"Market data error: {quote_errors[ticker]}")

        show_chart = st.toggle(
            "Show price chart",
            value=False,
            key=f"show-chart-{ticker}",
        )

        if show_chart:
            period_key = f"chart-period-{ticker}"
            chart_period = st.session_state.get(period_key, "1mo")

            try:
                price_history = load_price_history(ticker, chart_period)
                chart_data = price_history.rename_axis("Date").reset_index()
                first_close = float(chart_data[ticker].iloc[0])
                last_close = float(chart_data[ticker].iloc[-1])
                percentage_change = (last_close - first_close) / first_close

                price_chart = (
                    alt.Chart(chart_data)
                    .mark_line(color="#2563eb", strokeWidth=2.5)
                    .encode(
                        x=alt.X("Date:T", title=None),
                        y=alt.Y(
                            f"{ticker}:Q",
                            title="Closing price (USD)",
                            scale=alt.Scale(zero=False),
                        ),
                        tooltip=[
                            alt.Tooltip("Date:T", title="Date"),
                            alt.Tooltip(f"{ticker}:Q", title="Close", format="$.2f"),
                        ],
                    )
                    .properties(height=280)
                    .interactive()
                )

                st.altair_chart(price_chart, use_container_width=True)
                st.metric(
                    f"{chart_period} change",
                    f"${last_close:,.2f}",
                    f"{percentage_change:+.2%}",
                )

            except MarketDataError as error:
                st.warning(f"Price history unavailable: {error}")

            st.radio(
                "Chart range",
                options=["5d", "1mo", "3mo", "6mo", "1y"],
                horizontal=True,
                key=period_key,
                label_visibility="collapsed",
                help="Historical daily closing prices from Yahoo Finance.",
            )

        try:
            articles = load_recent_news(ticker, limit=8)

        except NewsError as error:
            st.warning(f"News unavailable: {error}")
            continue

        st.markdown("#### Recent news")

        if not articles:
            st.info("No recent articles found.")
            continue

        for article in articles[:3]:
            if article["url"]:
                article_title = html.escape(article["title"])
                article_url = html.escape(article["url"], quote=True)
                st.markdown(
                    f'• <a href="{article_url}" target="_blank" '
                    f'rel="noopener noreferrer">{article_title}</a>',
                    unsafe_allow_html=True,
                )
                continue
            st.write(f"• {article['title']}")

        if len(articles) > 3:
            st.caption(f"{len(articles) - 3} additional articles will be included in the analysis.")

        if demo_mode:
            st.button(
                "AI analysis is available in the local version",
                key=f"analyze-{ticker}",
                disabled=True,
            )
            analyze_clicked = False
        else:
            analyze_clicked = st.button(
                f"Analyze {ticker}",
                key=f"analyze-{ticker}",
            )
        analysis_key = f"analysis-{ticker}"
        context_key = f"analysis-context-{ticker}"
        sources_key = f"analysis-sources-{ticker}"

        if analyze_clicked:
            with st.spinner(f"Analyzing {ticker}..."):
                try:
                    market_context = load_analysis_context(ticker)
                    st.session_state[analysis_key] = summarize_news(
                        ticker,
                        articles,
                        market_context,
                    )
                    st.session_state[context_key] = market_context
                    st.session_state[sources_key] = articles

                except (AIError, MarketDataError) as error:
                    st.error(f"AI analysis unavailable: {error}")
                    continue

        analysis = st.session_state.get(analysis_key)
        analysis_context = st.session_state.get(context_key)
        analysis_sources = st.session_state.get(sources_key, articles)

        if analysis is not None:
            st.markdown('<div class="analysis-eyebrow">LATEST AI RESEARCH</div>', unsafe_allow_html=True)
            st.markdown(
                f'<div class="analysis-heading">{ticker} research summary</div>',
                unsafe_allow_html=True,
            )
            st.caption("Live research only — the end-of-session job saves one final report after market close.")

            (
                recommendation_column,
                sentiment_column,
                risk_column,
                confidence_column,
            ) = st.columns(4)

            with recommendation_column:
                st.metric("Research label", analysis.recommendation.title())

            with sentiment_column:
                st.metric(
                    "Sentiment",
                    analysis.sentiment.title(),
                )

            with risk_column:
                st.metric(
                    "Risk level",
                    analysis.risk_level.title(),
                )

            with confidence_column:
                st.metric(
                    "Confidence",
                    f"{analysis.confidence:.0%}",
                )

            st.markdown(
                f'<div class="analysis-summary">{html.escape(analysis.summary)}</div>',
                unsafe_allow_html=True,
            )
            st.caption(f"Evidence score: {analysis.evidence_score:+d}. A single article cannot change the research label.")

            if analysis_context is not None:
                st.markdown("#### Market context used")
                change_column, range_column = st.columns(2)

                with change_column:
                    st.metric(
                        "One-month price change",
                        f"{analysis_context['one_month_change']:+.2%}",
                    )

                with range_column:
                    st.metric(
                        "One-month range",
                        (
                            f"${analysis_context['one_month_low']:,.2f} — "
                            f"${analysis_context['one_month_high']:,.2f}"
                        ),
                    )

            st.markdown("#### Key points")

            for point in analysis.key_points:
                st.write(f"• {point}")

            if analysis.evidence:
                with st.expander("Evidence and sources"):
                    for evidence_index, item in enumerate(analysis.evidence, start=1):
                        article = analysis_sources[item.article_index - 1]
                        st.markdown(
                            f"**{evidence_index}. {item.claim}**  "
                            f"({item.impact.title()} · {item.materiality.title()} impact)"
                        )
                        st.caption(
                            f"Source {item.article_index}: "
                            f"{article['publisher']} — {article['published']}"
                        )

                        if article["url"]:
                            st.link_button(
                                f"Read source {item.article_index}",
                                article["url"],
                                key=f"source-{ticker}-{evidence_index}",
                            )


def render_analysis_history() -> None:
    """Render previously saved AI analyses from the local database."""

    render_page_heading(
        "RESEARCH ARCHIVE",
        "Analysis History",
        "Review saved stock research by trading date.",
    )

    report_dates = get_daily_report_dates()

    if not report_dates:
        st.info("No end-of-session reports have been saved yet.")
        return

    value_history = get_portfolio_value_history()
    st.markdown("### Portfolio Timeline")

    if len(value_history) > 1:
        timeline_data = pd.DataFrame(value_history)
        timeline_data["trade_date"] = pd.to_datetime(timeline_data["trade_date"])
        timeline_chart = (
            alt.Chart(timeline_data)
            .mark_line(color="#2563eb", strokeWidth=2.5)
            .encode(
                x=alt.X("trade_date:T", title=None),
                y=alt.Y(
                    "portfolio_value:Q",
                    title="Portfolio value (USD)",
                    scale=alt.Scale(zero=False),
                ),
                tooltip=[
                    alt.Tooltip("trade_date:T", title="Trading date"),
                    alt.Tooltip(
                        "portfolio_value:Q",
                        title="Portfolio value",
                        format="$.2f",
                    ),
                ],
            )
            .properties(height=260)
            .interactive()
        )
        st.altair_chart(timeline_chart, use_container_width=True)
    else:
        st.caption("The value timeline appears after at least two saved trading days.")

    research_tickers = get_saved_analysis_tickers()
    if research_tickers:
        st.markdown("### Stock Research Timeline")
        selected_ticker = st.selectbox(
            "Stock",
            research_tickers,
            key="research-timeline-ticker",
        )
        research_history = get_stock_research_history(selected_ticker)

        if len(research_history) > 1:
            research_data = pd.DataFrame(research_history)
            research_data["trade_date"] = pd.to_datetime(research_data["trade_date"])
            research_chart = (
                alt.Chart(research_data)
                .mark_line(color="#2563eb", strokeWidth=2.5, point=True)
                .encode(
                    x=alt.X("trade_date:T", title=None),
                    y=alt.Y("evidence_score:Q", title="Evidence score"),
                    tooltip=[
                        alt.Tooltip("trade_date:T", title="Trading date"),
                        alt.Tooltip("recommendation:N", title="Research label"),
                        alt.Tooltip("sentiment:N", title="Sentiment"),
                        alt.Tooltip("risk_level:N", title="Risk level"),
                        alt.Tooltip("evidence_score:Q", title="Evidence score"),
                    ],
                )
                .properties(height=230)
                .interactive()
            )
            st.altair_chart(research_chart, use_container_width=True)

            latest_research = research_history[-1]
            prior_research = research_history[-2]
            label_column, score_column, risk_column = st.columns(3)

            with label_column:
                st.metric(
                    "Latest research label",
                    latest_research["recommendation"].title(),
                )

            with score_column:
                score_change = (
                    latest_research["evidence_score"]
                    - prior_research["evidence_score"]
                )
                st.metric(
                    "Evidence score",
                    f"{latest_research['evidence_score']:+d}",
                    f"{score_change:+d} vs prior report",
                )

            with risk_column:
                st.metric(
                    "Risk level",
                    latest_research["risk_level"].title(),
                )
        else:
            st.caption(
                "This timeline appears after the selected stock has two saved reports."
            )

    selected_date = st.selectbox("Trading date", report_dates)
    report = get_daily_trading_report(selected_date)

    if report is None:
        st.warning("The selected trading report could not be loaded.")
        return

    selected_history_index = next(
        (
            index
            for index, entry in enumerate(value_history)
            if entry["trade_date"] == selected_date
        ),
        0,
    )
    previous_entry = (
        value_history[selected_history_index - 1]
        if selected_history_index > 0
        else None
    )
    previous_report = (
        get_daily_trading_report(str(previous_entry["trade_date"]))
        if previous_entry is not None
        else None
    )

    close_column, value_column, change_column, count_column = st.columns(4)

    with close_column:
        st.metric("Market close", report["market_close"][:16])

    with value_column:
        st.metric("Portfolio value", f"${report['portfolio_value']:,.2f}")

    with change_column:
        if previous_entry is None:
            st.metric("Change since prior report", "—")
        else:
            previous_value = float(previous_entry["portfolio_value"])
            value_change = report["portfolio_value"] - previous_value
            percent_change = value_change / previous_value if previous_value else 0.0
            st.metric(
                "Change since prior report",
                f"${value_change:+,.2f}",
                f"{percent_change:+.2%}",
            )

    with count_column:
        st.metric("Stock analyses", len(report["analyses"]))

    briefing = report["briefing"]
    if briefing:
        st.markdown("### Daily Portfolio Briefing")
        st.info(briefing.get("summary", "No portfolio summary was saved."))

        attention_tickers = briefing.get("attention_tickers", [])
        if attention_tickers:
            st.warning("Attention flags: " + ", ".join(attention_tickers))

        for point in briefing.get("key_points", []):
            st.write(f"â€¢ {point}")

    if previous_report is not None:
        current_attention = set(briefing.get("attention_tickers", []))
        previous_attention = set(
            previous_report["briefing"].get("attention_tickers", [])
        )
        new_attention = sorted(current_attention - previous_attention)
        cleared_attention = sorted(previous_attention - current_attention)

        st.markdown(f"### Change since {previous_report['trade_date']}")
        new_column, cleared_column = st.columns(2)

        with new_column:
            st.metric("New attention flags", len(new_attention))
            if new_attention:
                st.caption(", ".join(new_attention))

        with cleared_column:
            st.metric("Cleared attention flags", len(cleared_attention))
            if cleared_attention:
                st.caption(", ".join(cleared_attention))

        if not new_attention and not cleared_attention:
            st.caption("No attention-flag changes were recorded from the prior report.")

    st.markdown("### Stock Research")
    for analysis in report["analyses"]:
        label = analysis["ticker"]

        with st.expander(label):
            st.write(analysis["summary"])

            sentiment_column, risk_column, confidence_column = st.columns(3)

            with sentiment_column:
                st.metric("Sentiment", analysis["sentiment"].title())

            with risk_column:
                st.metric("Risk level", analysis["risk_level"].title())

            with confidence_column:
                st.metric("Confidence", f"{analysis['confidence']:.0%}")

            st.markdown("#### Key points")
            for point in analysis["key_points"]:
                st.write(f"• {point}")
            evidence = analysis.get("evidence", [])
            sources = analysis.get("sources", [])
            if evidence and sources:
                with st.expander("Evidence and sources"):
                    for evidence_index, item in enumerate(evidence, start=1):
                        article_index = item.get("article_index", 0)
                        if not isinstance(article_index, int) or not 1 <= article_index <= len(sources):
                            continue

                        source = sources[article_index - 1]
                        st.markdown(f"**{evidence_index}. {item.get('claim', '')}**")
                        st.caption(
                            f"Source {article_index}: {source.get('publisher', 'Unknown')} "
                            f"— {source.get('published', 'Unknown')}"
                        )
                        if source.get("url"):
                            st.link_button(
                                f"Read source {article_index}",
                                source["url"],
                                key=(
                                    f"history-source-{selected_date}-{label}-"
                                    f"{evidence_index}"
                                ),
                            )


def render_portfolio_editor() -> None:
    """Render local controls for editing the portfolio JSON file."""

    render_page_heading(
        "LOCAL PORTFOLIO",
        "Manage Holdings",
        "Add, remove, or adjust positions saved on this computer.",
    )
    st.info("Changes are saved locally to portfolio.json and do not affect the public demo.")

    uploaded_positions = st.file_uploader(
        "Import brokerage positions CSV",
        type=["csv"],
        help="The file must include Ticker and Quantity columns. Cash sweep rows are skipped.",
    )

    if uploaded_positions is not None:
        try:
            csv_text = uploaded_positions.getvalue().decode("utf-8-sig")
            imported_holdings = import_positions_csv(csv_text)
        except (UnicodeDecodeError, PortfolioError) as error:
            st.error(f"Could not import positions: {error}")
        else:
            st.caption(
                f"Found {len(imported_holdings)} market-traded positions. "
                "Cash and money-market sweep rows are excluded."
            )
            st.dataframe(
                pd.DataFrame(imported_holdings),
                hide_index=True,
                use_container_width=True,
            )

            if st.button("Replace local holdings with this CSV", key="import-positions"):
                try:
                    save_portfolio(imported_holdings)
                except PortfolioError as error:
                    st.error(f"Could not save imported positions: {error}")
                else:
                    st.cache_data.clear()
                    st.success("Imported positions saved to portfolio.json.")

    st.divider()
    st.markdown("### Edit holdings manually")

    try:
        holdings = load_portfolio()
    except PortfolioError as error:
        st.error(f"Could not load portfolio: {error}")
        return

    edited_holdings = st.data_editor(
        pd.DataFrame(holdings),
        column_config={
            "ticker": st.column_config.TextColumn("Ticker", required=True),
            "shares": st.column_config.NumberColumn(
                "Shares",
                min_value=0.000001,
                format="%.4f",
                required=True,
            ),
        },
        hide_index=True,
        num_rows="dynamic",
        use_container_width=True,
        key="portfolio-editor",
    )

    if st.button("Save portfolio", key="save-portfolio"):
        try:
            save_portfolio(edited_holdings.to_dict("records"))
        except PortfolioError as error:
            st.error(f"Could not save portfolio: {error}")
            return

        st.cache_data.clear()
        st.success("Portfolio saved. Open the Portfolio tab to view the updated positions.")


def main() -> None:
    """Initialize the dashboard and render its tabs."""

    apply_dashboard_style()
    try:
        configured_mode = st.secrets.get("APP_MODE")
    except FileNotFoundError:
        configured_mode = None
    demo_mode = get_app_mode(configured_mode) == "demo"

    if demo_mode:
        render_portfolio(demo_mode=True)
        return

    initialize_database()
    portfolio_tab, history_tab, editor_tab = st.tabs(
        ["Portfolio", "Analysis History", "Manage Holdings"]
    )

    with portfolio_tab:
        render_portfolio()

    with history_tab:
        render_analysis_history()

    with editor_tab:
        render_portfolio_editor()


if __name__ == "__main__":
    main()
