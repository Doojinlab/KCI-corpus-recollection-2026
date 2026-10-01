# AI 활용 중국어교육 연구의 현황과 공백: 공개 자료

논문 「AI 활용 중국어교육 연구의 현황과 공백: 영어·한국어교육과의 계량서지·네트워크 비교」의 판정 결과, 분석 스크립트, 결과 파일, 논문별 집계를 담은 저장소이다. 논문의 부록 A·B·C도 함께 둔다.

**English summary.** Data and code for *Current Status and Research Gaps in AI-Assisted Chinese Language Education: A Bibliometric and Network Comparison with English and Korean*. The corpus consists of 1,161 articles indexed in the Korea Citation Index (KCI) from 2020 to June 2026 (English 709, Korean 384, Chinese 68), selected from 1,644 candidates. This repository contains the coding results, coding guidelines, analysis scripts, result files, and per-article aggregates. Abstracts and reference lists retrieved from KCI are not redistributed; the articles can be looked up in KCI by their identifiers (artiId).

## 구성

| 경로 | 내용 |
|---|---|
| `부록A_판정지침_판정결과.md` | 부록 A. 판정 지침과 판정 결과 |
| `부록B_처리흐름_변수정의.md` | 부록 B. 처리 흐름, 변수 정의, 지표 산출식, 핵심 개념 정규화표 |
| `부록C_판정재현성_불일치.md` | 부록 C. 판정의 재현성(독립 재판정과의 일치도, 불일치 사례) |
| `data/KCI_코퍼스확정_1161_20261001.xlsx` | 논문별 판정 결과와 서지 정보(초록 열 없음). 시트: 0 안내, 1 포함 코퍼스 1,161편, 2 제외 483편과 제외 사유, 3 경계 사례 438편(저자 확인 표시), 4 첫 투고본 보고값과의 대조, 5 언어기능×연구방법 격자, 6 연도×언어군, 7 한국어군 학습자 맥락(L1·L2) |
| `data/rejudge/merged_1161_20261001.json` | 위 엑셀과 같은 판정 결과의 JSON(후보 1,644편, 포함 1,161편). 초록 필드는 뺐다. 분석 스크립트의 입력이다 |
| `data/rejudge/CODING_GUIDE.md` | 초록 판정·코딩 지침 |
| `data/rejudge/out/` | 1,644편 판정 출력(28묶음) |
| `data/rejudge/l1/`, `data/rejudge/r3/` | 경계 범주의 처리 규칙(`L1_RULE.md`, `R3_RULE.md`)과 재판정 출력 |
| `data/kappa/` | 일치도 표본 200편의 확정 판정값(`κ표본_정답키_1161_20261001.json`), 독립 재판정 지침(`ai2/AI2_GUIDE.md`)과 출력(`ai2/out/`, `ai2/ai2_merged_1161_20261001.json`) |
| `analysis/ref_aggregate_1161_20261001.csv` | 논문별 참고문헌 분류 집계: 참고문헌 수, 국내(한글)·중문(한자)·그 밖 국제 문헌 수, 학술지명이 있는 문헌 수, 교육·언어학·문학·기타 분야 문헌 수. 원고 <표 12>의 입력 |
| `analysis/school_level_1161_20261001.csv` | 논문별 학교급 표지(제목·초록에 초·중등 또는 대학 맥락이 드러나는지). 원고 5.2의 학교급 각주 입력 |
| `analysis/*_1161_20261001.md`, `.json` | 분석 결과: 희박화·초기하(`rarefaction`), 공백 유형과 규모 통제(`scale_checks`), 공저 네트워크 규모 기대값(`network_scale`), 주제 확산(`keyword_diffusion`), 공저·인용·참고문헌 표(`tables_4to8`), 일치도(`kappa`, `kappa_불일치`), 게재 학술지 분야(`journal_field`), 판정 요약(`rejudge_summary`) |
| `analysis/keyword_concepts.json` | 20개 핵심 개념 정규화표(부록 B.4) |
| `analysis/paper_targets.json` | 첫 투고본의 보고값. 일부 스크립트가 대조용으로 읽는다. 결과 파일의 '논문' 열이 이 값이다 |
| `scripts/` | 수집(Node.js: `harvest_supp.js`, `import_full.js`, `reextract_originals.js`, `build_corpus_full.js`, `kci_engine/`), 판정 병합과 결정 반영(`rejudge/merge_rejudge.py`, `apply_l1.py`, `apply_r3.py`, `apply_r4.py`), 분석(`rejudge/` 아래 Python·perl), 그림(`figures/`) |
| `.env.example` | KCI Open API 인증키 설정 예시. 수집 스크립트를 다시 돌릴 때만 필요하다 |

