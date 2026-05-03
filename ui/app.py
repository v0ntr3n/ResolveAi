"""
ResolveAI - Modern Customer Support UI
A comprehensive, accessible, and responsive Streamlit interface.
"""

from __future__ import annotations

import os
from typing import Any
from datetime import datetime

import httpx
import streamlit as st
from streamlit.components.v1 import html


# =============================================================================
# Configuration
# =============================================================================

def backend_url() -> str:
    """Get the backend URL from environment or default."""
    explicit_url = os.getenv("RESOLVEAI_BACKEND_URL")
    if explicit_url:
        return explicit_url

    hostport = os.getenv("RESOLVEAI_BACKEND_HOSTPORT")
    if hostport:
        return f"http://{hostport}"

    return "http://127.0.0.1:8000"


# =============================================================================
# Custom CSS Styling
# =============================================================================

def load_custom_css() -> None:
    """Load custom CSS for enhanced styling."""
    st.markdown("""
    <style>
    /* Main container styling */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }
    
    /* Title styling */
    .main-title {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.5rem;
    }
    
    .subtitle {
        font-size: 1.1rem;
        color: #6b7280;
        margin-bottom: 2rem;
    }
    
    /* Chat message styling */
    .stChatMessage {
        padding: 1rem;
        border-radius: 12px;
        margin-bottom: 1rem;
    }
    
    .stChatMessage[data-testid="user-message"] {
        background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%);
        border-left: 4px solid #667eea;
    }
    
    .stChatMessage[data-testid="assistant-message"] {
        background: #f8fafc;
        border-left: 4px solid #10b981;
    }
    
    /* Metric cards */
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        text-align: center;
    }
    
    /* Quick action buttons */
    .quick-action {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 0.75rem 1.5rem;
        border-radius: 8px;
        border: none;
        cursor: pointer;
        font-weight: 500;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    
    .quick-action:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
    }
    
    /* Status badges */
    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
    }
    
    .status-delivered {
        background: #d1fae5;
        color: #065f46;
    }
    
    .status-pending {
        background: #fef3c7;
        color: #92400e;
    }
    
    .status-shipped {
        background: #dbeafe;
        color: #1e40af;
    }
    
    .status-processing {
        background: #e0e7ff;
        color: #3730a3;
    }
    
    /* Info cards */
    .info-card {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background: #f8fafc;
    }
    
    section[data-testid="stSidebar"] .block-container {
        padding-top: 2rem;
    }
    
    /* Chat input styling */
    .stChatInput textarea {
        border-radius: 12px !important;
        border: 2px solid #e2e8f0 !important;
        transition: border-color 0.2s !important;
    }
    
    .stChatInput textarea:focus {
        border-color: #667eea !important;
    }
    
    /* Responsive adjustments */
    @media (max-width: 768px) {
        .main-title {
            font-size: 1.75rem;
        }
        
        .quick-actions-grid {
            grid-template-columns: 1fr !important;
        }
    }
    
    /* Animation for typing indicator */
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    
    .typing-indicator {
        animation: pulse 1.5s infinite;
    }
    
    /* Escalation alert styling */
    .escalation-alert {
        background: #fef2f2;
        border-left: 4px solid #ef4444;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 0.5rem;
    }
    
    /* Language toggle */
    .lang-toggle {
        display: flex;
        gap: 0.5rem;
        margin-bottom: 1rem;
    }
    
    .lang-btn {
        padding: 0.5rem 1rem;
        border-radius: 6px;
        border: 2px solid #e2e8f0;
        background: white;
        cursor: pointer;
        transition: all 0.2s;
    }
    
    .lang-btn.active {
        background: #667eea;
        color: white;
        border-color: #667eea;
    }
    </style>
    """, unsafe_allow_html=True)


# =============================================================================
# API Functions
# =============================================================================

