import uuid
import streamlit as st
import requests
import os
import sys  # 💡 sys 모듈 누락 수정
from supabase import create_client, Client
from streamlit_javascript import st_javascript
from datetime import datetime, timezone


@st.cache_resource
def get_supabase_client():
    try:
        # 🌟 수정 후 (로컬: secrets.toml / 배포: Cloud Secrets 탭에서 자동 인식)
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
    except KeyError:
        # 설정 파일이나 클라우드 세팅이 누락되었을 때 부드럽게 에러 안내
        st.error("🚨 데이터베이스 연결 설정(secrets)이 누락되었습니다!")
        return None

    if not url or not key:
        return None
    
    return create_client(url, key)


def get_real_client_ip():
    """세션 상태를 이용해 IP 추출 과정에서의 무한 루프를 방지합니다."""
    if "cached_ip" in st.session_state:
        return st.session_state.cached_ip

    try:
        # 🚨 key 인자를 추가하여 위젯 충돌을 방지합니다.
        js_code = "await fetch('https://api.ipify.org?format=json').then(r => r.json()).then(d => d.ip)"
        client_ip = st_javascript(js_code, key="ip_tracker_js")
        
        if client_ip == 0 or not client_ip:
            return None # LOADING 대신 None 반환하여 메인 화면이 뜨게 함
        
        st.session_state.cached_ip = client_ip
        return client_ip
    except:
        return "Unknown"


# 1. 💡 세션 ID를 발급/조회하는 함수 추가 (log_app_usage 함수 위쪽에 배치)
def get_or_create_session_id():
    if 'session_id' not in st.session_state:
        # 접속 시 최초 1회만 고유 ID 생성 (예: 'a1b2c3d4...')
        st.session_state['session_id'] = uuid.uuid4().hex
    return st.session_state['session_id']


def log_app_usage(app_name="unknown_app", action="page_view", details=None):
    real_ip = get_real_client_ip()
    
    # IP가 아직 로딩 중이면 로그 기록을 일단 건너뜁니다 (화면 멈춤 방지)
    if not real_ip:
        return False

    try:
        client = get_supabase_client()
        if not client:
            return False

        loc_data = {}
        if real_ip not in ["Unknown"]:
            try:
                res = requests.get(f"http://ip-api.com/json/{real_ip}?fields=status,country,regionName,city,lat,lon", timeout=1)
                loc_data = res.json() if res.status_code == 200 else {}
            except: pass

        current_session = get_or_create_session_id()

        user_agent = st.context.headers.get("User-Agent", "Unknown") if hasattr(st, "context") else "Unknown"
        
        # 💡 [핵심 수정] 타임존 이중 계산 방지를 위해 명시적인 UTC 시간(ISO 포맷) 사용
        utc_time = datetime.now(timezone.utc).isoformat()

        log_data = {
            "session_id": current_session,
            "app_name": app_name,
            "action": action,
            "timestamp": utc_time,  # 💡 UTC 시간 전송 (Supabase가 KST로 변환)
            "country": loc_data.get('country', "Unknown"),
            "region": loc_data.get('regionName', "Unknown"),
            "city": loc_data.get('city', "Unknown"),
            "lat": loc_data.get('lat', 0.0),
            "lon": loc_data.get('lon', 0.0),
            "ip_address": real_ip,
            "details": details if details else {},
            "user_agent": user_agent
        }

        # ==========================================================
        # 🚨 [스마트 봇 차단] 정상적인 유저는 통과시키고 헬스체크 핑만 차단
        # ==========================================================
        
        # 1. 이름에 대놓고 'bot', 'uptime', 'cron' 등이 들어간 기계는 즉시 차단
        if user_agent and any(keyword in user_agent.lower() for keyword in ["bot", "uptime", "cron"]):
            return False
            
        # 2. 기기 정보(User-Agent)와 IP 주소가 "둘 다" Unknown일 때만 헬스체크 핑으로 간주하고 차단
        # (스트림릿 버전 차이로 하나만 Unknown이 뜨는 정상 유저는 통과시켜 줍니다)
        if user_agent == "Unknown" and real_ip == "Unknown":
            return False
        
        # ==========================================================
        
        client.table('usage_logs').insert(log_data, returning='minimal').execute()
        return True
    except Exception as e:
        print(f"🚨 트래커 에러: {e}")
        return False