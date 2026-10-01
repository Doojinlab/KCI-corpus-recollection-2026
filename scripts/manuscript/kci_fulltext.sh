#!/usr/bin/env bash
# KCI 원문 PDF 받기(선행연구 쪽수 확인용). 사용: scripts/manuscript/kci_fulltext.sh ART003187966 [저장 폴더]
# 논문 페이지에서 fncDown('KCI_FI…')를 찾아, 같은 세션 쿠키와 Referer로 원문 내려받기 주소를 부른다.
# 원문 파일이 없는 논문(최신호 등)은 "원문 파일 ID 없음"으로 끝난다. 받은 PDF는 저작권 때문에 저장소에 올리지 않는다.
# PDF의 한글은 글꼴 문제로 pdftotext에서 빠지는 경우가 많다. 쪽 번호는 pdftotext로, 본문은 render_pdf.ps1로 그려서 읽는다.
set -euo pipefail
A="$1"; OUT="${2:-.}"; mkdir -p "$OUT"
B="https://www.kci.go.kr/kciportal/ci/sereArticleSearch"
CK="$OUT/.kci_cookie.txt"
curl -s -L -m 60 -A "Mozilla/5.0" -c "$CK" -b "$CK" -o "$OUT/$A.html" "$B/ciSereArtiView.kci?sereArticleSearchBean.artiId=$A"
FI=$(grep -o "fncDown('KCI_FI[0-9]*')" "$OUT/$A.html" | head -1 | grep -o 'KCI_FI[0-9]*' || true)
if [ -z "$FI" ]; then echo "$A: 원문 파일 ID 없음"; exit 1; fi
curl -s -L -m 120 -A "Mozilla/5.0" -c "$CK" -b "$CK" -e "$B/ciSereArtiView.kci?sereArticleSearchBean.artiId=$A" \
  -o "$OUT/$A.pdf" "$B/ciSereArtiOrteServHistIFrame.kci?sereArticleSearchBean.artiId=$A&sereArticleSearchBean.orteFileId=$FI"
echo "$A $FI $(head -c 5 "$OUT/$A.pdf") $(stat -c %s "$OUT/$A.pdf") bytes"
