import os

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

def get_supabase_client():
    global _supabase_client
    if _supabase_client is None and TRACKING_ENABLED:
        supabase_url = "https://gkzbiacodysnrzbpvavm.supabase.co"
        supabase_key = "sb_publishable_P-YwlgcC6aIEo7udF6utzQ_zvLAi2X5"
        _supabase_client = create_client(supabase_url, supabase_key)
    return _supabase_client

def get_location_data():
    if not TRACKING_ENABLED:
        return None
    try:
        response = requests.get('http://ip-api.com/json/?fields=status,country,regionName,city,lat,lon', timeout=3)
        data = response.json()
        if data['status'] == 'success':
            return {
                'country': data['country'],
                'region': data['regionName'],
                'city': data['city'],
                'lat': data['lat'],
                'lon': data['lon']
            }
    except Exception:
        pass
    return None

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
        print(f"🚨 [디버그] Supabase 전송 중 에러 발생: {e}")