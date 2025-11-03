"""
Database Utilities
Provides database management and initialization utilities
"""

import sqlite3
from typing import List, Dict, Any
import os


class DatabaseManager:
    """Manages water facts database"""

    def __init__(self, database_path: str):
        """
        Initialize database manager

        Args:
            database_path: Path to SQLite database
        """
        self.database_path = database_path
        self.conn = None

    def initialize_database(self):
        """Initialize database with schema"""
        self.conn = sqlite3.connect(self.database_path)
        cursor = self.conn.cursor()

        # Create water_facts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS water_facts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                topic TEXT NOT NULL,
                content TEXT NOT NULL,
                source TEXT NOT NULL,
                confidence REAL DEFAULT 0.8,
                location TEXT DEFAULT 'general',
                last_updated TEXT DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT
            )
        """)

        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_category ON water_facts(category)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_topic ON water_facts(topic)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_location ON water_facts(location)")

        self.conn.commit()

    def add_sample_data(self):
        """Add sample water facts to database"""
        sample_facts = [
            {
                'category': 'safety',
                'topic': 'safety',
                'content': 'EPA sets legal limits on over 90 contaminants in drinking water. These standards ensure that tap water is safe for consumption.',
                'source': 'EPA',
                'confidence': 0.95,
                'location': 'general'
            },
            {
                'category': 'treatment',
                'topic': 'disinfection',
                'content': 'Chlorine is added to drinking water as a disinfectant to kill harmful bacteria and viruses. The levels used are safe and EPA-regulated.',
                'source': 'CDC',
                'confidence': 0.95,
                'location': 'general'
            },
            {
                'category': 'testing',
                'topic': 'testing',
                'content': 'Public water systems test for contaminants daily, weekly, monthly, and annually depending on the contaminant and system size.',
                'source': 'EPA',
                'confidence': 0.90,
                'location': 'general'
            },
            {
                'category': 'quality',
                'topic': 'standards',
                'content': 'Tap water is more strictly regulated than bottled water. EPA drinking water standards are often more stringent than FDA bottled water standards.',
                'source': 'EPA',
                'confidence': 0.90,
                'location': 'general'
            },
            {
                'category': 'contaminants',
                'topic': 'lead',
                'content': 'Lead typically enters drinking water through plumbing materials. The EPA action level for lead is 15 ppb. Most public water systems meet this standard.',
                'source': 'EPA',
                'confidence': 0.90,
                'location': 'general'
            },
            {
                'category': 'treatment',
                'topic': 'fluoride',
                'content': 'Fluoride is added to water to prevent tooth decay at levels recommended by CDC (0.7 mg/L). This level is safe and effective.',
                'source': 'CDC',
                'confidence': 0.95,
                'location': 'general'
            },
            {
                'category': 'contaminants',
                'topic': 'bacteria',
                'content': 'Public water systems monitor for coliform bacteria as an indicator of water quality. Positive tests trigger immediate action.',
                'source': 'EPA',
                'confidence': 0.95,
                'location': 'general'
            },
            {
                'category': 'quality',
                'topic': 'taste_odor',
                'content': 'Taste and odor in water are usually not health concerns. They often result from chlorine used for disinfection or natural minerals.',
                'source': 'Water Quality Association',
                'confidence': 0.85,
                'location': 'general'
            },
            {
                'category': 'regulations',
                'topic': 'reporting',
                'content': 'Water utilities must provide annual Consumer Confidence Reports (CCR) showing test results for all regulated contaminants.',
                'source': 'EPA',
                'confidence': 0.95,
                'location': 'general'
            },
            {
                'category': 'health',
                'topic': 'health_effects',
                'content': 'Drinking water that meets EPA standards has no significant health risks. EPA standards are set well below levels that could cause health effects.',
                'source': 'EPA',
                'confidence': 0.95,
                'location': 'general'
            }
        ]

        cursor = self.conn.cursor()
        for fact in sample_facts:
            cursor.execute("""
                INSERT INTO water_facts (category, topic, content, source, confidence, location)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                fact['category'],
                fact['topic'],
                fact['content'],
                fact['source'],
                fact['confidence'],
                fact['location']
            ))

        self.conn.commit()
        print(f"Added {len(sample_facts)} sample facts to database")

    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search database for facts

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            List of matching facts
        """
        if not self.conn:
            self.conn = sqlite3.connect(self.database_path)
            self.conn.row_factory = sqlite3.Row

        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, category, topic, content, source, confidence, location, last_updated
            FROM water_facts
            WHERE content LIKE ? OR topic LIKE ?
            LIMIT ?
        """, (f'%{query}%', f'%{query}%', limit))

        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()


def setup_database(database_path: str, add_samples: bool = True):
    """
    Setup water facts database

    Args:
        database_path: Path to database file
        add_samples: Whether to add sample data

    Returns:
        DatabaseManager instance
    """
    # Create directory if needed
    db_dir = os.path.dirname(database_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir)

    # Initialize database
    db_manager = DatabaseManager(database_path)
    db_manager.initialize_database()

    # Add sample data if requested
    if add_samples:
        db_manager.add_sample_data()

    return db_manager
