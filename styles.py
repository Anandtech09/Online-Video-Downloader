"""
Modern, responsive design system for StreamFlow.
Engineered for mobile touch screens (iPhone/Android) and laptop displays.
Features sleek glassmorphic containers, modern typography, zero AI cliches,
and clean contrast.
"""

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;600&display=swap');

:root {
    --brand-primary: #6366F1;
    --brand-accent: #06B6D4;
    --brand-success: #10B981;
    --brand-danger: #EF4444;
    --bg-dark: #0B0F19;
    --card-surface: #111827;
    --card-border: rgba(255, 255, 255, 0.08);
    --text-primary: #F9FAFB;
    --text-secondary: #9CA3AF;
}

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

/* Hide default streamlit elements */
#MainMenu {visibility: hidden;}
header {visibility: hidden;}
footer {visibility: hidden;}
.stDeployButton {display: none;}

/* Main App Container */
.block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 2.5rem !important;
    max-width: 1040px !important;
    margin: 0 auto;
}

/* Beautiful Hero Header */
.app-header {
    background: linear-gradient(135deg, rgba(99, 102, 241, 0.12) 0%, rgba(6, 182, 212, 0.08) 50%, rgba(15, 23, 42, 0.4) 100%);
    border: 1px solid rgba(99, 102, 241, 0.25);
    border-radius: 18px;
    padding: 2rem 1.5rem;
    margin-bottom: 1.5rem;
    text-align: center;
    backdrop-filter: blur(12px);
    box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.5);
}

.app-title {
    font-size: 2.4rem;
    font-weight: 800;
    letter-spacing: -0.5px;
    background: linear-gradient(135deg, #FFFFFF 0%, #E0E7FF 60%, #818CF8 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0 0 0.5rem 0;
}

.app-subtitle {
    color: var(--text-secondary);
    font-size: 0.98rem;
    max-width: 680px;
    margin: 0 auto;
    line-height: 1.5;
}

.platform-pills {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: 8px;
    margin-top: 1.2rem;
}

.platform-pill {
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.09);
    color: #D1D5DB;
    padding: 4px 12px;
    border-radius: 8px;
    font-size: 0.78rem;
    font-weight: 600;
}

/* Streamlit native container styling (eliminates empty divs) */
[data-testid="stVerticalBlockBorderWrapper"] {
    background: rgba(17, 24, 39, 0.75) !important;
    border: 1px solid var(--card-border) !important;
    border-radius: 16px !important;
    backdrop-filter: blur(16px) !important;
    padding: 1.25rem !important;
    margin-bottom: 1.25rem !important;
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.25) !important;
}

/* Security Verification Badge */
.security-badge {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: rgba(16, 185, 129, 0.12);
    border: 1px solid rgba(16, 185, 129, 0.35);
    color: #6EE7B7;
    padding: 6px 14px;
    border-radius: 10px;
    font-size: 0.82rem;
    font-weight: 600;
    margin: 10px 0;
}

/* Truncated Filename Callout */
.filename-box {
    background: rgba(15, 23, 42, 0.85);
    border: 1px dashed rgba(99, 102, 241, 0.45);
    border-radius: 10px;
    padding: 10px 14px;
    margin: 10px 0;
}

.filename-label {
    font-size: 0.75rem;
    color: #9CA3AF;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.filename-value {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.95rem;
    font-weight: 600;
    color: #38BDF8;
    word-break: break-all;
    margin-top: 2px;
}

/* Specification Grid */
.spec-box {
    background: rgba(15, 23, 42, 0.6);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 10px;
    padding: 12px 16px;
    margin: 10px 0;
    font-size: 0.9rem;
    line-height: 1.6;
}

/* Direct Download to Device Button */
.direct-device-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
    background: linear-gradient(135deg, #4F46E5 0%, #06B6D4 100%);
    color: #FFFFFF !important;
    text-decoration: none !important;
    font-weight: 700;
    font-size: 1rem;
    padding: 15px 22px;
    border-radius: 12px;
    margin-top: 12px;
    margin-bottom: 8px;
    box-shadow: 0 4px 18px rgba(79, 70, 229, 0.45);
    transition: all 0.25s ease;
    text-align: center;
    width: 100%;
}

.direct-device-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 24px rgba(6, 182, 212, 0.6);
    color: #FFFFFF !important;
    text-decoration: none !important;
}

/* Streamlit Download Button Customization */
div.stDownloadButton > button {
    background: linear-gradient(135deg, #10B981 0%, #059669 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    font-weight: 700 !important;
    padding: 0.75rem 1.5rem !important;
    box-shadow: 0 4px 16px rgba(16, 185, 129, 0.35) !important;
    width: 100% !important;
    min-height: 48px !important;
}

div.stDownloadButton > button:hover {
    box-shadow: 0 6px 22px rgba(16, 185, 129, 0.55) !important;
    transform: translateY(-1px);
}

/* Streamlit Buttons */
div.stButton > button {
    border-radius: 12px !important;
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    padding: 0.65rem 1.2rem !important;
    min-height: 48px !important;
    transition: all 0.2s ease !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
}

div.stButton > button:hover {
    border-color: var(--brand-primary) !important;
    box-shadow: 0 0 16px rgba(99, 102, 241, 0.35) !important;
    transform: translateY(-1px);
}

/* Inputs styling */
div.stTextInput > div > div > input, div.stTextArea textarea {
    border-radius: 12px !important;
    border: 1px solid rgba(255, 255, 255, 0.12) !important;
    background-color: rgba(17, 24, 39, 0.85) !important;
    color: #F9FAFB !important;
    padding: 0.75rem 1rem !important;
    font-size: 0.95rem !important;
}

div.stTextInput > div > div > input:focus, div.stTextArea textarea:focus {
    border-color: var(--brand-primary) !important;
    box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.3) !important;
}

/* Tab Navigation */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background-color: rgba(17, 24, 39, 0.6);
    padding: 6px;
    border-radius: 14px;
    border: 1px solid rgba(255, 255, 255, 0.06);
    margin-bottom: 1.25rem;
}

.stTabs [data-baseweb="tab"] {
    height: 44px;
    border-radius: 10px;
    color: #9CA3AF;
    font-weight: 600;
    padding: 0 16px;
    border: none !important;
}

.stTabs [aria-selected="true"] {
    background-color: var(--brand-primary) !important;
    color: white !important;
    box-shadow: 0 4px 14px rgba(99, 102, 241, 0.35);
}

/* Mobile responsiveness */
@media (max-width: 768px) {
    .app-title {
        font-size: 1.85rem !important;
    }
    .app-header {
        padding: 1.4rem 1rem !important;
        border-radius: 14px !important;
    }
    .stTabs [data-baseweb="tab-list"] {
        width: 100% !important;
        overflow-x: auto;
    }
    div.stButton > button {
        width: 100% !important;
    }
}
</style>
"""
