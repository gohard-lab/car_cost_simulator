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
    """Streamlit Cloud 헤더에서 실제 시청자의 IP를 집요하게 추출합니다."""
    try:
        headers = st.context.headers
        
        # 클라우드/프록시 환경에서 IP가 숨어있을 만한 모든 헤더 키 후보군을 뒤집니다.
        proxy_keys = [
            "X-Forwarded-For", "x-forwarded-for", 
            "X-Real-Ip", "x-real-ip", 
            "Client-IP", "client-ip"
        ]
        
        for key in proxy_keys:
            if key in headers:
                ip_list = headers.get(key)
                if ip_list:
                    # 여러 IP가 쉼표로 연결되어 있을 수 있으므로 첫 번째 값 추출
                    real_ip = ip_list.split(",")[0].strip()
                    
                    # 사설/내부망 IP(공유기 등)가 아니라면 진짜 방문자로 인정하고 즉시 반환!
                    if not real_ip.startswith(("192.168.", "10.", "172.", "127.")):
                        return real_ip
    except Exception:
        pass
    
    return None

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
    # base_url = f"http://ip-api.com/json/{real_ip}" if real_ip else "http://ip-api.com/json/"
    
    # 사설 IP라 None이 반환되었다면, 알아서 공인 IP를 찾도록 주소를 비워서 보냅니다.
    url = f"http://ip-api.com/json/{real_ip}" if real_ip else "http://ip-api.com/json/"
    req_url = f"{url}?fields=status,country,regionName,city,lat,lon"

    # 사용자님이 기존에 쓰시던 세부 필드(regionName 등) 옵션을 그대로 붙여줍니다.
    #  req_url = f"{base_url}?fields=status,country,regionName,city,lat,lon"
    
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