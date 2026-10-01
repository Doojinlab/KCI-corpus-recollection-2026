#!/usr/bin/perl
# 5장 논의의 근거 점검: 게재 학술지 분야(KCI 학문 분류), 중국어군 번역×질적·사례 좌표의 저자 집중,
# 중국어군의 학교급 맥락(제목·초록 키워드).
# 입력: data/rejudge/merged_1161_20261001.json (include=='Y'가 확정 1,161편, lang3 = 언어 범주)
# 실행: perl scripts/rejudge/journal_field.pl > analysis/journal_field_1161_20261001.md
# Python이 없는 PC에서 Git for Windows에 들어 있는 perl로 계산했다. JSON::PP는 7MB 파일에서 느려
# 레코드를 '}, {"arti_id"'로 나눠 필요한 필드만 정규식으로 읽는다(필드 값에 큰따옴표가 없는 항목만 사용).
use strict; use warnings; use utf8;
binmode STDOUT, ':utf8';

my $path = $ARGV[0] // 'data/rejudge/merged_1161_20261001.json';
open my $fh, '<:raw', $path or die "$path: $!";
my $raw = do { local $/; <$fh> }; close $fh;
utf8::decode($raw);

my (%n, %lv2, %edu2, %eduany, %zh_j, %zh_field, @zh, %ctx);
my $n_abs = 0;   # 초록이 든 레코드 수(공개용 판정 파일에는 초록이 없다)
our @CTX_ORDER = ('영어', '한국어(L1)', '한국어(L2)', '한국어(미명시)', '중국어');
my $re_school = qr/초등|중학|고등학교|고교|중등|다문화 ?(?:학생|아동)|小学|中学|高中/;
my $re_univ   = qr/대학(?!수학능력)|학부|유학생|교양|전공|학문 목적|大学|本科|university|undergraduate|college/i;
for my $r (split /\}, \{"arti_id"/, $raw) {
    my ($inc) = $r =~ /"include": "(\w*)"/;
    next unless defined $inc && $inc eq 'Y';
    my ($l)  = $r =~ /"lang3": "([^"]*)"/;
    {
        my ($ln) = $r =~ /"learner": "([^"]*)"/; $ln = '미명시' if !defined $ln || $ln eq '';
        my $g = $l eq '한국어' ? "한국어($ln)" : $l;
        my ($tt) = $r =~ /"title_ko": "([^"]*)"/; my ($aa) = $r =~ /"abstract_ko": "([^"]*)"/;
        $n_abs++ if defined $aa;
        my $txt = ($tt // '') . ' ' . ($aa // '');
        my $s = $txt =~ $re_school ? 1 : 0; my $u = $txt =~ $re_univ ? 1 : 0;
        $ctx{$g}{n}++; $ctx{$g}{s} += $s; $ctx{$g}{u} += $u; $ctx{$g}{none}++ unless $s || $u;
    }
    my ($kf) = $r =~ /"kci_field": "([^"]*)"/;  $kf //= '';
    my ($j)  = $r =~ /"journal": "([^"]*)"/;    $j  //= '';
    my @p = split / > /, $kf;
    my $mid = $p[1] // '(분류 없음)';
    $n{$l}++;
    $lv2{$l}{$mid}++;
    $edu2{$l}++   if $mid eq '교육학';
    $eduany{$l}++ if $kf =~ /교육/;
    if ($l eq '중국어') {
        $zh_j{$j}++; $zh_field{$mid}++;
        my ($au) = $r =~ /"authors": "([^"]*)"/;
        my ($f)  = $r =~ /"func": "([^"]*)"/;
        my ($m)  = $r =~ /"meth": "([^"]*)"/;
        my ($y)  = $r =~ /"year": (\d+)/;
        my ($t)  = $r =~ /"title_ko": "([^"]*)"/;
        my ($ab) = $r =~ /"abstract_ko": "([^"]*)"/;
        push @zh, { au => $au // '', f => $f // '', m => $m // '', y => $y // '', t => $t // '', ab => $ab // '' };
    }
}
my @L = ('영어', '한국어', '중국어');
sub pct { sprintf '%.1f%%', 100 * $_[0] / $_[1] }

