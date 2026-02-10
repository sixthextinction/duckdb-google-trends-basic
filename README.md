# Self-hosted competitive intelligence for indie devs

This is a proof-of-concept for a **lightweight, FOSS alternative to Google Trends** that tracks search engine results (SERPs) over time and calculates search interest trends. 

It uses Bright Data's SERP API to fetch Google results for keywords and stores them in DuckDB. The system automatically calculates a **Search Interest Score** (0-100) based on SERP movement—similar to Google Trends—by tracking new domains entering top 10, rank improvements, and SERP reshuffles.

**Core Features:**
1. **Daily snapshots**: Collects SERP data via CLI (`fetch` command)
2. **Search Interest Score**: Automatic 0-100 score calculation per keyword per day (like Google Trends)

**Additional Analytics:**
- Rank volatility (standard deviation, average rank, change frequency)
- New entrants (first appearances in top 10)
- Content changes (title/snippet updates over time)

The CLI includes commands like `analyze`, `volatility`, `new-entrants`, `changes`, `calculate-scores`, and `scores` to explore historical SERP data for SEO and competitive research.

## Features

- **Daily snapshots**: Fetch and store SERP results for keywords
- **Search Interest Score**: Automatic 0-100 score calculation based on SERP movement (like Google Trends)
- **Rank volatility**: Track how rankings change over time
- **New entrants**: Detect URLs appearing for the first time
- **Content changes**: Monitor title and snippet updates

## Setup

```bash
pip install -r requirements.txt
```

Set environment variables:
- `BRIGHT_DATA_API_KEY`
- `BRIGHT_DATA_ZONE`

## Quick Start Tutorial

Let's track the keyword "nextjs" for a week:

**Day 1: Fetch initial snapshot**
```bash
python main.py fetch --keywords "nextjs"
python main.py analyze --query "nextjs"
# Output: Total snapshots: 1 (not enough for trends yet)
```

**Day 2-7: Fetch daily**
```bash
# Run this daily (or set up a cron job)
python main.py fetch --keywords "nextjs"
```

**After 7 days: View the trend**
```bash
python main.py scores --query "nextjs" --days 7
# Shows interest score trend over time and generates nextjs_trend.png
```

**See which sites entered top 10:**
```bash
python main.py new-entrants --query "nextjs" --days 7
```

**Track rank volatility:**
```bash
python main.py volatility --query "nextjs" --days 7
```

**Note:** To test the tool with sample data, run the seed script:
```bash
python seed_data.py --reset  # Optionally clear existing data first
python seed_data.py
```

## Usage

## Fetch SERP snapshots

```bash
python  main.py  fetch  --keywords  "python"  "javascript"  "react"
```

**Options:**
- `--keywords`: List of keywords to track (required)
- `--num-results`: Number of results per keyword (default: 10)
- `--delay`: Delay between requests in seconds (default: 1.0)

**Sample output:**
```
Fetching snapshots for 3 keywords...
[1/3] 'python': 10 results
[2/3] 'javascript': 10 results
[3/3] 'react': 10 results

Total snapshots in database: 30
```

What happens:

-   Connects to Bright Data API
-   For each keyword, fetches Google search results (default 10 per keyword)
-   Extracts organic results (title, snippet, URL, rank)
-   Creates data/serp_data.duckdb if it doesn't exist
-   Stores each result with timestamp, query, rank, domain
-   Automatically calculates interest scores (if previous snapshot exists)
-   Waits 1 second between requests (configurable with --delay)

**Important:** Interest scores require at least 2 snapshots on different days. Fetch snapshots daily to build historical trends.

## View summary statistics

```bash
python  main.py  analyze  --query  "python"
```

**Sample output:**
```
=== Summary for 'python' ===
Total snapshots: 45
Unique URLs: 127
Unique domains: 23
First snapshot: 2026-01-15
Last snapshot: 2026-02-06
```

What happens:

-   Opens DuckDB in read-only mode
-   Counts snapshots, unique URLs, unique domains
-   Shows first/last snapshot dates

## Analyze rank volatility

```bash
python  main.py  volatility  --query  "python"  --days  30
```

**Sample output:**
```
=== Rank Volatility for 'python' (last 30 days) ===

Top 10 most volatile URLs:

| url | domain | snapshot_count | avg_rank | best_rank | worst_rank | rank_stddev | rank_changes | volatility_pct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| https://www.python.org/ | python.org | 30 | 1.5 | 1 | 3 | 0.67 | 15 | 51.7 |
| https://www.w3schools.com/python/ | w3schools.com | 30 | 2.3 | 1 | 5 | 1.12 | 18 | 62.1 |
| https://en.wikipedia.org/wiki/Python_(programming_language) | wikipedia.org | 28 | 4.1 | 2 | 8 | 1.89 | 12 | 44.4 |
| https://www.codecademy.com/catalog/language/python | codecademy.com | 25 | 5.2 | 3 | 10 | 2.15 | 10 | 41.7 |
```

What happens:

-   Analyzes last 30 days of snapshots
-   Calculates: average rank, best/worst rank, standard deviation, change frequency
-   Ranks URLs by volatility (most unstable first)
-   Prints top 50 most volatile URLs

## Find new entrants

```bash
python  main.py  new-entrants  --query  "python"  --days  7
```

