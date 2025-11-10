import random, requests

WEBHOOK_URL = "https://hooks.slack.com/triggers/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"
CHANNEL_ID = "C09QKN9JUR4"

members = ["성지윤", "이송현", "김준영"]

random.shuffle(members)
groups = [[m] for m in members]

message = "\n".join([
    f"[그룹 {i+1}]\n" + ", ".join(groups[i])
    for i in range(len(groups))
])

payload = {
    "channel": CHANNEL_ID,
    "message": message
}

response = requests.post(WEBHOOK_URL, json=payload)
print("전송 결과:", response.status_code, response.text)
