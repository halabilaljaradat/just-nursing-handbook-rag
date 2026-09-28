# JUST Nursing Handbook Q&A (RAG)

A retrieval-augmented generation (RAG) system that answers questions about the academic regulations of the Jordan University of Science and Technology (JUST) Faculty of Nursing Student Handbook (2024). Ask a question in plain English and get an answer grounded in the handbook, with the source chunk cited.

Beyond the demo, this project **measures retrieval quality** on a hand-labelled question set, and documents one real failure I found, diagnosed, and partly fixed.

## Why this project

LLMs don't know a specific university's rules, and when asked anyway they tend to guess confidently. RAG fixes this by retrieving the relevant passages first and asking the model to answer only from them.

I chose this handbook because no LLM has memorised it. If an answer is correct, retrieval worked. The model didn't just happen to know it.

## How it works

```
INDEXING (once)
Handbook PDF (pp. 29-41) -> extract text -> clean -> chunk -> embed -> vectors

QUERYING (every question)
Question -> embed -> cosine similarity vs. all chunks -> top-5 chunks
         -> prompt (question + chunks) -> Gemini -> cited answer
```

| Stage | What I did | Tool |
|---|---|---|
| Extract | Pulled text from pages 29-41 (Academic Regulations through Clinical Guidelines) | `pdftotext -layout` |
| Clean | Removed stray page-number lines left by extraction | shell / regex |
| Chunk | Split on paragraph breaks and on bullet markers (the PDF's bullets are an invisible private-use character, `\uf0b7`), keeping each list's lead-in sentence attached to every bullet | `scripts/chunk.py` |
| Embed | 168 chunks -> 384-dimensional vectors | `all-MiniLM-L6-v2` (sentence-transformers, runs locally) |
| Retrieve | Cosine similarity, top-k = 5 | sentence-transformers `util.cos_sim` |
| Generate | Answer using only the retrieved chunks, cite chunk IDs, say so if the answer isn't there | Gemini API |
| Interface | Simple web UI | Gradio |

I limited the index to pages 29-41 because those pages hold the concrete, checkable rules (credit hours, attendance, grading, postponement). The rest of the handbook is descriptive text that produces few answerable questions.

## Evaluation

I wrote 13 questions, each with the ID of the one chunk that contains the answer (checked by reading the chunk). For each question I check whether that chunk appears in the top 1, 3, and 5 retrieved results.

| Metric | Before fix | After fix |
|---|---|---|
| Recall@1 | 0.69 (9/13) | 0.69 (9/13) |
| Recall@3 | 0.85 (11/13) | 0.85 (11/13) |
| Recall@5 | 0.92 (12/13) | **1.00 (13/13)** |

## A failure I found and what I learned from it

**The failing question:** "What is the maximum duration to complete the Bachelor's degree?" The correct chunk (id 1) was missing from the top 5, in every run.

**Hypothesis 1: the chunk mixed two topics.** Chunk 1 held the credit-hour and duration facts and also text about advisor responsibilities, which could dilute its embedding. I split it in two. The retrieved results were *identical* to before, so this hypothesis was wrong.

**Hypothesis 2: a vocabulary gap.** The chunk says "B.Sc." but the question says "Bachelor's degree". I added "(Bachelor's Degree)" next to "B.Sc." in the chunk. The chunk moved from outside the top 5 to **rank 4**, which took Recall@5 from 0.92 to 1.00.

**What I take from it:** the chunk that ranked first contains the phrase "maximum duration for the award of the Bachelor's Degree" but does not actually state the duration. That suggests this embedding model leans on wording overlap more than I expected, especially for domain abbreviations. The fix helped Recall@5 only. It did not change Recall@1 or Recall@3.

## Limitations

- **Small evaluation set.** With 13 questions, each one moves recall by about 8 points.
- **Optimistic by construction.** I wrote the questions after reading the chunks, so their wording may echo the source text.
- **Tuned on the test set.** I made the wording fix after seeing that exact question fail in my evaluation set, so the Recall@5 of 1.00 is partly fitted to it. A fair test needs fresh questions written without looking at the chunks.
- **Generation was only spot-checked.** I ran a handful of questions by hand. Every completed answer carried a chunk citation and one combined facts from two chunks correctly, but I did not score faithfulness systematically.
- **Narrow scope.** Only handbook pages 29-41 are indexed.
- **Free-tier constraints.** I started with `gemini-3.8-flash`, hit its free-tier cap of roughly 20 requests per day, and switched to `gemini-3.5-flash-lite`. Model names and quotas change, so update the model name in the notebook if it stops working.

## Run it yourself

```bash
git clone https://github.com/halabilaljaradat/<repo-name>.git
cd <repo-name>
python -m venv venv
venv\Scripts\activate          # Windows  (Mac/Linux: source venv/bin/activate)
pip install -r requirements.txt
```

1. Get a free API key from Google AI Studio.
2. Copy `.env.example` to `.env` and put your key in it. `.env` is git-ignored, so it never gets uploaded.
3. Open `pipeline.ipynb`, select the `venv` kernel, and run the cells in order. The last cell launches the Gradio interface at `http://127.0.0.1:7860`.

## Repository contents

```
pipeline.ipynb            embeddings, retrieval, evaluation, generation, Gradio UI
chunks_v2.json            the 168 chunks used for retrieval (after the fix)
scripts/chunk.py          paragraph + bullet chunker (input: cleaned text extract)
scripts/apply_chunk1_fix.py   splits chunk 1 and adds the full "Bachelor's Degree" wording
requirements.txt
.env.example              template for your API key
```

To rebuild the chunks from the PDF: extract pages 29-41 with `pdftotext -f 29 -l 41 -layout`, delete the lone page-number lines, save as `cleaned.txt`, run `scripts/chunk.py`, then `scripts/apply_chunk1_fix.py`.

## Source

Text is taken from the JUST Faculty of Nursing Student Handbook (2024), published by the university. All rights to the handbook remain with JUST.