**Sample output:**
```
=== New Entrants for 'python' (last 7 days) ===

Found 3 new URLs:

| url | domain | first_seen | first_rank | title | snippet |
| --- | --- | --- | --- | --- | --- |
| https://realpython.com/ | realpython.com | 2026-02-04 | 7 | Real Python - Python Tutorials | Learn Python programming with Real Python's comprehensive tutorials and courses... |
| https://www.pythonforbeginners.com/ | pythonforbeginners.com | 2026-02-05 | 9 | Python For Beginners | A comprehensive guide to learning Python programming from scratch... |
| https://docs.python-guide.org/ | docs.python-guide.org | 2026-02-06 | 8 | The Hitchhiker's Guide to Python | Best practices and recommendations for Python development... |
```

What happens:

-   Finds URLs that appeared for the first time in last 7 days
-   Shows first appearance date, initial rank, title, snippet
-   Prints up to 50 new URLs in markdown table format

## Track content changes

```bash
python main.py changes --query "python" --days 30
```

**Sample output:**
```
=== Content Changes for 'python' (last 30 days) ===

Found 5 changes:

| url | domain | snapshot_date | rank | prev_title | new_title | prev_snippet | new_snippet | title_changed | snippet_changed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| https://www.python.org/ | python.org | 2026-02-03 | 1 | Welcome to Python.org | Welcome to Python.org - Official Site | Python is a programming language... | Python is a programming language that lets you work quickly... | 1 | 1 |
| https://www.w3schools.com/python/ | w3schools.com | 2026-02-01 | 2 | Python Tutorial | Python Tutorial - Learn Python | Learn Python. Python is a... | Learn Python. Python is a popular programming language... | 1 | 1 |
```

What happens:

-   Compares titles/snippets across snapshots
-   Detects when titles or snippets changed
-   Shows before/after values
-   Prints up to 50 changes, sorted by date

## Calculate interest scores

If you have existing snapshots but no interest scores, calculate them retroactively:

```bash
python main.py calculate-scores --keywords "python" "javascript" "react"
```

**Options:**
- `--keywords`: Keywords to calculate scores for (all if omitted)

**What happens:**
- Calculates interest scores for all snapshot dates that have a previous day's data
- Scores are stored in the `interest_scores` table
- Requires at least 2 snapshots on different days per keyword

**Note:** Interest scores are automatically calculated when fetching new snapshots (if previous data exists). This command is useful for backfilling scores for existing historical data.

## View interest scores

View interest scores for a keyword over time:

```bash
python main.py scores --query "python" --days 90
```

**Options:**
- `--query`: Keyword to view scores for (required)
- `--days`: Number of days to analyze (default: 90)
- `--output`: Output PNG file path (default: `{query}_trend.png`)

The command automatically generates a PNG chart showing the interest score trend over time. By default, it saves to `{query}_trend.png` (e.g., `python_trend.png`). Use `--output` to specify a custom filename.

**Sample output:**
```
=== Interest Scores for 'python' (last 90 days) ===

Found 45 scores:

| snapshot_date | interest_score | new_domains_count | avg_rank_improvement | reshuffle_frequency |
| --- | --- | --- | --- | --- |
| 2026-01-15 | 45.2 | 2 | 1.5 | 0.6 |
| 2026-01-16 | 52.3 | 3 | 2.1 | 0.7 |
| 2026-01-17 | 38.7 | 1 | 0.8 | 0.5 |
...

Chart saved to: python_trend.png
```

The command generates a PNG chart file showing the interest score trend as a line graph with markers, suitable for including in reports or Medium posts.

What happens:

-   Retrieves interest scores from the `interest_scores` table
-   Shows scores over time with component breakdowns in markdown table format
-   Generates a PNG line chart showing the interest score trend over time

**Note:** If no scores are found, run `calculate-scores` first or fetch snapshots on multiple days.

## Multi-Query Comparison Charts

Compare multiple keywords side-by-side with an enhanced visualization:

```bash
python generate_comparison_chart.py --queries "nextjs" "react" "vue" --days 30 --style modern
```

**Options:**
- `--queries`: List of keywords to compare (required)
- `--days`: Number of days to analyze (default: 30)
- `--output`: Output PNG file path (default: `comparison_trend.png`)
- `--style`: Chart style - `modern`, `minimal`, or `vibrant` (default: `modern`)

This generates a visually enhanced chart with:
- Multiple colored trend lines with area fills
- Peak value annotations
- Modern styling with improved typography
- Side-by-side comparison for competitive analysis

## Search Interest Score

The system automatically calculates a **Search Interest Score** (0-100) for each keyword on each day. This score aggregates SERP movement into a single trendline similar to Google Trends:

- **New domains entering top 10**: 0-40 points
- **Average rank improvement**: 0-30 points  
- **SERP reshuffle frequency**: 0-30 points

High scores indicate lots of SERP movement = rising interest. Scores are stored in the `interest_scores` table and can be viewed with the `scores` command.

## Project Structure

```
duckdb-google-trends-basic/
├── src/
│   ├── duckdb_manager.py   # Database schema and operations
│   ├── serp_client.py       # Bright Data API client
│   ├── scraper.py           # Snapshot fetcher
│   └── analytics.py         # Analytics queries
├── data/                    # DuckDB database files
├── main.py                  # CLI entry point
└── requirements.txt
```
