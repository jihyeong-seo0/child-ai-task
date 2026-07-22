# =========================================================
# 환경오염 해결 아이디어 + 생성형 AI 대화 앱 (Streamlit)
# - Solar API(모델: solar-open2)를 openai 라이브러리로 사용
# - 초보자를 위해 한국어 주석을 최대한 자세히 달았어요.
# =========================================================

# 1) 필요한 라이브러리 불러오기 ----------------------------
import json                       # 저장한 기록을 파일(JSON)로 내려받을 때 사용
import datetime                   # 활동지에 오늘 날짜를 넣기 위해 사용
import streamlit as st            # 화면(웹앱)을 만들어 주는 라이브러리
from openai import OpenAI         # Solar API를 호출할 때 쓰는 라이브러리


# 2) 페이지 기본 설정 --------------------------------------
st.set_page_config(page_title="환경오염 해결 아이디어", page_icon="🌍")


# 3) AI에게 줄 '성격' (시스템 프롬프트) --------------------
SYSTEM_PROMPT = "너는 따뜻하고 친절한 데이터 분석 선생님이야. 반드시 순수 한국어로만 답해"


# 4) Solar API 연결 클라이언트 만들기 ----------------------
# - api_key: 코드에 직접 쓰지 않고 비밀 금고(secrets)에서 불러옵니다.
# - base_url: Solar API 접속 주소
client = OpenAI(
    api_key=st.secrets["SOLAR_API_KEY"],
    base_url="https://api.upstage.ai/v1",
)


# 5) 사이드바(왼쪽 메뉴) - 이름 / 학년 / 기록 확인 암호 ----
with st.sidebar:
    st.header("학생 정보")

    # 이름: 이 이름이 '하나의 코드(구분자)'가 되어
    #      아이디어/프롬프트/결과물을 이 이름에 묶어 저장합니다.
    name = st.text_input("이름을 입력하세요")

    # 나이(학년): 초등학교 5학년 / 6학년 중에서 선택
    grade = st.radio("나이(학년)를 선택하세요", ["초등학교 5학년", "초등학교 6학년"])

    st.divider()
    # 기록 확인 암호: '4087'을 맞게 입력한 사람만 저장된 기록을 볼 수 있어요.
    암호 = st.text_input("기록 확인 암호", type="password", placeholder="선생님만 입력")
    암호맞음 = (암호 == "4087")  # 암호가 맞으면 True


# 6) 화면 맨 위 제목 - 시험지(활동지)처럼 꾸미기 -----------
오늘 = datetime.date.today().strftime("%Y년 %m월 %d일")
이름_표시 = name if name else "&nbsp;" * 10   # 이름이 없으면 빈 칸처럼 보이게

