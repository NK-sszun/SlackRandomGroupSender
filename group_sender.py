import os
import random
import requests
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# GitHub Secrets 또는 환경 변수에서 값 가져오기
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
SLACK_CHANNEL_ID = os.environ.get("SLACK_CHANNEL_ID")
WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL")

# 제외할 멤버 목록을 환경 변수에서 가져오기
# "홍길동,성춘향" 과 같은 문자열을 ['홍길동', '성춘향'] 리스트로 변환
excluded_string = os.environ.get("EXCLUDED_MEMBERS", "")
if excluded_string:
    # 쉼표(,)로 이름을 나누고, 각 이름의 앞뒤 공백을 제거
    EXCLUDED_MEMBERS = [name.strip() for name in excluded_string.split(',')]
else:
    EXCLUDED_MEMBERS = []
    
# Slack 클라이언트 초기화
client = WebClient(token=SLACK_BOT_TOKEN)

def get_channel_members(channel_id, excluded_list):
    """지정된 채널의 모든 멤버 이름을 가져옵니다."""
    try:
        # conversations.members API를 호출하여 멤버 ID 목록 가져오기
        result = client.conversations_members(channel=channel_id)
        member_ids = result["members"]
        
        members = []
        for member_id in member_ids:
            # users.info API를 호출하여 각 멤버의 정보 가져오기
            user_info = client.users_info(user=member_id)
            
            if not user_info["user"]["is_bot"]: # 봇은 제외
                # 'real_name' 또는 'name' 필드에서 이름을 가져옵니다.
                full_name = user_info["user"].get("real_name") or user_info["user"].get("name")
                
                # 이름에 '[' 기호가 포함되어 있다면, 그 앞부분만 잘라내고 공백을 제거합니다.
                clean_name = full_name.split('[')[0].strip()

                print(f'슬랙 이름: "{clean_name}" (길이: {len(clean_name)})')

                # '제외할 멤버' 목록에 이름이 없다면 최종 명단에 추가
                is_excluded = clean_name in excluded_list
                if is_excluded:
                    print("  -> [결과] 제외 명단과 일치! (제외 처리)")
                
                if not is_excluded:
                    members.append(clean_name)
        
        return members
        
    except SlackApiError as e:
        print(f"Error fetching members: {e.response['error']}")
        return []

# --- 메인 로직 ---

# 채널 멤버 자동으로 가져오기
print(f"제외할 멤버: {', '.join(EXCLUDED_MEMBERS) if EXCLUDED_MEMBERS else '없음'}")
members = get_channel_members(SLACK_CHANNEL_ID, EXCLUDED_MEMBERS)

if not members:
    print("멤버를 가져오지 못했거나, 모든 멤버가 제외되었습니다. 스크립트를 종료합니다.")
else:
    print(f"그룹 생성 대상 멤버 ({len(members)}명): {', '.join(members)}")
    group_count = 3
    random.shuffle(members)

    groups = [[] for _ in range(group_count)]

    # 라운드 로빈 배치
    for idx, member in enumerate(members):
        groups[idx % group_count].append(member)

    payload = {
        "group1": "[그룹 1]",
        "group2": "[그룹 2]",
        "group3": "[그룹 3]",
        "members1": ", ".join(groups[0]) if groups[0] else "멤버 없음",
        "members2": ", ".join(groups[1]) if groups[1] else "멤버 없음",
        "members3": ", ".join(groups[2]) if groups[2] else "멤버 없음"
    }

    response = requests.post(WEBHOOK_URL, json=payload)
    print("전송 결과:", response.status_code, response.text)