print "# 게재 학술지 분야와 중국어군 맥락 점검 — 확정 코퍼스 (1161_20261001)\n\n";
print "근거: `data/rejudge/merged_1161_20261001.json`(include=='Y'), 스크립트 `scripts/rejudge/journal_field.pl`.\n";
print "학문 분야는 KCI 서지정보의 `kci_field`(대분류 > 중분류 > …)이며, 아래 표는 중분류 기준이다.\n\n";

print "## 1. 교육학 분야 학술지에 실린 논문\n\n";
print "| 언어군 | 편수 | 교육학(중분류) | 분류 어디든 '교육' 포함(참고) |\n|---|---|---|---|\n";
for my $l (@L) {
    printf "| %s | %d | %d (%s) | %d (%s) |\n", $l, $n{$l}, $edu2{$l} // 0, pct($edu2{$l} // 0, $n{$l}), $eduany{$l} // 0, pct($eduany{$l} // 0, $n{$l});
}
print "\n- 참고 열은 분류 깊이가 논문마다 달라(예: 『중국어교육과 연구』는 '인문학 > 중국어와문학'까지만 기재) 중국어군을 과소 집계할 수 있으므로 본문에는 쓰지 않는다.\n\n";

print "## 2. 중분류 분포(언어군별 상위 6)\n\n";
for my $l (@L) {
    my @k = sort { $lv2{$l}{$b} <=> $lv2{$l}{$a} || $a cmp $b } keys %{ $lv2{$l} };
    @k = @k[0 .. ($#k < 5 ? $#k : 5)];
    print "- $l: ", join(', ', map { "$_ $lv2{$l}{$_}(" . pct($lv2{$l}{$_}, $n{$l}) . ")" } @k), "\n";
}
my $zh_lit = ($zh_field{'중국어와문학'} // 0) + ($zh_field{'통역번역학'} // 0);
printf "\n중국어군 68편 가운데 중국어와문학 %d편 + 통역번역학 %d편 = %d편(%s).\n\n",
    $zh_field{'중국어와문학'} // 0, $zh_field{'통역번역학'} // 0, $zh_lit, pct($zh_lit, $n{'중국어'});

print "## 3. 중국어군 게재 학술지\n\n";
print join(', ', map { "$_ $zh_j{$_}" } sort { $zh_j{$b} <=> $zh_j{$a} || $a cmp $b } keys %zh_j), "\n\n";

print "## 4. 중국어군 번역×질적·사례 좌표의 저자 집중\n\n";
my @tc = grep { $_->{f} eq '번역' && $_->{m} eq '질적·사례' } @zh;
my %ac;
for my $p (@tc) { for my $a (split /;\s*/, $p->{au}) { (my $k = $a) =~ s/\(.*//; $k =~ s/\s+//g; $ac{$k}++ } }
my ($top) = sort { $ac{$b} <=> $ac{$a} } keys %ac;
my @yrs = sort map { $_->{y} } @tc;
printf "- 이 좌표 %d편(%s–%s년) 가운데 %d편이 같은 저자의 연속 연구이다(저자명은 원자료에 있음).\n\n", scalar(@tc), $yrs[0], $yrs[-1], $ac{$top};

print "## 5. 학교급 맥락(제목·초록 키워드, 중복 가능)\n\n";
print "※ 이 판정 파일에는 초록이 없어 아래 학교급은 제목만으로 판정한 값이다. 원고의 값은 analysis/school_level_*.csv(제목·초록 기준)를 쓴다.\n\n" unless $n_abs;
print "초·중등: 초등·중학·고등학교·고교·중등·다문화 학생/아동(중문 小学·中学·高中). 대학: 대학(대학수학능력시험 제외)·학부·유학생·교양·전공·학문 목적(중문 大学·本科, 영문 university·undergraduate·college). 수능 문항으로 AI 성능을 본 연구는 수업 맥락이 아니므로 어느 쪽에도 넣지 않는다.\n\n";
print "| 언어군 | 편수 | 초·중등 | 대학 | 둘 다 없음 |\n|---|---|---|---|---|\n";
for my $g (@CTX_ORDER) {
    my $c = $ctx{$g} or next;
    printf "| %s | %d | %d | %d | %d |\n", $g, $c->{n}, $c->{s}, $c->{u}, $c->{none};
}
print "\n- 5장 5.2 첫째 각주의 근거다. 키워드 판정이므로 학교급이 드러나지 않은 논문(담론·성능평가 등)은 '둘 다 없음'에 들어간다.\n";
