"""
Analytics queries for SERP data
"""

import duckdb
from typing import Dict, Any, Optional
from datetime import datetime, timedelta


def _ensure_schema_exists(db_path: str):
    """Ensure database schema exists (creates tables if needed)"""
    # Open in write mode temporarily to ensure schema exists
    temp_conn = duckdb.connect(db_path)
    try:
        # Create interest_scores table if it doesn't exist
        temp_conn.execute("""
            CREATE TABLE IF NOT EXISTS interest_scores (
                query TEXT NOT NULL,
                snapshot_date DATE NOT NULL,
                interest_score DOUBLE NOT NULL,
                new_domains_count INTEGER,
                avg_rank_improvement DOUBLE,
                reshuffle_frequency DOUBLE,
                UNIQUE(query, snapshot_date)
            )
        """)
        
        # Create index
        try:
            temp_conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_interest_scores 
                ON interest_scores(query, snapshot_date)
            """)
        except:
            pass
    finally:
        temp_conn.close()


class SERPAnalytics:
    """Analytics queries for SERP snapshots"""
    
    def __init__(self, db_path: str = "data/serp_data.duckdb"):
        # Ensure schema exists before opening read-only connection
        _ensure_schema_exists(db_path)
        self.conn = duckdb.connect(db_path, read_only=True)
    
    def rank_volatility(self, query: str, days: int = 30) -> Dict[str, Any]:
        """
        Calculate rank volatility for URLs over time
        
        Returns URLs with their rank changes, standard deviation, etc.
        """
        cutoff_date = datetime.now().date() - timedelta(days=days)
        
        result = self.conn.execute("""
            WITH rank_changes AS (
                SELECT 
                    url,
                    domain,
                    rank,
                    snapshot_date,
                    LAG(rank) OVER (PARTITION BY url ORDER BY snapshot_date) as prev_rank
                FROM serp_snapshots
                WHERE query = ? 
                  AND snapshot_date >= ?
                ORDER BY url, snapshot_date
            ),
            volatility AS (
                SELECT 
                    url,
                    domain,
                    COUNT(*) as snapshot_count,
                    AVG(rank) as avg_rank,
                    MIN(rank) as best_rank,
                    MAX(rank) as worst_rank,
                    STDDEV(rank) as rank_stddev,
                    COUNT(CASE WHEN prev_rank IS NOT NULL AND rank != prev_rank THEN 1 END) as rank_changes
                FROM rank_changes
                GROUP BY url, domain
            )
            SELECT 
                url,
                domain,
                snapshot_count,
                ROUND(avg_rank, 2) as avg_rank,
                best_rank,
                worst_rank,
                ROUND(rank_stddev, 2) as rank_stddev,
                rank_changes,
                ROUND(CAST(rank_changes AS DOUBLE) / NULLIF(snapshot_count - 1, 0) * 100, 1) as volatility_pct
            FROM volatility
            WHERE snapshot_count > 1
            ORDER BY rank_stddev DESC, avg_rank ASC
            LIMIT 50
        """, [query, cutoff_date]).df()
        
        return {
            'query': query,
            'days': days,
            'results': result
        }
    
    def new_entrants(self, query: str, days: int = 7) -> Dict[str, Any]:
        """
        Find URLs that appeared for the first time in recent snapshots
        """
        cutoff_date = datetime.now().date() - timedelta(days=days)
        
        result = self.conn.execute("""
            WITH first_appearance AS (
                SELECT 
                    url,
                    domain,
                    MIN(snapshot_date) as first_seen
                FROM serp_snapshots
                WHERE query = ?
                GROUP BY url, domain
            ),
            recent_entrants AS (
                SELECT 
                    fa.url,
                    fa.domain,
                    fa.first_seen,
                    s.rank as first_rank,
                    s.title,
                    s.snippet
                FROM first_appearance fa
                JOIN serp_snapshots s 
                    ON fa.url = s.url 
                    AND fa.first_seen = s.snapshot_date
                    AND s.query = ?
                WHERE fa.first_seen >= ?
            )
            SELECT 
                url,
                domain,
                first_seen,
                first_rank,
                title,
                snippet
            FROM recent_entrants
            ORDER BY first_seen DESC, first_rank ASC
            LIMIT 50
        """, [query, query, cutoff_date]).df()
        
        return {
            'query': query,
            'days': days,
            'results': result
        }
    
    def content_changes(self, query: str, days: int = 30) -> Dict[str, Any]:
        """
        Detect title and snippet changes over time
        """
        cutoff_date = datetime.now().date() - timedelta(days=days)
        
        result = self.conn.execute("""
            WITH changes AS (
                SELECT 
                    url,
                    domain,
                    snapshot_date,
                    rank,
                    title,
                    snippet,
                    LAG(title) OVER (PARTITION BY url ORDER BY snapshot_date) as prev_title,
                    LAG(snippet) OVER (PARTITION BY url ORDER BY snapshot_date) as prev_snippet
                FROM serp_snapshots
                WHERE query = ? 
                  AND snapshot_date >= ?
            )
            SELECT 
                url,
                domain,
                snapshot_date,
                rank,
                prev_title,
                title as new_title,
                prev_snippet,
                snippet as new_snippet,
                CASE 
                    WHEN prev_title IS NOT NULL AND title != prev_title THEN 1 
                    ELSE 0 
                END as title_changed,
                CASE 
                    WHEN prev_snippet IS NOT NULL AND snippet != prev_snippet THEN 1 
                    ELSE 0 
                END as snippet_changed
            FROM changes
            WHERE (prev_title IS NOT NULL AND title != prev_title)
               OR (prev_snippet IS NOT NULL AND snippet != prev_snippet)
            ORDER BY snapshot_date DESC, rank ASC
            LIMIT 50
        """, [query, cutoff_date]).df()
        
        return {
            'query': query,
            'days': days,
            'results': result
        }
    
    def interest_scores(self, query: str, days: int = 90, 
                        start_date: Optional[datetime] = None, 
                        end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Get interest scores for a query over time"""
        if start_date is not None:
            start = start_date.date() if hasattr(start_date, 'date') else start_date
        else:
            start = datetime.now().date() - timedelta(days=days)
        end = end_date.date() if end_date and hasattr(end_date, 'date') else (end_date or datetime.now().date())
        
        result = self.conn.execute("""
            SELECT 
                snapshot_date,
                interest_score,
                new_domains_count,
                avg_rank_improvement,
                reshuffle_frequency
            FROM interest_scores
            WHERE query = ?
              AND snapshot_date >= ?
              AND snapshot_date <= ?
            ORDER BY snapshot_date ASC
        """, [query, start, end]).df()
        
        return {
            'query': query,
            'days': days,
            'results': result
        }
    
    def summary_stats(self, query: str) -> Dict[str, Any]:
        """Get summary statistics for a query"""
        result = self.conn.execute("""
            SELECT 
                COUNT(DISTINCT snapshot_date) as total_snapshots,
                COUNT(DISTINCT url) as unique_urls,
                COUNT(DISTINCT domain) as unique_domains,
                MIN(snapshot_date) as first_snapshot,
                MAX(snapshot_date) as last_snapshot
            FROM serp_snapshots
            WHERE query = ?
        """, [query]).fetchone()
        
        return {
            'query': query,
            'total_snapshots': result[0],
            'unique_urls': result[1],
            'unique_domains': result[2],
            'first_snapshot': result[3],
            'last_snapshot': result[4]
        }
    
    def close(self):
        """Close database connection"""
        self.conn.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
