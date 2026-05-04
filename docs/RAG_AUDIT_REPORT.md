# RAG Pipeline Audit Report

## Executive Summary
**Overall RAGAS Score: 0.346** - Critical logic errors and misalignments identified.

---

## 🔴 CRITICAL ISSUES (Must Fix)

### 1. Missing Retrieval for Non-Policy Intents
**Location:** `app/agent/graph.py` lines 15-46
**Impact:** Context Precision = 0.000

**Problem:**
```python
def route_intent(state: SupportState) -> str:
    if intent == "order_status": return "order_status"  # No retrieval!
    if intent == "refund": return "refund"              # No retrieval!
    if intent == "address_change": return "address_change"  # No retrieval!
    return "policy"  # Only policy gets retrieval
```

Only `policy` intent goes through `retrieve_policy_node`. Other intents generate responses WITHOUT retrieving context, but RAGAS evaluation retrieves context separately - creating a fundamental misalignment.

**Fix:** All intents should retrieve relevant policy context before response generation.

---

### 2. Policy Node Context Selection Bug
**Location:** `app/agent/nodes.py` lines 322-325
**Impact:** Faithfulness degradation

**Problem:**
```python
sections = context["content"].split("## Vietnamese")
english_text = sections[0].strip()  # Includes "## English" header!
vietnamese_text = sections[1].strip() if len(sections) > 1 else context["content"]
```

This assumes:
1. All files have "## Vietnamese" section
2. Splitting on "## Vietnamese" gives clean English section

But `shipping_policy.md` structure:
```
# Shipping Policy
## English
- content...
## Vietnamese
- content...
```

Result: English text includes "## English" header and doesn't properly extract content.

---

### 3. Keyword Fallback Returns Entire Files
**Location:** `app/services/retrieval.py` lines 353-363
**Impact:** Context Precision = 0.000

**Problem:**
```python
def _keyword_fallback(self, query: str) -> dict[str, str]:
    # ... finds file ...
    return {"source": selected_file, "content": path.read_text(encoding="utf-8")}
```

Returns ENTIRE file content instead of relevant chunks. No chunking, no relevance filtering. This completely breaks Context Precision.

---

### 4. Knowledge Base Content Gaps
**Location:** `data/knowledge_base/shipping_policy.md`
**Impact:** Context Recall = 0.100

**Problem:** Test case asks "How long does shipping take?" expecting "5-7 business days" but `shipping_policy.md` doesn't contain this information!

Current content:
- Processing time: 2 business days
- No standard/express/international shipping timeframes

The expected answers in test cases contain information NOT in knowledge base.

---

## 🟠 HIGH PRIORITY ISSUES

### 5. Context-Language Mismatch in Policy Node
**Location:** `app/agent/nodes.py` lines 320-332

The policy node extracts language-specific sections, but:
1. Not all policy files have bilingual content
2. Some files have different section structures
3. The extraction logic is fragile

---

### 6. Retrieval k Parameter Too Low
**Location:** `app/services/retrieval.py` line 244

Changed from k=3 to k=5, but still may miss relevant information for complex queries.

---

## 🟡 MEDIUM PRIORITY ISSUES

### 7. No Relevance Score Threshold
Retrieved chunks are returned regardless of distance score. No filtering for irrelevant chunks.

### 8. Chunk Quality Issues
Chunks may split mid-sentence, losing semantic coherence.

### 9. No Query Rewriting
User queries are not rewritten or expanded before retrieval.

---

## 🔧 RECOMMENDED FIXES (Priority Order)

1. **Fix graph routing** - All intents should retrieve context
2. **Fix keyword fallback** - Chunk content, don't return whole files
3. **Fix policy context extraction** - Handle all file formats correctly
4. **Update knowledge base** - Add missing shipping timeframes
5. **Align test cases** - Ensure expected answers exist in knowledge base

---

## Expected Impact After Fixes

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Context Precision | 0.000 | 0.60+ | ∞ |
| Context Recall | 0.100 | 0.70+ | +600% |
| Faithfulness | 0.591 | 0.80+ | +35% |
| Answer Relevancy | varies | 0.75+ | Stabilized |
| **Overall** | 0.346 | **0.70+** | +100% |
