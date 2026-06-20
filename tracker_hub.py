import uuid
import streamlit as st
import requests
import os
import sys
from supabase import create_client, Client
from streamlit_javascript import st_javascript
from datetime import datetime, timezone


@st.cache_resource
def get_supabase_client():
    try:
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
    except KeyError:
        st.error("🚨 Database configuration (secrets) is missing!")
        return None

    if not url or not key:
        return None
    
    return create_client(url, key)


def get_real_client_ip():
    """Extract real client IP prioritizing Streamlit context headers to minimize 'Unknown' location metrics."""
    # 1. Try extracting from X-Forwarded-For header (Streamlit Cloud Proxy environment)
    if hasattr(st, "context") and st.context.headers:
        xff = st.context.headers.get("X-Forwarded-For")
        if xff:
            # Take the first IP if multiple proxies are chained
            return xff.split(",")[0].strip()

    # 2. Fallback to cached session state IP
    if "cached_ip" in st.session_state:
        return st.session_state.cached_ip

    # 3. Fallback to JavaScript API call if headers are unavailable
    try:
        js_code = "await fetch('https://api.ipify.org?format=json').then(r => r.json()).then(d => d.ip)"
        client_ip = st_javascript(js_code, key="ip_tracker_js")
        
        if client_ip == 0 or not client_ip:
            return None
        
        st.session_state.cached_ip = client_ip
        return client_ip
    except:
        return "Unknown"


def get_or_create_session_id():
    """Generate or retrieve a unique session hexadecimal ID for the current user session."""
    if 'session_id' not in st.session_state:
        st.session_state['session_id'] = uuid.uuid4().hex
    return st.session_state['session_id']


def log_app_usage(app_name="unknown_app", action="page_view", details=None):
    """Log user activities to Supabase database while filtering out automated bot activities."""
    user_agent = st.context.headers.get("User-Agent", "Unknown") if hasattr(st, "context") else "Unknown"
    
    # ==========================================================
    # 🚨 [SMART BOT SHIELD] Block GitHub Actions, curl, and automated pings immediately
    # ==========================================================
    if user_agent and any(keyword in user_agent.lower() for keyword in ["github", "curl", "wget", "bot", "uptime", "cron", "polymath"]):
        return False
    # ==========================================================

    real_ip = get_real_client_ip()

    # 🔥 [CRITICAL FIX] Immediately drop headless ping requests that fail JavaScript evaluation
    if not real_ip or real_ip in ["Pending", "Unknown"]:
        return False
    
    # ==========================================================
    # 🚨 Secondary Shield: Block if both identification metrics fail
    # ==========================================================
    if user_agent == "Unknown" and real_ip == "Unknown":
        return False

    try:
        client = get_supabase_client()
        if not client:
            return False

        loc_data = {}
        if real_ip not in ["Unknown", "Pending"]:
            try:
                res = requests.get(f"http://ip-api.com/json/{real_ip}?fields=status,country,regionName,city,lat,lon", timeout=1)
                loc_data = res.json() if res.status_code == 200 else {}
            except: 
                pass

        current_session = get_or_create_session_id()
        utc_time = datetime.now(timezone.utc).isoformat()

        log_data = {
            "session_id": current_session,
            "app_name": app_name,
            "action": action,
            "timestamp": utc_time,
            "country": loc_data.get('country', "Unknown"),
            "region": loc_data.get('regionName', "Unknown"),
            "city": loc_data.get('city', "Unknown"),
            "lat": loc_data.get('lat', 0.0),
            "lon": loc_data.get('lon', 0.0),
            "ip_address": real_ip,
            "details": details if details else {},
            "user_agent": user_agent
        }
        
        client.table('usage_logs').insert(log_data, returning='minimal').execute()
        return True
    except Exception as e:
        print(f"🚨 Tracker Error: {e}")
        return False