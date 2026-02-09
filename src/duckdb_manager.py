"""
DuckDB manager for SERP snapshots
"""

import duckdb
import os
from typing import Optional, List, Dict, Any
from datetime import datetime


class DuckDBManager:
    """Manages DuckDB connection and SERP snapshot schema"""
    
    def __init__(self, db_path: str = "data/serp_data.duckdb"):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        self.conn = duckdb.connect(db_path)
        self._create_schema()
    
    # initialize the schema for the database
    def _create_schema(self):
        """Create schema for SERP snapshots"""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS serp_snapshots (
                snapshot_id BIGINT PRIMARY KEY,
                query TEXT NOT NULL,
                snapshot_date DATE NOT NULL,
                snapshot_timestamp TIMESTAMP NOT NULL,
                url TEXT NOT NULL,
                title TEXT,
                snippet TEXT,
                domain TEXT,
                rank INTEGER NOT NULL,
                UNIQUE(query, snapshot_date, url)
            )
        """)
        
        # Interest scores table
        self.conn.execute("""
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
        
        # Indexes for fast queries
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_query_date 
            ON serp_snapshots(query, snapshot_date)
        """)
        
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_url_query 
            ON serp_snapshots(url, query)
        """)
        
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_interest_scores 
            ON interest_scores(query, snapshot_date)
        """)
    
    # inserting snapshots
    def insert_snapshot(self, results: List[Dict[str, Any]], query: str, 
                       snapshot_date: Optional[datetime] = None):
        """Insert a daily snapshot of SERP results"""
        if snapshot_date is None:
            snapshot_date = datetime.now()
        
        snapshot_timestamp = snapshot_date
        snapshot_date_only = snapshot_date.date() if hasattr(snapshot_date, 'date') else snapshot_date
        
        if not results:
            return
        
        def extract_domain(url: str) -> str:
            if not url:
                return ""
            try:
                from urllib.parse import urlparse
                parsed = urlparse(url)
                return parsed.netloc.replace("www.", "")
            except:
                return ""
        
        # Get max snapshot_id
        max_id_result = self.conn.execute(
            "SELECT COALESCE(MAX(snapshot_id), 0) FROM serp_snapshots"
        ).fetchone()
        next_id = (max_id_result[0] if max_id_result else 0) + 1
        
        rows = []
        for idx, result in enumerate(results):
            url = result.get('url', result.get('link', ''))
            domain = extract_domain(url)
            
            rows.append({
                'snapshot_id': next_id + idx,
                'query': query,
                'snapshot_date': snapshot_date_only,
                'snapshot_timestamp': snapshot_timestamp,
                'url': url,
                'title': result.get('title', ''),
                'snippet': result.get('snippet', result.get('description', '')),
                'domain': domain,
                'rank': idx + 1
            })
        
        import pandas as pd
        df = pd.DataFrame(rows)
        
        # Insert or ignore duplicates
        self.conn.execute("""
            INSERT OR IGNORE INTO serp_snapshots 
            SELECT * FROM df
        """)
        
        # Calculate and store interest score
        self._calculate_interest_score(query, snapshot_date_only)
    
    # calculating the interest score (internal)
    def _calculate_interest_score(self, query: str, snapshot_date):
        """Calculate Search Interest Score (0-100) based on SERP movement"""
        # Get previous day's snapshot for comparison
        prev_date_result = self.conn.execute("""
            SELECT MAX(snapshot_date) 
            FROM serp_snapshots 
            WHERE query = ? 
              AND snapshot_date < ?
        """, [query, snapshot_date]).fetchone()
        
        if not prev_date_result or not prev_date_result[0]:
            # First snapshot, no comparison possible
            return
        
        prev_date = prev_date_result[0]
        
        # Get current top 10 domains
        current_domains = self.conn.execute("""
            SELECT DISTINCT domain 
            FROM serp_snapshots 
            WHERE query = ? 
              AND snapshot_date = ?
              AND rank <= 10
        """, [query, snapshot_date]).fetchall()
        current_domains_set = {row[0] for row in current_domains}
        
        # Get previous top 10 domains
        prev_domains = self.conn.execute("""
            SELECT DISTINCT domain 
            FROM serp_snapshots 
            WHERE query = ? 
              AND snapshot_date = ?
              AND rank <= 10
        """, [query, prev_date]).fetchall()
        prev_domains_set = {row[0] for row in prev_domains}
        
        # Count new domains entering top 10
        new_domains = current_domains_set - prev_domains_set
        new_domains_count = len(new_domains)
        
        # Calculate average rank improvement for existing domains
        rank_changes = self.conn.execute("""
            WITH current_ranks AS (
                SELECT domain, rank
                FROM serp_snapshots
                WHERE query = ? AND snapshot_date = ? 
                  AND rank <= 10
            ),
            prev_ranks AS (
                SELECT domain, rank
                FROM serp_snapshots
                WHERE query = ? AND snapshot_date = ?
                  AND rank <= 10
            )
            SELECT 
                c.domain,
                c.rank as current_rank,
                p.rank as prev_rank,
                (p.rank - c.rank) as rank_improvement
            FROM current_ranks c
            JOIN prev_ranks p ON c.domain = p.domain
        """, [query, snapshot_date, query, prev_date]).fetchall()
        
        if rank_changes:
            avg_rank_improvement = sum(row[3] for row in rank_changes) / len(rank_changes)
        else:
            avg_rank_improvement = 0.0
        
        # Calculate reshuffle frequency (how many domains changed position)
        reshuffle_count = len(rank_changes)
        reshuffle_frequency = reshuffle_count / max(len(current_domains_set), 1)
        
        # Normalize to 0-100 score
        # I'm calculating a final score from 3 weighted sub-scores:
        # - New domains: 0-10 domains = 0-40 points
        # - Rank improvement: -10 to +10 = 0-30 points (normalized)
        # - Reshuffle frequency: 0-1 = 0-30 points
        
        new_domains_score = min(new_domains_count * 4, 40)  # Max 40 points
        rank_improvement_score = min(max((avg_rank_improvement + 10) / 20 * 30, 0), 30)  # Max 30 points
        reshuffle_score = reshuffle_frequency * 30  # Max 30 points
        
        interest_score = new_domains_score + rank_improvement_score + reshuffle_score
        
        # Store interest score
        self.conn.execute("""
            INSERT OR REPLACE INTO interest_scores 
            (query, snapshot_date, interest_score, new_domains_count, avg_rank_improvement, reshuffle_frequency)
            VALUES (?, ?, ?, ?, ?, ?)
        """, [query, snapshot_date, interest_score, new_domains_count, avg_rank_improvement, reshuffle_frequency])
    
    # calculating the interest score for all snapshots
    def calculate_all_interest_scores(self, query: Optional[str] = None):
        """Calculate interest scores for all existing snapshots"""
        # Get all unique query/date combinations that don't have scores yet
        if query:
            dates_query = """
                SELECT DISTINCT query, snapshot_date
                FROM serp_snapshots
                WHERE query = ?
                ORDER BY query, snapshot_date
            """
            snapshot_dates = self.conn.execute(dates_query, [query]).fetchall()
        else:
            dates_query = """
                SELECT DISTINCT query, snapshot_date
                FROM serp_snapshots
                ORDER BY query, snapshot_date
            """
            snapshot_dates = self.conn.execute(dates_query).fetchall()
        
        calculated = 0
        for query_name, snapshot_date in snapshot_dates:
            try:
                # Check if score already exists
                existing = self.conn.execute("""
                    SELECT COUNT(*) FROM interest_scores
                    WHERE query = ? AND snapshot_date = ?
                """, [query_name, snapshot_date]).fetchone()
                
                if existing[0] == 0:
                    # Calculate score
                    self._calculate_interest_score(query_name, snapshot_date)
                    calculated += 1
            except Exception as e:
                # Skip if calculation fails (e.g., no previous snapshot)
                continue
        
        return calculated
    
    # getting the total number of snapshots
    def get_snapshot_count(self) -> int:
        """Get total number of snapshots"""
        result = self.conn.execute("SELECT COUNT(*) FROM serp_snapshots").fetchone()
        return result[0] if result else 0
    
    # close database connection
    def close(self):
        """Close database connection"""
        self.conn.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
