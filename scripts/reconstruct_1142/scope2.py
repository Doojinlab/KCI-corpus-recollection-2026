# -*- coding: utf-8 -*-
"""scope2 — 논문 3.2 기준(제출본)을 재현하는 스코프 판정 규칙 2판.
포함 2조건: (1) AI 도구를 언어 교육·학습·평가 맥락에서 다룸 (2) 영어·한국어·중국어 중 하나.
제외(각주 2): 제2외국어 / 메타버스·VR / AI신호부재 / 모어국어경계 / 비AI에듀테크 / 비교육 번역품질
+ 교육맥락없음(순수 NLP·언어학·문학·번역학) / 언어비특정.
한국어군 = L1 국어교육 + L2 한국어교육 (각주 3).
"""
import re, json

def R(*ps, flags=re.I):
    return re.compile('|'.join(ps), flags)

ZH = R(r'중국어', r'중어중문', r'\b중어\b', r'汉语', r'漢語', r'华语', r'華語', r'中文', r'\bCFL\b', r'\bTCFL\b', r'\bTCSL\b', r'\bHSK\b', r'chinese', r'mandarin', r'\bTOCFL\b', r'한어\b', r'중국\s*어문')
KO = R(r'한국어', r'\bKFL\b', r'\bKSL\b', r'korean (language|as a|learn|educat|teach|writ|speak|read|listen|vocab|grammar|pronun|proficien|class|student|textbook)', r'\bTOPIK\b', r'(?<![한외중])국어\s*교육', r'(?<![한외중])국어과', r'(?<![한외중])국어\s*교과', r'(?<![한외중])국어\s*수업', r'(?<![한외중])국어\s*교사', r'(?<![한외중])국어\s*학습', r'초등\s*국어', r'중등\s*국어', r'(?<![한외중])국어교육', r'화법', r'독서\s*교육', r'독서\s*지도', r'문학\s*교육', r'문학\s*수업', r'작문\s*교육', r'글쓰기\s*교육', r'글쓰기\s*수업', r'글쓰기\s*교과', r'글쓰기\s*교육과정', r'대학\s*글쓰기', r'교양\s*글쓰기', r'학술적?\s*글쓰기', r'논증적?\s*글쓰기', r'글쓰기\s*지도', r'읽기\s*교육', r'읽기\s*지도', r'읽기\s*학습', r'읽기\s*유창성', r'책읽기', r'그림책', r'시\s*쓰기', r'시\s*창작', r'문식성', r'사고와\s*표현', r'교양\s*국어', r'한글', r'우리말')
EN = R(r'영어', r'english', r'\bEFL\b', r'\bESL\b', r'\bTESOL\b', r'\bELT\b', r'\bTOEIC\b', r'\bTOEFL\b', r'\bIELTS\b', r'영작문', r'영문법', r'영문학')
OTHER = R(r'일본어', r'\b일어\b', r'일어\s*교육', r'일본어교육', r'프랑스어', r'\b불어\b', r'독일어', r'\b독어\b', r'스페인어', r'서반아어', r'러시아어', r'\b노어\b', r'베트남어', r'아랍어', r'이탈리아어', r'포르투갈어', r'태국어', r'인도네시아어', r'몽골어', r'터키어', r'튀르키예어', r'힌디어', r'japanese', r'french', r'german', r'spanish', r'russian', r'vietnamese', r'arabic', r'italian', r'portuguese', r'thai\b', r'indonesian', r'수화', r'수어', r'sign language', r'라틴어', r'latin', r'한문\s*교육', r'한문과')
FOREIGN_GENERIC = R(r'외국어', r'foreign language', r'second language', r'\bL2\b', r'다국어', r'multilingual', r'language learn', r'language educat', r'language teach', r'언어\s*교육', r'언어\s*학습', r'언어\s*교수')

FIELD_ZH = R(r'중국어와문학', r'중어중문')
FIELD_KO = R(r'한국어와문학', r'국어교육', r'한국어교육')
FIELD_EN = R(r'영어와문학', r'영어교육')
FIELD_OTHER = R(r'일본어와문학', r'프랑스어와문학', r'독일어와문학', r'스페인어와문학', r'러시아어와문학', r'기타동양어문학', r'기타서양어문학', r'베트남어')

