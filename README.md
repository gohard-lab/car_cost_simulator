# 🚗 잡학다식 개발자 (YouTube) - 오픈소스 프로젝트 저장소

안녕하세요. 자동차와 IT 기술의 경계를 탐구하는 유튜브 채널 **'잡학다식 개발자'**의 공식 소스코드 저장소입니다. 
본 저장소는 영상에서 다룬 파이썬(Python) 기반의 시뮬레이터와 데이터 분석 대시보드 코드를 포함하고 있습니다.

## 📁 주요 프로젝트 (Projects)

### 1. 1년 유지비 배틀 시뮬레이터 (`car_cost_simulator.py`)
* **개요:** 르노 클리오, BMW M2 컴페티션 등 실제 차량의 제원과 고급유/일반유/경유 단가를 실시간으로 반영하여 1년 총 유지비를 직관적으로 비교하는 대시보드입니다.
* **주요 기술:** `Streamlit`, `Altair`, 천 단위 콤마 자동 포맷팅.

### 2. 테슬라 비전 시뮬레이터 (`tesla_vision_simulator.py`)
* **개요:** 테슬라의 카메라 기반(Vision-only) 자율주행 알고리즘이 겪는 '센서 퓨전 딜레마'를 코드로 구현하고 분석한 시뮬레이터입니다.
* **주요 기술:** `OpenCV` (Haar Cascade 기반 차량 인식), 판단 지연 및 유령 제동(Phantom Brake) 로직 구현.

### 3. 글로벌 사용량 분석 대시보드 (`supabase_analytics.py`)
* **개요:** 각 프로그램이 실행될 때 발생하는 트래픽과 익명화된 통계를 실시간으로 시각화하여 보여주는 관리자용 시스템입니다.
* **주요 기술:** `Supabase` (PostgreSQL RLS 보안 적용), `Pandas`.

---

## 🚀 실행 방법 (How to Run)

본 프로젝트는 최신 파이썬 패키지 관리자인 `uv`를 표준으로 사용하여 의존성을 안전하게 관리합니다.

### 1. 저장소 복제 및 패키지 설치
```bash
git clone [https://github.com/gohard-lab/youtube-analytics-app.git](https://github.com/gohard-lab/youtube-analytics-app.git)
cd youtube-analytics-app
uv sync