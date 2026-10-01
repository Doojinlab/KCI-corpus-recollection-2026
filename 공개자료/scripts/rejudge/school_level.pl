#!/usr/bin/perl
# school_level.pl — 논문별 학교급 맥락 집계(원고 5.2 첫째 각주의 공개용 입력).
#
# 초록은 재배포하지 않으므로, 제목·초록에서 판정한 학교급 표지만 논문마다 남긴다.
# 판정 규칙은 scripts/rejudge/journal_field.pl 5절과 같다(같은 정규식, 같은 필드 읽기).
#   - 초·중등: 초등·중학·고등학교·고교·중등·다문화 학생/아동(중문 小学·中学·高中)
#   - 대학: 대학(대학수학능력시험 제외)·학부·유학생·교양·전공·학문 목적(중문 大学·本科, 영문 university·undergraduate·college)
#   - 한 논문이 두 범주에 모두 들 수 있다.
#
# 사용: perl scripts/rejudge/school_level.pl [data/rejudge/merged_1161_20261001.json]
# 산출: analysis/school_level_1161_20261001.csv(UTF-8, BOM), 표준 출력에 journal_field.pl 5절과 같은 표
use strict; use warnings; use utf8;
binmode STDOUT, ':utf8';

my $path = $ARGV[0] // 'data/rejudge/merged_1161_20261001.json';
open my $fh, '<:raw', $path or die "$path: $!";
my $raw = do { local $/; <$fh> }; close $fh;
utf8::decode($raw);

my $re_school = qr/초등|중학|고등학교|고교|중등|다문화 ?(?:학생|아동)|小学|中学|高中/;
my $re_univ   = qr/대학(?!수학능력)|학부|유학생|교양|전공|학문 목적|大学|本科|university|undergraduate|college/i;
my (@rows, %ctx);
for my $r (split /\}, \{"arti_id"/, $raw) {
    my ($inc) = $r =~ /"include": "(\w*)"/;
    next unless defined $inc && $inc eq 'Y';
    my ($id) = $r =~ /(ART\d+)/;
    my ($l)  = $r =~ /"lang3": "([^"]*)"/;
    my ($ln) = $r =~ /"learner": "([^"]*)"/; $ln = '미명시' if !defined $ln || $ln eq '';
    my ($tt) = $r =~ /"title_ko": "([^"]*)"/; my ($aa) = $r =~ /"abstract_ko": "([^"]*)"/;
    my $txt = ($tt // '') . ' ' . ($aa // '');
    my $s = $txt =~ $re_school ? 1 : 0; my $u = $txt =~ $re_univ ? 1 : 0;
    push @rows, [$id, $l, ($l eq '한국어' ? $ln : ''), $s, $u];   # 학습자 맥락(L1/L2)은 한국어군에만 쓴다
    my $g = $l eq '한국어' ? "한국어($ln)" : $l;
    $ctx{$g}{n}++; $ctx{$g}{s} += $s; $ctx{$g}{u} += $u; $ctx{$g}{none}++ unless $s || $u;
}

(my $date) = $path =~ /merged_([0-9_]+)\.json$/; $date //= '1161_20261001';
my $out = "analysis/school_level_$date.csv";
open my $o, '>:encoding(UTF-8)', $out or die "$out: $!";
print $o "\x{FEFF}artiId,언어군,학습자맥락,초중등,대학\n";
print $o join(',', @$_), "\n" for sort { $a->[0] cmp $b->[0] } @rows;
close $o;

printf "확정 코퍼스 %d편 → %s\n\n", scalar(@rows), $out;
print "| 언어군 | 편수 | 초·중등 | 대학 | 둘 다 없음 |\n|---|---|---|---|---|\n";
for my $g ('영어', '한국어(L1)', '한국어(L2)', '한국어(미명시)', '중국어') {
    my $c = $ctx{$g} or next;
    printf "| %s | %d | %d | %d | %d |\n", $g, $c->{n}, $c->{s} // 0, $c->{u} // 0, $c->{none} // 0;
}
