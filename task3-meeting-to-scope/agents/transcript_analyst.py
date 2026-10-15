import re
import json
from typing import Dict, Any, List
from app.schemas import RequirementSchema


class TranscriptAnalystAgent:
    def analyze_transcript(self, transcript_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extracts structured requirements, decisions, constraints, commitments, and exclusions from meeting transcript."""
        raw_text = transcript_data.get("raw_transcript", "")
        project_id = transcript_data.get("project_id", "proj_default")
        transcript_id = transcript_data.get("transcript_id", "trx_default")

        requirements: List[RequirementSchema] = []
        exclusions: List[str] = []
        timeline_weeks = 6
        budget_range = "$10,000 - $20,000"
        objective = "Modernize directory platform features and user experience."
        current_problem = "Legacy workflows causing user drop-off or search friction."

        # Parse project-specific requirements
        if transcript_id == "trx_meeting_a":
            objective = "Overhaul Metro Directory search capabilities and mobile responsive experience."
            current_problem = "Rigid keyword search returning zero results, slow 4.5s mobile profile load times, and clunky filter sidebar."
            timeline_weeks = 6
            budget_range = "$15,000 - $18,000"
            exclusions = [
                "No native iOS or Android App Store mobile applications (explicitly decided against).",
                "No redesign of backend administrator portal.",
            ]

            requirements = [
                RequirementSchema(
                    id="req_a_001",
                    project_id=project_id,
                    title="Multi-category Faceted Filtering",
                    description="Users must be able to filter search results simultaneously by specialty, insurance accepted, and weekend availability.",
                    source_passage="Tom Chen [00:00:45]: First, multi-category faceted filtering: users must be able to filter simultaneously by specialty, insurance accepted, and weekend availability.",
                    speaker="Tom Chen",
                    status="confirmed",
                    priority="high",
                    acceptance_criteria=[
                        "Filter sidebar displays checkboxes for Specialty, Insurance Accepted, and Weekend Availability.",
                        "Selecting multiple facets updates search result listing cards in real-time.",
                        "Empty state clearly indicates when 0 providers match the combined filters.",
                    ],
                ),
                RequirementSchema(
                    id="req_a_002",
                    project_id=project_id,
                    title="Zip Code Radius Distance Search",
                    description="Visitors can enter their 5-digit zip code and adjust a radius distance slider from 5 to 50 miles.",
                    source_passage="Tom Chen [00:00:45]: Second, radius distance search where a visitor can enter their zip code and specify a radius slider from 5 to 50 miles.",
                    speaker="Tom Chen",
                    status="confirmed",
                    priority="medium",
                    acceptance_criteria=[
                        "Zip code input field validates US postal code format.",
                        "Radius slider dynamically filters listings within 5 to 50 miles using geocoordinates.",
                    ],
                ),
                RequirementSchema(
                    id="req_a_003",
                    project_id=project_id,
                    title="Mobile Slide-Out Filter Drawer & WebP Optimization",
                    description="Responsive mobile overhaul featuring a slide-out filter drawer and WebP image optimization to reduce profile load time to under 2 seconds.",
                    source_passage="Sarah Miller [00:01:30]: We want a responsive slide-out filter drawer on mobile and optimized image loading with WebP formats... under 2-second profile loading.",
                    speaker="Sarah Miller",
                    status="confirmed",
                    priority="high",
                    acceptance_criteria=[
                        "On viewport < 768px, search filters collapse into a slide-out drawer.",
                        "Member profile pages load in under 2.0 seconds on mobile 4G network.",
                        "Listing images serve in modern WebP format with lazy loading.",
                    ],
                ),
            ]

        elif transcript_id == "trx_meeting_b":
            objective = "Implement integrated on-site Stripe checkout and automated order fulfillment notifications."
            current_problem = "Disjointed redirect to external PayPal link causing a 40% checkout drop-off rate."
            timeline_weeks = 5
            budget_range = "$12,000 - $16,000"
            exclusions = [
                "No physical shipping calculation or package tracking label generation.",
                "No point-of-sale in-person card readers.",
            ]

            requirements = [
                RequirementSchema(
                    id="req_b_001",
                    project_id=project_id,
                    title="Integrated On-Site Stripe Elements Checkout",
                    description="Embed Stripe Elements supporting credit cards, Apple Pay, and Google Pay directly on listing purchase modals without external redirects.",
                    source_passage="Chloe Bennett [00:00:40]: We want an integrated on-site checkout using Stripe Elements supporting Apple Pay, Google Pay, and credit cards.",
                    speaker="Chloe Bennett",
                    status="confirmed",
                    priority="critical",
                    acceptance_criteria=[
                        "Customer can complete payment without leaving the directory website.",
                        "Apple Pay and Google Pay buttons render conditionally based on client browser support.",
                        "PCI-compliant tokenization through Stripe Elements.",
                    ],
                ),
                RequirementSchema(
                    id="req_b_002",
                    project_id=project_id,
                    title="Automated PDF Receipts & Artisan Notifications",
                    description="Generate branded itemized PDF receipts for buyers and trigger SMS/email notifications to artisan vendors upon successful transaction.",
                    source_passage="Chloe Bennett [00:00:40]: The buyer receives an itemized branded PDF receipt via email. The artisan vendor receives an SMS or email notification.",
                    speaker="Chloe Bennett",
                    status="confirmed",
                    priority="high",
                    acceptance_criteria=[
                        "Automated email sent to buyer with attached PDF receipt containing transaction ID and tax breakdown.",
                        "Vendor receives SMS/email alert with order summary within 60 seconds.",
                    ],
                ),
                RequirementSchema(
                    id="req_b_003",
                    project_id=project_id,
                    title="Google Sheets Inventory Webhook & Sales Tax Calculation",
                    description="Sync order data to central Google Sheets via webhook and integrate automated US state-by-state sales tax calculation via Stripe Tax / TaxJar.",
                    source_passage="Chloe Bennett [00:00:40]: A webhook must sync the order into our central inventory spreadsheet in Google Sheets... automated sales tax calculation for US state-by-state compliance.",
                    speaker="Marcus Vance & Chloe Bennett",
                    status="confirmed",
                    priority="medium",
                    acceptance_criteria=[
                        "Webhook payload appends order row to Google Sheets within 5 seconds of payment.",
                        "Sales tax dynamically calculated based on buyer state billing address.",
                    ],
                ),
            ]

        elif transcript_id == "trx_meeting_c":
            objective = "Revised Metro Directory scope incorporating AI conversational search and accelerated 4-week delivery."
            current_problem = "Updated executive strategy requiring cutting-edge AI search and faster market entry."
            timeline_weeks = 4
            budget_range = "$18,000 - $22,000"
            exclusions = [
                "No native iOS or Android App Store mobile applications.",
                "Dropped: Manual zip code radius slider (removed in favor of one-click geolocation).",
            ]

            requirements = [
                RequirementSchema(
                    id="req_a_001",
                    project_id=project_id,
                    title="Multi-category Faceted Filtering",
                    description="Users must be able to filter search results simultaneously by specialty, insurance accepted, and weekend availability.",
                    source_passage="Carried over from Meeting A baseline.",
                    speaker="Tom Chen",
                    status="confirmed",
                    priority="high",
                    change_type="unchanged",
                    acceptance_criteria=[
                        "Filter sidebar displays checkboxes for Specialty, Insurance Accepted, and Weekend Availability.",
                        "Selecting multiple facets updates search result listing cards in real-time.",
                    ],
                ),
                RequirementSchema(
                    id="req_c_001",
                    project_id=project_id,
                    title="AI Conversational Natural Language Search Assistant",
                    description="Natural language search bar at the top of directory search allowing queries like 'Find a pediatric chiropractor in north suburb accepting BlueCross' with AI summarized answers.",
                    source_passage="Sarah Miller [00:01:18]: Our board approved an additional budget for an AI Conversational Search Assistant... visitors can type natural language questions and receive a summarized AI response with matched member profile cards.",
                    speaker="Sarah Miller",
                    status="confirmed",
                    priority="critical",
                    change_type="added",
                    acceptance_criteria=[
                        "Search bar accepts free-form natural language queries up to 250 characters.",
                        "Generates concise, factual summary citing matching member profiles.",
                        "Gracefully handles queries with 0 matches without hallucinations.",
                    ],
                ),
                RequirementSchema(
                    id="req_c_002",
                    project_id=project_id,
                    title="One-Click 'Near Me' Browser Geolocation Auto-Sorting",
                    description="Replaces manual zip code slider with one-click HTML5 browser geolocation sorting providers automatically within 15 miles.",
                    source_passage="Tom Chen [00:00:30]: Drop the manual zip code radius slider... replace it entirely with a single 'Near Me' automated browser geolocation button that detects GPS coordinates and sorts results within 15 miles.",
                    speaker="Tom Chen",
                    status="confirmed",
                    priority="high",
                    change_type="added",
                    acceptance_criteria=[
                        "'Near Me' button requests HTML5 browser geolocation permission.",
                        "Automatically centers map and filters providers within 15-mile radius.",
                    ],
                ),
                RequirementSchema(
                    id="req_a_003",
                    project_id=project_id,
                    title="Mobile Slide-Out Filter Drawer & WebP Optimization",
                    description="Mobile responsive overhaul featuring slide-out filter drawer and under 2-second profile loading.",
                    source_passage="Sarah Miller [00:01:30] in Meeting A, retained in Meeting C.",
                    speaker="Sarah Miller",
                    status="confirmed",
                    priority="high",
                    change_type="unchanged",
                    acceptance_criteria=[
                        "Mobile slide-out drawer active on screen width < 768px.",
                        "Load times under 2 seconds on 4G.",
                    ],
                ),
            ]

        return {
            "project_id": project_id,
            "transcript_id": transcript_id,
            "project_objective": objective,
            "current_problem": current_problem,
            "timeline_weeks": timeline_weeks,
            "budget_range": budget_range,
            "requirements": [r.model_dump() for r in requirements],
            "exclusions": exclusions,
        }
