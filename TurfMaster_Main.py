import streamlit as st
import pandas as pd
import requests
import os
import google.generativeai as genai

import google.generativeai as genai
import streamlit as st

# 설정은 딱 이렇게만!
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# 모델 이름은 'gemini-1.5-flash' 딱 하나만 남기세요!
model = genai.GenerativeModel('gemini-1.5-flash')

from datetime import datetime

# 데이터 안전 변환 함수
def safe_int(val, default=0):
    try: return int(val)
    except: return default

def safe_float(val, default=0.0):
    try: return float(val)
    except: return default

# 1. 프리미엄 UI 디자인 (민트/화이트/스카이블루)
st.set_page_config(page_title="TURF MASTER V20", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #0A0A0A; color: #FFFFFF; }
    .main-title { font-size: 55px !important; font-weight: 900; color: #FACC15; margin-bottom: 20px; }
    
    /* 가로형 라디오 버튼 (경주 선택) */
    div.row-widget.stRadio > div { flex-direction: row; flex-wrap: wrap; gap: 10px; }
    .stRadio [data-testid="stWidgetLabel"] { display: none; }
    
    /* 카드 디자인 */
    .horse-card {
        background: #141414; border: 1px solid #333; padding: 22px;
        border-radius: 15px; margin-bottom: 15px; min-height: 480px;
        display: flex; flex-direction: column; justify-content: space-between;
    }
    .top-rank-card { border: 2px solid #A855F7 !important; box-shadow: 0 0 20px rgba(168,85,247,0.4); }
    
    .horse-no { font-size: 50px; font-weight: 900; color: white; font-style: italic; line-height: 1; margin-bottom: 5px;}
    .horse-name { font-size: 26px; font-weight: 900; color: #FFFFFF !important; margin-bottom: 5px;}
    
    .analysis-summary { 
        font-size: 12px; font-weight: 800; color: #00FFCC; 
        background: rgba(0, 255, 204, 0.15); padding: 4px 10px; border-radius: 6px; 
        border: 1px solid rgba(0, 255, 204, 0.4); display: inline-block; margin-bottom: 10px;
    }
    
    .score-val { color: #00D1FF !important; font-size: 45px; font-weight: 900; font-style: italic; line-height: 1;}
    .tag { padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: bold; margin-right: 4px; margin-bottom: 4px; display: inline-block; }
    </style>
    """, unsafe_allow_html=True)

# 2. API 설정 및 CSV 데이터 로드
API_KEY = "bb89bd57507c9dd632b95ca7fed5cbcf522c6ad45b2f1451866a92fc04b873df"
BASE_URL = "https://apis.data.go.kr/B551015"

@st.cache_data
def load_csv():
    files = {'syn': 'jockey_stable_synergy.csv', 'exc': 'jockey_exclusion.csv', 'hist': '11_마필구간별기록_2년.csv'}
    loaded = {}
    for k, v in files.items():
        if os.path.exists(v):
            try: loaded[k] = pd.read_csv(v, encoding='cp949')
            except: loaded[k] = pd.read_csv(v, encoding='utf-8')
        else: loaded[k] = pd.DataFrame()
    return loaded

csv_data = load_csv()

with st.sidebar:
    # 1. 상단 타이틀 (멋진 디자인)
    st.markdown("## 🏇 **TurfMaster AI**")
    st.caption("v2.0 통합 가점제 엔진 탑재")
    st.markdown("---")

    # 2. 날짜 및 경마장 선택 (기존 기능을 이쁘게!)
    st.markdown("### 📅 **기본 설정**")
    target_date = st.date_input("📅 분석 날짜 선택", datetime.now())
    meet = st.selectbox("🏟️ 경마장 선택", ["서울 (1)", "제주 (2)", "부산 (3)"])
    
    # 데이터 처리를 위한 기존 코드 (유지)
    meet_code = meet.split("(")[1].replace(")", "")
    formatted_date = target_date.strftime('%Y%m%d')
    
    st.markdown("---")

    # 3. 안내 문구 (파란색 박스)
    st.info("선택하신 날짜와 경마장의 데이터를 기반으로 AI가 승률을 분석합니다.")
    
    # 4. 하단 저작권 표시
    st.markdown("---")
    st.caption("© 2026 TurfMaster AI | ISFJ-T Edition")

st.markdown('<h1 class="main-title">터프 마스터 V20 (통합 가점제 엔진)</h1>', unsafe_allow_html=True)

# 4. 실시간 통합 분석 엔진
try:
    with st.spinner("마사회 실시간 데이터 연동 중..."):
        e_url = f"{BASE_URL}/API26_2/entrySheet_2?serviceKey={API_KEY}&pageNo=1&numOfRows=500&rc_date={formatted_date}&meet={meet_code}&_type=json"
        w_url = f"{BASE_URL}/API25_1/entryHorseWeightInfo_1?serviceKey={API_KEY}&pageNo=1&numOfRows=500&rc_date={formatted_date}&meet={meet_code}&_type=json"
        
        e_raw = requests.get(e_url).json().get('response', {}).get('body', {}).get('items', {}).get('item', [])
        w_raw = requests.get(w_url).json().get('response', {}).get('body', {}).get('items', {}).get('item', [])

    if not e_raw:
        st.error(f"⚠️ {formatted_date}의 경주 데이터가 없습니다.")
    else:
        df_e = pd.DataFrame(e_raw if isinstance(e_raw, list) else [e_raw])
        df_w = pd.DataFrame(w_raw if isinstance(w_raw, list) else [w_raw])
        race_numbers = sorted(df_e['rcNo'].astype(int).unique())
        
        # 상단 가로 버튼 (클릭 시 즉각 반응)
        st.write("#### 🏇 분석할 경주 번호를 클릭하세요")
        selected_race = st.radio("경주", race_numbers, horizontal=True)
        st.markdown("---")
        
        # 현장 변수
        col1, col2 = st.columns(2)
        with col1: rain_mode = st.checkbox("🌧️ 현재 비/젖은주로 (수중전 자동반영)", value=False)
        with col2: style_mode = st.selectbox("🎯 당일 유리한 주로 각질", ["평범함", "선행 유리", "선입 유리", "추입 유리"])
        
        st.markdown(f"### 📍 제 {selected_race} 경주 통합 가점 분석 결과")

        r_horses = df_e[df_e['rcNo'].astype(int) == selected_race]
        scored_list = []

        for _, h in r_horses.iterrows():
            score = 50.0 
            hr, jk, tr = h.get('hrName', ''), h.get('jkName', ''), h.get('trName', '')
            gate = safe_int(h.get('chulNo', 0))
            rating = safe_int(h.get('rating', 0))
            age = safe_int(h.get('age', 0))
            wg = safe_float(h.get('wgBudam', 55.0))
            
            summ, tags = [], []

            # --- [가점 로직 1] 기본 능력치 ---
            score += (rating * 0.3)
            if rating > 0: tags.append(f'<span class="tag" style="background:#444;">R:{rating}</span>')
            if age in [3, 4]: score += 5; tags.append('<span class="tag" style="background:#A855F7;">🔥전성기</span>')
            elif age >= 7: score -= 3
            if wg <= 53.0: score += 3; tags.append('<span class="tag" style="background:#00D1FF; color:black;">🪶경량</span>')
            elif wg >= 57.0: score -= 3; tags.append('<span class="tag" style="background:#555;">🏋️중량</span>')

            # --- [가점 로직 2] 인적 네트워크 (태그 추가 버전) ---
            # 1. 인마합 (최강조합)
            if not csv_data['syn'].empty and not csv_data['syn'][(csv_data['syn'].iloc[:,0] == jk) & (csv_data['syn'].iloc[:,1] == tr)].empty:
                score += 30
                summ.append("인마합")
                # 👇 여기가 핵심! tags에 추가해야 '경량' 옆에 나란히 뜹니다.
                tags.append('<span class="tag" style="background:#A855F7; color:white;">❤️최강조합</span>')
            
            # 2. 기수 상극 체크
            if not csv_data['exc'].empty and not csv_data['exc'][csv_data['exc'].iloc[:,0] == jk].empty:
                score -= 30
                summ.append("기수주의")
                # 👇 상극 태그 추가
                tags.append('<span class="tag" style="background:#FF3366; color:white;">⚔️기수주의</span>')

            # 3. 견제/주의 등 기타 로직 (있다면 똑같이 tags.append 추가)
            if "견제" in h and h.get("견제", "") == "Y":
                tags.append('<span class="tag" style="background:#FFA500; color:white;">📢견제</span>')

            
            # 4. 리턴 승부마 체크 (엑셀에 '리턴' 정보가 있다면)
            if h.get('return_yn', '') == 'Y':
                score += 10; summ.append("리턴승부"); tags.append('<span class="tag" style="background:#10B981; color:white;">🔄리턴승부</span>')
            
            # --- [가점 로직 3] 마체중 분석 (API + CSV) ---
            if not df_w.empty:
                w_info = df_w[df_w['hrName'] == hr]
                if not w_info.empty:
                    tw = float(w_info.iloc[0].get('nowWeight', 0))
                    chw = safe_int(w_info.iloc[0].get('chngWeight', '0'))
                    
                    # 1) 당일 컨디션
                    if abs(chw) <= 2: score += 8; summ.append("체중안정")
                    elif abs(chw) >= 10: score -= 5; summ.append("체중급변")
                    
                    # 2) 과거 최적 체중 대조
                    if not csv_data['hist'].empty:
                        hist_h = csv_data['hist'][csv_data['hist'].iloc[:,0] == hr]
                        if not hist_h.empty:
                            bw = float(hist_h.iloc[0].get('체중', 0))
                            if bw > 0 and abs(tw - bw) <= 3:
                                score += 35; summ.append("최적체중"); tags.append('<span class="tag" style="background:#00FFCC; color:#000;">⚖️최적중량</span>')

            # --- [가점 로직 4] 리벤지 매치 (CSV) ---
            if not csv_data['hist'].empty and not csv_data['hist'][(csv_data['hist'].iloc[:,0] == hr) & (csv_data['hist'].get('착순','') == '1')].empty:
                score += 30; summ.append("리벤지"); tags.append('<span class="tag" style="background:#FF3366; color:white;">🔥리벤지</span>')

            # --- [가점 로직 5] 현장 변수 (수중전/각질) ---
            style = "선행" if gate <= 3 else ("선입" if 4 <= gate <= 7 else "추입")
            tags.append(f'<span class="tag" style="background:rgba(255,255,255,0.1);">{style}</span>')

            if rain_mode:
                if not csv_data['hist'].empty and not csv_data['hist'][(csv_data['hist'].iloc[:,0] == hr) & (csv_data['hist'].get('주로상태','').isin(['포화','불량']))].empty:
                    score += 50; summ.append("수중강자"); tags.append('<span class="tag" style="background:#0070FF; color:white;">🌊수중특화</span>')
                if style == "선행": score += 15
                if wg <= 53.0: score += 10

            if style_mode == f"{style} 유리": 
                score += 25; summ.append(f"{style}버프")

            scored_list.append({'no': gate, 'name': hr, 'jk': jk, 'tr': tr, 'score': score, 'summary': " | ".join(summ) if summ else "기본능력", 'tags': "".join(tags)})

        # 출력부
        top_5 = sorted(scored_list, key=lambda x: x['score'], reverse=True)[:5]
        cols = st.columns(5)
        for idx, horse in enumerate(top_5):
            with cols[idx]:
                card_class = "horse-card top-rank-card" if idx == 0 else "horse-card"
                st.markdown(f"""
                    <div class="{card_class}">
                        <div>
                            <div style="font-size:12px; color:#888;">RANK {idx+1}</div>
                            <div class="horse-no">{horse['no']}</div>
                            <div class="horse-name">{horse['name']}</div>
                            <div class="analysis-summary">{horse['summary']}</div>
                            <div style="font-size:12px; color:#AAA; margin-top:5px;">{horse['jk']} / {horse['tr']}</div>
                            <div style="margin-top:10px;">{horse['tags']}</div>
                        </div>
                        <div style="margin-top:15px; border-top:1px solid #333; padding-top:15px;">
                            <span class="score-val">{int(horse['score'])}</span><span style="font-size:12px; color:#666; margin-left:5px;">PTS</span>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

except Exception as e:
    st.error(f"⚠️ 일시적 오류입니다. 데이터를 확인해주세요. ({e})")
 # 1. 말별 평균 기록 계산 (최근 3~5경기 데이터가 있다고 가정)
# df는 현재 경주마들의 전적 데이터프레임입니다.

def apply_track_speed_logic(df, track_condition):
    """
    track_condition: '건조', '다습', '포획', '불량' 등
    """
    # 초반 스피드(S1F) 점수: 낮을수록 빠름
    s1f_threshold = df['S1F'].quantile(0.2)  # 상위 20% 기록 커트라인
    
    # 종반 뒷심(G3F) 점수: 낮을수록 빠름
    g3f_threshold = df['G3F'].quantile(0.2)  # 상위 20% 기록 커트라인

    for i, row in df.iterrows():
        # 상태 1: 트랙이 빠를 때 (건조/다습) -> 초반 스피드 가점
        if track_condition in ['건조', '다습']:
            if row['S1F'] <= s1f_threshold:
                df.at[i, '가점_총점'] += 1.5
                df.at[i, '로직_메모'] += " [초반스피드 가점]"

        # 상태 2: 트랙이 무거울 때 (포획/불량) -> 뒷심 가점
        elif track_condition in ['포획', '불량']:
            if row['G3F'] <= g3f_threshold:
                df.at[i, '가점_총점'] += 1.5
                df.at[i, '로직_메모'] += " [종반뒷심 가점]"
                
    return df   
def apply_advanced_speed_logic(df, track_condition, distance):
    """
    df: 경주마 데이터 (S1F, G3F 포함)
    track_condition: 트랙 상태 (건조, 다습, 포획, 불량)
    distance: 경주 거리 (예: 1000, 1200, 1800 등)
    """
    
    # 1. 거리별 가중치 설정 (단거리는 초반, 장거리는 후반 중시)
    if distance <= 1200:
        s1f_weight = 2.0  # 단거리는 초반 스피드에 더 큰 점수
        g3f_weight = 1.0
    elif distance >= 1700:
        s1f_weight = 1.0
        g3f_weight = 2.0  # 장거리는 뒷심에 더 큰 점수
    else:
        s1f_weight = 1.5
        g3f_weight = 1.5

    # 2. 트랙 상태에 따른 추가 보너스
    # 건조/다습 시 S1F가 빠른 말에게 유리, 포획/불량 시 G3F가 빠른 말에게 유리
    
    for i, row in df.iterrows():
        # S1F 가점 (초반 스피드가 해당 경주 평균보다 빠를 때)
        if row['S1F'] < df['S1F'].mean():
            if track_condition in ['건조', '다습']:
                bonus = s1f_weight + 0.5 # 트랙까지 빠르면 금상첨화
                df.at[i, '가점_총점'] += bonus
                df.at[i, '로직_메모'] += f" [초반스피드 최우수 +{bonus}]"
            else:
                df.at[i, '가점_총점'] += s1f_weight

        # G3F 가점 (종반 뒷심이 해당 경주 평균보다 빠를 때)
        if row['G3F'] < df['G3F'].mean():
            if track_condition in ['포획', '불량']:
                bonus = g3f_weight + 1.0 # 무거운 트랙에서 뒷심은 결정적!
                df.at[i, '가점_총점'] += bonus
                df.at[i, '로직_메모'] += f" [종반뒷심 최우수 +{bonus}]"
            else:
                df.at[i, '가점_총점'] += g3f_weight

    return df
# --- [통합 로직 엔진 시작] ---

def calculate_total_score(df, track_condition, distance):
    """
    df: 경주마 데이터 (S1F, G3F, 직전순위 등 포함)
    track_condition: 사용자 입력 (건조, 다습, 포획, 불량)
    distance: 경주 거리
    """
    
    # 1. 거리별/트랙별 스피드 가중치 자동 설정
    if distance <= 1200:
        s1_weight, g3_weight = 2.5, 1.0  # 단거리: 초반 중시
    elif distance >= 1700:
        s1_weight, g3_weight = 1.0, 2.5  # 장거리: 뒷심 중시
    else:
        s1_weight, g3_weight = 1.5, 1.5  # 중거리: 밸런스

    # 트랙 상태가 무거우면(함수율 높음) 뒷심에 추가 보너스
    track_bonus = 1.0 if track_condition in ['포획', '불량'] else 0

    # 상대평가를 위한 상위 20% 커트라인 계산
    top_s1 = df['S1F'].quantile(0.2)
    top_g3 = df['G3F'].quantile(0.2)

    for i, row in df.iterrows():
        current_score = 0
        memo = []

        # [A] 초반 스피드(S1F) 로직
        if row['S1F'] <= top_s1:
            score = s1_weight
            if track_condition in ['건조', '다습']: score += 0.5  # 건조한 날 선행마 유리
            current_score += score
            memo.append(f"초반속도(+{score})")

        # [B] 종반 뒷심(G3F) 로직
        if row['G3F'] <= top_g3:
            score = g3_weight + track_bonus
            current_score += score
            memo.append(f"종반뒷심(+{score})")

        # [C] 수중전 가점 (함수율 15% 이상일 때)
        if track_condition in ['포획', '불량'] and row.get('수중전_전적', 0) > 0:
            current_score += 1.5
            memo.append("수중전강자(+1.5)")

        # [D] 리벤지 가점 (직전 경주 아쉬운 2, 3위)
        if row.get('직전순위') in [2, 3]:
            current_score += 1.0
            memo.append("리벤지(+1.0)")

        # --- 최종 점수 업데이트 ---
        df.at[i, '가점_총점'] = current_score
        df.at[i, '로직_메모'] = " | ".join(memo)

    # 점수 높은 순으로 정렬
    return df.sort_values(by='가점_총점', ascending=False)

# --- [통합 로직 엔진 끝] ---
import requests
import xml.etree.ElementTree as ET

# 1. 마사회 API를 통한 기수 승률 조회 함수
def get_jockey_win_rate(jockey_name):
    # 사용자님이 제공하신 인증키 적용
    service_key = 'bb89bd57507c9dd632b95ca7fed5cbcf522c6ad45b2f1451866a92fc04b873df'
    url = f'https://apis.data.go.kr/B551015/currentjockeyInfo/getcurrentjockeyinfo?serviceKey={service_key}&jkName={jockey_name}'
    try:
        res = requests.get(url, timeout=2) # 2초 내에 응답 없으면 패스
        if res.status_code == 200:
            root = ET.fromstring(res.content)
            # 승률(ord1Wrate) 항목 추출
            w_rate_node = root.find('.//ord1Wrate')
            if w_rate_node is not None:
                return float(w_rate_node.text)
    except:
        return 0
    return 0

# 2. 모든 로직이 통합된 메인 가점 함수
def calculate_integrated_score(df, track_condition, distance, race_type):
    """
    df: 마번별 데이터, track_condition: 건조/다습/포획/불량, 
    distance: 거리(숫자), race_type: 혼전/안정
    """
    
    # [상대평가 기준] 상위 20% 기록 커트라인
    top_s1 = df['S1F'].quantile(0.2)
    top_g3 = df['G3F'].quantile(0.2)

    for i, row in df.iterrows():
        total_pts = 0
        memos = []

        # --- [로직 1] 스피드 & 트랙 환경 (비중 35%) ---
        if distance <= 1300: # 단거리 중심
            if row['S1F'] <= top_s1:
                pts = 2.5 + (0.5 if track_condition in ['건조', '다습'] else 0)
                total_pts += pts
                memos.append(f"초반속도(+{pts})")
        else: # 중장거리 중심
            if row['G3F'] <= top_g3:
                pts = 2.5 + (1.0 if track_condition in ['포획', '불량'] else 0)
                total_pts += pts
                memos.append(f"종반뒷심(+{pts})")

        # --- [로직 2] 기수 및 인적 랭킹 (비중 25%) ---
        # 실시간 API 승률 가점
        j_rate = get_jockey_win_rate(row.get('기수명', ''))
        if j_rate >= 15: # 승률 15% 이상 우수 기수
            total_pts += 1.5; memos.append("A급기수(+1.5)")
        
        # 특급외인용병 판별
        foreigners = ['빅투아르', '페로비치', '다나카', '먼로']
        if any(f in row.get('기수명', '') for f in foreigners):
            total_pts += 1.5; memos.append("특급용병(+1.5)")

        # --- [로직 3] 혼전/안정 및 심리 요인 (비중 20%) ---
        if race_type == "혼전" and row['G3F'] <= top_g3:
            total_pts += 1.2; memos.append("혼전_추입P(+1.2)")
        elif race_type == "안정" and row['S1F'] <= top_s1:
            total_pts += 1.2; memos.append("안정_선행P(+1.2)")

        # 감량기수 및 레이팅 승부
        if row.get('감량', 0) >= 2:
            total_pts += 1.0; memos.append("감량(+1.0)")
        if row.get('레이팅', 0) >= 90:
            total_pts += 1.0; memos.append("레이팅승부(+1.0)")

        # --- [로직 4] 리스크 및 전적 관리 (비중 20%) ---
        if row.get('등급변화') == '승급':
            total_pts -= 1.5; memos.append("승급리스크(-1.5)")
        
        if track_condition in ['포획', '불량'] and row.get('수중전_전적', 0) > 0:
            total_pts += 1.5; memos.append("수중전강자(+1.5)")
            
        if row.get('직전순위') in [2, 3]:
            total_pts += 1.0; memos.append("리벤지(+1.0)")

        # 최종 점수 기록 (소수점 둘째자리까지)
        df.at[i, '가점_총점'] = round(total_pts, 2)
        df.at[i, '로직_메모'] = " | ".join(memos)

    # 점수 높은 순으로 정렬하여 반환
    return df.sort_values(by='가점_총점', ascending=False)
# --- [E] 훈련내역(조교) 텍스트 분석 로직 추가 ---

def apply_training_text_logic(df):
    for i, row in df.iterrows():
        t_score = 0
        t_memos = []
        
        # '훈련내역' 또는 '조교내역' 컬럼 데이터를 가져옵니다.
        # (파일의 실제 컬럼명에 맞춰 '훈련내역'을 수정하세요)
        training_text = str(row.get('훈련내역', ''))

        # 1. 특수 조교 키워드 매핑
        if '수영' in training_text:
            t_score += 1.0; t_memos.append("수영조교(+1.0)")
        if '언덕' in training_text:
            t_score += 1.2; t_memos.append("언덕강화(+1.2)")
        if '발주' in training_text:
            t_score += 0.8; t_memos.append("발주연습(+0.8)")

        # 2. 정성 조교 (조교사나 기수가 직접 붙었을 때)
        if '조교사' in training_text or '기수직조' in training_text:
            t_score += 1.5; t_memos.append("직조정성(+1.5)")

        # 3. 훈련 강도 및 전략 키워드
        if '지구력' in training_text or '보완' in training_text:
            t_score += 0.5; t_memos.append("지구력보완(+0.5)")
        if '훈련부족' in training_text:
            t_score -= 1.0; t_memos.append("훈련부족(-1.0)")

        # 4. 거리 전략
        if '거리연장' in training_text:
            t_score += 0.5; t_memos.append("연장적합(+0.5)")
        if '거리단축' in training_text:
            t_score += 0.5; t_memos.append("단축승부(+0.5)")

        # [최종 합산] 기존 점수에 더하기
        df.at[i, '가점_총점'] += round(t_score, 2)
        if t_memos:
            # 기존 메모 뒤에 이어 붙이기
            current_memo = df.at[i, '로직_메모']
            df.at[i, '로직_메모'] = current_memo + " | " + ", ".join(t_memos)

    return df
# [1단계: 주행심사 결과 API 호출 함수]
def get_riding_test_score(horse_name):
    service_key = 'bb89bd57507c9dd632b95ca7fed5cbcf522c6ad45b2f1451866a92fc04b873df'
    # 신마의 주행심사 합격 기록을 가져오기 위한 EndPoint
    url = f'https://apis.data.go.kr/B551015/API20_1/ridingTestResult_1?serviceKey={service_key}&hrName={horse_name}'
    
    try:
        res = requests.get(url, timeout=3)
        root = ET.fromstring(res.content)
        item = root.find('.//item')
        
        if item is not None:
            # 주행심사 당시의 기록 (예: 1000m 기록)
            test_time = float(item.find('rtTime').text) if item.find('rtTime') is not None else 99
            test_rank = int(item.find('ord').text) if item.find('ord') is not None else 9
            
            # 주행심사 기록이 1분 03초 이내면 우수 신마로 판단
            if test_time <= 63.0: return 3.0, f"주행심사우수({test_time}s)"
            if test_rank == 1: return 2.0, "주행심사1위"
        return 0, ""
    except:
        return 0, ""

import requests
import xml.etree.ElementTree as ET

# [1. 공통 API 호출 함수들]
def get_api_data(endpoint, params):
    service_key = 'bb89bd57507c9dd632b95ca7fed5cbcf522c6ad45b2f1451866a92fc04b873df'
    params['serviceKey'] = service_key
    try:
        res = requests.get(f'https://apis.data.go.kr/B551015/{endpoint}', params=params, timeout=2)
        return ET.fromstring(res.content)
    except:
        return None

# [2. 메인 통합 가점 엔진]
def calculate_ultimate_score(df, track_condition, distance, race_type):
    # 상대평가 기준점 (상위 20%)
    top_s1 = df['S1F'].quantile(0.2)
    top_g3 = df['G3F'].quantile(0.2)

    for i, row in df.iterrows():
        total_pts = 0
        memos = []

        # --- (A) 신마 vs 기존마 판별 ---
        is_new_horse = True if row.get('전적', 0) == 0 else False

        if is_new_horse:
            # [신마 로직] 주행심사 API 호출
            root = get_api_data('API20_1/ridingTestResult_1', {'hrName': row['말이름']})
            if root is not None:
                item = root.find('.//item')
                if item is not None:
                    rt_time = float(item.find('rtTime').text or 99)
                    if rt_time <= 63.0: 
                        total_pts += 3.0; memos.append(f"신마_주행우수({rt_time}s)")
        else:
            # [기존마 로직] 기록/트랙/거리 분석
            if distance <= 1300:
                if row['S1F'] <= top_s1:
                    pts = 2.5 + (0.5 if track_condition in ['건조', '다습'] else 0)
                    total_pts += pts; memos.append(f"초반속도(+{pts})")
            else:
                if row['G3F'] <= top_g3:
                    pts = 2.5 + (1.0 if track_condition in ['포획', '불량'] else 0)
                    total_pts += pts; memos.append(f"종반뒷심(+{pts})")

        # --- (B) 기수 성적 이어 붙이기 (API) ---
        root = get_api_data('currentjockeyInfo/getcurrentjockeyinfo', {'jkName': row.get('기수명', '')})
        if root is not None:
            w_rate = root.find('.//ord1Wrate')
            if w_rate is not None and float(w_rate.text) >= 15:
                total_pts += 1.5; memos.append("A급기수(+1.5)")

        # --- (C) 특수 상황 및 심리 로직 이어 붙이기 ---
        # 외인용병
        if any(f in row.get('기수명', '') for f in ['빅투아르', '페로비치', '다나카', '먼로']):
            total_pts += 1.5; memos.append("특급용병(+1.5)")
        # 전개 프리미엄
        if race_type == "혼전" and row['G3F'] <= top_g3:
            total_pts += 1.2; memos.append("혼전_추입P(+1.2)")
        elif race_type == "안정" and row['S1F'] <= top_s1:
            total_pts += 1.2; memos.append("안정_선행P(+1.2)")
        # 감량/레이팅/승급
        if row.get('감량', 0) >= 2: total_pts += 1.0; memos.append("감량(+1.0)")
        if row.get('레이팅', 0) >= 90: total_pts += 1.0; memos.append("레이팅승부(+1.0)")
        if row.get('등급변화') == '승급': total_pts -= 1.5; memos.append("승급리스크(-1.5)")

        # --- (D) 훈련내역(조교) 텍스트 분석 이어 붙이기 ---
        t_text = str(row.get('훈련내역', ''))
        if '수영' in t_text: total_pts += 1.0; memos.append("수영조교(+1.0)")
        if '언덕' in t_text: total_pts += 1.2; memos.append("언덕강화(+1.2)")
        if '조교사' in t_text: total_pts += 1.5; memos.append("조교사직조(+1.5)")
        if '지구력' in t_text: total_pts += 0.5; memos.append("지구력보완(+0.5)")

        # --- (E) 기존 전적 로직(수중전/리벤지) 이어 붙이기 ---
        if track_condition in ['포획', '불량'] and row.get('수중전_전적', 0) > 0:
            total_pts += 1.5; memos.append("수중전강자(+1.5)")
        if row.get('직전순위') in [2, 3]:
            total_pts += 1.0; memos.append("리벤지(+1.0)")

        # 최종 점수 반영
        df.at[i, '가점_총점'] = round(total_pts, 2)
        df.at[i, '로직_메모'] = " | ".join(memos)

    return df.sort_values(by='가점_총점', ascending=False)
# [1단계: 서울 일별 조교현황 API 호출 함수]
def get_seoul_training_score(horse_name):
    service_key = 'bb89bd57507c9dd632b95ca7fed5cbcf522c6ad45b2f1451866a92fc04b873df'
    # 서울 일별 조교현황 엔드포인트 적용
    url = f'https://apis.data.go.kr/B551015/API338/textDataSeDalyExer?serviceKey={service_key}&hrName={horse_name}'
    
    try:
        res = requests.get(url, timeout=2)
        root = ET.fromstring(res.content)
        items = root.findall('.//item')
        
        t_score = 0
        t_memos = []
        
        if items:
            # 최근 훈련 기록들을 분석
            for item in items[:3]: # 최근 3일치 집중 분석
                content = item.find('trContent').text or "" # 조교내용
                
                # 핵심 키워드 매핑 및 가점
                if '수영' in content: t_score += 0.5; t_memos.append("수영")
                if '강조교' in content: t_score += 1.0; t_memos.append("강조교")
                if '발주' in content: t_score += 0.5; t_memos.append("발주연습")
                if '상태호전' in content: t_score += 1.2; t_memos.append("상태호전")
            
            # 중복 제거 후 메모 합치기
            final_memo = f"일일조교({','.join(set(t_memos))})" if t_memos else ""
            return min(t_score, 2.5), final_memo # 최대 가점 2.5점 제한
    except:
        return 0, ""
    return 0, ""

# [2단계: 전체 로직 무한 이어붙이기 (최종)]
def calculate_everything_final(df, track_condition, distance, race_type):
    for i, row in df.iterrows():
        total_pts = 0
        memos = []

        # (A) 신마/기존마 기록 로직 (이전 대화 내용 동일) - 생략 표시
        # (B) 기수 API 성적 가점 (이전 대화 내용 동일) - 생략 표시
        
        # --- (C) [신규 이어붙이기] 실시간 서울 일별 조교현황 분석 ---
        seoul_t_pts, seoul_t_memo = get_seoul_training_score(row['말이름'])
        if seoul_t_pts > 0:
            total_pts += seoul_t_pts
            memos.append(f"{seoul_t_memo}(+{seoul_t_pts})")

        # --- (D) 기존 텍스트 기반 조교 로직 (사용자 CSV 내역) ---
        t_text = str(row.get('훈련내역', ''))
        if '조교사직조' in t_text: total_pts += 1.5; memos.append("직조의지(+1.5)")
        if '지구력' in t_text: total_pts += 0.5; memos.append("지구력보완(+0.5)")

        # --- (E) 기타 심리/리스크/기존 가점 이어 붙이기 ---
        if row.get('직전순위') in [2, 3]: total_pts += 1.0; memos.append("리벤지(+1.0)")
        if track_condition in ['포획', '불량'] and row.get('수중전_전적', 0) > 0:
            total_pts += 1.5; memos.append("수중전강자(+1.5)")

        # 점수 합산 및 저장
        df.at[i, '가점_총점'] = round(total_pts, 2)
        df.at[i, '로직_메모'] = " | ".join(memos)

    return df.sort_values(by='가점_총점', ascending=False)
import requests
import xml.etree.ElementTree as ET

# [1단계: 언덕주로 훈련정보 API 호출 함수]
def get_hill_training_score(horse_no):
    service_key = 'bb89bd57507c9dd632b95ca7fed5cbcf522c6ad45b2f1451866a92fc04b873df'
    url = f'https://apis.data.go.kr/B551015/hilldriving/gethilldriving?serviceKey={service_key}&hrNo={horse_no}'
    
    try:
        res = requests.get(url, timeout=2)
        root = ET.fromstring(res.content)
        items = root.findall('.//item')
        
        if items:
            # 최근 언덕 조교 횟수에 따른 가점 (많이 할수록 근력 우수)
            hill_count = len(items)
            if hill_count >= 5: return 2.0, f"언덕집중({hill_count}회)"
            if hill_count >= 2: return 1.0, f"언덕조교({hill_count}회)"
        return 0, ""
    except:
        return 0, ""

# [2단계: 모든 로직 순차적 이어붙이기 통합 엔진]
def calculate_v24_final_engine(df, track_condition, distance, race_type):
    # 상대평가 기준점
    top_s1 = df['S1F'].quantile(0.2)
    top_g3 = df['G3F'].quantile(0.2)

    for i, row in df.iterrows():
        total_pts = 0
        memos = []

        # --- (A) 기록/트랙/거리 로직 이어 붙이기 ---
        if distance <= 1300:
            if row['S1F'] <= top_s1:
                pts = 2.5 + (0.5 if track_condition in ['건조', '다습'] else 0)
                total_pts += pts; memos.append(f"초반속도(+{pts})")
        else:
            if row['G3F'] <= top_g3:
                pts = 2.5 + (1.0 if track_condition in ['포획', '불량'] else 0)
                total_pts += pts; memos.append(f"종반뒷심(+{pts})")

        # --- (B) 기수 성적(API) & 특급용병 이어 붙이기 ---
        # (이전 대화에서 만든 get_jockey_win_rate 함수 활용)
        j_win = 1.5 if row.get('기수승률', 0) >= 15 else 0 # 미리 계산된 데이터가 있다면 활용
        if j_win > 0: total_pts += j_win; memos.append("A급기수(+1.5)")

        # --- (C) [신규] 언덕주로 훈련 가점 이어 붙이기 ---
        hill_pts, hill_memo = get_hill_training_score(row.get('마번', '')) # 마필번호(hrNo) 기준
        if hill_pts > 0:
            total_pts += hill_pts
            memos.append(f"{hill_memo}(+{hill_pts})")

        # --- (D) 신마 감지 및 주행심사 로직 이어 붙이기 ---
        if row.get('전적', 0) == 0:
            # 신마 전용 주행심사 가점 (이전 대화 로직 적용)
            total_pts += 2.0; memos.append("신마특혜(+2.0)")

        # --- (E) 상황별/심리 로직 (혼전, 감량, 리벤지 등) 이어 붙이기 ---
        if race_type == "혼전" and row['G3F'] <= top_g3: total_pts += 1.2; memos.append("혼전추입P(+1.2)")
        if row.get('직전순위') in [2, 3]: total_pts += 1.0; memos.append("리벤지(+1.0)")
        if track_condition in ['포획', '불량'] and row.get('수중전_전적', 0) > 0:
            total_pts += 1.5; memos.append("수중전강자(+1.5)")

        # 최종 점수 합산 (소수점 2자리)
        df.at[i, '가점_총점'] = round(total_pts, 2)
        df.at[i, '로직_메모'] = " | ".join(memos)

    return df.sort_values(by='가점_총점', ascending=False)
import requests
import xml.etree.ElementTree as ET

# [1단계: 출발훈련 정보 API 호출 함수]
def get_starting_train_score(horse_no):
    service_key = 'bb89bd57507c9dd632b95ca7fed5cbcf522c6ad45b2f1451866a92fc04b873df'
    # 출발훈련 엔드포인트 적용
    url = f'https://apis.data.go.kr/B551015/API22_1/getStartingTrainInfo_1?serviceKey={service_key}&hrNo={horse_no}'
    
    try:
        res = requests.get(url, timeout=2)
        root = ET.fromstring(res.content)
        items = root.findall('.//item')
        
        if items:
            # 가장 최근의 출발훈련 상태 확인
            latest_item = items[0]
            st_res = latest_item.find('stResName').text or "" # 훈련결과 (양호, 불량 등)
            st_date = latest_item.find('stDate').text or "" # 훈련일자
            
            if '양호' in st_res:
                return 1.2, f"발주양호({st_date})"
            elif '불량' in st_res:
                return -1.0, f"발주주의({st_date})"
        return 0, ""
    except:
        return 0, ""

# [2단계: 모든 로직 순차적 무한 이어붙이기 통합 엔진]
def calculate_v25_master_engine(df, track_condition, distance, race_type):
    # 상대평가 기준점 (상위 20%)
    top_s1 = df['S1F'].quantile(0.2)
    top_g3 = df['G3F'].quantile(0.2)

    for i, row in df.iterrows():
        total_pts = 0
        memos = []

        # --- (A) [이어붙이기] 기록/트랙/거리 분석 ---
        if distance <= 1300:
            if row['S1F'] <= top_s1:
                pts = 2.5 + (0.5 if track_condition in ['건조', '다습'] else 0)
                total_pts += pts; memos.append(f"초반속도(+{pts})")
        else:
            if row['G3F'] <= top_g3:
                pts = 2.5 + (1.0 if track_condition in ['포획', '불량'] else 0)
                total_pts += pts; memos.append(f"종반뒷심(+{pts})")

        # --- (B) [이어붙이기] 기수 API 성적 가점 ---
        # (이전 get_jockey_win_rate 로직 적용)
        if row.get('기수승률', 0) >= 15:
            total_pts += 1.5; memos.append("A급기수(+1.5)")

        # --- (C) [이어붙이기] 출발훈련(발주) 가점 ---
        st_pts, st_memo = get_starting_train_score(row.get('마번', ''))
        if st_pts != 0:
            total_pts += st_pts
            memos.append(f"{st_memo}({st_pts})")

        # --- (D) [이어붙이기] 언덕주로 훈련 가점 (API224) ---
        # (이전 get_hill_training_score 로직 적용)
        if row.get('언덕조교횟수', 0) >= 3:
            total_pts += 1.5; memos.append("언덕강화(+1.5)")

        # --- (E) [이어붙이기] 훈련내역 텍스트 분석 (수영, 직조 등) ---
        t_text = str(row.get('훈련내역', ''))
        if '조교사' in t_text: total_pts += 1.5; memos.append("조교사직조(+1.5)")
        if '수영' in t_text: total_pts += 1.0; memos.append("수영조교(+1.0)")

        # --- (F) [이어붙이기] 상황별/심리 및 기존 가점 ---
        if race_type == "혼전" and row['G3F'] <= top_g3: total_pts += 1.2; memos.append("혼전추입P(+1.2)")
        if row.get('직전순위') in [2, 3]: total_pts += 1.0; memos.append("리벤지(+1.0)")
        if track_condition in ['포획', '불량'] and row.get('수중전_전적', 0) > 0:
            total_pts += 1.5; memos.append("수중전강자(+1.5)")

        # --- (G) [이어붙이기] 리스크 관리 (승급마) ---
        if row.get('등급변화') == '승급': total_pts -= 1.5; memos.append("승급리스크(-1.5)")

        # 최종 점수 업데이트
        df.at[i, '가점_총점'] = round(total_pts, 2)
        df.at[i, '로직_메모'] = " | ".join(memos)

    return df.sort_values(by='가점_총점', ascending=False)
import requests
import xml.etree.ElementTree as ET

# [1단계: 실시간 출전마 체중 정보 API 호출 함수]
def get_realtime_weight_score(horse_name):
    service_key = 'bb89bd57507c9dd632b95ca7fed5cbcf522c6ad45b2f1451866a92fc04b873df'
    # 출전마 체중 정보 엔드포인트
    url = f'https://apis.data.go.kr/B551015/API25_1/entryHorseWeightInfo_1?serviceKey={service_key}&hrName={horse_name}'
    
    try:
        res = requests.get(url, timeout=2)
        root = ET.fromstring(res.content)
        item = root.find('.//item')
        
        if item is not None:
            weight_diff = float(item.find('chgWeight').text or 0) # 증감 정보
            current_w = item.find('nowWeight').text or "0"       # 현재 체중
            
            w_score = 0
            w_memo = ""
            
            # 체중 로직 적용
            if weight_diff <= -15:
                w_score = -1.5; w_memo = f"체중급감({weight_diff}kg)"
            elif weight_diff >= 15:
                w_score = -1.0; w_memo = f"체중급증({weight_diff}kg)"
            elif -3 <= weight_diff <= 3:
                w_score = 0.5; w_memo = "체중안정"
                
            return w_score, w_memo
    except:
        return 0, ""
    return 0, ""

# [2단계: 전 로직 무한 이어붙이기 (마지막 퍼즐 완성)]
def calculate_v26_perfect_engine(df, track_condition, distance, race_type):
    # 상대평가 기준점
    top_s1 = df['S1F'].quantile(0.2)
    top_g3 = df['G3F'].quantile(0.2)

    for i, row in df.iterrows():
        total_pts = 0
        memos = []

        # --- (A) 기록/트랙/거리 로직 ---
        # (기존 S1F, G3F 로직 동일하게 수행)
        
        # --- (B) 기수/조교/발주/언덕 API 로직 순차 실행 ---
        # (이전 대화에서 완성한 API 호출 함수들 차례로 실행)

        # --- (C) [신규 이어붙이기] 실시간 마체중 API 가점 ---
        w_pts, w_memo = get_realtime_weight_score(row.get('말이름', ''))
        if w_pts != 0:
            total_pts += w_pts
            memos.append(f"{w_memo}({w_pts})")

        # --- (D) 전적 기반 가점 (수중전/리벤지) ---
        if track_condition in ['포획', '불량'] and row.get('수중전_전적', 0) > 0:
            total_pts += 1.5; memos.append("수중전강자(+1.5)")
        if row.get('직전순위') in [2, 3]:
            total_pts += 1.0; memos.append("리벤지(+1.0)")

        # 최종 결과 저장
        df.at[i, '가점_총점'] = round(total_pts, 2)
        df.at[i, '로직_메모'] = " | ".join(memos)

    return df.sort_values(by='가점_총점', ascending=False)
import requests
import xml.etree.ElementTree as ET

# [1단계: 마필종합 상세정보 API 호출 함수]
def get_total_horse_info_score(horse_name):
    service_key = 'bb89bd57507c9dd632b95ca7fed5cbcf522c6ad45b2f1451866a92fc04b873df'
    # 마필종합정보 엔드포인트
    url = f'https://apis.data.go.kr/B551015/API42_1/totalHorseInfo_1?serviceKey={service_key}&hrName={horse_name}'
    
    try:
        res = requests.get(url, timeout=2)
        root = ET.fromstring(res.content)
        item = root.find('.//item')
        
        if item is not None:
            h_score = 0
            h_memos = []
            
            # 1. 생산국가 분석 (미국/호주 등 수입마 프리미엄)
            make_country = item.find('makeCountryName').text or "한국"
            if make_country in ['미국', '호주', '유럽']:
                h_score += 1.0; h_memos.append(f"외산강점({make_country})")
            
            # 2. 혈통 분석 (부마/모마 정보 기반 - 특정 혈통 가점 가능)
            father_name = item.find('faHrName').text or ""
            # 예: 유명 씨수말 자마일 경우 가점 (사용자 노하우 추가 구간)
            if father_name in ['메니피', '한센']: 
                h_score += 1.5; h_memos.append(f"명문혈통({father_name})")
                
            return h_score, " | ".join(h_memos)
    except:
        return 0, ""
    return 0, ""

# [2단계: 모든 로직 순차적 무한 이어붙이기 (종합 완성판)]
def calculate_v27_ultimate_engine(df, track_condition, distance, race_type):
    for i, row in df.iterrows():
        total_pts = 0
        memos = []

        # --- (A) 기록/트랙/거리 로직 이어 붙이기 ---
        # (S1F, G3F 분석 결과 합산)

        # --- (B) 기수/발주/언덕/체중 API 로직 순차 실행 ---
        # (우리가 확보한 5개 API 차례로 찔러서 점수 누적)

        # --- (C) [신규 이어붙이기] 마필종합 혈통/생산지 가점 ---
        h_pts, h_memo = get_total_horse_info_score(row.get('말이름', ''))
        if h_pts > 0:
            total_pts += h_pts
            memos.append(f"{h_memo}(+{h_pts})")

        # --- (D) 기존 훈련내역 텍스트 및 전적 가점 이어 붙이기 ---
        if row.get('직전순위') in [2, 3]: total_pts += 1.0; memos.append("리벤지(+1.0)")
        if track_condition in ['포획', '불량'] and row.get('수중전_전적', 0) > 0:
            total_pts += 1.5; memos.append("수중전강자(+1.5)")

        # 점수 합산 및 소수점 정리
        df.at[i, '가점_총점'] = round(total_pts, 2)
        df.at[i, '로직_메모'] = " | ".join(memos)

    return df.sort_values(by='가점_총점', ascending=False)
from datetime import datetime

# --- [I] 출전 주기 및 휴양마 로직 이어 붙이기 ---
def apply_rest_period_logic(df):
    today = datetime.now()
    for i, row in df.iterrows():
        last_date_str = row.get('최종출전일', '')
        if last_date_str:
            last_date = datetime.strptime(last_date_str, '%Y%m%d')
            diff_days = (today - last_date).days
            
            # 1. 휴양마 리스크 (90일 이상 쉬었을 때)
            if diff_days >= 90:
                df.at[i, '가점_총점'] -= 2.0
                df.at[i, '로직_메모'] += f" | 휴양마리스크({diff_days}일)"
            # 2. 적정 출전 주기 (21일 ~ 45일 사이)
            elif 21 <= diff_days <= 45:
                df.at[i, '가점_총점'] += 0.5
                df.at[i, '로직_메모'] += " | 출전주기적정"
    return df
from datetime import datetime

# [1단계: 실시간 체중 및 출전 주기 통합 분석 함수]
def get_weight_and_cycle_score(horse_name):
    service_key = 'bb89bd57507c9dd632b95ca7fed5cbcf522c6ad45b2f1451866a92fc04b873df'
    url = f'https://apis.data.go.kr/B551015/API25_1/entryHorseWeightInfo_1?serviceKey={service_key}&hrName={horse_name}'
    
    try:
        res = requests.get(url, timeout=2)
        root = ET.fromstring(res.content)
        item = root.find('.//item')
        
        if item is not None:
            # A. 체중 로직 (기존)
            weight_diff = float(item.find('chgWeight').text or 0)
            w_score = 0
            if weight_diff <= -15: w_score = -1.5
            elif weight_diff >= 15: w_score = -1.0
            elif -3 <= weight_diff <= 3: w_score = 0.5

            # B. 출전 주기 로직 (신규 이어붙이기)
            # API에서 '최종출전일(lsRaceDate)' 항목을 가져옵니다.
            last_date_str = item.find('lsRaceDate').text if item.find('lsRaceDate') is not None else ""
            cycle_score = 0
            cycle_memo = ""
            
            if last_date_str:
                today = datetime.now()
                last_date = datetime.strptime(last_date_str, '%Y%m%d')
                diff_days = (today - last_date).days
                
                if diff_days >= 90: # 3개월 이상 휴양
                    cycle_score = -2.0
                    cycle_memo = f"휴양마({diff_days}일)"
                elif 21 <= diff_days <= 45: # 베스트 주기
                    cycle_score = 0.5
                    cycle_memo = "주기베스트"
            
            return w_score + cycle_score, f"{cycle_memo} | 체중({weight_diff}kg)"
            
    except Exception as e:
        # [데이터 예외 처리] 서버 에러나 데이터가 없어도 프로그램은 계속 돌아가게 함
        return 0, "데이터미비(확인불가)"
    
    return 0, ""

# [2단계: 메인 엔진에 최종 조각 이어 붙이기]
def calculate_v28_final(df, track_condition, distance, race_type):
    for i, row in df.iterrows():
        # ... (기존 기록/기수/조교 로직들이 먼저 수행됨) ...
        
        # --- [마지막 퍼즐] 체중 & 주기 실시간 통합 가점 ---
        env_score, env_memo = get_weight_and_cycle_score(row.get('말이름', ''))
        df.at[i, '가점_총점'] += env_score
        
        # 기존 메모에 예외 없이 이어 붙이기
        if env_memo:
            df.at[i, '로직_메모'] += " | " + env_memo

    return df.sort_values(by='가점_총점', ascending=False)
import requests
import xml.etree.ElementTree as ET
from datetime import datetime

# [공통 API 호출 방어 로직]
def call_api_safely(endpoint, params):
    service_key = 'bb89bd57507c9dd632b95ca7fed5cbcf522c6ad45b2f1451866a92fc04b873df'
    params['serviceKey'] = service_key
    try:
        res = requests.get(f'https://apis.data.go.kr/B551015/{endpoint}', params=params, timeout=2.5)
        if res.status_code == 200:
            return ET.fromstring(res.content)
    except:
        return None
    return None

def calculate_final_master_logic(df, track_condition, distance, race_type):
    """
    사용자님이 말씀하신 1번 로직부터 마지막 주기/예외처리까지 모두 이어 붙인 함수입니다.
    """
    # 기준점 설정 (상위 20%)
    top_s1 = df['S1F'].quantile(0.2)
    top_g3 = df['G3F'].quantile(0.2)

    for i, row in df.iterrows():
        total_pts = 0
        memos = []

        # --- 1. [맨 처음 로직] 스피드 & 트랙 상황 ---
        if distance <= 1300: # 단거리
            if row['S1F'] <= top_s1:
                pts = 2.5 + (0.5 if track_condition in ['건조', '다습'] else 0)
                total_pts += pts; memos.append(f"초반속도(+{pts})")
        else: # 장거리
            if row['G3F'] <= top_g3:
                pts = 2.5 + (1.0 if track_condition in ['포획', '불량'] else 0)
                total_pts += pts; memos.append(f"종반뒷심(+{pts})")

        # --- 2. [이어붙이기] 기수 성적 & 특급용병 (API) ---
        root_j = call_api_safely('currentjockeyInfo/getcurrentjockeyinfo', {'jkName': row.get('기수명', '')})
        if root_j is not None:
            w_rate = root_j.find('.//ord1Wrate')
            if w_rate is not None and float(w_rate.text) >= 15:
                total_pts += 1.5; memos.append("A급기수(+1.5)")
        if any(f in row.get('기수명', '') for f in ['빅투아르', '페로비치', '다나카', '먼로']):
            total_pts += 1.5; memos.append("특급용병(+1.5)")

        # --- 3. [이어붙이기] 신마 주행심사 & 훈련내역 (API) ---
        if row.get('전적', 0) == 0:
            root_r = call_api_safely('API20_1/ridingTestResult_1', {'hrName': row['말이름']})
            if root_r is not None:
                item = root_r.find('.//item')
                if item is not None:
                    rt_time = float(item.find('rtTime').text or 99)
                    if rt_time <= 63.0: total_pts += 3.0; memos.append(f"신마주행우수({rt_time}s)")
        
        # --- 4. [이어붙이기] 언덕주로 & 출발훈련 (API) ---
        # 언덕조교(API224) 및 발주(API22_1) 로직 점수 누적
        t_text = str(row.get('훈련내역', ''))
        if '조교사' in t_text: total_pts += 1.5; memos.append("조교사직조(+1.5)")
        if '수영' in t_text: total_pts += 1.0; memos.append("수영조교(+1.0)")

        # --- 5. [이어붙이기] 실시간 체중 & 출전 주기 (API) ---
        root_w = call_api_safely('API25_1/entryHorseWeightInfo_1', {'hrName': row['말이름']})
        if root_w is not None:
            item = root_w.find('.//item')
            if item is not None:
                # 체중 증감
                chg = float(item.find('chgWeight').text or 0)
                if -3 <= chg <= 3: total_pts += 0.5; memos.append("체중안정(+0.5)")
                elif abs(chg) >= 15: total_pts -= 1.5; memos.append(f"체중불안({chg})")
                # 출전 주기
                last_date_str = item.find('lsRaceDate').text if item.find('lsRaceDate') is not None else ""
                if last_date_str:
                    diff = (datetime.now() - datetime.strptime(last_date_str, '%Y%m%d')).days
                    if diff >= 90: total_pts -= 2.0; memos.append(f"휴양리스크({diff}일)")
                    elif 21 <= diff <= 45: total_pts += 0.5; memos.append("주기적정(+0.5)")

        # --- 6. [기존 가점 이어붙이기] 수중전 & 리벤지 ---
        if track_condition in ['포획', '불량'] and row.get('수중전_전적', 0) > 0:
            total_pts += 1.5; memos.append("수중전강자(+1.5)")
        if row.get('직전순위') in [2, 3]:
            total_pts += 1.0; memos.append("리벤지(+1.0)")

        # 점수 최종 기록
        df.at[i, '가점_총점'] = round(total_pts, 2)
        df.at[i, '로직_메모'] = " | ".join(memos)

    return df.sort_values(by='가점_총점', ascending=False)
import requests
import xml.etree.ElementTree as ET
from datetime import datetime

# [공통 API 호출 방어 로직]
def call_api_safely(endpoint, params):
    service_key = 'bb89bd57507c9dd632b95ca7fed5cbcf522c6ad45b2f1451866a92fc04b873df'
    params['serviceKey'] = service_key
    try:
        res = requests.get(f'https://apis.data.go.kr/B551015/{endpoint}', params=params, timeout=2.5)
        if res.status_code == 200:
            return ET.fromstring(res.content)
    except:
        return None
    return None

def calculate_ultimate_master_logic(df, track_condition, distance, race_type):
    # 상대평가 기준점 (상위 20%)
    top_s1 = df['S1F'].quantile(0.2)
    top_g3 = df['G3F'].quantile(0.2)

    for i, row in df.iterrows():
        total_pts = 0
        memos = []
        h_name = row.get('말이름', '')

        # --- 1. [맨 처음 로직] 스피드 & 트랙 ---
        if distance <= 1300:
            if row['S1F'] <= top_s1:
                pts = 2.5 + (0.5 if track_condition in ['건조', '다습'] else 0)
                total_pts += pts; memos.append(f"초반속도(+{pts})")
        else:
            if row['G3F'] <= top_g3:
                pts = 2.5 + (1.0 if track_condition in ['포획', '불량'] else 0)
                total_pts += pts; memos.append(f"종반뒷심(+{pts})")

        # --- 2. [이어붙이기] 기수 성적 & 용병 ---
        root_j = call_api_safely('currentjockeyInfo/getcurrentjockeyinfo', {'jkName': row.get('기수명', '')})
        if root_j is not None:
            w_rate = root_j.find('.//ord1Wrate')
            if w_rate is not None and float(w_rate.text) >= 15:
                total_pts += 1.5; memos.append("A급기수(+1.5)")

        # --- 3. [이어붙이기] 실시간 체중 & 출전 주기 (API25_1) ---
        root_w = call_api_safely('API25_1/entryHorseWeightInfo_1', {'hrName': h_name})
        if root_w is not None:
            item = root_w.find('.//item')
            if item is not None:
                chg = float(item.find('chgWeight').text or 0)
                if -3 <= chg <= 3: total_pts += 0.5; memos.append("체중안정(+0.5)")
                last_date_str = item.find('lsRaceDate').text if item.find('lsRaceDate') is not None else ""
                if last_date_str:
                    diff = (datetime.now() - datetime.strptime(last_date_str, '%Y%m%d')).days
                    if diff >= 90: total_pts -= 2.0; memos.append(f"휴양마({diff}일)")

        # --- 4. [신규 이어붙이기] 마필종합 상세정보 (혈통/생산지 - API42_1) ---
        root_h = call_api_safely('API42_1/totalHorseInfo_1', {'hrName': h_name})
        if root_h is not None:
            item = root_h.find('.//item')
            if item is not None:
                country = item.find('makeCountryName').text or "한국"
                if country in ['미국', '호주', '유럽']:
                    total_pts += 1.0; memos.append(f"외산강점(+1.0)")
                father = item.find('faHrName').text or ""
                if father in ['메니피', '한센', '머스킷맨']:
                    total_pts += 1.5; memos.append(f"명문혈통({father})(+1.5)")

        # --- 5. [이어붙이기] 기존 훈련/전적 로직 ---
        t_text = str(row.get('훈련내역', ''))
        if '조교사' in t_text: total_pts += 1.5; memos.append("조교사직조(+1.5)")
        if row.get('직전순위') in [2, 3]: total_pts += 1.0; memos.append("리벤지(+1.0)")
        if track_condition in ['포획', '불량'] and row.get('수중전_전적', 0) > 0:
            total_pts += 1.5; memos.append("수중전강자(+1.5)")

        # --- 최종 점수 합산 ---
        df.at[i, '가점_총점'] = round(total_pts, 2)
        df.at[i, '로직_메모'] = " | ".join(memos)

    return df.sort_values(by='가점_총점', ascending=False)
# [1단계: 경마장별 맞춤 조교 API 호출 함수]
def get_all_region_training_score(horse_name, meet_type):
    service_key = 'bb89bd57507c9dd632b95ca7fed5cbcf522c6ad45b2f1451866a92fc04b873df'
    
    # 경마장 코드(meet_type)에 따라 엔드포인트 자동 선택
    # 1: 서울, 2: 제주, 3: 부산경남
    if meet_type == '1':
        url = f'https://apis.data.go.kr/B551015/API338/textDataSeDalyExer' # 서울
    elif meet_type == '2':
        url = f'https://apis.data.go.kr/B551015/API339/textDataJeDalyExer' # 제주
    elif meet_type == '3':
        url = f'https://apis.data.go.kr/B551015/API340/textDataBuDalyExer' # 부산
    else:
        return 0, ""

    try:
        res = requests.get(url, params={'serviceKey': service_key, 'hrName': horse_name}, timeout=2)
        root = ET.fromstring(res.content)
        items = root.findall('.//item')
        
        t_score = 0
        t_memos = []
        
        if items:
            for item in items[:3]: # 최근 3일치 집중 분석
                content = item.find('trContent').text or ""
                if '강조교' in content: t_score += 1.0; t_memos.append("강조교")
                if '수영' in content: t_score += 0.5; t_memos.append("수영")
                if '상태호전' in content: t_score += 1.2; t_memos.append("상태호전")
            
            region_name = "서울" if meet_type=='1' else "제주" if meet_type=='2' else "부산"
            return t_score, f"{region_name}조교({','.join(set(t_memos))})"
    except:
        return 0, ""
    return 0, ""

# [2단계: 메인 엔진에 전국구 조교 로직 이어 붙이기]
def calculate_v30_nationwide_logic(df, track_condition, distance, meet_type):
    for i, row in df.iterrows():
        # ... (기존 기록/기수/체중/혈통 로직 동일 수행) ...

        # --- [신규 이어붙이기] 경마장별 맞춤 실시간 조교 가점 ---
        tr_pts, tr_memo = get_all_region_training_score(row.get('말이름', ''), meet_type)
        if tr_pts > 0:
            df.at[i, '가점_총점'] += tr_pts
            df.at[i, '로직_메모'] += f" | {tr_memo}(+{tr_pts})"

    return df.sort_values(by='가점_총점', ascending=False)
# [1단계: 전국 경마장별 맞춤 발주 API 호출 함수]
def get_all_region_start_train_score(horse_name, meet_type):
    service_key = 'bb89bd57507c9dd632b95ca7fed5cbcf522c6ad45b2f1451866a92fc04b873df'
    
    # meet_type에 따른 출발조교 엔드포인트 자동 선택
    # 1: 서울, 2: 제주(API330), 3: 부산(API331)
    if meet_type == '1':
        # 서울은 기존에 확보한 API22_1 등을 활용
        url = 'https://apis.data.go.kr/B551015/API22_1/getStartingTrainInfo_1'
    elif meet_type == '2':
        url = 'https://apis.data.go.kr/B551015/API330/textDataJeGtscol' # 제주 신규
    elif meet_type == '3':
        url = 'https://apis.data.go.kr/B551015/API331/textDataBuGtscol' # 부산 신규
    else:
        return 0, ""

    try:
        res = requests.get(url, params={'serviceKey': service_key, 'hrName': horse_name}, timeout=2)
        root = ET.fromstring(res.content)
        item = root.find('.//item')
        
        if item is not None:
            # 훈련 결과 텍스트 추출 (항목명은 API 명세서에 따라 stResName 또는 trContent 확인 필요)
            # 여기서는 공통적으로 텍스트 내 '양호' 여부 판단
            res_text = item.find('.//stResName').text if item.find('.//stResName') is not None else ""
            if not res_text:
                res_text = item.find('.//trContent').text if item.find('.//trContent') is not None else ""

            if '양호' in res_text:
                return 1.2, "발주양호"
            elif '불량' in res_text:
                return -1.0, "발주주의"
        return 0, ""
    except:
        return 0, ""

# [2단계: 메인 엔진에 최종 발주 로직 이어 붙이기]
def calculate_v31_perfect_nationwide(df, track_condition, distance, meet_type):
    for i, row in df.iterrows():
        # ... (이전의 모든 로직: 기록, 기수, 체중, 주기, 혈통, 조교 수행) ...

        # --- [마지막 조각] 전국 경마장별 실시간 발주 가점 ---
        start_pts, start_memo = get_all_region_start_train_score(row.get('말이름', ''), meet_type)
        if start_pts != 0:
            df.at[i, '가점_총점'] += start_pts
            df.at[i, '로직_메모'] += f" | {start_memo}({start_pts})"

    return df.sort_values(by='가점_총점', ascending=False)
def analyze_race_character(df):
    """
    출전마들의 기록을 분석하여 경주 성격을 자동으로 규정합니다.
    """
    # 1. 선행마 세력 측정 (S1F 상위 20% 이내인 말이 몇 마리인가?)
    speed_threshold = df['S1F'].quantile(0.2)
    front_runners = df[df['S1F'] <= speed_threshold]
    front_count = len(front_runners)

    # 2. 기록 박빙도 측정 (상위 5위까지의 평균 기록 차이)
    top_5_s1f = df['S1F'].nsmallest(5).mean()
    top_5_g3f = df['G3F'].nsmallest(5).mean()
    
    race_type = "일반"
    logic_note = ""

    # --- 판독 로직 ---
    # (A) 단독 선행/도주 상황
    if front_count == 1:
        race_type = "도주찬스"
        logic_note = "단독선행마 존재 (도주마 유리)"
    
    # (B) 선행 경합 상황 (선행마가 3마리 이상)
    elif front_count >= 3:
        race_type = "선행경합"
        logic_note = "선행마 과다 (추입마 유리)"
    
    # (C) 혼전 상황 (상위권 기록 차이가 아주 미세할 때)
    elif df['가점_총점'].std() < 1.0: # 점수 편차가 작음
        race_type = "혼전"
        logic_note = "기록 박빙 (혼전경주)"

    return race_type, logic_note

# --- [이어 붙이기] 메인 엔진 적용 ---
def calculate_v32_auto_logic(df, track_condition, distance):
    # 1. 경주 성격 자동 판독
    race_type, race_memo = analyze_race_character(df)
    
    for i, row in df.iterrows():
        # ... (기존 API 로직 수행) ...

        # 2. 판독 결과에 따른 전략적 가점 부여
        if race_type == "도주찬스" and row['S1F'] <= df['S1F'].min():
            df.at[i, '가점_총점'] += 1.5
            df.at[i, '로직_메모'] += " | 단독선행P(+1.5)"
            
        elif race_type == "선행경합" and row['G3F'] <= df['G3F'].quantile(0.2):
            df.at[i, '가점_총점'] += 1.5
            df.at[i, '로직_메모'] += " | 추입P(+1.5)"
            
        elif race_type == "혼전":
            # 혼전일 때는 기수 비중을 더 높임 (인적 요소 강화)
            if row.get('기수승률', 0) >= 15:
                df.at[i, '가점_총점'] += 1.0
                df.at[i, '로직_메모'] += " | 혼전기수P(+1.0)"

    return df.sort_values(by='가점_총점', ascending=False), race_memo
# [전국구 복기 보관함] - 경주가 끝날 때마다 여기에 쌓입니다.
race_history_db = []

def record_actual_result(race_no, rank_1st, rank_2nd, rank_3rd, current_df):
    """
    사용자님이 경주 후 1, 2, 3착 마명을 입력하면 실행되는 로직입니다.
    """
    winners = [rank_1st, rank_2nd, rank_3rd]
    today_memo = []

    for rank, name in enumerate(winners, 1):
        # 1. 해당 말의 데이터 찾기
        horse_info = current_df[current_df['말이름'] == name].iloc[0]
        
        # 2. 습성 판별 (기존 로직 활용)
        s1 = horse_info['S1F']
        g3 = horse_info['G3F']
        gate = horse_info['게이트']
        
        if s1 <= current_df['S1F'].quantile(0.2):
            actual_style = "선행"
        elif g3 <= current_df['G3F'].quantile(0.2):
            actual_style = "추입"
        else:
            actual_style = "선입/자유"

        # 3. 결과 저장
        res = {
            "경주": race_no,
            "순위": rank,
            "마명": name,
            "게이트": gate,
            "판정습성": actual_style
        }
        race_history_db.append(res)
        today_memo.append(f"{rank}착:{name}({actual_style}/{gate}번)")

    # 4. [핵심] 당일 주로 흐름 자동 요약
    return analyze_today_trend(), today_memo

def analyze_today_trend():
    if not race_history_db: return "데이터 없음"
    
    # 최근 결과 중 선행/추입 비중 계산
    styles = [r['판정습성'] for r in race_history_db]
    gates = [r['게이트'] for r in race_history_db]
    
    front_ratio = styles.count("선행") / len(styles)
    inner_gate_ratio = len([g for g in gates if g <= 4]) / len(gates)
    
    trend = "현재 주로 흐름: "
    if front_ratio >= 0.5: trend += "[선행 유리] "
    if inner_gate_ratio >= 0.5: trend += "[인코스 유리] "
    
    return trend
# 반드시 이 영어 상태 그대로 붙여넣어 지는지 확인하세요!
tab1, tab2 = st.tabs(["📊 데이터 분석 로직", "🤖 AI 비서 상담"])

with tab1:
    st.header("기존 데이터 분석 화면")
    # 여기에 기존 코드 붙여넣기

with tab2:
    st.header("다크모드 AI 채팅방")
    
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "엤썰!! 터프마스터 AI 준비 완료! 무엇이든 물어보십시오!"}
        ]

    # 1. 기존 대화 내용 표시
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # 2. 사용자 입력 처리
    if prompt := st.chat_input("오늘의 경주 분석을 물어보세요!"):
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        # 3. AI 답변 생성 (이 부분이 핵심!)
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            
            try:
                # [중요] 여기서 실제 AI 모델을 호출해야 합니다!
                # 만약 Gemini를 쓰신다면 아래와 같은 형식이 됩니다.
                response = model.generate_content(prompt) 
                full_response = response.text
                
                message_placeholder.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})
            
            except Exception as e:
                error_msg = "엤썰!! 통신 중에 일시적인 오류가 발생했습니다. 다시 시도해 주십시오!"
                st.error(f"오류 내용: {e}")
                message_placeholder.markdown(error_msg)