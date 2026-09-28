import re
import json

with open("cleaned.txt", "r", encoding="utf-8") as f:
    text = f.read()

# Split on blank-line gaps (paragraph breaks) — pdftotext -layout leaves
# a blank line between distinct clauses/paragraphs in this document.
raw_blocks = re.split(r'\n\s*\n', text)

chunks = []
current_section = "ACADEMIC REGULATIONS"  # fallback heading

# Headings in this document are short ALL-CAPS or Title-Case lines with
# no trailing period, sitting on their own line — track the most recent
# one so every chunk remembers which section it belongs to.
for block in raw_blocks:
    block = block.strip()
    if not block:
        continue
    lines = [l.strip() for l in block.split("\n") if l.strip()]
    if not lines:
        continue

    # Heuristic: a 1-3 word / short line with no ending punctuation and
    # not starting with a number is likely a section heading, not content.
    first_line = lines[0]
    is_heading_only = (
        len(lines) == 1
        and len(first_line) < 60
        and not first_line.endswith((".", ":", ")"))
        and not re.match(r'^\d', first_line)
    )
    if is_heading_only:
        current_section = first_line
        continue

    merged = " ".join(lines)
    if len(merged) < 40:  # too short to be a useful standalone chunk
        continue

    BULLET = "\uf0b7"  # invisible Wingdings bullet char left by pdftotext
    if BULLET in merged:
        parts = merged.split(BULLET)
        lead_in_full = parts[0].strip()
        # Only the final sentence actually introduces the list — the
        # rest is unrelated context that would get duplicated 10+ times.
        sentences = [s.strip() for s in lead_in_full.split(".") if s.strip()]
        lead_in = sentences[-1] + "." if sentences else ""
        for item in parts[1:]:
            item = item.strip()
            if len(item) < 15:
                continue
            # Keep the lead-in attached so the chunk stands alone.
            full = f"{lead_in} {item}" if lead_in else item
            chunks.append({
                "id": len(chunks),
                "section": current_section,
                "text": full,
                "char_count": len(full)
            })
    else:
        chunks.append({
            "id": len(chunks),
            "section": current_section,
            "text": merged,
            "char_count": len(merged)
        })

with open("chunks.json", "w", encoding="utf-8") as f:
    json.dump(chunks, f, indent=2, ensure_ascii=False)

print(f"Total chunks: {len(chunks)}")
print(f"Char count range: {min(c['char_count'] for c in chunks)} - {max(c['char_count'] for c in chunks)}")
print(f"Average: {sum(c['char_count'] for c in chunks) // len(chunks)}")
print("\n--- First 3 chunks ---")
for c in chunks[:3]:
    print(f"\n[{c['id']}] Section: {c['section']}")
    print(c['text'][:200] + ("..." if len(c['text']) > 200 else ""))