def detect_local_language(message: str) -> str:
    """Detect language from message content."""
    lowered = message.lower()
    vietnamese_markers = ("đơn", "hoàn tiền", "địa chỉ", "chính sách", "ở đâu", "giao hàng", "vận đơn")
    return "vi" if any(token in lowered for token in vietnamese_markers) else "en"


def fetch_json(method: str, path: str, payload: dict[str, Any] | None = None) -> Any:
    """Fetch JSON from backend API."""
    try:
        with httpx.Client(base_url=backend_url(), timeout=30.0) as client:
            response = client.request(method, path, json=payload)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        st.error(f"Connection error: {e}")
        return None


# =============================================================================
# UI Components
# =============================================================================

def render_header() -> None:
    """Render the main header with title and subtitle."""
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown('<h1 class="main-title">ResolveAI</h1>', unsafe_allow_html=True)
        st.markdown('<p class="subtitle">Autonomous Tier-1 Customer Support</p>', unsafe_allow_html=True)
    
    with col2:
        # Language preference
        lang = st.selectbox(
            "Language",
            options=["English", "Tiếng Việt"],
            index=0,
            label_visibility="collapsed"
        )
        st.session_state.language = "vi" if lang == "Tiếng Việt" else "en"


def render_metrics_dashboard() -> None:
    """Render the metrics dashboard with styled cards."""
    st.markdown("### Dashboard")
    
    metrics = fetch_json("GET", "/metrics")
    if not metrics:
        metrics = {"total_conversations": 0, "resolved_count": 0, "escalation_count": 0}
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size: 2rem; font-weight: 700; color: #667eea;">{metrics.get("total_conversations", 0)}</div>
            <div style="color: #6b7280; font-size: 0.875rem;">Total Conversations</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size: 2rem; font-weight: 700; color: #10b981;">{metrics.get("resolved_count", 0)}</div>
            <div style="color: #6b7280; font-size: 0.875rem;">Resolved</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size: 2rem; font-weight: 700; color: #ef4444;">{metrics.get("escalation_count", 0)}</div>
            <div style="color: #6b7280; font-size: 0.875rem;">Escalations</div>
        </div>
        """, unsafe_allow_html=True)


def render_quick_actions() -> None:
    """Render quick action buttons for common queries."""
    st.markdown("### Quick Actions")
    
    lang = st.session_state.get("language", "en")
    
    if lang == "vi":
        actions = [
            ("Tra cứu đơn hàng", "Đơn hàng DEMO-001 đang ở đâu?"),
            ("Yêu cầu hoàn tiền", "Hoàn tiền đơn DEMO-002 vì hàng bị hỏng"),
            ("Đổi địa chỉ", "Đổi địa chỉ đơn DEMO-003 đến 123 Nguyễn Huệ"),
            ("Chính sách", "Chính sách hoàn tiền là gì?"),
        ]
    else:
        actions = [
            ("Track Order", "Where is my order DEMO-001?"),
            ("Request Refund", "Refund order DEMO-002 because it is damaged"),
            ("Change Address", "Change address for DEMO-003 to 123 Main Street"),
            ("Policy Info", "What is the refund policy?"),
        ]
    
    cols = st.columns(4)
    for idx, (label, query) in enumerate(actions):
        with cols[idx]:
            if st.button(label, use_container_width=True, key=f"quick_{idx}"):
                st.session_state.quick_query = query


def render_demo_orders() -> None:
    """Render demo orders for testing."""
    st.markdown("### Demo Orders")
    
    demo_orders = [
        {"id": "DEMO-001", "status": "delivered", "amount": 45.99, "refund_ok": True, "lang": "EN"},
        {"id": "DEMO-002", "status": "delivered", "amount": 89.50, "refund_ok": True, "lang": "VI"},
        {"id": "DEMO-003", "status": "pending", "amount": 150.00, "addr_ok": True, "lang": "EN"},
        {"id": "DEMO-008", "status": "delivered", "amount": 175.00, "refund_ok": False, "lang": "VI"},
    ]
    
    for order in demo_orders:
        status_colors = {
            "delivered": "status-delivered",
            "pending": "status-pending",
            "shipped": "status-shipped",
            "processing": "status-processing",
        }
        
        badges = f'<span class="status-badge {status_colors.get(order["status"], "")}">{order["status"]}</span>'
        if order.get("refund_ok"):
            badges += ' <span class="status-badge" style="background: #d1fae5; color: #065f46;">Refund OK</span>'
        if order.get("addr_ok"):
            badges += ' <span class="status-badge" style="background: #dbeafe; color: #1e40af;">Addr OK</span>'
        
        st.markdown(f"""
        <div style="display: flex; justify-content: space-between; align-items: center; padding: 0.5rem 0; border-bottom: 1px solid #e2e8f0;">
            <div>
                <strong>{order["id"]}</strong> 
                <span style="color: #6b7280; font-size: 0.875rem;">(${order["amount"]})</span>
            </div>
            <div>{badges}</div>
        </div>
        """, unsafe_allow_html=True)


def render_escalations() -> None:
    """Render escalations list with styled cards."""
    st.markdown("### Recent Escalations")
    
    rows = fetch_json("GET", "/escalations")
    if not rows:
        st.info("No escalations at this time.")
        return
    
    for row in rows[:5]:
        st.markdown(f"""
        <div class="escalation-alert">
            <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                <strong>Order: {row['order_id']}</strong>
                <span style="color: #6b7280; font-size: 0.75rem;">SLA: {row['sla_hours']}h</span>
            </div>
            <div style="font-size: 0.875rem; color: #374151;">
                <strong>Intent:</strong> {row['intent']} | 
                <strong>Reason:</strong> {row['reason']} | 
                <strong>Evidence:</strong> {row['evidence_needed']}
            </div>
        </div>
        """, unsafe_allow_html=True)


def render_last_decision() -> None:
    """Render the last AI decision details."""
    if not st.session_state.get("last_response"):
        return
    
    response = st.session_state.last_response
    
    st.markdown("### Last Decision")
    
    intent_colors = {
        "order_status": "#3b82f6",
        "refund": "#ef4444",
        "address_change": "#10b981",
        "policy_question": "#8b5cf6",
    }
    
    intent_color = intent_colors.get(response.get("intent", ""), "#6b7280")
    
    st.markdown(f"""
    <div class="info-card">
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
            <div>
                <div style="color: #6b7280; font-size: 0.75rem; text-transform: uppercase;">Language</div>
                <div style="font-weight: 600;">{response.get('language', 'en').upper()}</div>
            </div>
            <div>
                <div style="color: #6b7280; font-size: 0.75rem; text-transform: uppercase;">Intent</div>
                <div style="font-weight: 600; color: {intent_color};">{response.get('intent', 'N/A')}</div>
            </div>
            <div>
                <div style="color: #6b7280; font-size: 0.75rem; text-transform: uppercase;">Tool Used</div>
                <div style="font-weight: 600;">{response.get('tool_used', 'N/A')}</div>
            </div>
            <div>
                <div style="color: #6b7280; font-size: 0.75rem; text-transform: uppercase;">Confidence</div>
                <div style="font-weight: 600;">{response.get('confidence_score', 0):.0%}</div>
            </div>
        </div>
        <div style="margin-top: 1rem; padding-top: 1rem; border-top: 1px solid #e2e8f0;">
            <div style="display: flex; align-items: center; gap: 0.5rem;">
                <span style="color: #6b7280;">Requires Human:</span>
                <span style="font-weight: 600; color: {'#ef4444' if response.get('requires_human') else '#10b981'};">
                    {'Yes' if response.get('requires_human') else 'No'}
                </span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_help_section() -> None:
    """Render help and FAQ section."""
    lang = st.session_state.get("language", "en")
    
    with st.expander("Help & Tips" if lang == "en" else "Trợ giúp"):
        if lang == "vi":
            st.markdown("""
            **Cách sử dụng:**
            - **Tra cứu đơn hàng**: Nhập mã đơn hàng (VD: DEMO-001, ORD-000001)
            - **Hoàn tiền**: Yêu cầu hoàn tiền kèm lý do (hỏng, sai hàng, thiếu hàng)
            - **Đổi địa chỉ**: Yêu cầu đổi địa chỉ giao hàng mới
            - **Chính sách**: Hỏi về chính sách hoàn tiền, vận chuyển, v.v.
            
            **Mẹo:**
            - Luôn cung cấp mã đơn hàng chính xác
            - Mô tả rõ lý do khi yêu cầu hoàn tiền
            - Chỉ đơn hàng ở trạng thái "delivered" mới được hoàn tiền
            """)
        else:
            st.markdown("""
            **How to use:**
            - **Track orders**: Enter order ID (e.g., DEMO-001, ORD-000001)
            - **Refunds**: Request refund with reason (damaged, wrong item, missing)
            - **Address change**: Provide new shipping address
            - **Policies**: Ask about refund, shipping, or other policies
            
            **Tips:**
            - Always provide the correct order ID
            - Clearly state the reason for refund requests
            - Only "delivered" orders are eligible for refunds
            """)