## 재현

모든 명령은 저장소 최상위 폴더에서 실행한다. Python 스크립트는 Python 3 표준 라이브러리를 쓰며, 엑셀을 읽거나 쓰는 스크립트는 `openpyxl`, 그림 스크립트는 `Pillow`가 필요하다. 난수 시드는 각 스크립트에 고정되어 있다.

**공개 자료만으로 실행할 수 있는 것**

| 원고 | 명령 |
|---|---|
| <표 12>와 4.4.3 참고문헌 각주, 5.2 학교급 각주 | `perl scripts/rejudge/aggregates_summary.pl --date 1161_20261001` |
| 격자 점유의 희박화와 연구방법 구성의 초기하 비교(<표 5> 등) | `python scripts/rejudge/rarefaction_final.py --date 1161_20261001` |
| 공백 유형, 확산대기 좌표의 기대값, 언어기능·연구방법의 규모 통제 비교(<표 6> 등) | `python scripts/rejudge/scale_checks.py --date 1161_20261001` |
| 주제군 최초 출현과 규모를 맞춘 출현 연도(<표 7> 등) | `python scripts/rejudge/keyword_diffusion.py --date 1161_20261001` |
| 독립 재판정과의 일치도(3.3, 부록 C) | `python scripts/rejudge/kappa_compute.py --date 1161_20261001 --coded data/kappa/ai2/ai2_merged_1161_20261001.json --name1 "독립 재판정"`, `python scripts/rejudge/appendix_c.py --date 1161_20261001` |
| 게재 학술지 분야(4.4.3 각주) | `perl scripts/rejudge/journal_field.pl data/rejudge/merged_1161_20261001.json`(이 파일의 5절 학교급은 초록이 없으면 달라지므로 학교급은 위 집계를 쓴다) |

**KCI 원자료가 필요한 것**

공저 네트워크와 피인용·참고문헌 표(`network_scale.py`, `tables_4to8.py`), 두 집계의 생성(`ref_aggregate.pl`, `school_level.pl`), 판정 병합과 결정 반영(`merge_rejudge.py`, `apply_*.py`), 일치도 표본의 코딩지 생성(`kappa_sample.py`)은 초록과 참고문헌 목록이 든 원자료(`data/corpus_full_merged.json`)나 중간 산출물을 입력으로 쓴다. 원자료는 수집 스크립트로 KCI Open API에서 다시 받을 수 있다(`.env.example`을 `.env`로 복사하고 인증키를 넣는다). 다만 피인용 수처럼 조회 시점에 따라 바뀌는 값이 있으므로, 원고의 값은 엑셀의 서지 정보(2026년 9월 29일 조회)와 `analysis/`의 결과 파일을 기준으로 한다.

## 재배포하지 않는 자료

- KCI에서 받은 초록과 참고문헌 목록: 저작권과 KCI 이용 조건을 고려하여 싣지 않았다. 대신 논문 식별자(artiId)와 KCI 링크를 엑셀에 두었고, 이 자료가 필요한 두 지표는 논문별 집계로 제공한다.
- 판정에 넣은 입력 묶음: 초록이 들어 있어 싣지 않았다. 판정 지침과 판정 출력은 모두 실었다.

## 판정 방식

포함 여부와 코딩은 연구자가 정한 지침(`data/rejudge/CODING_GUIDE.md`, 부록 A)에 따라 대규모 언어모델이 수행하였다. 경계 사례로 표시된 438편은 연구자가 초록을 직접 검토하여 판정을 확정하였다(엑셀 3번 시트). 같은 지침을 다른 언어모델이 확정 판정값을 보지 않고 적용한 독립 재판정과의 일치도는 부록 C에 있다. 두 판정자는 같은 계열의 언어모델이므로 이 일치도는 판정의 재현성을 보여 줄 뿐 연구자 판정과의 일치를 보여 주지 않는다.
