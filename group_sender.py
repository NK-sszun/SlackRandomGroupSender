import random
import requests

WEBHOOK_URL = "https://hooks.slack.com/triggers/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"

members = [
    "김준호2", "이윤호", "홍창모", "성지윤",
    "조성국", "윤정민", "곽경석", "이송현", "최민규",
    "조경빈", "서정민2", "이우성", "황성원",
    "박인환", "김준영2", "김준호", "이상령"
]

group_count = 3

# 제외할 멤버
A = "이송현"
B = "박인환"

# 나머지 멤버들만 셔플
others = [m for m in members if m not in (A, B)]
random.shuffle(others)

# 기본 그룹 구성
groups = [[] for _ in range(group_count)]

# 나머지 멤버들을 라운드 로빈으로 배치
for idx, member in enumerate(others):
    groups[idx % group_count].append(member)

# A를 랜덤 그룹의 랜덤 위치에 삽입
group_for_A = random.randint(0, group_count - 1)
pos_A = random.randint(0, len(groups[group_for_A]))
groups[group_for_A].insert(pos_A, A)

# B는 A가 들어간 그룹이 아닌 곳 중 랜덤 선택
available_groups_for_B = [i for i in range(group_count) if i != group_for_A]
group_for_B = random.choice(available_groups_for_B)

pos_B = random.randint(0, len(groups[group_for_B]))
groups[group_for_B].insert(pos_B, B)

# 페이로드 구성
payload = {
    "group1": "[그룹 1]",
    "group2": "[그룹 2]",
    "group3": "[그룹 3]",
    "members1": ", ".join(groups[0]),
    "members2": ", ".join(groups[1]),
    "members3": ", ".join(groups[2])
}

response = requests.post(WEBHOOK_URL, json=payload)
print("전송 결과:", response.status_code, response.text)
