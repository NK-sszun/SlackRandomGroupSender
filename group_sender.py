import random
import requests

WEBHOOK_URL = "https://hooks.slack.com/triggers/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"

members = [
    "김준호2", "이윤호", "홍창모", "성지윤",
    "조성국", "윤정민", "이송현", "최민규",
    "조경빈", "서정민2", "이우성", "황성원",
    "박인환", "김준영2", "이상령", "안승근"
]

group_count = 3

A = "이송현"
B = "박인환"

# A, B 제외 후 셔플
others = [m for m in members if m not in (A, B)]
random.shuffle(others)

# 기본 그룹
groups = [[] for _ in range(group_count)]

# 라운드 로빈 배치
for idx, member in enumerate(others):
    groups[idx % group_count].append(member)

def get_min_size_group_indices(groups, exclude=None):
    indices = [
        i for i in range(len(groups))
        if exclude is None or i not in exclude
    ]
    min_size = min(len(groups[i]) for i in indices)
    return [i for i in indices if len(groups[i]) == min_size]

# A 삽입: 가장 인원 적은 그룹
candidates_for_A = get_min_size_group_indices(groups)
group_for_A = random.choice(candidates_for_A)
pos_A = random.randint(0, len(groups[group_for_A]))
groups[group_for_A].insert(pos_A, A)

# B 삽입: A가 없는 그룹 중, 가장 인원 적은 그룹
candidates_for_B = get_min_size_group_indices(groups, exclude={group_for_A})
group_for_B = random.choice(candidates_for_B)
pos_B = random.randint(0, len(groups[group_for_B]))
groups[group_for_B].insert(pos_B, B)

# 페이로드
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