# HTML로 시험지 느낌의 머리글을 그립니다. (unsafe_allow_html=True 필요)
st.markdown(
    f"""
    <div style="border:2px solid #2b2b2b; border-radius:10px; padding:18px 22px;
                background:#fafafa; margin-bottom:14px;">
      <div style="display:flex; justify-content:space-between; align-items:center;
                  font-size:13px; color:#555; letter-spacing:1px;">
        <span>🌱 환경 · 데이터 수업 활동지</span>
        <span>{오늘}</span>
      </div>
      <div style="border-top:1px dashed #bbb; margin:10px 0;"></div>
      <div style="text-align:center; font-size:26px; font-weight:800;
                  color:#1a1a1a; line-height:1.45;">
        환경오염을 해결하기 위한<br>아이디어를 작성해주세요
      </div>
      <div style="border-top:1px dashed #bbb; margin:12px 0 10px 0;"></div>
      <div style="display:flex; gap:26px; font-size:15px; color:#333;">
        <span>이름 : <b>{이름_표시}</b></span>
        <span>학년 : <b>{grade}</b></span>
        <span>점수 : ______</span>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# 7) 세션 상태 준비하기 ------------------------------------
# 세션 상태(session_state)는 새로고침해도 값이 유지되는 '기억 장치'예요.
# - messages: 지금 진행 중인 대화 내용(AI가 이전 대화를 기억하게 해줌)
# - records : 이름별로 저장한 아이디어/대화 기록 (이름이 '코드' 역할)
if "messages" not in st.session_state:
    st.session_state.messages = []
if "records" not in st.session_state:
    st.session_state.records = {}


# 8) 이름별 저장 공간을 만들어 주는 도우미 함수 ------------
def 이름_저장공간_준비(학생이름):
    """해당 이름의 저장 공간이 없으면 새로 만들어 줍니다."""
    if 학생이름 not in st.session_state.records:
        st.session_state.records[학생이름] = {
            "학년": grade,   # 선택한 학년
            "아이디어": [],   # 학생이 직접 쓴 아이디어들
            "대화": [],      # (프롬프트, 결과물) 쌍으로 저장되는 AI 대화
        }
    # 학년은 바뀔 수 있으니 항상 최신 값으로 갱신
    st.session_state.records[학생이름]["학년"] = grade


# =========================================================
# 9) [첫 번째 칸] 아이디어 작성 칸
# =========================================================
st.header("✏️ 아이디어 작성 칸")
st.caption("환경오염을 해결할 나만의 아이디어를 자유롭게 적어 보세요.")

# 여러 줄을 쓸 수 있는 입력 상자
아이디어_내용 = st.text_area(
    "나의 아이디어", height=140, placeholder="예) 학교에서 분리수거 게임을 만들어요!"
)

# 아이디어 저장 버튼
if st.button("아이디어 저장하기"):
    if not name:  # 이름이 비어 있으면 저장하지 않음
        st.warning("먼저 사이드바에서 이름을 입력해 주세요.")
    elif not 아이디어_내용.strip():  # 내용이 비어 있으면 저장하지 않음
        st.warning("아이디어 내용을 입력해 주세요.")
    else:
        이름_저장공간_준비(name)
        st.session_state.records[name]["아이디어"].append(아이디어_내용)
        st.success(f"'{name}' 학생의 아이디어가 저장되었어요! 👍")

# 저장된 아이디어는 '암호를 맞게 입력한 사람'만 볼 수 있어요.
if name and name in st.session_state.records and st.session_state.records[name]["아이디어"]:
    if 암호맞음:
        저장된_아이디어들 = st.session_state.records[name]["아이디어"]
        with st.expander(f"📌 '{name}' 학생이 저장한 아이디어 보기 ({len(저장된_아이디어들)}개)"):
            for 번호, 글 in enumerate(저장된_아이디어들, start=1):
                st.write(f"{번호}. {글}")
    else:
        st.info("🔒 저장된 아이디어는 사이드바에 암호를 입력해야 볼 수 있어요.")


# 두 칸을 시각적으로 구분하는 선
st.divider()


# =========================================================
# 10) [두 번째 칸] 생성형 AI 대화 칸
# =========================================================
st.header("🤖 생성형 AI 대화 칸")
st.caption("아이디어에 대해 AI 선생님과 이야기해 보세요.")

# 대화가 길어져도 위쪽 '아이디어 작성 칸'이 사라지지 않도록,
# 대화 내용은 높이가 고정된 '스크롤 상자' 안에서만 흐르게 만듭니다.
# -> 상자 안에서만 스크롤되므로 글쓰기란이 항상 보입니다.
대화상자 = st.container(height=420)

# (1) 지금까지의 대화를 말풍선으로 상자 안에 그려 주기
with 대화상자:
    for 메시지 in st.session_state.messages:
        with st.chat_message(메시지["role"]):  # "user"(학생) 또는 "assistant"(AI)
            st.markdown(메시지["content"])


# (2) 스트리밍으로 받은 글자를 실시간으로 흘려보내 주는 도우미 함수
def 실시간_글자흐름(스트림):
    """AI가 보내주는 조각(chunk)에서 글자만 뽑아 하나씩 내보냅니다."""
    for 조각 in 스트림:
        내용 = 조각.choices[0].delta.content
        if 내용:
            yield 내용


# (3) 화면 아래쪽 채팅 입력창
질문 = st.chat_input("메시지를 입력하세요")

if 질문:
    # 이름을 안 적었으면 결과를 이름에 묶어 저장할 수 없으니 먼저 안내
    if not name:
        st.warning("사이드바에서 이름을 먼저 입력해 주세요. 이름으로 대화가 저장됩니다.")
        st.stop()

    # 새 대화도 위와 같은 '고정된 상자' 안에 이어서 그립니다.
    with 대화상자:
        # 3-1) 학생 메시지를 기억에 추가하고 말풍선으로 표시
        st.session_state.messages.append({"role": "user", "content": 질문})
        with st.chat_message("user"):
            st.markdown(질문)

        # 3-2) AI의 답변을 말풍선으로 이어서 보여 주기
        with st.chat_message("assistant"):
            try:
                스트림 = client.chat.completions.create(
                    model="solar-open2",       # 모델 이름은 반드시 이 글자 그대로!
                    messages=(
                        [{"role": "system", "content": SYSTEM_PROMPT}]
                        + st.session_state.messages
                    ),
                    stream=True,               # 스트리밍(글자가 실시간으로 흘러나옴)
                    reasoning_effort="none",   # 추론(생각) 끄기 -> 답이 더 빨리 나옴
                )
                # 흘러나오는 글자를 실시간으로 써 주고, 완성된 전체 답변을 돌려받습니다.
                답변 = st.write_stream(실시간_글자흐름(스트림))

            except Exception:
                # 실패해도 무서운 에러 화면 대신 친절한 안내를 보여 줍니다.
                답변 = None
                st.error(
                    "앗, 답변을 가져오는 데 문제가 생겼어요. 😢\n\n"
                    "잠시 후 다시 시도해 주세요. 문제가 계속되면 인터넷 연결이나 "
                    "API 키(SOLAR_API_KEY) 설정을 확인해 주세요."
                )

    # 3-3) AI 답변이 정상적으로 왔다면, 기억과 저장 기록에 남기기
    if 답변:
        st.session_state.messages.append({"role": "assistant", "content": 답변})
        이름_저장공간_준비(name)
        st.session_state.records[name]["대화"].append(
            {"프롬프트": 질문, "결과물": 답변}
        )


# =========================================================
# 11) 사이드바 아래쪽 - 암호를 맞힌 사람만 기록 내려받기
# =========================================================
with st.sidebar:
    st.divider()
    st.subheader("저장된 기록 (선생님용)")

    if not 암호맞음:
        # 암호가 없거나 틀리면 기록을 보여 주지 않습니다.
        st.caption("🔒 기록을 보려면 위의 '기록 확인 암호'를 바르게 입력하세요.")
    elif not st.session_state.records:
        st.caption("아직 저장된 기록이 없어요.")
    else:
        # 전체 기록을 한 번에 내려받기
        전체_텍스트 = json.dumps(
            st.session_state.records, ensure_ascii=False, indent=2
        )
        st.download_button(
            label="전체 기록 내려받기 (JSON)",
            data=전체_텍스트,
            file_name="환경수업_전체기록.json",
            mime="application/json",
        )

        # 학생 한 명을 골라 그 학생 기록만 내려받기
        선택이름 = st.selectbox("학생 선택", list(st.session_state.records.keys()))
        개별_텍스트 = json.dumps(
            {선택이름: st.session_state.records[선택이름]},
            ensure_ascii=False,
            indent=2,
        )
        st.download_button(
            label=f"'{선택이름}' 기록 내려받기 (JSON)",
            data=개별_텍스트,
            file_name=f"{선택이름}_기록.json",
            mime="application/json",
        )
