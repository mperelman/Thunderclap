import json

# Load endnotes
with open('data/endnotes.json', encoding='utf-8') as f:
    endnotes = json.load(f)

print("="*80)
print("ENDNOTES.JSON STRUCTURE")
print("="*80)
print(f"Type: {type(endnotes)}")
print(f"Total entries: {len(endnotes)}")

if isinstance(endnotes, dict):
    print(f"Sample keys: {list(endnotes.keys())[:5]}")
    first_key = list(endnotes.keys())[0]
    print(f"\nSample entry ({first_key}):")
    print(f"  {endnotes[first_key][:200] if isinstance(endnotes[first_key], str) else endnotes[first_key]}")
elif isinstance(endnotes, list):
    print(f"Sample entry:")
    print(f"  {endnotes[0]}")

print("\n" + "="*80)
print("CHUNK_TO_ENDNOTES.JSON STRUCTURE")
print("="*80)

# Load chunk to endnotes mapping
with open('data/chunk_to_endnotes.json', encoding='utf-8') as f:
    chunk_mapping = json.load(f)

print(f"Type: {type(chunk_mapping)}")
print(f"Total chunks with endnotes: {len(chunk_mapping)}")

if isinstance(chunk_mapping, dict) and chunk_mapping:
    first_chunk = list(chunk_mapping.keys())[0]
    print(f"\nSample chunk mapping ({first_chunk}):")
    print(f"  Endnote IDs: {chunk_mapping[first_chunk]}")

# Search for Hohenemser in endnotes
print("\n" + "="*80)
print("SEARCHING ENDNOTES FOR 'HOHENEMSER'")
print("="*80)

hohenemser_endnotes = []
if isinstance(endnotes, dict):
    for key, text in endnotes.items():
        if isinstance(text, str) and 'hohenemser' in text.lower():
            hohenemser_endnotes.append((key, text))
elif isinstance(endnotes, list):
    for i, item in enumerate(endnotes):
        text = str(item)
        if 'hohenemser' in text.lower():
            hohenemser_endnotes.append((i, item))

print(f"Found {len(hohenemser_endnotes)} endnotes mentioning 'Hohenemser'")

for key, text in hohenemser_endnotes[:5]:
    print(f"\nEndnote {key}:")
    print(f"  {text[:300] if isinstance(text, str) else text}...")



