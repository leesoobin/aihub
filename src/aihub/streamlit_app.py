import streamlit as st
from okta_jwt_verifier import JWTVerifier
import requests
from urllib.parse import urlencode
import json
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import streamlit.components.v1 as components


load_dotenv()

OKTA_DOMAIN = os.getenv("OKTA_DOMAIN")
CLIENT_ID = os.getenv("OKTA_CLIENT_ID")
CLIENT_SECRET = os.getenv("OKTA_CLIENT_SECRET")
REDIRECT_URI = "http://localhost:8501/"  # Streamlit 기본 포트
SCOPES = ["openid", "profile", "email", "offline_access"]  # offline_access 추가
API_BASE_URL = "http://localhost:8000"

def init_session_state():
    """세션 상태 초기화"""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "selected_model" not in st.session_state:
        st.session_state.selected_model = "GPT-4"
    if "selected_agents" not in st.session_state:
        st.session_state.selected_agents = ["일반 대화"]
    if "selected_rag" not in st.session_state:
        st.session_state.selected_rag = "NONE"
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "user_info" not in st.session_state:
        st.session_state.user_info = None
    if "access_token" not in st.session_state:
        st.session_state.access_token = None
    if "refresh_token" not in st.session_state:
        st.session_state.refresh_token = None
    if "token_expiry" not in st.session_state:
        st.session_state.token_expiry = None

def get_login_url():
    """Okta 로그인 URL 생성"""
    params = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "redirect_uri": REDIRECT_URI,
        "state": "state",
        "prompt": "consent"  # 항상 동의 화면 표시
    }
    return f"https://{OKTA_DOMAIN}/oauth2/v1/authorize?{urlencode(params)}"

def refresh_access_token():
    """리프레시 토큰을 사용하여 새 액세스 토큰 발급"""
    if not st.session_state.refresh_token:
        return False
    
    try:
        token_url = f"https://{OKTA_DOMAIN}/oauth2/v1/token"
        data = {
            "grant_type": "refresh_token",
            "refresh_token": st.session_state.refresh_token,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "scope": " ".join(SCOPES)
        }
        response = requests.post(token_url, data=data)
        
        if response.status_code == 200:
            token_data = response.json()
            st.session_state.access_token = token_data["access_token"]
            st.session_state.token_expiry = datetime.now() + timedelta(seconds=token_data.get("expires_in", 3600))
            if "refresh_token" in token_data:
                st.session_state.refresh_token = token_data["refresh_token"]
            return True
    except Exception as e:
        st.error(f"토큰 갱신 실패: {str(e)}")
    
    return False

def is_token_valid():
    """토큰 유효성 검사 및 필요시 갱신"""
    if not st.session_state.access_token or not st.session_state.token_expiry:
        return False
    
    # 토큰 만료 10분 전부터 갱신 시도
    if datetime.now() > st.session_state.token_expiry - timedelta(minutes=10):
        return refresh_access_token()
    
    return True

def handle_authentication(token_response):
    """인증 토큰 처리"""
    if "access_token" in token_response:
        st.session_state.access_token = token_response["access_token"]
        st.session_state.token_expiry = datetime.now() + timedelta(seconds=token_response.get("expires_in", 3600))
        
        # 리프레시 토큰 저장
        if "refresh_token" in token_response:
            st.session_state.refresh_token = token_response["refresh_token"]
        
        user_info = get_user_info(token_response["access_token"])
        if user_info:
            st.session_state.authenticated = True
            st.session_state.user_info = user_info
            record_user_access(user_info)
            return True
    return False

def exchange_code_for_token(code):
    """인증 코드를 토큰으로 교환"""
    token_url = f"https://{OKTA_DOMAIN}/oauth2/v1/token"
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope": " ".join(SCOPES)
    }
    response = requests.post(token_url, data=data)
    return response.json()

def get_user_info(access_token):
    userinfo_url = f"https://{OKTA_DOMAIN}/oauth2/v1/userinfo"
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(userinfo_url, headers=headers)
    user_info = response.json()
    log_to_console(user_info)
    return response.json()

def log_to_console(message):
    """JavaScript를 사용해 브라우저 콘솔에 메시지 출력"""
    js_code = f"""
    <script>
        console.log({json.dumps(message)});
    </script>
    """
    components.html(js_code)

def record_user_access(user_info):
    """사용자 접근 기록 저장"""
    try:
        user_data = {
            "okta_id": user_info.get("sub", ""),
            "name": user_info.get("name", "Unknown"),
            "email": user_info.get("email", ""),
            "access_token": st.session_state.access_token,
            "refresh_token": st.session_state.refresh_token
        }
        print(user_data)
        
        # API 경로 수정
        response = requests.post(
            f"{API_BASE_URL}/api/v1/users/okta/{user_data['okta_id']}",
            json=user_data
        )
        
        if response.status_code == 200:
            return True
        elif response.status_code == 401:  # 토큰 만료
            st.session_state.authenticated = False
            st.rerun()
        else:
            st.error(f"접근 기록 저장 실패: {response.text}")
            return False
            
    except Exception as e:
        st.error(f"API 호출 중 오류 발생: {str(e)}")
        return False

