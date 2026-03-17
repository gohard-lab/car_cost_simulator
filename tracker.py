import os
import streamlit as st
import requests

# 1. 패키지가 있는지 확인하고, 없으면 조용히 넘어갑니다.
try:
    import requests
    from supabase import create_client, Client
    TRACKING_ENABLED = True
    print("✅ [디버그] 통계 패키지 로드 성공!")
except ImportError as e:
    TRACKING_ENABLED = False
    print(f"❌ [디버그] 패키지가 없어서 통계가 꺼졌습니다: {e}")

_supabase_client = None

def get_real_client_ip():
    """Streamlit Cloud 헤더에서 실제 시청자의 IP를 추출합니다."""
    try:
        # Streamlit 1.37 이상 버전의 최신 기능인 st.context를 사용합니다.
        headers = st.context.headers
        
        # 클라우드 환경에서는 X-Forwarded-For 헤더에 진짜 방문자 IP가 담깁니다.
        if "X-Forwarded-For" in headers:
            ip_list = headers.get("X-Forwarded-For")
            # "시청자IP, 거쳐온서버IP" 형태이므로 첫 번째 값을 가져옵니다.
            real_ip = ip_list.split(",")[0].strip()
            return real_ip
    except Exception:
        pass
    
    return None # 로컬(내 컴퓨터) 환경이거나 IP를 못 찾은 경우

def get_supabase_client():
    global _supabase_client
    if _supabase_client is None and TRACKING_ENABLED:
        supabase_url = "https://gkzbiacodysnrzbpvavm.supabase.co"
        supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdremJpYWNvZHlzbnJ6YnB2YXZtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzM1NzE2MTgsImV4cCI6MjA4OTE0NzYxOH0.Lv5uVeNZOyo21tgyl2jjGcESoLl_iQTJYp4jdCwuYDU"
        _supabase_client = create_client(supabase_url, supabase_key)
    return _supabase_client

def get_location_data():
    """실제 IP를 기반으로 위치 정보를 가져옵니다."""
    real_ip = get_real_client_ip()
    
    # IP를 찾았으면 해당 IP를 넣고, 못 찾았으면(로컬) 빈칸으로 요청합니다.
    base_url = f"http://ip-api.com/json/{real_ip}" if real_ip else "http://ip-api.com/json/"
    
    # 사용자님이 기존에 쓰시던 세부 필드(regionName 등) 옵션을 그대로 붙여줍니다.
    req_url = f"{base_url}?fields=status,country,regionName,city,lat,lon"
    
    try:
        response = requests.get(req_url, timeout=3)
        data = response.json()
        
        if data.get('status') == 'success':
            return {
                'country': data.get('country'),
                'region': data.get('regionName'),
                'city': data.get('city'),
                'lat': data.get('lat'),
                'lon': data.get('lon')
            }
    except Exception:
        pass
        
    return None

# def get_location_data():
#     if not TRACKING_ENABLED:
#         return None
#     try:
#         response = requests.get('http://ip-api.com/json/?fields=status,country,regionName,city,lat,lon', timeout=3)
#         data = response.json()
#         if data['status'] == 'success':
#             return {
#                 'country': data['country'],
#                 'region': data['regionName'],
#                 'city': data['city'],
#                 'lat': data['lat'],
#                 'lon': data['lon']
#             }
#     except Exception:
#         pass
#     return None

def log_app_usage(app_name: str, action: str, details: dict = None):
    # 2. 패키지가 설치되지 않은 유저라면 여기서 함수를 즉시 종료합니다.
    if not TRACKING_ENABLED:
        print("⚠️ [디버그] TRACKING_ENABLED가 False라서 전송 취소됨.")
        return

    try:
        supabase = get_supabase_client()
        location = get_location_data()
        
        log_data = {
            'app_name': app_name,
            'action': action,
            'details': details or {},
        }
        
        if location:
            log_data.update({
                'country': location['country'],
                'region': location['region'],
                'city': location['city'],
                'lat': location['lat'],
                'lon': location['lon']
            })
            
        # 데이터를 쏘고 결과를 받아서 출력해봅니다.(결과를 받지 않는 걸로 변경)
        # response = supabase.table('usage_logs').insert(log_data).execute()
        response = supabase.table('usage_logs').insert(log_data, returning='minimal').execute()
        print(f"✅ [디버그] 데이터 전송 성공! 결과: {response.data}")
        
    except Exception as e:
        # 에러가 나면 조용히 넘어가지 않고 화면에 빨간 글씨로 출력합니다!
        # print(f"🚨 [디버그] Supabase 전송 중 에러 발생: {e}")
        pass