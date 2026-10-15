import pytest
from ingestion.content_extractor import extract_article_content, generate_stable_id

SAMPLE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>How to Configure Payment Gateways - Brilliant Directories</title>
    <link rel="canonical" href="https://support.brilliantdirectories.com/support/solutions/articles/12000012345" />
</head>
<body>
    <header><nav><a href="/">Home</a></nav></header>
    <div class="breadcrumb">
        <ul>
            <li><a href="/support/home">Home</a></li>
            <li><a href="/support/solutions/12000001516">Finance & Payments</a></li>
            <li>How to Configure Payment Gateways</li>
        </ul>
    </div>
    <article class="article-body">
        <h1>How to Configure Payment Gateways</h1>
        <p>This guide explains how to connect Stripe, PayPal, or Authorize.net to your directory website.</p>
        
        <h2>Prerequisites</h2>
        <ul>
            <li>An active Brilliant Directories admin account.</li>
            <li>Your Stripe API Secret and Publishable keys.</li>
        </ul>

        <h2>Step-by-step Setup</h2>
        <p>Follow these instructions to configure Stripe:</p>
        <p>1. Navigate to <strong>Settings &gt; Payment Settings</strong> in the admin panel.</p>
        <p>2. Select <strong>Stripe</strong> from the payment gateway dropdown menu.</p>
        <figure>
            <img src="https://support.brilliantdirectories.com/images/stripe_settings.png" alt="Stripe Gateway Settings" />
            <figcaption>Select Stripe from the Payment Gateway dropdown list.</figcaption>
        </figure>

        <h2>Supported Gateways Comparison</h2>
        <table>
            <thead>
                <tr>
                    <th>Gateway</th>
                    <th>Recurring Billing</th>
                    <th>Currency Support</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>Stripe</td>
                    <td>Yes</td>
                    <td>135+ Currencies</td>
                </tr>
                <tr>
                    <td>PayPal Standard</td>
                    <td>Limited</td>
                    <td>25 Currencies</td>
                </tr>
            </tbody>
        </table>
    </article>
    <footer><p>&copy; 2026 Brilliant Directories</p></footer>
</body>
</html>
"""

def test_extract_article_content():
    url = "https://support.brilliantdirectories.com/support/solutions/articles/12000012345"
    extracted = extract_article_content(url, SAMPLE_HTML)

    assert extracted["id"] == "art_12000012345"
    assert extracted["url"] == url
    assert extracted["title"] == "How to Configure Payment Gateways"
    assert "Finance & Payments" in extracted["category"]
    assert "Stripe API Secret" in extracted["content"]
    assert len(extracted["headings"]) >= 3
    assert len(extracted["tables"]) == 1
    assert extracted["tables"][0]["headers"] == ["Gateway", "Recurring Billing", "Currency Support"]
    assert len(extracted["images"]) == 1
    assert extracted["images"][0]["alt"] == "Stripe Gateway Settings"
    assert extracted["content_hash"] is not None


def test_generate_stable_id():
    url1 = "https://support.brilliantdirectories.com/support/solutions/articles/987654"
    url2 = "https://support.brilliantdirectories.com/custom/article-slug"
    assert generate_stable_id(url1) == "art_987654"
    assert generate_stable_id(url2).startswith("art_")
