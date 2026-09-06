"""Unit tests for pre_push_verify.scanner."""
from pre_push_verify.scanner import scan_text


def test_detects_aws_access_key():
    fake_aws = "A" + "KIA" + "9988776655443322"
    diff = f"+{fake_aws}"
    findings = scan_text(diff)
    assert len(findings) == 1
    assert findings[0].rule_name == "AWS Access Key ID"


def test_detects_openai_key():
    fake_openai = "s" + "k-" + ("a1b2c3d4e5" * 3)
    diff = f"+{fake_openai}"
    findings = scan_text(diff)
    assert len(findings) == 1
    assert findings[0].rule_name == "OpenAI Secret Key"


def test_detects_anthropic_key():
    fake_anthropic = "s" + "k-ant-api03-" + ("a1b2c3d4e5" * 4)
    diff = f"+{fake_anthropic}"
    findings = scan_text(diff)
    assert len(findings) == 1
    assert findings[0].rule_name == "Anthropic API Key"


def test_detects_groq_key():
    fake_groq = "g" + "sk_" + ("a1b2c3d4e5" * 4)
    diff = f"+{fake_groq}"
    findings = scan_text(diff)
    assert len(findings) == 1
    assert findings[0].rule_name == "Groq API Key"


def test_detects_stripe_key():
    fake_stripe = "s" + "k_live_" + ("a1b2c3d4e5" * 3)
    diff = f"+{fake_stripe}"
    findings = scan_text(diff)
    assert len(findings) == 1
    assert findings[0].rule_name == "Stripe Secret Key"


def test_detects_private_key_header():
    fake_header = "-----" + "BEGIN RSA PRIVATE KEY" + "-----"
    diff = f"+{fake_header}"
    findings = scan_text(diff)
    assert len(findings) == 1
    assert findings[0].rule_name == "RSA Private Key Header"


def test_ignores_safe_placeholders():
    diff = """
    +GROQ_API_KEY=gsk_test_mock_free_key_123
    +OPENAI_API_KEY=sk_test_placeholder_example
    +STRIPE_KEY=your-api-key-here
    """
    findings = scan_text(diff)
    assert len(findings) == 0


def test_clean_code_passes():
    diff = """
    +def calculate_total(items):
    +    return sum(item.price for item in items)
    """
    findings = scan_text(diff)
    assert len(findings) == 0
