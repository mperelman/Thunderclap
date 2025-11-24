import json

data = json.load(open('data/identity_detection_v3.json', encoding='utf-8'))
identities = data['identities']

# Sort by chunk count
sorted_ids = sorted(identities.keys(), key=lambda x: identities[x]['chunk_count'], reverse=True)

print('\n=== ALL 342 IDENTITIES (sorted by chunk count) ===\n')
for id in sorted_ids:
    print(f'{id:30s} {identities[id]["chunk_count"]:4d} chunks')

