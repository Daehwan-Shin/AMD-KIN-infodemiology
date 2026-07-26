# Multimedia Appendix 2 — Answer-Signal Detection Lexicons

Full Korean keyword lexicons and refinement rules used to detect the eight answer-ecosystem signals reported in the main text (Figure 5; N=1,989 strict-AMD threads). Source: `analysis/answer_signals.py`.

## Detection procedure

1. For each strict-AMD thread, all answer texts (`answer_1…5_content` + `answers_json`) were concatenated and converted to lower case.
2. **Embedded question quotations** — blocks delimited by `#질문 … #답변` / `##질문 … ##답변` — were removed, so signals were detected **only in the responder's text** (not the echoed patient question).
3. A signal was flagged if the cleaned answer text contained **any** of its keywords (case-insensitive substring match), subject to the refinement rules in the final section.
4. Reported prevalences use the **refined detector (v2)**; refinements are conservative and reduce false positives, so counts are lower bounds.

> Keywords are listed in the original Korean (the detection language); an English gloss of each signal name is given in parentheses.

---

## 1. Examination / clinic-visit recommendation (검사·안과 방문 권유)
`검사 받` · `검사받` · `검사를 받` · `검사를받` · `안과 가보` · `안과로 가` · `안과 방문` · `안과를 방문` · `진료 받` · `진료받` · `진료를 받` · `정밀검사` · `검진 받` · `진찰 받` · `안과에 가` · `병원에 가보`

## 2. Supplement recommendation (영양제 권유)
`루테인` · `영양제` · `오메가` · `지아잔틴` · `아스타잔틴` · `보충제` · `눈영양` · `눈 영양` · `복용하세요` · `드세요` · `섭취하` · `챙겨 드` · `복용을 권` · `드셔` · `아레즈` · `오큐바이트` · `areds`

## 3. Surgery / laser mention (수술·레이저 언급)
`수술` · `레이저` · `광응고` · `광역학` · `pdt` · `유리체절제`

## 4. Injection mention (주사치료 언급)
`주사` · `안구주사` · `안내주사` · `유리체내` · `항체주사` · `아바스틴`(Avastin) · `루센티스`(Lucentis) · `아일리아`(Eylea) · `바비스모`(Vabysmo) · `비오뷰`(Beovu) · `마쿠젠`(Macugen) · `항vegf` · `anti-vegf` · `주입술`

## 5. External link / blog (외부 링크·블로그)
`http` · `www.` · `blog.` · `cafe.` · `.com` · `.kr` · `네이버 검색` · `네임카드` · `유튜브` · `블로그에` · `카페에`

## 6. Hospital / clinic referral (병원·의원 추천)
Recommendation-context keywords:
`병원을 추천` · `안과를 추천` · `병원 추천` · `안과 추천` · `추천해 드` · `추천해드` · `추천드립니다` · `명의` · `잘하는 병원` · `잘보는` · `잘 보는 안과` · `잘봐주` · `잘 봐주` · `유명한 안과` · `전문의가 있는 안과` · `병원으로 가보` · `병원으로 가시` · `으로 가보세요` · `알아보세요`

Plus a **proximity rule**: `원장님` is counted only when one of `추천` · `잘본` · `잘 본` · `잘봐` · `잘 봐` · `알아보` · `유명` · `계시` occurs within ±25 characters (to capture "Dr. ○○ is recommended / well-regarded" while excluding the responder's own sign-off, e.g. "○○원장입니다").

## 7. Traditional-medicine mention (한방·침·한약 언급)
`한방` · `한약` · `한의원` · `한의사` · `침 치료` · `침치료` · `침을 맞` · `뜸` · `약침` · `한방치료` · `한방병원` · `해독요법` · `한의학`

## 8. Cure / vision-recovery claim (시력회복·완치 표현)
`완치` · `시력회복` · `시력 회복` · `원상복구` · `정상으로 회복` · `정상으로 돌아` · `특효` · `낫습니다` · `낫게 해` · `회복된다`

Plus a guard for `100%`: counted only in the combinations `100% 완치` / `100% 회복` / `100%회복` (bare "100%" is ignored).

---

## Refinement rules (v2 — four false-positive patterns removed)

1. **Question-quote removal** — `#질문 … #답변` blocks stripped before detection, so a keyword appearing in the quoted patient question is not counted.
2. **Sign-off exclusion (signal 6)** — a responder's own name/title (e.g. "○○원장입니다") is not counted as a referral; a recommendation context is required (keyword list or `원장님` proximity rule above).
3. **Negation exclusion (signal 8)** — `완치` is **not** counted when one of `아니` · `없` · `보장은 없` · `개념보다` · `어렵` · `불가` occurs within ±25 characters (e.g. "완치는 어렵습니다", "완치 개념보다는…").
4. **Irrelevant-token guard (signal 8)** — bare `100%` is ignored unless combined with 완치/회복 (above).

---

## Validation (precision)

For each signal, 25 keyword-matched threads were manually adjudicated as true/false positive; positive predictive value (PPV) was computed with Wilson 95% CIs.

- Supplement recommendation: 96% (80.5–99.3)
- External link / blog: 100% (86.7–100)
- Hospital / clinic referral: 40% (23.4–59.3)
- **Pooled PPV: 70.5% (63.8–76.4)**

Recall (sensitivity) was not estimated; reported prevalences are therefore conservative lower bounds. Low-PPV signals (e.g. hospital referral) should be interpreted cautiously.
