"""
Seed database with synthetic data for testing/demos
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from duckdb_manager import DuckDBManager

# Realistic Next.js SERP results (expanded to allow new domains)
DOMAINS = [
    ("https://nextjs.org/", "nextjs.org", "Next.js by Vercel - The React Framework"),
    ("https://vercel.com/docs/frameworks/nextjs", "vercel.com", "Next.js Documentation | Vercel Docs"),
    ("https://github.com/vercel/next.js", "github.com", "vercel/next.js: The React Framework"),
    ("https://www.w3schools.com/nextjs/", "w3schools.com", "Next.js Tutorial - W3Schools"),
    ("https://nextjs.org/docs", "nextjs.org", "Next.js Documentation"),
    ("https://www.freecodecamp.org/news/nextjs-tutorial/", "freecodecamp.org", "Next.js Tutorial for Beginners"),
    ("https://nextjs.org/learn", "nextjs.org", "Learn Next.js - Interactive Course"),
    ("https://blog.logrocket.com/nextjs-tutorial/", "logrocket.com", "Next.js Tutorial: Building a Full-Stack App"),
    ("https://www.youtube.com/watch?v=nextjs", "youtube.com", "Next.js Full Course for Beginners"),
    ("https://www.reddit.com/r/nextjs/", "reddit.com", "r/nextjs - Next.js Community"),
    # Additional domains for dramatic new entrants
    ("https://www.tutorialspoint.com/nextjs/", "tutorialspoint.com", "Next.js Tutorial - TutorialsPoint"),
    ("https://www.javatpoint.com/nextjs", "javatpoint.com", "Next.js Tutorial - JavaTpoint"),
    ("https://www.geeksforgeeks.org/nextjs/", "geeksforgeeks.org", "Next.js Tutorial - GeeksforGeeks"),
    ("https://www.codecademy.com/learn/nextjs", "codecademy.com", "Learn Next.js - Codecademy"),
    ("https://www.udemy.com/course/nextjs/", "udemy.com", "Next.js Complete Course - Udemy"),
]

SNIPPETS = [
    "Production-ready React framework with the best developer experience and all the features you need for production.",
    "Learn how to build full-stack React applications with Next.js, the React framework for production.",
    "Next.js gives you the best developer experience with all the features you need for production: hybrid static & server rendering, TypeScript support, smart bundling, route pre-fetching, and more.",
    "Get started with Next.js in minutes. Learn the fundamentals and advanced features of the React framework.",
    "Complete guide to building modern web applications with Next.js, including routing, API routes, and deployment.",
    "Step-by-step tutorial covering Next.js basics, server-side rendering, static site generation, and more.",
    "Interactive course that teaches you Next.js from scratch. Build real-world applications as you learn.",
    "Comprehensive Next.js tutorial covering everything from setup to deployment. Includes code examples and best practices.",
    "Watch this complete Next.js course for beginners. Learn React, server-side rendering, and full-stack development.",
    "Join the Next.js community on Reddit. Get help, share projects, and discuss the latest Next.js features and updates.",
]

def generate_snapshot_for_date(date, base_ranks=None, day_index=0):
    """Generate a snapshot with dramatic variation for visual interest"""
    results = []
    import random
    
    # Start with base ranks, then add dramatic variation
    if base_ranks is None:
        base_ranks = list(range(1, 11))
    
    ranks = base_ranks.copy()
    
    # Create dramatic changes based on day to ensure visible trend
    # Strategy: Vary new domains entering and rank improvements dramatically
    
    if day_index == 0:
        # Baseline - stable, low activity (no changes from previous)
        pass  # Keep original ranks - this will be first snapshot so no score
    elif day_index == 1:
        # Day 1: Very minor changes (low score ~20-30)
        # Just swap 1-2 positions
        idx1, idx2 = random.sample(range(len(ranks)), 2)
        ranks[idx1], ranks[idx2] = ranks[idx2], ranks[idx1]
    elif day_index == 2:
        # Day 2: Moderate activity - reshuffle several positions (~40-50)
        for _ in range(4):
            idx1, idx2 = random.sample(range(len(ranks)), 2)
            ranks[idx1], ranks[idx2] = ranks[idx2], ranks[idx1]
    elif day_index == 3:
        # Day 3: NEW DOMAIN ENTERS + big reshuffle (high score ~60-75)
        # Remove domain at position 10, add new one at position 4-6
        removed = ranks.pop()  # Remove last domain
        new_domain = 11  # New domain ID (tutorialspoint)
        insert_pos = random.randint(3, 5)  # Enter at rank 4-6
        ranks.insert(insert_pos, new_domain)
        # Big reshuffle - move many domains
        for _ in range(6):
            idx1, idx2 = random.sample(range(len(ranks)), 2)
            ranks[idx1], ranks[idx2] = ranks[idx2], ranks[idx1]
    elif day_index == 4:
        # Day 4: ANOTHER NEW DOMAIN + massive reshuffle (peak score ~75-90)
        # Remove a different domain, add another new one
        if len(ranks) >= 10:
            removed_idx = random.randint(7, len(ranks)-1)
            removed = ranks.pop(removed_idx)
        new_domain = 12  # Another new domain (javatpoint)
        insert_pos = random.randint(2, 4)  # Enter at rank 3-5
        ranks.insert(insert_pos, new_domain)
        # Massive reshuffle - almost all domains move
        for _ in range(8):
            idx1, idx2 = random.sample(range(len(ranks)), 2)
            ranks[idx1], ranks[idx2] = ranks[idx2], ranks[idx1]
    elif day_index == 5:
        # Day 5: Settle down - fewer changes (~35-45)
        for _ in range(3):
            idx1, idx2 = random.sample(range(len(ranks)), 2)
            ranks[idx1], ranks[idx2] = ranks[idx2], ranks[idx1]
    elif day_index == 6:
        # Day 6: Another reshuffle but less dramatic (~45-55)
        for _ in range(5):
            idx1, idx2 = random.sample(range(len(ranks)), 2)
            ranks[idx1], ranks[idx2] = ranks[idx2], ranks[idx1]
    
    for i, rank in enumerate(ranks[:10]):
        domain_idx = rank - 1
        if domain_idx < len(DOMAINS):
            url, domain, title = DOMAINS[domain_idx]
            snippet = SNIPPETS[domain_idx] if domain_idx < len(SNIPPETS) else SNIPPETS[0]
            
            results.append({
                'url': url,
                'link': url,  # Some APIs use 'link'
                'title': title,
                'snippet': snippet,
                'description': snippet,  # Some APIs use 'description'
            })
    
    return results, ranks

def seed_nextjs_data():
    """Seed database with 7 days of Next.js data"""
    with DuckDBManager() as db:
        print("Seeding database with synthetic Next.js data...")
        
        # Start from 7 days ago
        start_date = datetime.now() - timedelta(days=7)
        base_ranks = list(range(1, 11))
        
        for day in range(7):
            snapshot_date = start_date + timedelta(days=day)
            results, new_ranks = generate_snapshot_for_date(snapshot_date, base_ranks, day_index=day)
            
            db.insert_snapshot(results, "nextjs", snapshot_date=snapshot_date)
            print(f"  Added snapshot for {snapshot_date.date()}: {len(results)} results")
            
            # Update base ranks for next day (some domains move)
            base_ranks = new_ranks
        
        total = db.get_snapshot_count()
        print(f"\nTotal snapshots in database: {total}")
        print("\nYou can now run:")
        print('  python main.py scores --query "nextjs" --days 7')

if __name__ == "__main__":
    seed_nextjs_data()
