"""Apply the chunk-1 fix to chunks.json and write chunks_v2.json.

Problem: chunk 1 mixed two topics (credit hours / duration limits, and advisor
responsibilities), and used the abbreviation "B.Sc." while questions say
"Bachelor's degree".
Fix:
  1. Split chunk 1: keep the credit-hour/duration sentence at id 1, and append
     the advisor text as a NEW chunk at the end (appending, not inserting, so
     every other chunk id stays the same).
  2. Add "(Bachelor's Degree)" next to "B.Sc." so both wordings appear.
"""
import json

with open("chunks.json", "r", encoding="utf-8") as f:
    chunks = json.load(f)

part_a = ("Course load B.Sc. (Bachelor's Degree) in Nursing requires 134 credit hours, "
          "to be completed in an average duration of four years and within the "
          "maximum duration of six years.")
part_b = ("The student is responsible for his course load which is commensurate with his "
          "abilities and comprehension. The advisor should review the student's record and "
          "advise him/her to register for only the courses included in his/her study plan, "
          "and which are commensurate with his abilities and study progress. However the "
          "followings should be taken into consideration:")

chunks[1]["text"] = part_a
chunks[1]["char_count"] = len(part_a)
chunks.append({
    "id": len(chunks),
    "section": chunks[1]["section"],
    "text": part_b,
    "char_count": len(part_b),
})

with open("chunks_v2.json", "w", encoding="utf-8") as f:
    json.dump(chunks, f, indent=2, ensure_ascii=False)

print(f"Wrote chunks_v2.json with {len(chunks)} chunks")