"""
DuckDB Google Trends - CLI
"""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from scraper import fetch_snapshots
from analytics import SERPAnalytics
from duckdb_manager import DuckDBManager


def df_to_markdown(df, max_cell_length=200): # max_cell_length is the maximum length of a cell in the markdown table
    """Convert DataFrame to markdown table format"""
    if len(df) == 0:
        return ""
    
    # Truncate long text fields
    df_display = df.copy()
    for col in df_display.columns:
        if df_display[col].dtype == 'object':
            df_display[col] = df_display[col].astype(str).apply(
                lambda x: x[:max_cell_length] + '...' if len(x) > max_cell_length else x
            )
    
    # Build markdown table
    lines = []
    
    # Header
    headers = '| ' + ' | '.join(df_display.columns) + ' |'
    lines.append(headers)
    
    # Separator
    separator = '| ' + ' | '.join(['---'] * len(df_display.columns)) + ' |'
    lines.append(separator)
    
    # Rows
    for _, row in df_display.iterrows():
        cells = []
        for col in df_display.columns:
            value = str(row[col])
            # Escape pipe characters in cells
            value = value.replace('|', '\\|')
            cells.append(value)
        lines.append('| ' + ' | '.join(cells) + ' |')
    
    return '\n'.join(lines)


def cmd_fetch(args):
    """Fetch snapshots for keywords"""
    keywords = args.keywords or []
    if not keywords:
        print("Error: No keywords provided")
        return
    
    fetch_snapshots(keywords, num_results=args.num_results, delay=args.delay)


def cmd_analyze(args):
    """Run analytics for a query"""
    with SERPAnalytics() as analytics:
        stats = analytics.summary_stats(args.query)
        
        print(f"\n=== Summary for '{args.query}' ===")
        print(f"Total snapshots: {stats['total_snapshots']}")
        print(f"Unique URLs: {stats['unique_urls']}")
        print(f"Unique domains: {stats['unique_domains']}")
        print(f"First snapshot: {stats['first_snapshot']}")
        print(f"Last snapshot: {stats['last_snapshot']}")


def cmd_volatility(args):
    """Show rank volatility"""
    with SERPAnalytics() as analytics:
        result = analytics.rank_volatility(args.query, days=args.days)
        
        print(f"\n=== Rank Volatility for '{result['query']}' (last {result['days']} days) ===")
        if len(result['results']) == 0:
            print("No data found")
            return
        
        print(f"\nTop {len(result['results'])} most volatile URLs:\n")
        print(df_to_markdown(result['results']))


def cmd_new_entrants(args):
    """Show new entrants"""
    with SERPAnalytics() as analytics:
        result = analytics.new_entrants(args.query, days=args.days)
        
        print(f"\n=== New Entrants for '{result['query']}' (last {result['days']} days) ===")
        if len(result['results']) == 0:
            print("No new entrants found")
            return
        
        print(f"\nFound {len(result['results'])} new URLs:\n")
        print(df_to_markdown(result['results']))


def cmd_changes(args):
    """Show title/snippet changes"""
    with SERPAnalytics() as analytics:
        result = analytics.content_changes(args.query, days=args.days)
        
        print(f"\n=== Content Changes for '{result['query']}' (last {result['days']} days) ===")
        if len(result['results']) == 0:
            print("No changes found")
            return
        
        print(f"\nFound {len(result['results'])} changes:\n")
        print(df_to_markdown(result['results']))


def cmd_calculate_scores(args):
    """Calculate interest scores for existing snapshots"""
    keywords = args.keywords or []
    
    with DuckDBManager() as db:
        if keywords:
            print(f"Calculating interest scores for {len(keywords)} keywords...")
            total = 0
            for keyword in keywords:
                count = db.calculate_all_interest_scores(query=keyword)
                total += count
                if count > 0:
                    print(f"  '{keyword}': {count} scores calculated")
        else:
            print("Calculating interest scores for all keywords...")
            total = db.calculate_all_interest_scores()
        
        print(f"\nTotal interest scores calculated: {total}")
        if total == 0:
            print("\nNote: Interest scores require at least 2 snapshots on different days.")
            print("Fetch snapshots on multiple days to build historical data.")