AI_STRONG = R(r'\bAI\b', r'인공지능', r'chat\s*-?gpt', r'\bgpt', r'생성형', r'generative', r'챗봇', r'chatbot', r'chat\s*bot', r'\bLLM', r'거대\s*언어\s*모델', r'대규모\s*언어\s*모델', r'대형\s*언어\s*모델', r'초거대', r'large language model', r'language model', r'머신\s*러닝', r'기계\s*학습', r'machine learning', r'딥\s*러닝', r'deep learning', r'자동\s*채점', r'자동\s*평가', r'automated (essay )?scoring', r'automated writing evaluation', r'\bAWE\b', r'음성\s*인식', r'speech recognition', r'\bASR\b', r'기계\s*번역', r'machine translation', r'\bNMT\b', r'\bMT\b', r'번역기', r'파파고', r'papago', r'deepl', r'구글\s*번역', r'google translate', r'neural', r'뉴럴', r'\bBERT\b', r'transformer', r'트랜스포머', r'자연어\s*처리', r'\bNLP\b', r'딥시크', r'deepseek', r'어니봇', r'ernie', r'gemini', r'제미나이', r'claude', r'클로드', r'copilot', r'코파일럿', r'bard', r'바드', r'지능형', r'intelligent', r'\bITS\b', r'자동\s*피드백', r'automated feedback', r'grammarly', r'그래멀리', r'\bTTS\b', r'음성\s*합성', r'text-to-speech', r'AI\s*스피커', r'인공지능\s*스피커', r'클로바', r'clova', r'알렉사', r'alexa', r'시리\b', r'\bsiri\b', r'자연어', r'언어\s*모델', r'적응형', r'adaptive learning', r'딥\s*러닝', r'프롬프트', r'prompt', r'하이퍼클로바', r'hyperclova', r'llama', r'라마', r'midjourney', r'미드저니', r'dall', r'달리\b', r'stable diffusion', r'perplexity', r'퍼플렉시티', r'notebooklm', r'wrtn', r'뤼튼', r'suno', r'수노', r'AI\s*튜터', r'튜터링\s*시스템', r'자동\s*생성', r'automatic(ally)? generat', r'컴퓨터\s*적응', r'인공\s*지능', r'artificial intelligence', r'기계\s*독해', r'text mining', r'텍스트\s*마이닝', r'토픽\s*모델', r'감성\s*분석', r'\bELIZA\b', r'스마트\s*스피커', r'smart speaker', r'로봇', r'robot', r'음성\s*비서', r'voice assistant', r'\bAI-', r'AI\s*기반', r'AI\s*활용', r'인공지능', r'딥러닝', r'GPT')
AI_CORE = R(r'AI', r'인공\s*지능', r'chat\s*-?gpt', r'gpt', r'생성형', r'generative', r'챗봇', r'chatbot', r'LLM', r'언어\s*모델', r'language model', r'머신\s*러닝', r'기계\s*학습', r'machine learning', r'딥\s*러닝', r'deep learning', r'자동\s*채점', r'automated (essay )?scoring', r'automated writing evaluation', r'음성\s*인식', r'speech recognition', r'기계\s*번역', r'machine translation', r'번역기', r'파파고', r'papago', r'deepl', r'neural', r'BERT', r'transformer', r'딥시크', r'deepseek', r'어니봇', r'gemini', r'제미나이', r'claude', r'클로드', r'copilot', r'grammarly', r'그래멀리', r'artificial intelligence', r'지능형\s*튜터', r'intelligent tutoring', r'AI\s*스피커', r'인공지능\s*스피커', r'클로바', r'clova', r'알렉사', r'alexa', r'하이퍼클로바', r'뤼튼', r'wrtn', r'NMT', r'ASR', r'TTS', r'음성\s*합성', r'text-to-speech')
META = R(r'메타버스', r'metaverse', r'\bVR\b', r'\bAR\b', r'\bXR\b', r'\bMR\b', r'가상\s*현실', r'증강\s*현실', r'virtual reality', r'augmented reality', r'제페토', r'zepeto', r'게더타운', r'gather\s*town', r'이프랜드', r'ifland', r'가상\s*세계', r'virtual world', r'로블록스', r'roblox', r'마인크래프트', r'minecraft')
EDTECH = R(r'에듀테크', r'edtech', r'교육공학', r'플립드', r'flipped', r'블렌디드', r'blended', r'온라인\s*수업', r'온라인\s*학습', r'online (class|learn|course)', r'비대면', r'원격\s*수업', r'원격\s*교육', r'distance learn', r'\bLMS\b', r'앱\b', r'애플리케이션', r'application', r'모바일', r'mobile', r'스마트폰', r'smartphone', r'유튜브', r'youtube', r'줌\b', r'\bzoom\b', r'게이미피케이션', r'gamification', r'디지털\s*교과서', r'digital textbook', r'\bMOOC', r'K-MOOC', r'디지털\s*리터러시', r'digital literacy', r'ICT', r'테크놀로지', r'technology', r'디지털\s*도구', r'digital tool', r'소프트웨어', r'software', r'구글\s*클래스룸', r'google classroom', r'패들렛', r'padlet', r'카훗', r'kahoot', r'퀴즈렛', r'quizlet', r'디지털\s*전환', r'디지털\s*기술', r'멀티미디어', r'multimedia', r'스크래치', r'scratch', r'코딩\s*교육', r'컴퓨터\s*보조', r'\bCALL\b', r'\bMALL\b', r'웹\s*기반', r'web-based', r'하이플렉스', r'hyflex', r'디지털\s*교육', r'온라인\s*플랫폼', r'온라인\s*교육', r'e-?러닝', r'e-?learning', r'이러닝', r'화상', r'디지털')
EDU = R(r'교육', r'교수', r'학습', r'수업', r'교실', r'학습자', r'교재', r'교과', r'교사', r'교원', r'학생', r'리터러시', r'literacy', r'teach', r'learn', r'educat', r'pedagog', r'instruct', r'classroom', r'curricul', r'student', r'\bL2\b', r'\bEFL\b', r'\bESL\b', r'\bKFL\b', r'\bCFL\b', r'\bCALL\b', r'\bMALL\b', r'학교', r'school', r'대학', r'university', r'college', r'수능', r'튜터', r'tutor', r'과제', r'피드백', r'feedback', r'평가', r'assess', r'채점', r'scoring', r'\bHSK\b', r'\bTOPIK\b', r'\bTOEIC\b', r'\bTOEFL\b', r'유아', r'아동', r'children', r'초등', r'중등', r'고등', r'학교')
TRANS_ONLY = R(r'번역\s*품질', r'오역', r'번역\s*오류', r'번역학', r'번역\s*평가', r'번역\s*전략', r'번역\s*투', r'번역\s*양상', r'번역\s*비교', r'번역\s*연구', r'post-?edit', r'포스트\s*에디팅', r'포스트에디팅', r'translation quality', r'translation error', r'통역\s*품질', r'번역\s*텍스트', r'자막', r'subtitl', r'문학\s*번역', r'literary translation', r'번역가', r'통역사', r'translator', r'interpreter', r'번역\s*산업', r'번역\s*시장', r'통번역\s*산업', r'로컬라이제이션', r'localization', r'번역\s*수용', r'번역\s*방법', r'번역\s*사례', r'번역\s*문제', r'번역\s*결과', r'번역\s*수행', r'번역\s*능력', r'번역\s*성능', r'번역\s*정확', r'번역\s*차이', r'번역\s*고찰', r'번역\s*분석', r'번역\s*연구', r'번역본', r'번역문', r'역본', r'중역', r'통역\s*교육', r'번역\s*교육', r'번역\s*수업', r'번역\s*교수', r'통번역\s*교육', r'translation (teaching|education|class|pedagog|training)')
TRANS_EDU = R(r'통역\s*교육', r'번역\s*교육', r'번역\s*수업', r'번역\s*교수', r'통번역\s*교육', r'통번역\s*수업', r'통번역\s*교육', r'translation (teaching|education|class|pedagog|training|course|learner|student)', r'번역\s*학습자', r'번역\s*전공\s*학생', r'통번역\s*학과', r'번역\s*훈련', r'번역\s*과제', r'번역\s*수강', r'통번역\s*전공', r'번역\s*교재', r'교육\s*번역', r'번역\s*학습', r'학습자\s*번역', r'번역\s*활동')
NLP_ONLY = R(r'음운론', r'통사론', r'형태론', r'의미론', r'화용론', r'코퍼스\s*언어학', r'형태소\s*분석', r'구문\s*분석', r'개체명', r'어휘\s*의미망', r'corpus linguistics', r'품사\s*태깅', r'\bPOS\b', r'의존\s*구문', r'파싱', r'parsing', r'임베딩', r'embedding', r'파인튜닝', r'fine-?tun', r'데이터셋\s*구축', r'말뭉치\s*구축', r'벤치마크', r'benchmark', r'양자화', r'quantiz', r'토크나이', r'tokeniz', r'언어\s*모델\s*(성능|평가|비교)', r'어휘\s*의미', r'연어\b', r'collocation', r'담화\s*표지', r'discourse marker', r'문법성\s*판단', r'통사\s*구조', r'논항', r'화행', r'speech act', r'의미\s*분석', r'어원', r'음성학', r'phonetic', r'음향', r'acoustic')
LIT_ONLY = R(r'소설', r'시가', r'희곡', r'문학\s*작품', r'작가론', r'novel', r'poetry', r'poem', r'fiction', r'영화\s*(분석|연구|번역)', r'드라마\s*(분석|연구|번역)', r'철학', r'philosoph', r'종교', r'미학', r'신화', r'설화', r'고전\s*(문학|소설|시가)', r'사상사', r'문학\s*번역', r'literary translation', r'문학\s*연구', r'문학\s*비평', r'담론\s*분석', r'문학사')
L1_BOUNDARY = R(r'국어\s*교육', r'국어과', r'국어\s*교과', r'국어\s*수업', r'국어\s*교사', r'국어\s*학습', r'초등\s*국어', r'중등\s*국어', r'국어교육', r'화법', r'독서\s*교육', r'문학\s*교육', r'작문\s*교육', r'대학\s*글쓰기', r'교양\s*글쓰기', r'글쓰기\s*교육', r'글쓰기\s*수업', r'학술\s*글쓰기', r'글쓰기\s*교과', r'사고와\s*표현', r'의사소통\s*교육', r'교양\s*국어', r'writing education', r'writing class', r'college writing', r'academic writing', r'모어\s*화자', r'모국어', r'문식성', r'매체\s*교육', r'매체\s*문식', r'미디어\s*리터러시', r'국어')
KFL = R(r'한국어\s*교육', r'\bKFL\b', r'\bKSL\b', r'외국어로서', r'제2언어로서', r'한국어\s*학습', r'한국어\s*교재', r'한국어\s*능력', r'한국어\s*교수', r'한국어\s*수업', r'한국어\s*학습자', r'유학생', r'결혼\s*이민', r'이주민', r'다문화', r'재외동포', r'korean (language )?(education|learn|teach)', r'korean as a', r'\bTOPIK\b', r'외국인\s*학습자', r'외국인\s*유학생', r'중국인\s*학습자', r'중국인\s*유학생', r'외국인', r'foreign student', r'international student', r'한국어\s*문법', r'한국어\s*어휘', r'한국어\s*발음', r'한국어\s*쓰기', r'한국어\s*말하기', r'한국어\s*읽기', r'한국어\s*듣기', r'한국어\s*작문', r'한국어\s*번역', r'한국어\s*교사', r'한국어\s*교원', r'한국어\s*평가', r'한국어\s*학습', r'한국어\s*수준', r'한국어\s*능력', r'학습자\s*한국어', r'한국어', r'korean')

