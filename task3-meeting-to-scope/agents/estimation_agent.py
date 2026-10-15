from typing import List, Dict, Any
from app.schemas import RequirementSchema, TaskEstimateSchema


class EstimationAgent:
    def estimate_tasks(self, requirements: List[RequirementSchema]) -> List[TaskEstimateSchema]:
        """Break requirements into technical engineering tasks with 3-point hour estimates."""
        tasks: List[TaskEstimateSchema] = []

        for req in requirements:
            req_id = req.id
            title = req.title

            if "faceted" in title.lower():
                tasks.append(TaskEstimateSchema(
                    task_id=f"tsk_{req_id}_1",
                    requirement_ids=[req_id],
                    task_name="Faceted Search Backend Query & Form Field Mapping",
                    low_hours=8.0,
                    most_likely_hours=12.0,
                    high_hours=18.0,
                    rationale="Configure custom member form fields, sub-categories, and SQL query filters in BD admin.",
                    assumptions=["Standard BD category hierarchy is intact."],
                    dependencies=["Client category structure."],
                ))
                tasks.append(TaskEstimateSchema(
                    task_id=f"tsk_{req_id}_2",
                    requirement_ids=[req_id],
                    task_name="Faceted Multi-Select UI Widget & Dynamic Refresh",
                    low_hours=12.0,
                    most_likely_hours=16.0,
                    high_hours=24.0,
                    rationale="Build responsive multi-checkbox sidebar widget with AJAX live-filtering.",
                    assumptions=["jQuery/Bootstrap frontend compatibility."],
                    dependencies=["Faceted Search Backend."],
                ))

            elif "radius" in title.lower():
                tasks.append(TaskEstimateSchema(
                    task_id=f"tsk_{req_id}_1",
                    requirement_ids=[req_id],
                    task_name="Google Maps Geocoding API & Zip Code Radius Slider Setup",
                    low_hours=6.0,
                    most_likely_hours=10.0,
                    high_hours=14.0,
                    rationale="Enable BD Radius Search add-on, configure Google Maps API key, style 5-50 mile range slider.",
                    assumptions=["Google Cloud project with active billing is provided."],
                    dependencies=["Google Maps API Credentials."],
                ))

            elif "mobile" in title.lower() or "webp" in title.lower():
                tasks.append(TaskEstimateSchema(
                    task_id=f"tsk_{req_id}_1",
                    requirement_ids=[req_id],
                    task_name="Mobile Slide-Out Drawer & Viewport Optimization",
                    low_hours=10.0,
                    most_likely_hours=14.0,
                    high_hours=20.0,
                    rationale="Implement CSS off-canvas navigation drawer for search filters on mobile viewports (<768px).",
                    assumptions=["Standard responsive viewport meta tags active."],
                    dependencies=[],
                ))
                tasks.append(TaskEstimateSchema(
                    task_id=f"tsk_{req_id}_2",
                    requirement_ids=[req_id],
                    task_name="Image Asset WebP Conversion & Performance Tuning",
                    low_hours=6.0,
                    most_likely_hours=8.0,
                    high_hours=12.0,
                    rationale="Configure CDN image compression, lazy-loading attributes, and test load times under 2.0s.",
                    assumptions=["Images hosted on Brilliant Directories CDN."],
                    dependencies=[],
                ))

            elif "stripe" in title.lower() or "checkout" in title.lower():
                tasks.append(TaskEstimateSchema(
                    task_id=f"tsk_{req_id}_1",
                    requirement_ids=[req_id],
                    task_name="Stripe Elements On-Site Modal Checkout Integration",
                    low_hours=14.0,
                    most_likely_hours=20.0,
                    high_hours=28.0,
                    rationale="Embed Stripe Elements supporting credit cards, Apple Pay, and Google Pay with webhook signature validation.",
                    assumptions=["Stripe account verified for connected payments."],
                    dependencies=["Stripe API keys."],
                ))

            elif "pdf" in title.lower() or "notification" in title.lower():
                tasks.append(TaskEstimateSchema(
                    task_id=f"tsk_{req_id}_1",
                    requirement_ids=[req_id],
                    task_name="Automated Branded PDF Receipt Generator & Email Delivery",
                    low_hours=8.0,
                    most_likely_hours=12.0,
                    high_hours=16.0,
                    rationale="Setup transactional email template with dynamic PDF invoice attachment.",
                    assumptions=["SMTP/SendGrid deliverability active."],
                    dependencies=["Stripe checkout event."],
                ))

            elif "webhook" in title.lower() or "tax" in title.lower():
                tasks.append(TaskEstimateSchema(
                    task_id=f"tsk_{req_id}_1",
                    requirement_ids=[req_id],
                    task_name="Google Sheets Order Webhook & Stripe Tax Configuration",
                    low_hours=8.0,
                    most_likely_hours=12.0,
                    high_hours=16.0,
                    rationale="Deploy Zapier/Lambda webhook endpoint to append rows to Google Sheets; enable Stripe Tax calculation.",
                    assumptions=["Google Workspace spreadsheet shared with service account."],
                    dependencies=[],
                ))

            elif "ai conversational" in title.lower():
                tasks.append(TaskEstimateSchema(
                    task_id=f"tsk_{req_id}_1",
                    requirement_ids=[req_id],
                    task_name="Member Directory Vector Embedding Indexing Pipeline",
                    low_hours=14.0,
                    most_likely_hours=20.0,
                    high_hours=28.0,
                    rationale="Export member profiles, compute vector embeddings, index into pgvector database service.",
                    assumptions=["Member profiles contain clean bios and categories."],
                    dependencies=["Directory member database access."],
                ))
                tasks.append(TaskEstimateSchema(
                    task_id=f"tsk_{req_id}_2",
                    requirement_ids=[req_id],
                    task_name="Natural Language Search Bar UI & LLM Synthesis Endpoint",
                    low_hours=16.0,
                    most_likely_hours=22.0,
                    high_hours=32.0,
                    rationale="Develop conversational search bar widget, streaming LLM response container, and citation links.",
                    assumptions=["Anthropic Claude API access configured."],
                    dependencies=["Vector Embedding Pipeline."],
                ))

            elif "near me" in title.lower() or "geolocation" in title.lower():
                tasks.append(TaskEstimateSchema(
                    task_id=f"tsk_{req_id}_1",
                    requirement_ids=[req_id],
                    task_name="HTML5 One-Click Browser Geolocation & 15-Mile Distance Sorting",
                    low_hours=6.0,
                    most_likely_hours=8.0,
                    high_hours=12.0,
                    rationale="Implement navigator.geolocation API client button, reverse geocode coordinates, and trigger 15-mile sorted search.",
                    assumptions=["HTTPS enabled across all client pages."],
                    dependencies=["Google Maps Geocoding API."],
                ))

            else:
                tasks.append(TaskEstimateSchema(
                    task_id=f"tsk_{req_id}_general",
                    requirement_ids=[req_id],
                    task_name=f"Engineering Implementation for {title}",
                    low_hours=8.0,
                    most_likely_hours=12.0,
                    high_hours=16.0,
                    rationale="Standard technical configuration and automated unit testing.",
                    assumptions=[],
                    dependencies=[],
                ))

        # Add mandatory QA and Deployment tasks
        tasks.append(TaskEstimateSchema(
            task_id="tsk_qa_crossbrowser",
            requirement_ids=[r.id for r in requirements],
            task_name="End-to-End QA Testing & Cross-Browser Verification",
            low_hours=8.0,
            most_likely_hours=12.0,
            high_hours=16.0,
            rationale="Verify all acceptance criteria across Chrome, Safari, iOS mobile, and Android mobile.",
            assumptions=["Staging environment available."],
            dependencies=[],
        ))

        return tasks