def _generate_png_chart(df, query, days, output_path):
    """Generate PNG chart using matplotlib"""
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    from datetime import datetime
    
    # Handle date formatting
    dates = []
    for d in df['snapshot_date']:
        if isinstance(d, datetime):
            dates.append(d)
        elif isinstance(d, str):
            d_str = d.strip()
            try:
                if ' ' in d_str or 'T' in d_str:
                    if 'T' in d_str:
                        dates.append(datetime.fromisoformat(d_str.replace('Z', '+00:00')))
                    else:
                        dates.append(datetime.strptime(d_str, '%Y-%m-%d %H:%M:%S'))
                else:
                    dates.append(datetime.strptime(d_str, '%Y-%m-%d'))
            except ValueError:
                dates.append(datetime.strptime(d_str.split()[0], '%Y-%m-%d'))
        else:
            dates.append(datetime.combine(d, datetime.min.time()) if hasattr(d, 'date') else datetime.fromisoformat(str(d)))
    
    scores = df['interest_score'].astype(float).values
    
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(dates, scores, marker='o', linewidth=2, markersize=4, label=query)
    
    ax.set_xlabel('Date', fontsize=12)
    ax.set_ylabel('Interest Score (0-100)', fontsize=12)
    ax.set_title(f'Search Interest Trend: {query} ({days} days)', fontsize=14, fontweight='bold')
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, 100)
    
    # Format x-axis dates
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=max(1, days // 10)))
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()


def cmd_scores(args):
    """Show interest scores for a query"""
    with SERPAnalytics() as analytics:
        result = analytics.interest_scores(args.query, days=args.days)
        
        print(f"\n=== Interest Scores for '{result['query']}' (last {result['days']} days) ===")
        if len(result['results']) == 0:
            print("No interest scores found")
            print("Note: Interest scores require at least 2 snapshots on different days.")
            print("To calculate scores for existing data, run:")
            print(f"  python main.py calculate-scores --keywords {args.query}")
            return
        
        print(f"\nFound {len(result['results'])} scores:\n")
        print(df_to_markdown(result['results']))
        
        # Generate PNG chart
        output_path = args.output or f"{args.query.replace(' ', '_')}_trend.png"
        _generate_png_chart(result['results'], args.query, args.days, output_path)
        print(f"\nChart saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="DuckDB Google Trends")
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Fetch command
    fetch_parser = subparsers.add_parser('fetch', help='Fetch SERP snapshots')
    fetch_parser.add_argument('--keywords', nargs='+', help='Keywords to track')
    fetch_parser.add_argument('--num-results', type=int, default=10, help='Results per keyword')
    fetch_parser.add_argument('--delay', type=float, default=1.0, help='Delay between requests (seconds)')
    
    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Show summary statistics')
    analyze_parser.add_argument('--query', required=True, help='Query keyword')
    
    # Volatility command
    vol_parser = subparsers.add_parser('volatility', help='Show rank volatility')
    vol_parser.add_argument('--query', required=True, help='Query keyword')
    vol_parser.add_argument('--days', type=int, default=30, help='Days to analyze')
    
    # New entrants command
    new_parser = subparsers.add_parser('new-entrants', help='Show new URLs')
    new_parser.add_argument('--query', required=True, help='Query keyword')
    new_parser.add_argument('--days', type=int, default=7, help='Days to analyze')
    
    # Changes command
    changes_parser = subparsers.add_parser('changes', help='Show title/snippet changes')
    changes_parser.add_argument('--query', required=True, help='Query keyword')
    changes_parser.add_argument('--days', type=int, default=30, help='Days to analyze')
    
    # Calculate scores command
    calc_parser = subparsers.add_parser('calculate-scores', help='Calculate interest scores for existing snapshots')
    calc_parser.add_argument('--keywords', nargs='+', help='Keywords to calculate scores for (all if omitted)')
    
    # Scores command
    scores_parser = subparsers.add_parser('scores', help='Show interest scores for a query')
    scores_parser.add_argument('--query', required=True, help='Query keyword')
    scores_parser.add_argument('--days', type=int, default=90, help='Days to analyze')
    scores_parser.add_argument('--output', type=str, help='Output PNG file path (default: {query}_trend.png)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    commands = {
        'fetch': cmd_fetch,
        'analyze': cmd_analyze,
        'volatility': cmd_volatility,
        'new-entrants': cmd_new_entrants,
        'changes': cmd_changes,
        'calculate-scores': cmd_calculate_scores,
        'scores': cmd_scores
    }
    
    commands[args.command](args)


if __name__ == "__main__":
    main()
