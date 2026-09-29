# KCI AI 활용 언어교육 코퍼스 재수집 (2026-09)

논문 「AI 활용 중국어교육 연구의 현황과 공백: 영어·한국어교육과의 계량서지·네트워크 비교」
(중국언어연구 투고번호 J1_202600078)의 심사 대응을 위해, 논문 3.1의 검색 범위에 맞춰
KCI Open API로 후보 코퍼스를 다시 수집하고 상세 정보를 보강한 기록이다.

원 분석 파이프라인은 `Doojinlab/KCI-`(비공개)의 `kci_engine/`이며, 이 저장소는 그 가운데
재수집에 쓴 모듈만 복사해 담았다.

## 폴더

| 경로 | 내용 |
|---|---|
| `input/KCI_corpus_정리.xlsx` | 2026-07 1차 수집본(중국어 87 · 한국어 409 · 영어 974 · 통번역 151 · 복수언어 23). 재수집의 출발점 |
| `scripts/harvest_supp.js` | 보충 검색. 언어 표지 × AI 표지 조합 질의를 제목·주제어 필드로 전 페이지 수집 |
| `scripts/build_corpus.js` | 원본 + 보충 병합, 캐시된 articleDetail XML 파싱, 규칙 태그 부여 → `data/corpus_merged.json` |
| `scripts/build_xlsx.py` | `corpus_merged.json` → 코딩용 엑셀 |
| `scripts/kci_engine/` | KCI- 저장소에서 가져온 모듈(검색·상세·캐시·스코프·엑셀 임포트). 순수 Node, 외부 의존성 없음 |
| `data/KCI_AI언어교육_코퍼스_재수집_20260929.xlsx` | 결과 엑셀 (후보 4,255편, 코딩 열 포함) |
| `data/details.json` | 1차 수집본 1,470편(artiId 확보) |
| `data/supp_search.json`, `supp_search_log.json` | 보충 검색 결과 5,501편과 질의별 로그 |
| `data/corpus_merged.json` | 병합·보강 완료본 5,822편(초록·주제어·저자 소속·피인용·참고문헌 포함) |
| `data/kci_api_cache_rawxml.tgz` | API 원시 응답 XML 캐시(검색 페이지 + 상세 4,255건) |
| `analysis/grid_1142.json` | 제출본 그림 6(기능×방법 격자, 1,142편 기준)에서 복원한 언어군별 칸 편수 |
| `analysis/rarefaction.py` | 심사위원 2 요구 재분석: 희박화(36·39·45·54편)와 초기하 검정, 임계값 민감도 |
| `data/KCI_재수집_정직판정_20260929.xlsx` | **심사위원 제출용.** 논문 3.2 기준을 규칙+수동 판정으로 재적용한 코퍼스 1,312편(영 746·한 503·중 63). 목표치 맞춤 없음. 초록 열은 제출 전 삭제 |
| `data/KCI_논문재구성_1142_20260929.xlsx` | 참고용(제출 금지). 논문 보고값(667/421/54, 그림 6 격자)에 맞춰 절단·재배정한 것 |
| `data/KCI_코퍼스확정_20260930b.xlsx` | **심사위원 제출용(최신).** 1,644편 전편 초록 재판정·재코딩 확정 코퍼스 1,177편(영 729·한 378·중 70). 대학 교양 제외 반영. 초록 열 없음 |
| `data/KCI_코퍼스확정_20260930b_초록포함.xlsx` | 저자 검수용(초록 포함). 경계검수 시트에 저자 확정 기입 열 |
| `data/rejudge/CODING_GUIDE.md` | 재판정·코딩 지침(저자 결정 반영: [AI+언어교육]만 포함, 국어 교과 담론형 제외) |
| `data/rejudge/batches/`, `out/` | 배치 입력 60편 단위 28개와 배치별 판정 결과 |
| `data/rejudge/merged_20260930b.json` | 판정·코딩 병합 원자료(1,644편, 대학 교양 제외 반영) |
| `data/rejudge/l1/` | 한국어군 L1 145편 교양 재판정: 규칙 `L1_RULE.md`, 입력 `L1-L3.json`, 판정 `out/` |
| `scripts/rejudge/apply_l1.py` | 교양 제외 판정을 반영해 확정 코퍼스·엑셀·요약 재생성 |
| `scripts/rejudge/merge_rejudge.py` | 배치 병합·값 검증·엑셀·요약 생성 |
| `scripts/rejudge/keyword_diffusion.py` | 표 3·그림 4·4.3 재산출(규모 맞춤 최초 출현연도 포함) |
| `analysis/keyword_concepts.json` | 20개 핵심 개념 키워드 정규화표(논문 각주 10 복원) |
| `analysis/rejudge_summary_20260930.md` | 확정 코퍼스 항목별 집계와 논문 대조 |
| `analysis/keyword_diffusion_20260930.md` | 주제 확산 시차 재산출과 규모 보정 결과 |
| `코퍼스확정_20260930.md` | 확정 보고: 기준·편수 변화·유지/수정할 주장·저자 확인 사항 |
| `scripts/reconstruct_1142/` | scope2.py(규칙) → reconstruct.py [--honest] → build_recon_xlsx.py [--honest] → check_paper.py(논문 전 항목 대조) |
| `analysis/paper_targets.json` | 제출본 PDF에서 전사한 논문 보고값(표 2~12, 그림 2·3, 각주 2 등) |
| `논문대조_차이보고_20260929.md` | 재수집본과 논문의 항목별 차이 + 원고 수정 범위 |
| `RECONSTRUCTION_1142_20260929.md` | (참고용 재구성본의 방법 기록) |
| `manuscript/J1_202600078.hwp`, `.hwp.pdf` | 제출본 원고(hwp)와 PDF. 수정본은 별도 파일명으로 저장 |
| `review_response/J1_202600078_심사답변서.html` | 심사위원 3인 의견에 대한 항목별 답변 초안(제출본 기준 2판) |