def T(r):  # 강한 텍스트: 제목·주제어
    return ' '.join(x for x in [r.get('title_ko',''), r.get('title_en',''), r.get('kw_ko',''), r.get('kw_en','')] if x)
def F(r):  # 전체 텍스트
    return ' '.join(x for x in [T(r), r.get('abstract_ko',''), r.get('abstract_en','')] if x)

def lang_hits(t, field):
    h = {}
    h['ZH'] = len(ZH.findall(t)) + (2 if FIELD_ZH.search(field) else 0)
    h['KO'] = len(KO.findall(t)) + (2 if FIELD_KO.search(field) else 0)
    h['EN'] = len(EN.findall(t)) + (2 if FIELD_EN.search(field) else 0)
    h['OT'] = len(OTHER.findall(t)) + (2 if FIELD_OTHER.search(field) else 0)
    return h

SHEET2LANG = {'중국어': 'ZH', '한국어': 'KO', '영어·외국어': 'EN', '통번역': None, '복수언어': None}
LANGNAME = {'ZH': '중국어', 'KO': '한국어', 'EN': '영어'}

EDU_STRONG = R(r'능력', r'말하기', r'쓰기', r'읽기', r'듣기', r'발음', r'어휘', r'문법', r'작문', r'회화', r'독해', r'글쓰기', r'proficien', r'skill', r'ability', r'speaking', r'writing', r'reading', r'listening', r'pronunciation', r'vocabulary', r'grammar', r'writers?', r'L2', r'교육', r'교수', r'학습', r'수업', r'교실', r'교재', r'학생', r'학습자', r'교사', r'교원', r'teach', r'learn', r'student', r'classroom', r'instruct', r'pedagog', r'educat', r'\bEFL\b', r'\bESL\b', r'\bKFL\b', r'\bCFL\b', r'리터러시', r'literacy', r'초등', r'중등', r'고등학', r'대학생', r'university', r'college', r'유아', r'아동', r'children', r'수능', r'튜터', r'tutor', r'curricul', r'교과', r'\bTOPIK\b', r'\bHSK\b', r'\bTOEIC\b', r'\bTOEFL\b', r'학교', r'school', r'피드백', r'feedback', r'과제', r'assignment', r'\bL2\b', r'\bCALL\b', r'\bMALL\b', r'훈련', r'training', r'학업', r'academic', r'예비\s*교사', r'pre-?service')
EDU_CNT = R(r'교육', r'교수', r'학습', r'수업', r'학생', r'학습자', r'교사', r'teach', r'learn', r'student', r'classroom', r'instruct', r'pedagog', r'educat')
L1_WEAK = R(r'언어\s*발달', r'언어\s*능력', r'언어\s*선별', r'스피치', r'speech\s*education', r'자기소개서', r'비속어', r'발화\s*전사', r'말하기\s*불안', r'의사소통\s*능력', r'토론\s*수업', r'토론\s*학습', r'토론학습', r'프레젠테이션', r'논술', r'서술형', r'논설문', r'요약문', r'보고서\s*작성', r'논문\s*작성', r'글쓰기', r'writing', r'읽기', r'reading', r'독서', r'문학', r'literature', r'언어', r'language')