def render_chat_interface() -> None:
    """Render the main chat interface."""
    st.markdown("---")
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Handle quick query from buttons
    if st.session_state.get("quick_query"):
        prompt = st.session_state.quick_query
        st.session_state.quick_query = None
    else:
        # Chat input
        lang = st.session_state.get("language", "en")
        placeholder = "Nhập câu hỏi của bạn..." if lang == "vi" else "Type your question..."
        prompt = st.chat_input(placeholder)
    
    if not prompt:
        return
    
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Get AI response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..." if st.session_state.get("language", "en") == "en" else "Đang xử lý..."):
            response = fetch_json("POST", "/chat", {"message": prompt})
            
            if response:
                st.session_state.last_response = response
                st.markdown(response["response"])
                st.session_state.messages.append({"role": "assistant", "content": response["response"]})
            else:
                error_msg = "Sorry, I couldn't process your request. Please try again." if st.session_state.get("language", "en") == "en" else "Xin lỗi, tôi không thể xử lý yêu cầu của bạn. Vui lòng thử lại."
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})


# =============================================================================
# Main Application
# =============================================================================

def main() -> None:
    """Main application entry point."""
    # Page configuration
    st.set_page_config(
        page_title="ResolveAI - Customer Support",
        page_icon="🎯",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            "About": "ResolveAI - Autonomous Tier-1 Customer Support Agent",
            "Report a bug": "https://github.com/v0ntr3n/ResolveAi/issues",
        }
    )
    
    # Load custom styling
    load_custom_css()
    
    # Main content area
    render_header()
    
    # Two-column layout
    col_main, col_sidebar = st.columns([2, 1])
    
    with col_main:
        # Quick actions
        render_quick_actions()
        
        # Chat interface
        render_chat_interface()
    
    with col_sidebar:
        # Metrics dashboard
        render_metrics_dashboard()
        st.markdown("---")
        
        # Demo orders
        render_demo_orders()
        st.markdown("---")
        
        # Help section
        render_help_section()
    
    # Sidebar with detailed info
    with st.sidebar:
        st.markdown("### Details")
        
        # Last decision
        render_last_decision()
        st.markdown("---")
        
        # Escalations
        render_escalations()
        
        # Clear chat button
        if st.button("Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.last_response = None
            st.rerun()
        
        # Footer
        st.markdown("---")
        st.markdown("""
        <div style="text-align: center; color: #6b7280; font-size: 0.75rem;">
            ResolveAI v0.1.0<br>
            Powered by LangGraph & FastAPI
        </div>
        """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
