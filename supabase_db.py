# =========================================================
# supabase_db.py : 학생 기록을 Supabase(온라인 데이터베이스)에 저장하는 기능
#
# ★ 사용 전 준비 (딱 두 가지) ★
#  1) Supabase 대시보드 → SQL Editor 에서 supabase_setup.sql 내용을 실행해 표를 만듭니다.
#  2) 스트림릿 클라우드 → Settings → Secrets 에 아래 두 줄을 넣습니다.
#
#       SUPABASE_URL = "https://xxxxxxxx.supabase.co"
#       SUPABASE_KEY = "여기에 service_role 키"
#
#     (Supabase → Project Settings → API 에서 확인할 수 있어요.
#      service_role 키는 절대 코드나 깃허브에 직접 쓰지 마세요!)
# =========================================================

import datetime
import streamlit as st


# ---------------------------------------------------------
# 1) 연결 준비
# ---------------------------------------------------------
def 사용가능():
    """Secrets에 Supabase 정보가 들어 있는지 확인합니다."""
    try:
        return bool(st.secrets.get("SUPABASE_URL")) and bool(st.secrets.get("SUPABASE_KEY"))
    except Exception:
        return False


@st.cache_resource(show_spinner=False)
def _클라이언트():
    """Supabase에 연결하는 통로를 만듭니다. (한 번만 만들어 두고 계속 사용)"""
    from supabase import create_client
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])


# ---------------------------------------------------------
# 2) 한 학생의 기록을 통째로 저장(덮어쓰기)
#    - 같은 연구ID로 다시 저장하면 새로 쌓이지 않고 최신 내용으로 바뀝니다.
# ---------------------------------------------------------
def 학생저장(이름, 조용히=True):
    """한 학생의 모든 기록을 Supabase에 저장합니다.

    돌려주는 값: (성공여부, 안내문)
    조용히=True 이면 실패해도 화면에 오류를 크게 띄우지 않습니다.
    (학생이 문제를 푸는 도중에 방해받지 않도록 하기 위해서예요.)
    """
    if not 사용가능():
        return False, "Supabase 접속 정보(SUPABASE_URL / SUPABASE_KEY)가 없습니다."
    if not 이름:
        return False, "이름이 없습니다."

    정보 = st.session_state.get("records", {}).get(이름)
    if not 정보:
        return False, "저장할 기록이 없습니다."

    try:
        from tasks import 문제은행
    except Exception:
        문제은행 = {}

    try:
        sb = _클라이언트()
        연구ID = 정보.get("연구ID", "")
        학년 = 정보.get("학년", "")
        채점 = 정보.get("채점", {})
        지금 = datetime.datetime.now().isoformat()

        # (1) 참가자 정보 + AI 채점 요약
        세기 = {}
        for v in 채점.values():
            판정 = v.get("판정", "")
            세기[판정] = 세기.get(판정, 0) + 1
        요약 = (
            f"제출 {len(정보.get('인지과제', {}))}문항 · "
            f"정답 {세기.get('정답', 0)} / 부분정답 {세기.get('부분정답', 0)} / "
            f"오답 {세기.get('오답', 0)} / 무응답 {세기.get('무응답', 0)}"
            if 채점 else "아직 AI 채점을 실행하지 않았습니다."
        )
        sb.table("participants").upsert(
            {
                "research_id": 연구ID,
                "name": 이름,
                "grade": 학년,
                "ai_summary": 요약,
                "updated_at": 지금,
            },
            on_conflict="research_id",
        ).execute()

        # (2) 인지과제 답 (엑셀 A~E열에 해당)
        문제들 = 문제은행.get(학년, [])
        행들 = []
        for 번호, 학생답 in 정보.get("인지과제", {}).items():
            문제 = 문제들[번호] if 번호 < len(문제들) else {}
            판정정보 = 채점.get(번호, {})
            행들.append({
                "research_id": 연구ID,
                "name": 이름,
                "grade": 학년,
                "question_no": 번호 + 1,
                "question_type": 문제.get("유형", ""),
                "question": str(문제.get("문제", "")).replace("\n", " "),
                "student_answer": 학생답,
                "correct_answer": str(문제.get("정답", "")),
                "ai_verdict": 판정정보.get("판정", ""),
                "ai_reason": 판정정보.get("이유", ""),
                "saved_at": 지금,
            })
        if 행들:
            sb.table("cognitive_answers").upsert(
                행들, on_conflict="research_id,question_no"
            ).execute()

        # (3) 창의적 글쓰기 (엑셀 G~J열에 해당)
        글행들 = [
            {
                "research_id": 연구ID, "name": 이름, "grade": 학년,
                "seq": i, "content": 글, "saved_at": 지금,
            }
            for i, 글 in enumerate(정보.get("글쓰기", []), start=1)
        ]
        if 글행들:
            sb.table("writings").upsert(글행들, on_conflict="research_id,seq").execute()

        # (4) 생성형 AI 대화 (페이지별로 번호를 매겨 저장)
        대화행들, 쪽번호 = [], {}
        for 쌍 in 정보.get("대화", []):
            쪽 = 쌍.get("페이지", "")
            쪽번호[쪽] = 쪽번호.get(쪽, 0) + 1
            대화행들.append({
                "research_id": 연구ID, "name": 이름, "grade": 학년,
                "page": 쪽, "seq": 쪽번호[쪽],
                "prompt": 쌍.get("프롬프트", ""),
                "response": 쌍.get("결과물", ""),
                "saved_at": 지금,
            })
        if 대화행들:
            sb.table("ai_chats").upsert(
                대화행들, on_conflict="research_id,page,seq"
            ).execute()

        return True, f"'{이름}' 기록을 저장했어요. (연구ID: {연구ID})"

    except Exception as e:
        메시지 = f"Supabase 저장 실패: {type(e).__name__} - {str(e)[:120]}"
        if not 조용히:
            st.error(메시지)
        return False, 메시지