def validate_session():
    """세션 유효성 검증"""
    if not st.session_state.authenticated or not st.session_state.user_info:
        return False

    try:
        # API 경로 수정
        response = requests.get(
            f"{API_BASE_URL}/api/v1/users/validate/{st.session_state.user_info['sub']}"
        )
        return response.status_code == 200 and response.json()
    except:
        return False

def login_page():
    st.title("AIHub Chat - 로그인")
    st.write("계속하려면 Okta로 로그인하세요")
    
    login_url = get_login_url()
    st.markdown(f'<a href="{login_url}" target="_self"><button style="background-color:#1E88E5;color:white;padding:8px 16px;border-radius:4px;border:none;">Okta로 로그인</button></a>', unsafe_allow_html=True)

def sidebar():
    with st.sidebar:
        st.header("설정")
        
        # 모델 선택
        models = ["GPT-4", "GPT-3.5-turbo", "Claude", "Gemini"]
        selected_model = st.selectbox(
            "모델 선택",
            models,
            index=models.index(st.session_state.selected_model)
        )
        st.session_state.selected_model = selected_model
        
        # RAG 선택
        rag_options = ["NONE", "ElasticSearch", "Opensearch", "Chroma", "Qdrant"]
        selected_rag = st.selectbox(
            "RAG 선택",
            rag_options,
            index=rag_options.index(st.session_state.selected_rag)
        )
        st.session_state.selected_rag = selected_rag
        
        # 에이전트 다중 선택
        st.subheader("에이전트 선택")
        agents = {
            "아지트": "🗣️ 아지트 연동하여 일반적인 대화를 수행합니다",
            "위키": "💻 위키를 연동하여 일반적인 대화를 수행합니다.",
            "HIONE": "🌐 정보보호포탈을 연동하여 실시간 응답을 수행합니다.",
        }
        
        selected_agents = []
        for agent, description in agents.items():
            if st.checkbox(
                description,
                value=agent in st.session_state.selected_agents,
                key=f"agent_{agent}"
            ):
                selected_agents.append(agent)
        
        # 최소 1개는 선택되도록 함
        if not selected_agents:
            selected_agents = ["일반 대화"]
            st.warning("최소 1개의 에이전트를 선택해주세요!")
        
        st.session_state.selected_agents = selected_agents
        
        # 현재 설정 표시
        st.divider()
        st.caption("현재 설정")
        st.write(f"🤖 모델: {selected_model}")
        st.write(f"📚 RAG: {selected_rag}")
        st.write("🎯 활성화된 에이전트:")
        for agent in selected_agents:
            st.markdown(f"&nbsp;&nbsp;&nbsp;&nbsp;• {agent}")  # HTML 공백 문자로 들여쓰기

def chat_interface():
    st.title("AIHub Chat")
    
    # 로그아웃 버튼과 사용자 정보를 같은 줄에 표시
    col1, col2 = st.columns([6, 1])
    with col1:
        if st.session_state.user_info:
            st.write(f"환영합니다, {st.session_state.user_info.get('name')}님!")
    with col2:
        if st.button("로그아웃"):
            logout()
    
    # 사이드바 표시
    sidebar()
    
    # 채팅 인터페이스 표시
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("메시지를 입력하세요"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            
            # API 요청 데이터 준비
            request_data = {
                "messages": [{"role": "user", "content": prompt}],
                "model": st.session_state.selected_model,
                "agents": st.session_state.selected_agents,
                "rag": st.session_state.selected_rag
            }
            
            # SSE 요청
            response = requests.post(
                f"{API_BASE_URL}/api/v1/chat/stream",
                json=request_data,
                stream=True
            )
            
            if response.status_code == 200:
                for line in response.iter_lines():
                    if line:
                        line = line.decode('utf-8')
                        if line.startswith('data: '):
                            data = line[6:]
                            if data == '[DONE]':
                                break
                            try:
                                chunk = json.loads(data)
                                full_response += chunk['content']
                                message_placeholder.markdown(full_response)
                            except json.JSONDecodeError:
                                continue
                
                st.session_state.messages.append({"role": "assistant", "content": full_response})
            else:
                error_message = f"API 오류: {response.status_code}"
                st.error(error_message)
                st.session_state.messages.append({"role": "assistant", "content": error_message})

def main():
    init_session_state()
    
    # 토큰 유효성 검사 및 자동 로그인
    if st.session_state.access_token:
        if is_token_valid():
            user_info = get_user_info(st.session_state.access_token)
            if user_info:
                st.session_state.authenticated = True
                st.session_state.user_info = user_info
                record_user_access(user_info)
    
    # 인증 코드 처리
    if "code" in st.query_params and not st.session_state.authenticated:
        code = st.query_params["code"]
        token_response = exchange_code_for_token(code)
        if handle_authentication(token_response):
            st.query_params.clear()
            st.rerun()
    
    if st.session_state.authenticated:
        chat_interface()
    else:
        login_page()

def logout():
    """로그아웃 처리"""
    # 세션 상태 초기화
    st.session_state.authenticated = False
    st.session_state.user_info = None
    st.session_state.access_token = None
    st.session_state.refresh_token = None
    st.session_state.token_expiry = None
    st.session_state.messages = []
    st.rerun()

if __name__ == "__main__":
    main() 