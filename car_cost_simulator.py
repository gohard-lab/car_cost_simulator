import streamlit as st
import pandas as pd
import altair as alt
import requests

TRACKING_ENABLED = True

# --- 1. [추가] Supabase 사용량 추적 로직 (DB 트래픽 방어 적용) ---
def log_app_usage():
    if "is_tracked" not in st.session_state:
        try:
            # 기존에 만드신 tracker.py 모듈을 불러옵니다.
            from tracker import get_supabase_client, get_location_data

            supabase = get_supabase_client()
            location = get_location_data()

            log_data = {
                "app_name": "car_cost_simulator",
                "action": "app_executed",
                "details": {
                    "environment": "local_windows",
                    "version": "1.0.0",
                    "description": "Simulator launched via web file"
                }
            }

            if location:
                log_data.update({
                    'country': location['country'],
                    'region': location['region'],
                    'city': location['city'],
                    'lat': location['lat'],
                    'lon': location['lon']
                })

            # returning='minimal'을 사용하여 RLS(읽기 금지) 충돌을 방지합니다.
            supabase.table('usage_logs').insert(log_data, returning='minimal').execute()
        except Exception as e:
            # 트래커 오류가 발생하더라도 메인 시뮬레이터 앱은 멈추지 않도록 예외 처리합니다.
            # print("✅ [디버그] : {e} ")
            pass # 혹시 모를 에러에도 메인 앱은 죽지 않게 보호
        finally:
            # 성공하든 실패하든 세션당 딱 1번만 실행되도록 플래그를 세웁니다.
            st.session_state["is_tracked"] = True
            # print("✅ [성공]")

# --- 2. 숫자로 변환하는 함수 ---
def get_number(text_value):
    try:
        return int(str(text_value).replace(",", "").strip())
    except:
        return 0

# --- 3. [핵심] 입력이 끝나는 순간 콤마를 자동으로 찍어주는 마법의 함수 ---
def format_comma(widget_key):
    val = st.session_state[widget_key]
    try:
        num = int(str(val).replace(",", "").strip())
        st.session_state[widget_key] = f"{num:,}"
    except:
        st.session_state[widget_key] = "0"

# --- 4. 웹 페이지 기본 설정 및 트래커 실행 ---
st.set_page_config(page_title="유지비 배틀 시뮬레이터", page_icon="🚗", layout="wide")
log_app_usage() # 앱이 시작될 때 사용량 추적 함수 호출

st.title("🚗 내 차 vs 네 차! 1년 유지비 배틀 시뮬레이터")
st.markdown("---")

# --- 5. 사이드바: 기름값 세팅 (초기값 세팅 및 콜백 연결) ---
st.sidebar.header("⚙️ 시뮬레이션 공통 조건")
연간_주행거리 = st.sidebar.slider("1년 예상 주행거리 (km)", 5000, 50000, 15000, 1000)

st.sidebar.subheader("⛽ 현재 기름값 세팅")

if "price_normal" not in st.session_state: st.session_state["price_normal"] = "1,600"
if "price_premium" not in st.session_state: st.session_state["price_premium"] = "1,900"
if "price_diesel" not in st.session_state: st.session_state["price_diesel"] = "1,500"

가격_일반유_텍스트 = st.sidebar.text_input("일반유 (원/L)", key="price_normal", on_change=format_comma, args=("price_normal",))
가격_고급유_텍스트 = st.sidebar.text_input("고급유 (원/L)", key="price_premium", on_change=format_comma, args=("price_premium",))
가격_경유_텍스트 = st.sidebar.text_input("경유 (원/L)", key="price_diesel", on_change=format_comma, args=("price_diesel",))

가격_일반유 = get_number(가격_일반유_텍스트)
가격_고급유 = get_number(가격_고급유_텍스트)
가격_경유 = get_number(가격_경유_텍스트)
연료별_단가 = {"일반유": 가격_일반유, "고급유": 가격_고급유, "경유": 가격_경유}

# --- 6. 미니 데이터베이스 ---
차량_DB = {
    "2020 르노 클리오 (1.5 디젤)": {"연비": 17.0, "연료": "경유", "자동차세": 250000, "엔진오일": 100000},
    "2019 BMW M2 컴페티션 (3.0 가솔린)": {"연비": 8.0, "연료": "고급유", "자동차세": 780000, "엔진오일": 300000},
    "2024 현대 아반떼 (1.6 가솔린)": {"연비": 15.3, "연료": "일반유", "자동차세": 290000, "엔진오일": 80000},
    "2024 기아 쏘렌토 (2.2 디젤)": {"연비": 14.3, "연료": "경유", "자동차세": 570000, "엔진오일": 120000},
    "2024 현대 그랜저 (2.5 가솔린)": {"연비": 11.7, "연료": "일반유", "자동차세": 650000, "엔진오일": 100000},
    "직접 입력하기 ✍️": None 
}
차종_리스트 = list(차량_DB.keys())