# ---------------------------------------------------------
# 3) 학생이 무언가 저장할 때마다 조용히 자동 저장
#    - 실패해도 학생 화면을 방해하지 않습니다. (기록은 세션에 남아 있어요)
# ---------------------------------------------------------
def 자동저장(이름):
    if not 이름 or not 사용가능():
        return
    성공, 메시지 = 학생저장(이름, 조용히=True)
    # 마지막 결과를 기억해 두었다가 연구자 패널에서 확인할 수 있게 합니다.
    st.session_state["_supabase_최근"] = ("✅ " if 성공 else "⚠️ ") + 메시지


# ---------------------------------------------------------
# 4) 저장된 기록 수 확인 (연구자 패널에서 사용)
# ---------------------------------------------------------
def 저장현황():
    """Supabase에 저장된 참가자 수를 세어 봅니다."""
    if not 사용가능():
        return None, "Supabase 접속 정보가 없습니다."
    try:
        sb = _클라이언트()
        결과 = sb.table("participants").select("research_id", count="exact").execute()
        return (결과.count or 0), None
    except Exception as e:
        return None, f"{type(e).__name__} - {str(e)[:120]}"


# ---------------------------------------------------------
# 5) 지금 사용 중인 키가 어떤 종류인지 확인
#    - service_role(비밀) 키라야 RLS 보안 설정을 통과해 저장할 수 있어요.
#    - anon(공개) 키를 넣으면 "row-level security policy" 오류가 납니다.
# ---------------------------------------------------------
def 키종류():
    """돌려주는 값: ("service_role" / "anon" / "알 수 없음", 안내문)"""
    try:
        키 = st.secrets.get("SUPABASE_KEY", "") or ""
    except Exception:
        키 = ""
    if not 키:
        return "없음", "SUPABASE_KEY가 비어 있습니다."

    # (1) 새 형식 키
    if 키.startswith("sb_secret_"):
        return "service_role", "비밀(secret) 키를 쓰고 있어요. 정상입니다."
    if 키.startswith("sb_publishable_"):
        return "anon", "공개(publishable) 키예요. 비밀(secret) 키로 바꿔 주세요."

    # (2) 예전 형식 키(JWT) — 가운데 부분을 풀어 role 값을 봅니다.
    try:
        import base64, json
        가운데 = 키.split(".")[1]
        가운데 += "=" * (-len(가운데) % 4)          # 길이 맞추기
        정보 = json.loads(base64.urlsafe_b64decode(가운데))
        역할 = 정보.get("role", "")
        if 역할 == "service_role":
            return "service_role", "service_role 키를 쓰고 있어요. 정상입니다."
        if 역할 == "anon":
            return "anon", "anon(공개) 키예요. service_role 키로 바꿔 주세요."
        return "알 수 없음", f"역할: {역할 or '확인 불가'}"
    except Exception:
        return "알 수 없음", "키 형식을 확인할 수 없습니다."
