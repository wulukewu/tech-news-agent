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

    # Define default RSS feeds data structure (all verified working URLs)
    default_feeds = [
        # AI & Machine Learning
        {
            "name": "Google AI Blog",
            "url": "http://googleresearch.blogspot.com/atom.xml",
            "category": "AI & Machine Learning",
            "is_active": True,
        },
        {
            "name": "Simon Willison's Weblog",
            "url": "https://simonwillison.net/atom/everything/",
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
            "name": "InfoQ",
            "url": "https://feed.infoq.com/",
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
            "url": "https://netflixtechblog.medium.com/feed",
            "category": "Architecture & System Design",
            "is_active": True,
        },
        {
            "name": "ACM Queue",
            "url": "https://queue.acm.org/rss/feeds/queuecontent.xml",
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
            "url": "https://www.hashicorp.com/blog/feed.xml",
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
            "name": "Lobsters",
            "url": "https://lobste.rs/rss",
            "category": "Cybersecurity & InfoSec",
            "is_active": True,
        },
        {
            "name": "The Morning Paper",
            "url": "https://blog.acolyer.org/feed/",
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
            "name": "Go Weekly",
            "url": "https://golangweekly.com/rss/1jn0ck6",
            "category": "Core Programming Languages",
            "is_active": True,
        },
        # Data Engineering & Analytics
        {
            "name": "Seattle Data Guy",
            "url": "https://seattledataguy.substack.com/feed",
            "category": "Data Engineering & Analytics",
            "is_active": True,
        },
        {
            "name": "Data Engineering Weekly",
            "url": "https://www.dataengineeringweekly.com/feed",
            "category": "Data Engineering & Analytics",
            "is_active": True,
        },
        {
            "name": "Databricks Engineering",
            "url": "https://databricks.com/feed",
            "category": "Data Engineering & Analytics",
            "is_active": True,
        },
        {
            "name": "dbt Blog",
            "url": "https://www.getdbt.com/blog/rss.xml",
            "category": "Data Engineering & Analytics",
            "is_active": True,
        },
        {
            "name": "Analytics Vidhya",
            "url": "https://www.analyticsvidhya.com/feed/",
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
            "name": "Polygon Blog",
            "url": "https://blog.polygon.technology/feed/",
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
        # Web Development & Programming
        {
            "name": "freeCodeCamp",
            "url": "https://www.freecodecamp.org/news/rss/",
            "category": "Web Development & Programming",
            "is_active": True,
        },
        {
            "name": "CSS-Tricks",
            "url": "https://css-tricks.com/feed/",
            "category": "Web Development & Programming",
            "is_active": True,
        },
        {
            "name": "JavaScript Weekly",
            "url": "https://javascriptweekly.com/rss",
            "category": "Web Development & Programming",
            "is_active": True,
        },
        {
            "name": "A List Apart",
            "url": "https://alistapart.com/main/feed/",
            "category": "Web Development & Programming",
            "is_active": True,
        },
        {
            "name": "Real Python",
            "url": "https://realpython.com/atom.xml",
            "category": "Web Development & Programming",
            "is_active": True,
        },
        {
            "name": "Next.js Blog",
            "url": "https://nextjs.org/feed.xml",
            "category": "Web Development & Programming",
            "is_active": True,
        },
        # Official Documentation
        {
            "name": "MDN Web Docs Blog",
            "url": "https://developer.mozilla.org/en-US/blog/rss.xml",
            "category": "Official Documentation",
            "is_active": True,
        },
        {
            "name": "Node.js Blog",
            "url": "https://nodejs.org/en/feed/blog.xml",
            "category": "Official Documentation",
            "is_active": True,
        },
        {
            "name": "React Blog",
            "url": "https://react.dev/rss.xml",
            "category": "Official Documentation",
            "is_active": True,
        },
        {
            "name": "Google Developers Blog",
            "url": "https://developers.googleblog.com/feeds/posts/default",
            "category": "Official Documentation",
            "is_active": True,
        },
        # Official Updates
        {
            "name": "GitHub Blog",
            "url": "https://github.blog/feed/",
            "category": "Official Updates",
            "is_active": True,
        },
        {
            "name": "Vue.js News",
            "url": "https://blog.vuejs.org/feed.rss",
            "category": "Official Updates",
            "is_active": True,
        },
        # Community & Learning
        {
            "name": "Stack Overflow Blog",
            "url": "https://stackoverflow.blog/feed/",
            "category": "Community & Learning",
            "is_active": True,
        },
        {
            "name": "Dev.to",
            "url": "https://dev.to/feed",
            "category": "Community & Learning",
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
            "url": "https://selfh.st/feed/",
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
            "name": "Lobsters ML",
            "url": "https://lobste.rs/t/ml.rss",
            "category": "Platform Aggregators",
            "is_active": True,
        },
        {
            "name": "TLDR Tech",
            "url": "https://tldr.tech/api/rss/tech",
            "category": "Platform Aggregators",
            "is_active": True,
        },
        {
            "name": "Dev.to - System Design",
            "url": "https://dev.to/feed/tag/systemdesign",
            "category": "Platform Aggregators",
            "is_active": True,
        },
        # Tech News & Industry
        {
            "name": "Hacker News",
            "url": "https://news.ycombinator.com/rss",
            "category": "Tech News & Industry",
            "is_active": True,
        },
        {
            "name": "The Verge - Tech",
            "url": "https://www.theverge.com/rss/tech/index.xml",
            "category": "Tech News & Industry",
            "is_active": True,
        },
        {
            "name": "Ars Technica",
            "url": "https://feeds.arstechnica.com/arstechnica/technology-lab",
            "category": "Tech News & Industry",
            "is_active": True,
        },
        {
            "name": "VentureBeat",
            "url": "https://venturebeat.com/feed/",
            "category": "Tech News & Industry",
            "is_active": True,
        },
        {
            "name": "TechCrunch",
            "url": "https://techcrunch.com/feed/",
            "category": "Tech News & Industry",
            "is_active": True,
        },
        {
            "name": "Wired",
            "url": "https://www.wired.com/feed/rss",
            "category": "Tech News & Industry",
            "is_active": True,
        },
        # Engineering Blogs - Big Tech
        {
            "name": "Engineering at Meta",
            "url": "https://engineering.fb.com/feed/",
            "category": "Engineering Blogs - Big Tech",
            "is_active": True,
        },
        {
            "name": "Uber Engineering",
            "url": "https://www.uber.com/blog/engineering/rss/",
            "category": "Engineering Blogs - Big Tech",
            "is_active": True,
        },
        {
            "name": "Spotify Engineering",
            "url": "https://engineering.atspotify.com/feed/",
            "category": "Engineering Blogs - Big Tech",
            "is_active": True,
        },
        {
            "name": "Airbnb Engineering",
            "url": "https://medium.com/feed/airbnb-engineering",
            "category": "Engineering Blogs - Big Tech",
            "is_active": True,
        },
        {
            "name": "Slack Engineering",
            "url": "https://slack.engineering/feed",
            "category": "Engineering Blogs - Big Tech",
            "is_active": True,
        },
        {
            "name": "Shopify Engineering",
            "url": "https://shopifyengineering.myshopify.com/blogs/engineering.atom",
            "category": "Engineering Blogs - Big Tech",
            "is_active": True,
        },
        {
            "name": "Dropbox Tech",
            "url": "https://dropbox.tech/feed",
            "category": "Engineering Blogs - Big Tech",
            "is_active": True,
        },
        # Individual Engineers & Thought Leaders
        {
            "name": "Julia Evans",
            "url": "https://jvns.ca/atom.xml",
            "category": "Individual Engineers & Thought Leaders",
            "is_active": True,
        },
        {
            "name": "Joel on Software",
            "url": "https://www.joelonsoftware.com/feed/",
            "category": "Individual Engineers & Thought Leaders",
            "is_active": True,
        },
        {
            "name": "Dan Luu",
            "url": "https://danluu.com/atom.xml",
            "category": "Individual Engineers & Thought Leaders",
            "is_active": True,
        },
        {
            "name": "Overreacted (Dan Abramov)",
            "url": "https://overreacted.io/rss.xml",
            "category": "Individual Engineers & Thought Leaders",
            "is_active": True,
        },
        {
            "name": "Lil'Log (Lilian Weng)",
            "url": "https://lilianweng.github.io/lil-log/feed.xml",
            "category": "Individual Engineers & Thought Leaders",
            "is_active": True,
        },
        {
            "name": "Martin Kleppmann",
            "url": "https://feeds.feedburner.com/martinkl?format=xml",
            "category": "Individual Engineers & Thought Leaders",
            "is_active": True,
        },
        {
            "name": "Josh Comeau",
            "url": "https://joshwcomeau.com/rss.xml",
            "category": "Individual Engineers & Thought Leaders",
            "is_active": True,
        },
        # Open Source & Developer Tools
        {
            "name": "Docker Blog",
            "url": "https://www.docker.com/blog/feed/",
            "category": "Open Source & Developer Tools",
            "is_active": True,
        },
        {
            "name": "CNCF Blog",
            "url": "https://www.cncf.io/feed/",
            "category": "Open Source & Developer Tools",
            "is_active": True,
        },
        {
            "name": "Nvidia Developer Blog",
            "url": "https://developer.nvidia.com/blog/feed",
            "category": "Open Source & Developer Tools",
            "is_active": True,
        },
        {
            "name": "PyTorch Blog",
            "url": "https://pytorch.org/feed",
            "category": "Open Source & Developer Tools",
            "is_active": True,
        },
        {
            "name": "AWS Blog",
            "url": "https://aws.amazon.com/blogs/aws/feed/",
            "category": "Open Source & Developer Tools",
            "is_active": True,
        },
        # Research & Academia
        {
            "name": "OpenAI Engineering",
            "url": "https://openai.com/news/engineering/rss.xml",
            "category": "Research & Academia",
            "is_active": True,
        },
        {
            "name": "DeepMind Blog",
            "url": "https://deepmind.com/blog/feed/basic/",
            "category": "Research & Academia",
            "is_active": True,
        },
        {
            "name": "BAIR (Berkeley AI)",
            "url": "http://bair.berkeley.edu/blog/feed.xml",
            "category": "Research & Academia",
            "is_active": True,
        },
        {
            "name": "The Gradient",
            "url": "https://thegradient.pub/rss/",
            "category": "Research & Academia",
            "is_active": True,
        },
        {
            "name": "MIT News - AI",
            "url": "http://news.mit.edu/rss/topic/artificial-intelligence2",
            "category": "Research & Academia",
            "is_active": True,
        },
        {
            "name": "Amazon Science",
            "url": "https://www.amazon.science/index.rss",
            "category": "Research & Academia",
            "is_active": True,
        },
        # Product & Startup
        {
            "name": "Product Hunt",
            "url": "http://www.producthunt.com/feed",
            "category": "Product & Startup",
            "is_active": True,
        },
        {
            "name": "First Round Review",
            "url": "http://firstround.com/review/feed.xml",
            "category": "Product & Startup",
            "is_active": True,
        },
        {
            "name": "Irrational Exuberance (Will Larson)",
            "url": "https://lethain.com/feeds/",
            "category": "Product & Startup",
            "is_active": True,
        },
        {
            "name": "Mind the Product",
            "url": "https://www.mindtheproduct.com/feed/",
            "category": "Product & Startup",
            "is_active": True,
        },
        # Database & Storage
        {
            "name": "PostgreSQL News",
            "url": "https://www.postgresql.org/news.rss",
            "category": "Database & Storage",
            "is_active": True,
        },
        {
            "name": "Redis Blog",
            "url": "https://redis.io/blog/feed/",
            "category": "Database & Storage",
            "is_active": True,
        },
        {
            "name": "MongoDB Blog",
            "url": "https://www.mongodb.com/blog/rss",
            "category": "Database & Storage",
            "is_active": True,
        },
        {
            "name": "PlanetScale Blog",
            "url": "https://planetscale.com/blog/feed.rss",
            "category": "Database & Storage",
            "is_active": True,
        },
        {
            "name": "Supabase Blog",
            "url": "https://supabase.com/rss.xml",
            "category": "Database & Storage",
            "is_active": True,
        },
        # Security
        {
            "name": "OWASP Blog",
            "url": "https://owasp.org/feed.xml",
            "category": "Security",
            "is_active": True,
        },
        {
            "name": "Snyk Blog",
            "url": "https://snyk.io/blog/feed/",
            "category": "Security",
            "is_active": True,
        },
        {
            "name": "Trail of Bits Blog",
            "url": "https://blog.trailofbits.com/feed/",
            "category": "Security",
            "is_active": True,
        },
        {
            "name": "Schneier on Security",
            "url": "https://www.schneier.com/feed/atom/",
            "category": "Security",
            "is_active": True,
        },
        # Python & Data Science
        {
            "name": "Python Official News",
            "url": "https://blog.python.org/feeds/posts/default",
            "category": "Python & Data Science",
            "is_active": True,
        },
        {
            "name": "Towards Data Science",
            "url": "https://towardsdatascience.com/feed",
            "category": "Python & Data Science",
            "is_active": True,
        },
        {
            "name": "Analytics Vidhya",
            "url": "https://www.analyticsvidhya.com/feed/",
            "category": "Python & Data Science",
            "is_active": True,
        },
        {
            "name": "Seattle Data Guy",
            "url": "https://seattledataguy.substack.com/feed",
            "category": "Python & Data Science",
            "is_active": True,
        },
        # TypeScript & JavaScript Ecosystem
        {
            "name": "TypeScript Blog",
            "url": "https://devblogs.microsoft.com/typescript/feed/",
            "category": "TypeScript & JavaScript Ecosystem",
            "is_active": True,
        },
        {
            "name": "Deno Blog",
            "url": "https://deno.com/feed",
            "category": "TypeScript & JavaScript Ecosystem",
            "is_active": True,
        },
        {
            "name": "Bun Blog",
            "url": "https://bun.sh/blog.rss",
            "category": "TypeScript & JavaScript Ecosystem",
            "is_active": True,
        },
        # Frontend & Mobile (expanded)
        {
            "name": "web.dev",
            "url": "https://web.dev/feed.xml",
            "category": "Frontend & Mobile Development",
            "is_active": True,
        },
        {
            "name": "Flutter Blog",
            "url": "https://medium.com/feed/flutter",
            "category": "Frontend & Mobile Development",
            "is_active": True,
        },
        {
            "name": "React Native Blog",
            "url": "https://reactnative.dev/blog/rss.xml",
            "category": "Frontend & Mobile Development",
            "is_active": True,
        },
        # Engineering Management & Career
        {
            "name": "StaffEng",
            "url": "https://staffeng.com/feed.xml",
            "category": "Engineering Management & Career",
            "is_active": True,
        },
        {
            "name": "Lenny's Newsletter",
            "url": "https://www.lennysnewsletter.com/feed",
            "category": "Engineering Management & Career",
            "is_active": True,
        },
        {
            "name": "LeadDev",
            "url": "https://leaddev.com/feed",
            "category": "Engineering Management & Career",
            "is_active": True,
        },
        # Community Aggregators (expanded)
        {
            "name": "Reddit r/programming",
            "url": "https://www.reddit.com/r/programming/top.rss?t=day",
            "category": "Platform Aggregators",
            "is_active": True,
        },
        {
            "name": "Reddit r/MachineLearning",
            "url": "https://www.reddit.com/r/MachineLearning/top.rss?t=day",
            "category": "Platform Aggregators",
            "is_active": True,
        },
        {
            "name": "TLDR AI",
            "url": "https://tldr.tech/api/rss/ai",
            "category": "Platform Aggregators",
            "is_active": True,
        },
        {
            "name": "TLDR DevOps",
            "url": "https://tldr.tech/api/rss/devops",
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
