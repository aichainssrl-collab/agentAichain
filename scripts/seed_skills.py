"""Seed comprehensive skill catalog inspired by OpenClaw (ClawHub).

Run: python scripts/seed_skills.py

This creates ~85 skills across 20 categories with proper agno_tool_class mapping.
Each skill has name, description, category, and the Agno tool class it maps to.
"""

import asyncio
import sys
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from agent_aichain.core.config import settings
from agent_aichain.models.skill import Skill

# ── Skill catalog ──────────────────────────────────────────────────────────────
# Format: (name, description, category, agno_tool_class)
# None for agno_tool_class means "custom tool — user must implement"

SKILLS: list[tuple[str, str, str, str | None]] = [

    # ═══ Productivity ═══
    ("calendar",      "Manage calendar events via Google/Outlook API",            "productivity",  None),
    ("email_gmail",   "Read, compose, search Gmail via Gmail API",                "productivity",  None),
    ("email_outlook", "Read, compose, search Outlook emails",                     "productivity",  None),
    ("notion",        "Search and update Notion pages and databases",             "productivity",  None),
    ("slack",         "Send messages and read channels in Slack",                 "productivity",  None),
    ("task_manager",  "Manage todo lists and project tasks",                      "productivity",  None),
    ("sheets",        "Read and write Google Sheets",                             "productivity",  None),
    ("drive",         "Search and manage Google Drive files",                     "productivity",  None),

    # ═══ Development ═══
    ("github",        "GitHub PRs, issues, repo management",                      "development",   None),
    ("code_review",   "Automated code review with linting and quality checks",    "development",   None),
    ("docker",        "Docker container management and image builds",             "development",   None),
    ("kubernetes",    "K8s cluster management and deployment",                    "development",   None),
    ("jira",          "Jira ticket creation, update and sprint management",       "development",   None),
    ("confluence",    "Read/write Confluence pages",                              "development",   None),
    ("sentry",        "Monitor Sentry error events and releases",                 "development",   None),
    ("github_actions","GitHub Actions workflows management",                      "development",   None),

    # ═══ Communication ═══
    ("send_email",    "Send emails via SMTP",                                     "communication", None),
    ("telegram",      "Send and receive Telegram messages",                       "communication", None),
    ("whatsapp",      "WhatsApp Business API messaging",                          "communication", None),
    ("discord",       "Discord channel and DM messaging",                         "communication", None),
    ("zoom",          "Create and manage Zoom meetings",                          "communication", None),

    # ═══ Research ═══
    ("web_search",    "Search the web (DuckDuckGo)",                              "research",      "DuckDuckGoTools"),
    ("wikipedia",     "Search Wikipedia for factual information",                 "research",      "WikipediaTools"),
    ("news",          "Fetch latest news from multiple sources",                  "research",      "NewsApiTools"),
    ("arxiv",         "Search academic papers on arXiv",                          "research",      "ArxivTools"),
    ("hackernews",    "HackerNews stories and trends",                            "research",      "HackerNewsTools"),
    ("pdf_reader",    "Extract and analyse text from PDF files",                 "research",      None),
    ("web_scraper",   "Scrape and extract content from web pages",                "research",      None),
    ("youtube",       "Search and analyse YouTube videos",                        "research",      "YoutubeTools"),

    # ═══ AI Models ═══
    ("image_gen",     "Generate images from prompts (OpenAI DALL-E)",            "ai_models",     "OpenAITools"),
    ("text_to_speech","Convert text to speech (ElevenLabs)",                     "ai_models",     None),
    ("embedding",     "Generate text embeddings for vector search",              "ai_models",     None),
    ("vision",        "Image analysis and understanding (Claude/GPT Vision)",    "ai_models",     None),

    # ═══ Marketing ═══
    ("seo_analysis",  "SEO analysis and keyword research",                        "marketing",     None),
    ("content_gen",   "Generate blog posts, articles, ad copy",                   "marketing",     None),
    ("social_posts",  "Schedule and publish social media posts",                  "marketing",     None),
    ("analytics",     "Google Analytics data and insights",                       "marketing",     None),
    ("email_marketing","Email campaign management (Mailchimp, SendGrid)",         "marketing",     None),
    ("semrush",       "SEMrush competitive analysis",                             "marketing",     None),

    # ═══ Sales ═══
    ("crm",           "CRM integration (HubSpot, Salesforce)",                    "sales",         None),
    ("lead_research", "Lead identification and qualification",                    "sales",         None),
    ("proposal_gen",  "Generate proposals and quotes",                            "sales",         None),
    ("stripe",        "Stripe payment and subscription management",               "sales",         None),

    # ═══ Finance ═══
    ("calculator",    "Advanced calculator with math functions",                  "finance",       "CalculatorTools"),
    ("stock_quotes",  "Real-time stock prices and financial data",                "finance",       "YFinanceTools"),
    ("crypto",        "Cryptocurrency prices and market data",                    "finance",       "CoinGeckoTools"),
    ("currency",      "Live currency exchange rates",                             "finance",       None),
    ("invoice_gen",   "Generate and send invoices",                               "finance",       None),

    # ═══ Cloud & Infra ═══
    ("aws",           "AWS resource management (EC2, S3, Lambda)",               "cloud",         None),
    ("gcp",           "GCP resource management (Cloud Run, Cloud SQL)",           "cloud",         None),
    ("cloudflare",    "Cloudflare DNS, CDN, Workers management",                  "cloud",         None),
    ("supabase",      "Supabase project management",                              "cloud",         None),
    ("terraform",     "Terraform plan and apply infrastructure changes",          "cloud",         None),

    # ═══ DevOps ═══
    ("docker_mgmt",   "Docker image build, push, and manage",                     "devops",        "DockerTools"),
    ("git",           "Git operations: clone, branch, commit, push",             "devops",        "GitTools"),
    ("ssh",           "SSH into remote servers and execute commands",            "devops",        None),
    ("ci_cd",         "Trigger and monitor CI/CD pipelines",                     "devops",        None),
    ("monitoring",    "Infrastructure monitoring and alerting",                  "devops",        None),

    # ═══ Security ═══
    ("vulnerability", "Run vulnerability scans and report",                      "security",      None),
    ("secret_scan",   "Detect secrets and credentials in code",                  "security",      None),
    ("firewall",      "Manage firewall rules and ports",                         "security",      None),

    # ═══ Data ═══
    ("database",      "SQL query execution on PostgreSQL/MySQL",                 "data",          "SqliteDb"),
    ("csv_analysis",  "Read, analyse and transform CSV data",                    "data",          None),
    ("json_transform","Transform and validate JSON data",                        "data",          None),
    ("vector_search", "Vector similarity search (Pinecone/Qdrant/Weaviate)",     "data",          None),

    # ═══ Content ═══
    ("wordpress",     "Create and manage WordPress posts",                       "content",       "WordpressTools"),
    ("markdown",      "Markdown file creation and conversion",                   "content",       None),
    ("obsidian",      "Obsidian vault search and note creation",                 "content",       None),
    ("presentation",  "Generate presentations (PowerPoint/Google Slides)",       "content",       None),

    # ═══ Media Generation ═══
    ("image_edit",    "AI-powered image editing and enhancement",                "media_generation", None),
    ("video_summary", "Video analysis and summarization",                        "media_generation", None),
    ("audio_transcribe","Transcribe audio to text",                              "media_generation", None),

    # ═══ Automation ═══
    ("python_exec",   "Execute Python code safely in sandbox",                   "automation",    "PythonTools"),
    ("file_ops",      "File operations: read, write, search, organize",          "automation",    "FileTools"),
    ("webhook",       "Send and receive webhooks",                               "automation",    None),
    ("scheduler",     "Schedule recurring tasks and reminders",                  "automation",    None),
    ("zapier",        "Trigger Zapier workflows and integrations",               "automation",    None),
]


def main():
    db_url = str(settings.database_url).replace("+asyncpg", "")
    engine = create_engine(db_url, echo=False)

    with Session(engine) as session:
        existing = {s.name for s in session.scalars(select(Skill)).all()}

        added = 0
        skipped = 0
        for name, desc, cat, tool_class in SKILLS:
            if name in existing:
                skipped += 1
                continue
            skill = Skill(
                name=name,
                description=desc,
                category=cat,
                agno_tool_class=tool_class,
                is_active=True,
            )
            session.add(skill)
            added += 1

        session.commit()
        print(f"Skills seed complete: {added} added, {skipped} already exist (total catalog: {len(SKILLS)} entries)")


if __name__ == "__main__":
    main()