def judge(r):
    """→ dict(include, reason, group, learner, conf, notes)"""
    t, f, field = T(r), F(r), r.get('kci_field', '') or ''
    sheet = r.get('orig_group', '')
    prior = SHEET2LANG.get(sheet)
    h = lang_hits(t, field)
    hf = lang_hits(f, field)
    ai_strong = bool(AI_STRONG.search(t))
    ai_any = ai_strong or bool(AI_CORE.search(f))
    edu_strong = bool(EDU_STRONG.search(t))
    edu_cnt = len(EDU_CNT.findall(f))
    edu = edu_strong or edu_cnt >= 3
    meta = bool(META.search(t))
    edtech = bool(EDTECH.search(t))
    notes = []
    # ── 언어군 결정 ──
    cand = {k: v for k, v in h.items() if v > 0 and k != 'OT'}
    if prior and h[prior] > 0:
        grp = prior
    elif h['OT'] > 0 and h['OT'] >= max(cand.values(), default=0) and not re.search(r'한국어\s*(교육|학습|학습자|교재|능력|수업)|KFL|KSL|중국어\s*(교육|학습|학습자|수업)|영어\s*(교육|학습|학습자|수업)|EFL|ESL', t, re.I):
        grp = 'OT'
    elif cand:
        grp = max(cand, key=cand.get)
        if prior and grp != prior:
            notes.append(f'시트{sheet}→{LANGNAME[grp]} 재배정')
    elif h['OT'] > 0:
        grp = 'OT'
    else:
        candf = {k: v for k, v in hf.items() if v > 0 and k != 'OT'}
        if prior and hf[prior] > 0:
            grp = prior; notes.append('언어표지 초록에서만')
        elif candf and max(candf.values()) >= 2:
            grp = max(candf, key=candf.get); notes.append('언어표지 초록에서만')
            if prior and grp != prior: notes.append(f'시트{sheet}→{LANGNAME[grp]} 재배정')
        elif hf['OT'] > 0 and not prior:
            grp = 'OT'
        elif L1_WEAK.search(t) and (sheet in ('한국어', '영어·외국어') or not prior):
            if re.search(r'글쓰기|writing|읽기|reading|독서|문학|literature|작문|논술|서술형|논설문', t, re.I) and edu_strong:
                grp = 'KO'; notes.append('L1 글쓰기·읽기 교육→한국어군(L1)')
            else:
                return dict(include='N', reason='모어국어경계', group='', conf=0.6, notes=notes)
        elif prior and FOREIGN_GENERIC.search(f):
            grp = prior; notes.append('언어 비특정(외국어 일반)→시트 언어군 유지')
        else:
            grp = None
    # ── 제외 판정(우선순위) ──
    if grp == 'OT':
        return dict(include='N', reason='제2외국어', group='', conf=0.9, notes=notes)
    if grp is None:
        return dict(include='N', reason='언어비특정', group='', conf=0.7, notes=notes)
    gname = LANGNAME[grp]
    if meta and not ai_strong:
        return dict(include='N', reason='메타버스VR', group=gname, conf=0.85, notes=notes)
    if not ai_any:
        if edtech:
            return dict(include='N', reason='비AI에듀테크', group=gname, conf=0.8, notes=notes)
        return dict(include='N', reason='AI신호부재', group=gname, conf=0.9, notes=notes)
    if not ai_strong and edtech:
        return dict(include='N', reason='비AI에듀테크', group=gname, conf=0.7, notes=notes)
    if not ai_strong:
        notes.append('AI 언급 초록에만')
    if not edu:
        if TRANS_ONLY.search(t) or sheet == '통번역':
            return dict(include='N', reason='번역품질', group=gname, conf=0.75, notes=notes)
        return dict(include='N', reason='교육맥락없음', group=gname, conf=0.8, notes=notes)
    trans_edu = bool(TRANS_EDU.search(f)) or edu_strong
    if sheet == '통번역' and not trans_edu:
        return dict(include='N', reason='번역품질', group=gname, conf=0.7, notes=notes + ['통번역 시트, 교육 맥락 약함'])
    if not edu_strong and TRANS_ONLY.search(t) and edu_cnt < 5:
        return dict(include='N', reason='번역품질', group=gname, conf=0.6, notes=notes)
    if not edu_strong and NLP_ONLY.search(t) and edu_cnt < 5:
        return dict(include='N', reason='교육맥락없음', group=gname, conf=0.65, notes=notes + ['NLP·언어학'])
    if not edu_strong and LIT_ONLY.search(t) and edu_cnt < 5:
        return dict(include='N', reason='교육맥락없음', group=gname, conf=0.6, notes=notes + ['문학·문화 담론'])
    learner = ''
    if grp == 'KO':
        kfl = bool(re.search(r'한국어|KFL|KSL|외국인|유학생|다문화|이주|재외|korean', t, re.I)) or bool(re.search(r'한국어\s*교육|외국인|유학생|KFL|KSL|다문화|이주|재외동포|외국어로서', f))
        l1 = bool(re.search(r'(?<![한외중])국어|글쓰기|독서|화법|문학\s*(교육|수업)|읽기\s*(교육|지도)|책읽기|그림책|시\s*쓰기|문식성|사고와\s*표현|작문\s*교육', t)) and not re.search(r'한국어|KFL|KSL|외국인|유학생|korean', t, re.I)
        learner = 'L1' if l1 else ('L2' if kfl else '미명시')
    conf = 0.9 if ai_strong and edu_strong else (0.7 if ai_strong else 0.55)
    if sheet in ('통번역', '복수언어'): conf -= 0.15
    if any('재배정' in n for n in notes): conf -= 0.1
    if any('초록에서만' in n for n in notes): conf -= 0.1
    return dict(include='Y', reason='', group=gname, learner=learner, conf=conf, notes=notes)

