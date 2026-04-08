"""
사대보험 환급 컨설팅 - 백엔드 서버
- POST /api/submit : 신청 폼 데이터 → 노션 데이터베이스 저장
"""

import os
import json
import requests
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import anthropic

app = Flask(__name__, static_folder='.')
CORS(app)

# ── 환경변수 ──────────────────────────────────────────
ANTHROPIC_API_KEY   = os.environ.get('ANTHROPIC_API_KEY', '')
NOTION_API_KEY      = os.environ.get('NOTION_API_KEY', '')
NOTION_DATABASE_ID  = os.environ.get('NOTION_DATABASE_ID', '')

NOTION_HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}

# ── 메인 페이지 서빙 ──────────────────────────────────
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')




# ── 신청 폼 제출 → 노션 ───────────────────────────────
@app.route('/api/submit', methods=['POST'])
def submit_form():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400

    # 필수 필드 검증
    required_fields = ['company_name', 'employee_count', 'contact_name',
                       'contact_phone', 'contact_email',
                       'pension_status', 'executive_insurance']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'Missing required field: {field}'}), 400

    # 직원 수 정수 변환
    try:
        employee_count = int(data.get('employee_count', 0))
    except (ValueError, TypeError):
        employee_count = 0

    # 퇴직연금 가입 시기 처리 (YYYY-MM 연월 형식)
    pension_date_str = data.get('pension_date')
    pension_date_prop = None
    if pension_date_str:
        try:
            # YYYY-MM 형식 검증 후 노션 date 형식(YYYY-MM-DD)으로 변환 (1일로 고정)
            datetime.strptime(pension_date_str, '%Y-%m')
            pension_date_prop = {"date": {"start": pension_date_str + "-01"}}
        except ValueError:
            pension_date_prop = None

    # 신청일시
    now_str = datetime.now().strftime('%Y-%m-%dT%H:%M:%S+09:00')

    # ── 노션 properties 구성 ──────────────────────────
    properties = {
        # Title (필수)
        "회사명": {
            "title": [{"text": {"content": data.get('company_name', '')}}]
        },
        "상시근로자수": {
            "number": employee_count
        },
        "담당자 이름": {
            "rich_text": [{"text": {"content": data.get('contact_name', '')}}]
        },
        "담당자 연락처": {
            "phone_number": data.get('contact_phone', '')
        },
        "담당자 이메일": {
            "email": data.get('contact_email', '')
        },
        "퇴직연금 가입 여부": {
            "select": {"name": data.get('pension_status', '모름')}
        },
        "등기임원 사대보험 가입": {
            "select": {"name": data.get('executive_insurance', '모름')}
        },
        "신청일시": {
            "date": {"start": now_str}
        },
        "처리 상태": {
            "select": {"name": "신청 접수"}
        },
    }

    # 개인정보 동의 (노션 컬럼이 있을 경우에만 전송)
    if data.get('privacy_agreed'):
        properties["개인정보 수집 및 이용 동의"] = {"checkbox": True}

    # 퇴직연금 가입 시기 (조건부)
    if pension_date_prop:
        properties["퇴직연금 가입 시기"] = pension_date_prop

    # 가입자 성명 및 직책 (조건부)
    executive_members = data.get('executive_members', '')
    if executive_members:
        properties["가입자 성명 및 직책"] = {
            "rich_text": [{"text": {"content": executive_members}}]
        }

    # ── 노션 API 호출 ──────────────────────────────────
    payload = {
        "parent": {"database_id": NOTION_DATABASE_ID},
        "properties": properties,
    }

    try:
        response = requests.post(
            "https://api.notion.com/v1/pages",
            headers=NOTION_HEADERS,
            json=payload,
            timeout=10
        )

        if response.status_code == 200:
            return jsonify({"success": True, "message": "신청이 완료되었습니다."})
        else:
            error_detail = response.json()
            print(f"[Notion Error] {response.status_code}: {error_detail}")
            return jsonify({
                "error": "노션 저장 중 오류가 발생했습니다.",
                "detail": error_detail.get("message", "")
            }), 500

    except requests.exceptions.Timeout:
        return jsonify({"error": "요청 시간이 초과되었습니다. 잠시 후 다시 시도해 주세요."}), 504
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"네트워크 오류: {str(e)}"}), 500


# ── 서버 실행 ─────────────────────────────────────────
if __name__ == '__main__':
    # 시작 전 환경변수 확인
    missing = []
    if not ANTHROPIC_API_KEY:  missing.append('ANTHROPIC_API_KEY')
    if not NOTION_API_KEY:     missing.append('NOTION_API_KEY')
    if not NOTION_DATABASE_ID: missing.append('NOTION_DATABASE_ID')

    if missing:
        print(f"⚠️  누락된 환경변수: {', '.join(missing)}")
        print("   .env 파일을 확인하거나 환경변수를 설정해 주세요.\n")
    else:
        print("✅ 환경변수 확인 완료")

    print("🚀 서버 시작: http://localhost:8080")
    app.run(host='0.0.0.0', port=8080, debug=False)
