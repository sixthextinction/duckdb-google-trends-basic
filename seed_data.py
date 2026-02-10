"""
Seed database with synthetic data for testing/demos.
Self-contained: inserts static data only.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent / "src"))
from duckdb_manager import DuckDBManager

# Static snapshot data: list of {query, date, results}
# Each results entry: {url, title, snippet}
# Order varies by day to produce interest score variation
STATIC_SNAPSHOTS = [
    # nextjs
    {"query": "nextjs", "date": "2024-01-01", "order": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]},
    {"query": "nextjs", "date": "2024-01-02", "order": [0, 2, 1, 3, 4, 5, 6, 7, 8, 9]},
    {"query": "nextjs", "date": "2024-01-03", "order": [0, 1, 2, 4, 3, 5, 6, 7, 8, 9]},
    {"query": "nextjs", "date": "2024-01-04", "order": [1, 0, 2, 3, 4, 5, 6, 7, 8, 9]},
    {"query": "nextjs", "date": "2024-01-05", "order": [0, 1, 2, 3, 5, 4, 6, 7, 8, 9]},
    {"query": "nextjs", "date": "2024-01-06", "order": [0, 1, 2, 3, 4, 5, 6, 8, 7, 9]},
    {"query": "nextjs", "date": "2024-01-07", "order": [0, 1, 2, 3, 4, 5, 6, 7, 9, 8]},
    # react
    {"query": "react", "date": "2024-01-01", "order": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]},
    {"query": "react", "date": "2024-01-02", "order": [0, 2, 1, 3, 4, 5, 6, 7, 8, 9]},
    {"query": "react", "date": "2024-01-03", "order": [2, 0, 1, 3, 4, 5, 6, 7, 8, 9]},
    {"query": "react", "date": "2024-01-04", "order": [0, 1, 3, 2, 4, 5, 6, 7, 8, 9]},
    {"query": "react", "date": "2024-01-05", "order": [0, 1, 2, 3, 5, 4, 6, 7, 8, 9]},
    {"query": "react", "date": "2024-01-06", "order": [0, 1, 2, 3, 4, 6, 5, 7, 8, 9]},
    {"query": "react", "date": "2024-01-07", "order": [0, 1, 2, 3, 4, 5, 6, 7, 9, 8]},
    # vue
    {"query": "vue", "date": "2024-01-01", "order": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]},
    {"query": "vue", "date": "2024-01-02", "order": [0, 2, 1, 3, 4, 5, 6, 7, 8, 9]},
    {"query": "vue", "date": "2024-01-03", "order": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]},
    {"query": "vue", "date": "2024-01-04", "order": [1, 0, 2, 3, 4, 5, 6, 7, 8, 9]},
    {"query": "vue", "date": "2024-01-05", "order": [0, 1, 2, 4, 3, 5, 6, 7, 8, 9]},
    {"query": "vue", "date": "2024-01-06", "order": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]},
    {"query": "vue", "date": "2024-01-07", "order": [0, 1, 2, 3, 4, 5, 6, 8, 7, 9]},
    # angular
    {"query": "angular", "date": "2024-01-01", "order": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]},
    {"query": "angular", "date": "2024-01-02", "order": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]},
    {"query": "angular", "date": "2024-01-03", "order": [0, 2, 1, 3, 4, 5, 6, 7, 8, 9]},
    {"query": "angular", "date": "2024-01-04", "order": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]},
    {"query": "angular", "date": "2024-01-05", "order": [0, 1, 2, 3, 5, 4, 6, 7, 8, 9]},
    {"query": "angular", "date": "2024-01-06", "order": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]},
    {"query": "angular", "date": "2024-01-07", "order": [0, 1, 2, 3, 4, 5, 6, 7, 9, 8]},
]

# Base results per query (indexed by order above)
QUERY_BASES = {
    "nextjs": [
        {"url": "https://nextjs.org/", "title": "Next.js by Vercel", "snippet": "React framework for production."},
        {"url": "https://vercel.com/docs/nextjs", "title": "Next.js Docs | Vercel", "snippet": "Documentation for Next.js."},
        {"url": "https://github.com/vercel/next.js", "title": "vercel/next.js", "snippet": "The React Framework."},
        {"url": "https://www.w3schools.com/nextjs/", "title": "Next.js Tutorial", "snippet": "Learn Next.js basics."},
        {"url": "https://nextjs.org/docs", "title": "Next.js Documentation", "snippet": "Official docs."},
        {"url": "https://www.freecodecamp.org/news/nextjs/", "title": "Next.js Tutorial", "snippet": "Tutorial for beginners."},
        {"url": "https://nextjs.org/learn", "title": "Learn Next.js", "snippet": "Interactive course."},
        {"url": "https://blog.logrocket.com/nextjs/", "title": "Next.js Tutorial", "snippet": "Building full-stack apps."},
        {"url": "https://www.youtube.com/watch?v=nextjs", "title": "Next.js Course", "snippet": "Video course."},
        {"url": "https://www.reddit.com/r/nextjs/", "title": "r/nextjs", "snippet": "Next.js community."},
    ],
    "react": [
        {"url": "https://react.dev/", "title": "React", "snippet": "Library for user interfaces."},
        {"url": "https://reactjs.org/", "title": "React - A JavaScript library", "snippet": "Build user interfaces."},
        {"url": "https://github.com/facebook/react", "title": "facebook/react", "snippet": "React repository."},
        {"url": "https://www.w3schools.com/react/", "title": "React Tutorial", "snippet": "Learn React."},
        {"url": "https://react.dev/learn", "title": "Learn React", "snippet": "Official tutorial."},
        {"url": "https://www.freecodecamp.org/news/react/", "title": "React Tutorial", "snippet": "Beginners guide."},
        {"url": "https://www.codecademy.com/learn/react", "title": "Learn React", "snippet": "Codecademy course."},
        {"url": "https://blog.logrocket.com/react/", "title": "React Tutorial", "snippet": "Modern web apps."},
        {"url": "https://www.youtube.com/watch?v=react", "title": "React Course", "snippet": "Video course."},
        {"url": "https://www.reddit.com/r/reactjs/", "title": "r/reactjs", "snippet": "React community."},
    ],
    "vue": [
        {"url": "https://vuejs.org/", "title": "Vue.js", "snippet": "Progressive JavaScript framework."},
        {"url": "https://github.com/vuejs/core", "title": "vuejs/core", "snippet": "Vue framework."},
        {"url": "https://www.w3schools.com/vuejs/", "title": "Vue.js Tutorial", "snippet": "Learn Vue.js."},
        {"url": "https://vuejs.org/tutorial/", "title": "Vue.js Tutorial", "snippet": "Official guide."},
        {"url": "https://www.freecodecamp.org/news/vuejs/", "title": "Vue.js Tutorial", "snippet": "Beginners guide."},
        {"url": "https://www.codecademy.com/learn/vue-js", "title": "Learn Vue.js", "snippet": "Codecademy course."},
        {"url": "https://blog.logrocket.com/vuejs/", "title": "Vue.js Tutorial", "snippet": "Modern web apps."},
        {"url": "https://www.youtube.com/watch?v=vuejs", "title": "Vue.js Course", "snippet": "Video course."},
        {"url": "https://www.reddit.com/r/vuejs/", "title": "r/vuejs", "snippet": "Vue.js community."},
        {"url": "https://www.tutorialspoint.com/vuejs/", "title": "Vue.js Tutorial", "snippet": "TutorialsPoint."},
    ],
    "angular": [
        {"url": "https://angular.io/", "title": "Angular", "snippet": "Web framework."},
        {"url": "https://github.com/angular/angular", "title": "angular/angular", "snippet": "Angular framework."},
        {"url": "https://www.w3schools.com/angular/", "title": "Angular Tutorial", "snippet": "Learn Angular."},
        {"url": "https://angular.io/tutorial", "title": "Angular Tutorial", "snippet": "Official guide."},
        {"url": "https://www.freecodecamp.org/news/angular/", "title": "Angular Tutorial", "snippet": "Beginners guide."},
        {"url": "https://www.codecademy.com/learn/angular", "title": "Learn Angular", "snippet": "Codecademy course."},
        {"url": "https://blog.logrocket.com/angular/", "title": "Angular Tutorial", "snippet": "Modern web apps."},
        {"url": "https://www.youtube.com/watch?v=angular", "title": "Angular Course", "snippet": "Video course."},
        {"url": "https://www.reddit.com/r/angular/", "title": "r/angular", "snippet": "Angular community."},
        {"url": "https://www.tutorialspoint.com/angular/", "title": "Angular Tutorial", "snippet": "TutorialsPoint."},
    ],
}


def _build_results(query: str, order: list) -> list:
    base = QUERY_BASES[query]
    return [
        {"url": base[i]["url"], "title": base[i]["title"], "snippet": base[i]["snippet"]}
        for i in order
    ]


def seed_data(reset: bool = False):
    """Insert static synthetic data into the database."""
    with DuckDBManager() as db:
        if reset:
            db.conn.execute("DELETE FROM interest_scores")
            db.conn.execute("DELETE FROM serp_snapshots")
            print("Database reset.")
        for s in STATIC_SNAPSHOTS:
            results = _build_results(s["query"], s["order"])
            snapshot_date = datetime.strptime(s["date"], "%Y-%m-%d")
            db.insert_snapshot(results, s["query"], snapshot_date=snapshot_date)
        total = db.get_snapshot_count()
        print(f"Seeded {len(STATIC_SNAPSHOTS)} snapshots. Total in DB: {total}")


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Seed database with static synthetic data")
    p.add_argument("--reset", action="store_true", help="Clear existing data before seeding")
    seed_data(reset=p.parse_args().reset)
