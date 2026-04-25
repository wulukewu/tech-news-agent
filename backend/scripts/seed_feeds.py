#!/usr/bin/env python3
"""
Seed script for initializing default RSS feeds in Supabase database.

This script:
1. Loads environment variables from .env file
2. Validates required Supabase credentials
3. Establishes connection to Supabase
4. Inserts predefined RSS feeds into the feeds table

Usage:
    python scripts/seed_feeds.py
"""

import os

from dotenv import load_dotenv
from supabase import Client, create_client


def main():
    """Main function to seed feeds into Supabase database."""

    # Load environment variables from .env file
    load_dotenv()

    # Validate required environment variables
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")

    if not supabase_url:
        raise ValueError(
            "Error: Missing required environment variable: SUPABASE_URL\n"
            "Please copy .env.example to .env and fill in the values"
        )

    if not supabase_key:
        raise ValueError(
            "Error: Missing required environment variable: SUPABASE_KEY\n"
            "Please copy .env.example to .env and fill in the values"
        )

    # Create Supabase client connection
    try:
        supabase: Client = create_client(supabase_url, supabase_key)
        print("Successfully connected to Supabase")
    except Exception as e:
        raise ConnectionError(
            f"Error: Failed to connect to Supabase\n"
            f"Please check:\n"
            f"1. SUPABASE_URL is correct (format: https://xxx.supabase.co)\n"
            f"2. SUPABASE_KEY is valid (check Supabase Dashboard > Settings > API)\n"
            f"3. Network connection is available\n"
            f"Details: {e!s}"
        )

    # Define default RSS feeds data structure
    default_feeds = [
        # AI & Machine Learning
        {
            "name": "Google AI Blog",
            "url": "http://googleresearch.blogspot.com/atom.xml",
            "category": "AI & Machine Learning",
            "is_active": True,
        },
        {
            "name": "OpenAI Engineering",
            "url": "https://openai.com/news/engineering/rss.xml",
            "category": "AI & Machine Learning",
            "is_active": True,
        },
        {
            "name": "arXiv cs.AI",
            "url": "https://rss.arxiv.org/rss/cs.AI",
            "category": "AI & Machine Learning",
            "is_active": True,
        },
        {
            "name": "MarkTechPost",
            "url": "https://www.marktechpost.com/feed/",
            "category": "AI & Machine Learning",
            "is_active": True,
        },
        {
            "name": "MIT Technology Review - AI",
            "url": "https://www.technologyreview.com/topic/artificial-intelligence/feed/",
            "category": "AI & Machine Learning",
            "is_active": True,
        },
        {
            "name": "KDnuggets",
            "url": "https://www.kdnuggets.com/feed",
            "category": "AI & Machine Learning",
            "is_active": True,
        },
        # Architecture & System Design
        {
            "name": "High Scalability",
            "url": "http://feeds.feedburner.com/HighScalability",
            "category": "Architecture & System Design",
            "is_active": True,
        },
        {
            "name": "ByteByteGo",
            "url": "https://blog.bytebytego.com/feed",
            "category": "Architecture & System Design",
            "is_active": True,
        },
        {
            "name": "Quastor",
            "url": "https://blog.quastor.org/feed",
            "category": "Architecture & System Design",
            "is_active": True,
        },
        {
            "name": "Martin Fowler Blog",
            "url": "https://martinfowler.com/feed.atom",
            "category": "Architecture & System Design",
            "is_active": True,
        },
        {
            "name": "Netflix Tech Blog",
            "url": "https://netflixtechblog.com/feed",
            "category": "Architecture & System Design",
            "is_active": True,
        },
        {
            "name": "Uber Engineering",
            "url": "https://www.uber.com/en-GB/blog/london/engineering/rss/",
            "category": "Architecture & System Design",
            "is_active": True,
        },
        {
            "name": "Stripe Engineering",
            "url": "https://stripe.com/blog/feed.rss",
            "category": "Architecture & System Design",
            "is_active": True,
        },
        # Cloud Native, DevOps & SRE
        {
            "name": "Kubernetes Official Blog",
            "url": "https://kubernetes.io/feed.xml",
            "category": "Cloud Native, DevOps & SRE",
            "is_active": True,
        },
        {
            "name": "SRE Weekly",
            "url": "https://sreweekly.com/feed",
            "category": "Cloud Native, DevOps & SRE",
            "is_active": True,
        },
        {
            "name": "HashiCorp Blog",
            "url": "https://www.hashicorp.com/blog.atom",
            "category": "Cloud Native, DevOps & SRE",
            "is_active": True,
        },
        {
            "name": "Cloudflare Blog",
            "url": "https://blog.cloudflare.com/rss/",
            "category": "Cloud Native, DevOps & SRE",
            "is_active": True,
        },
        {
            "name": "DZone DevOps",
            "url": "https://feeds.dzone.com/devops",
            "category": "Cloud Native, DevOps & SRE",
            "is_active": True,
        },
        # Cybersecurity & InfoSec
        {
            "name": "Krebs on Security",
            "url": "https://krebsonsecurity.com/feed/",
            "category": "Cybersecurity & InfoSec",
            "is_active": True,
        },
        {
            "name": "Google Project Zero",
            "url": "https://googleprojectzero.blogspot.com/feeds/posts/default",
            "category": "Cybersecurity & InfoSec",
            "is_active": True,
        },
        {
            "name": "BleepingComputer",
            "url": "https://www.bleepingcomputer.com/feed",
            "category": "Cybersecurity & InfoSec",
            "is_active": True,
        },
        {
            "name": "Dark Reading",
            "url": "https://www.darkreading.com/rss/all.xml",
            "category": "Cybersecurity & InfoSec",
            "is_active": True,
        },
        {
            "name": "PortSwigger Research",
            "url": "https://portswigger.net/research/rss",
            "category": "Cybersecurity & InfoSec",
            "is_active": True,
        },
        # Core Programming Languages
        {
            "name": "The Rust Blog",
            "url": "https://blog.rust-lang.org/feed.xml",
            "category": "Core Programming Languages",
            "is_active": True,
        },
        {
            "name": "This Week in Rust",
            "url": "https://this-week-in-rust.org/rss.xml",
            "category": "Core Programming Languages",
            "is_active": True,
        },
        {
            "name": "The Go Blog",
            "url": "http://blog.golang.org/feeds/posts/default",
            "category": "Core Programming Languages",
            "is_active": True,
        },
        {
            "name": "GolangCode",
            "url": "https://golangcode.com/index.xml",
            "category": "Core Programming Languages",
            "is_active": True,
        },
        # Data Engineering & Analytics
        {
            "name": "Seattle Data Guy",
            "url": "https://www.theseattledataguy.com/feed/",
            "category": "Data Engineering & Analytics",
            "is_active": True,
        },
        {
            "name": "Databricks Engineering",
            "url": "https://databricks.com/blog/category/engineering/feed",
            "category": "Data Engineering & Analytics",
            "is_active": True,
        },
        {
            "name": "Towards Data Science",
            "url": "https://towardsdatascience.com/feed",
            "category": "Data Engineering & Analytics",
            "is_active": True,
        },
        # Web3 & Blockchain Engineering
        {
            "name": "Ethereum Foundation Blog",
            "url": "https://blog.ethereum.org/feed.xml",
            "category": "Web3 & Blockchain Engineering",
            "is_active": True,
        },
        {
            "name": "Arbitrum (Offchain Labs)",
            "url": "https://blog.arbitrum.io/rss/",
            "category": "Web3 & Blockchain Engineering",
            "is_active": True,
        },
        {
            "name": "Alchemy Blog",
            "url": "https://alchemy.com/blog/rss",
            "category": "Web3 & Blockchain Engineering",
            "is_active": True,
        },
        # Frontend & Mobile Development
        {
            "name": "Kodeco (Ray Wenderlich)",
            "url": "http://www.raywenderlich.com/feed",
            "category": "Frontend & Mobile Development",
            "is_active": True,
        },
        {
            "name": "Smashing Magazine",
            "url": "https://www.smashingmagazine.com/feed/",
            "category": "Frontend & Mobile Development",
            "is_active": True,
        },
        # Tech Strategy & Engineering Management
        {
            "name": "The Pragmatic Engineer",
            "url": "https://blog.pragmaticengineer.com/rss/",
            "category": "Tech Strategy & Engineering Management",
            "is_active": True,
        },
        {
            "name": "Stratechery",
            "url": "https://stratechery.com/feed/",
            "category": "Tech Strategy & Engineering Management",
            "is_active": True,
        },
        # Self-Hosted, FOSS & Privacy
        {
            "name": "selfh.st Weekly",
            "url": "https://rss.slfh.st/weekly/",
            "category": "Self-Hosted, FOSS & Privacy",
            "is_active": True,
        },
        {
            "name": "Home Assistant",
            "url": "https://www.home-assistant.io/atom.xml",
            "category": "Self-Hosted, FOSS & Privacy",
            "is_active": True,
        },
        # Platform Aggregators
        {
            "name": "Hacker News Best",
            "url": "https://hnrss.org/best",
            "category": "Platform Aggregators",
            "is_active": True,
        },
        {
            "name": "Hacker News Active",
            "url": "https://hnrss.org/active",
            "category": "Platform Aggregators",
            "is_active": True,
        },
        {
            "name": "Hacker News Launches",
            "url": "https://hnrss.org/launches",
            "category": "Platform Aggregators",
            "is_active": True,
        },
        {
            "name": "Reddit r/ExperiencedDevs Top Monthly",
            "url": "https://www.reddit.com/r/ExperiencedDevs/top/.rss?t=month",
            "category": "Platform Aggregators",
            "is_active": True,
        },
        {
            "name": "Reddit r/MachineLearning Top Weekly",
            "url": "https://www.reddit.com/r/MachineLearning/top/.rss?t=week",
            "category": "Platform Aggregators",
            "is_active": True,
        },
        {
            "name": "Dev.to - System Design",
            "url": "https://dev.to/feed/tag/systemdesign",
            "category": "Platform Aggregators",
            "is_active": True,
        },
    ]

    print("Supabase client initialized successfully")
    print(f"Ready to seed {len(default_feeds)} feeds...")

    # Insert feeds with error handling
    inserted_count = 0
    skipped_count = 0

    for feed in default_feeds:
        try:
            # Attempt to insert the feed
            supabase.table("feeds").insert(feed).execute()
            inserted_count += 1
            print(f"✓ Inserted: {feed['name']}")
        except Exception as e:
            error_message = str(e).lower()

            # Handle duplicate URL error
            if "duplicate" in error_message or "unique" in error_message:
                skipped_count += 1
                print(f"⊘ Skipped (duplicate URL): {feed['name']} - {feed['url']}")
                continue

            # Handle connection errors
            elif (
                "connection" in error_message
                or "network" in error_message
                or "timeout" in error_message
            ):
                raise ConnectionError(
                    f"Error: Network error while inserting feed '{feed['name']}'\n"
                    f"Please check your internet connection and try again\n"
                    f"If the problem persists, check Supabase status at status.supabase.com\n"
                    f"Details: {e!s}"
                )

            # Re-raise other unexpected errors
            else:
                raise Exception(
                    f"Error: Unexpected error while inserting feed '{feed['name']}'\n"
                    f"Details: {e!s}"
                )

    # Print summary
    print("\n" + "=" * 50)
    print("Seeding completed!")
    print(f"Successfully inserted: {inserted_count} feeds")
    if skipped_count > 0:
        print(f"Skipped (duplicates): {skipped_count} feeds")
    print("=" * 50)


if __name__ == "__main__":
    main()
