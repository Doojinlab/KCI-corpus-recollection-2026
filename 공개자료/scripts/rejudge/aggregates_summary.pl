#!/usr/bin/perl
# aggregates_summary.pl — 공개한 논문별 집계 두 개만으로 원고의 해당 수치를 다시 계산한다.
#   analysis/ref_aggregate_<DATE>.csv  → <표 12> 언어군별 참고문헌 지식 원천(과 4.4.3 각주의 대상 편수·학술지명 없는 비율)
#   analysis/school_level_<DATE>.csv   → 5.2 첫째 각주의 학교급 편수
# 두 집계는 KCI 원자료(참고문헌 목록, 초록)에서 ref_aggregate.pl, school_level.pl로 만들었다.
#
# 사용: perl scripts/rejudge/aggregates_summary.pl [--date 1161_20261001]
use strict; use warnings; use utf8;
binmode STDOUT, ':encoding(UTF-8)';

my $DATE = '1161_20261001';
for my $i (0 .. $#ARGV) { $DATE = $ARGV[$i + 1] if $ARGV[$i] eq '--date' }
my @G = ('영어', '한국어', '중국어');

sub read_csv {
  my $f = shift;
  open my $h, '<:encoding(UTF-8)', $f or die "$f: $!";
  my $head = <$h>; $head =~ s/^\x{FEFF}//; $head =~ s/\r?\n$//;
  my @k = split /,/, $head; my @rows;
  while (my $l = <$h>) { $l =~ s/\r?\n$//; next if $l eq ''; my %r; @r{@k} = split /,/, $l, -1; push @rows, \%r }
  close $h; return @rows;
}

my @ref = read_csv("analysis/ref_aggregate_$DATE.csv");
print "## <표 12> 언어군별 참고문헌 지식 원천\n\n";
print "| 언어군 | 대상 편수 | 편당 평균 참고문헌 | 국내 | 국제(그 가운데 중문) | 학술지명 없음 | 교육 | 언어학 | 문학 | 기타 |\n";
print "|---|---|---|---|---|---|---|---|---|---|\n";
for my $g (@G) {
  my @all = grep { $_->{'언어군'} eq $g } @ref;
  my @w = grep { $_->{'참고문헌목록'} eq 'Y' } @all;
  my %s; for my $r (@w) { $s{$_} += $r->{$_} for qw(참고문헌수 국내_한글 중문_한자 그밖_국제 학술지명있음 교육 언어학 문학 기타) }
  my $n = $s{'참고문헌수'}; my $nj = $s{'학술지명있음'};
  printf "| %s | %d/%d | %.1f건 | %.1f%% | %.1f%% (%.1f%%) | %.0f%% | %.1f%% | %.1f%% | %.1f%% | %.1f%% |\n",
    $g, scalar(@w), scalar(@all), $n / @w, 100 * $s{'국내_한글'} / $n, 100 * ($s{'중문_한자'} + $s{'그밖_국제'}) / $n,
    100 * $s{'중문_한자'} / $n, 100 - 100 * $nj / $n,
    100 * $s{'교육'} / $nj, 100 * $s{'언어학'} / $nj, 100 * $s{'문학'} / $nj, 100 * $s{'기타'} / $nj;
}
print "\n국내·국제는 참고문헌 전체, 분야(교육·언어학·문학·기타)는 학술지명이 있는 문헌을 분모로 한다.\n\n";

my @sch = read_csv("analysis/school_level_$DATE.csv");
print "## 5.2 첫째 각주: 제목·초록에 드러난 학교급\n\n";
print "| 언어군 | 편수 | 초·중등 | 대학 | 둘 다 없음 |\n|---|---|---|---|---|\n";
for my $g ('영어', '한국어(L1)', '한국어(L2)', '한국어(미명시)', '중국어') {
  my @r = grep { my $k = $_->{'언어군'} eq '한국어' ? "한국어($_->{'학습자맥락'})" : $_->{'언어군'}; $k eq $g } @sch;
  next unless @r;
  my $s = grep { $_->{'초중등'} } @r; my $u = grep { $_->{'대학'} } @r; my $none = grep { !$_->{'초중등'} && !$_->{'대학'} } @r;
  printf "| %s | %d | %d | %d | %d |\n", $g, scalar(@r), $s, $u, $none;
}
print "\n한 논문이 두 범주에 모두 들 수 있다. 원고는 한국어군 가운데 외국어 학습자(L2) 연구만 보고한다.\n";