## 수집 범위와 절차

1. 1차 수집본의 ①②③ 시트 1,470편을 artiId 기준으로 불러온다 (`kci_engine/import_xlsx.js`).
2. 보충 검색: 언어 표지 12종 × AI 표지 11종 + 영문·중문 제목 조합, 제목(title)과 주제어(keyword) 필드 각각.
   심사위원 2가 제안한 대체 검색어(HSK, 한자, 중국어 학습, TOPIK)와 중국어 모델명(어니봇·딥시크),
   L1 국어·글쓰기 질의를 포함한다. 질의별 KCI 건수는 엑셀 "3. 검색로그" 시트에 있다.
3. artiId로 병합·중복 제거하고 발행연도 2020–2026만 남긴다.
4. 전 편에 `articleDetail`을 호출해 초록(국·영), 주제어(국·영), 저자(소속), 발행기관, KCI 분류, DOI,
   피인용(citation-count), 참고문헌 목록을 받는다. 응답은 30일 캐시에 보존한다.
5. 규칙 태그(언어군·언어기능·연구방법·AI/교육 표지)는 제목+주제어+초록 문자열 규칙에 따른 참고값이다.
   논문 3.2의 포함·제외 기준에 따른 판정과 코딩은 엑셀의 주황색 열에 사람이 기입한다.

## 결과 요약 (2026-09-29 수집)

| 항목 | 편수 |
|---|---|
| 후보 코퍼스(2020–2026) | 4,255 |
| 그중 1차 수집본 | 1,470 |
| 그중 보충 검색 신규 | 2,785 (중국어 힌트 485 · 한국어 2,076 · 영어 224) |
| 초록 확보 | 4,215 |
| 참고문헌 블록 확보 | 3,266 (참고문헌 행 98,810) |
| 1차 수집본 중 API 질의로 재포착된 편수 | 1,149 / 1,470 |

이 파일은 최종 코퍼스(1,142편)가 아니라 그 앞 단계의 후보 코퍼스다. 보충 신규분은 대부분 범위 밖이며
스코프 판정이 필요하다.

## 재현

### 초록 재판정(2026-09-30, 현행)

```bash
python scripts/rejudge/merge_rejudge.py --date 20260930 --xlsx   # 배치 판정 병합·검증(1,232편)
python scripts/rejudge/apply_l1.py --date 20260930b              # 대학 교양 제외 반영(1,177편)
python scripts/rejudge/keyword_diffusion.py --date 20260930b --corpus data/rejudge/merged_20260930b.json
```

### 재수집(2026-09-29)

```bash
cp .env.example .env            # KCI_API_KEY=발급키
cd scripts
node kci_engine/import_xlsx.js ../input/KCI_corpus_정리.xlsx ../data/details.json
node harvest_supp.js            # → ../data/supp_search.json (캐시가 있으면 네트워크 생략)
node -e "require('./kci_engine/details_service.js').buildDetails(require('../data/details.json'),{live:true})"
node build_corpus.js            # → ../data/corpus_merged.json
cd .. && python scripts/build_xlsx.py data/out.xlsx   # openpyxl 필요
python analysis/rarefaction.py
```

캐시를 쓰려면 `data/kci_api_cache_rawxml.tgz`를 `data/cache/`로 풀어 둔다.

## 주의

- `.env`(인증키)는 커밋하지 않는다.
- 초록·참고문헌은 KCI 원자료이므로 외부 재배포 시 KCI 이용약관을 확인한다. 이 저장소는 비공개로 둔다.
- 피인용 수는 조회일 기준이며 논문 표 5·6(2026-07-01 조회)과 다를 수 있다.