# --- 7. 메인 화면: 차량 선택 및 직접 입력 ---
col1, col2 = st.columns(2)

def get_car_data(col_obj, title, default_index, unique_id):
    with col_obj:
        st.subheader(title)
        선택된_차 = st.selectbox("차종 선택", 차종_리스트, index=default_index, key=f"{unique_id}_선택")
        
        if 선택된_차 == "직접 입력하기 ✍️":
            차량명 = st.text_input("🚗 차량 이름", "내 자동차", key=f"{unique_id}_이름")
            연비 = st.number_input("🎯 공인 연비 (km/L)", value=10.0, step=0.1, key=f"{unique_id}_연비")
            연료 = st.selectbox("⛽ 연료 종류", ["일반유", "고급유", "경유"], key=f"{unique_id}_연료")
            
            tax_key = f"{unique_id}_자동차세_txt"
            oil_key = f"{unique_id}_엔진오일_txt"
            
            if tax_key not in st.session_state: st.session_state[tax_key] = "300,000"
            if oil_key not in st.session_state: st.session_state[oil_key] = "100,000"
            
            자동차세_텍스트 = st.text_input("💸 1년 자동차세 (원)", key=tax_key, on_change=format_comma, args=(tax_key,))
            엔진오일_텍스트 = st.text_input("🛢️ 엔진오일 1회 교체비 (원)", key=oil_key, on_change=format_comma, args=(oil_key,))
            
            자동차세 = get_number(자동차세_텍스트)
            엔진오일 = get_number(엔진오일_텍스트)
            
            return 차량명, {"연비": 연비, "연료": 연료, "자동차세": 자동차세, "엔진오일": 엔진오일}
        else:
            st.info(f"✅ [{선택된_차}]의 제원 데이터가 적용되었습니다.")
            return 선택된_차, 차량_DB[선택된_차]

차량1_이름, 차량1_제원 = get_car_data(col1, "🥊 첫 번째 차량 (RED)", 0, "car1") 
차량2_이름, 차량2_제원 = get_car_data(col2, "🥊 두 번째 차량 (BLUE)", 1, "car2")

# --- 8. 유지비 계산 로직 ---
def calculate_cost(제원):
    if 제원["연비"] == 0:
        연간_기름값 = 0
    else:
        연간_기름값 = (연간_주행거리 / 제원["연비"]) * 연료별_단가[제원["연료"]]
        
    총_유지비 = 연간_기름값 + 제원["자동차세"] + 제원["엔진오일"]
    return int(연간_기름값), int(총_유지비)

차량1_기름값, 차량1_총유지비 = calculate_cost(차량1_제원)
차량2_기름값, 차량2_총유지비 = calculate_cost(차량2_제원)

# --- 9. 결과 시각화 ---
st.markdown("---")
st.subheader("📊 1년 유지비 배틀 결과!")

결과_데이터 = {
    "차량": [f"🔴 {차량1_이름}", f"🔵 {차량2_이름}"],
    "1년 총 유지비": [차량1_총유지비, 차량2_총유지비]
}
df = pd.DataFrame(결과_데이터)

chart = alt.Chart(df).mark_bar().encode(
    x=alt.X("차량", axis=alt.Axis(labelAngle=0, labelLimit=0)), 
    y="1년 총 유지비",
    color=alt.Color("차량", scale=alt.Scale(domain=[f"🔴 {차량1_이름}", f"🔵 {차량2_이름}"], range=["#FF4B4B", "#1C83E1"]), legend=None)
)
st.altair_chart(chart, use_container_width=True)

col3, col4 = st.columns(2)
with col3:
    st.metric(label=f"🔴 {차량1_이름}", value=f"{차량1_총유지비:,} 원", delta=f"순수 기름값: {차량1_기름값:,} 원", delta_color="off")
with col4:
    st.metric(label=f"🔵 {차량2_이름}", value=f"{차량2_총유지비:,} 원", delta=f"순수 기름값: {차량2_기름값:,} 원", delta_color="off")