if __name__ == '__main__':
    import sys
    from collections import Counter
    rows = json.load(open('C:/Users/Administrator/KCI-corpus-recollection-2026/data/corpus_full_merged.json', encoding='utf-8'))
    orig = [r for r in rows if r['src'] in ('원본', '원본+보충')]
    res = [(r, judge(r)) for r in orig]
    inc = [j for r, j in res if j['include'] == 'Y']
    print('포함', len(inc), Counter(j['group'] for j in inc))
    print('제외사유', Counter(j['reason'] for r, j in res if j['include'] == 'N'))
    print('시트별 포함', Counter((r['orig_group'], j['group']) for r, j in res if j['include'] == 'Y'))
    print('시트별 제외', Counter((r['orig_group'], j['reason']) for r, j in res if j['include'] == 'N'))
    print('KO learner', Counter(j.get('learner') for j in inc if j['group'] == '한국어'))
    if len(sys.argv) > 1:
        key = sys.argv[1]  # e.g. "N:영어·외국어:언어비특정"
        inc_, sh, rs = key.split(':')
        for r, j in res:
            if j['include'] == inc_ and r['orig_group'] == sh and (j['reason'] == rs or (inc_ == 'Y' and j['group'] == rs)):
                print(' ', r['arti_id'], r['year'], '|', r['title_ko'][:60], '|', r['kw_ko'][:40], '|', ';'.join(j['notes']))
