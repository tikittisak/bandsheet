#!/usr/bin/env python3
import json, re, os

TEMPLATE = '/Users/ti_am1/Vaults/ti.muse/bandsheet/_template.html'
OUT_DIR  = '/Users/ti_am1/Vaults/ti.muse/bandsheet/parkhaus108/'

CI = {"bar":"#ff3b30","bg":"#fff1f0","lbl":"#b00008"}
CV = {"bar":"#3b82f6","bg":"#eef4fd","lbl":"#1e40af"}
CP = {"bar":"#f59e0b","bg":"#fffbeb","lbl":"#78350f"}
CH = {"bar":"#ffcc00","bg":"#fffbe6","lbl":"#7a5e00"}
CB = {"bar":"#059669","bg":"#eafaf4","lbl":"#064e3b"}
CS = {"bar":"#8b5cf6","bg":"#f5f3ff","lbl":"#4c1d95"}
CR = {"bar":"#ff6b30","bg":"#fff3ed","lbl":"#8a2e00"}

def b(c,a='',h=False): return {'c':c,'a':a,'h':h}
def bs(*chords): return [b(c) for c in chords]
def sec(id,lbl,bars,col,note='',nh=True,rs=[]):
    return {'id':id,'label':lbl,'note':note,'noteHidden':nh,'lyric':'','color':col,'bars':bars,'rowSizes':rs}
def nsec(id,lbl,c1,c2='',col=None):
    return {'id':id,'type':'note','label':lbl,'cols':[c1,c2],'color':col}

def generate(slug,title,artist,key,bpm,time_sig,sections):
    with open(TEMPLATE,'r',encoding='utf-8') as f: html=f.read()
    html=html.replace('<title>New Song · Band Sheet</title>',f'<title>{title} · Band Sheet</title>')
    html=re.sub(r'(id="tb-filename"[^>]*value=")[^"]*(")',rf'\g<1>{title}\g<2>',html)
    html=re.sub(r'(id="tb-artist"[^>]*value=")[^"]*(")',rf'\g<1>— {artist}\g<2>',html)
    html=re.sub(r'(id="meta-key"[^>]*value=")[^"]*(")',rf'\g<1>{key}\g<2>',html)
    html=re.sub(r'(id="meta-bpm"[^>]*value=")[^"]*(")',rf'\g<1>{bpm}\g<2>',html)
    html=re.sub(r'(id="meta-time"[^>]*value=")[^"]*(")',rf'\g<1>{time_sig}\g<2>',html)
    sj=json.dumps(sections,ensure_ascii=False)
    start=html.index('var SECTIONS = '); end=html.index('// ── END DATA ──')
    html=html[:start]+'var SECTIONS = '+sj+';\n'+html[end:]
    with open(os.path.join(OUT_DIR,f'{slug}.html'),'w',encoding='utf-8') as f: f.write(html)
    print(f'✓ {slug}.html')

# ── 01 ดีเกินไป ──────────────────────────────────────────────────────────────
generate('01-dee-gern-pai','ดีเกินไป','Smile Buffalo','D','90','4/4',[
    sec('intro','Intro',bs('D','A','Bm','A','D','A','Bm','A'),CI,rs=[4,4]),
    sec('verse1','Verse 1',bs('D','A','Bm','Bm','D','A','Bm','Bm','Em','A','Em','A'),CV,rs=[4,4,4]),
    sec('chorus1','Chorus',bs('D','A','Bm','G|A','D','A','Bm','G'),CH,rs=[4,4]),
    sec('riff1','Riff',bs('D','A','Bm','G|A','D','A','Bm','Em','Bm'),CR,rs=[4,4]),
    sec('verse2','Verse 2',bs('D','A','Bm','Bm','D','A','Bm','Bm','Em','A','Em','A'),CV,rs=[4,4,4]),
    sec('chorus2','Chorus 2',bs('D','A','Bm','G|A','D','A','Bm','G'),CH,rs=[4,4]),
    sec('chorus3','Chorus 3',bs('D','A','Bm','G|A','D','A','Bm','G'),CH,rs=[4,4]),
    sec('post','Post-Chorus',bs('D','A','Bm','G|A','D','A','Bm','G|A'),CH,rs=[4,4]),
    sec('outro','Outro',bs('D','A','Bm','D','A','Bm','G|A','D'),CI,rs=[4,4]),
])

# ── 02 ลมหายใจ ───────────────────────────────────────────────────────────────
generate('02-lom-hai-jai','ลมหายใจ','ป๊อด โมเดิร์นด็อก','G','120','4/4',[
    sec('intro','Intro',bs('G','G','Em','Em','C','C','D7','D7'),CI,rs=[4,4]),
    sec('verse1','Verse 1',bs('G','G','Em','Em','C','C','D7','D7','G','G','Em','Em','C','C','D7','D7'),CV,rs=[4,4,4,4]),
    sec('prechorus1','Pre-Chorus',bs('Em','Em','C','C','Am','C','D7','D7'),CP,rs=[4,4]),
    sec('chorus1','Chorus',bs('G','G','Em','Em','C','C','D7','D7','G','G','Em','Em','C','C','D7','D7'),CH,rs=[4,4,4,4]),
    sec('verse2','Verse 2',bs('G','G','Em','Em','C','C','D7','D7','G','G','Em','Em','C','C','D7','D7'),CV,rs=[4,4,4,4]),
    sec('prechorus2','Pre-Chorus 2',bs('Em','Em','C','C','Am','C','D7','D7'),CP,rs=[4,4]),
    sec('chorus2','Chorus 2',bs('G','G','Em','Em','C','C','D7','D7','G','G','Em','Em','C','C','D7','D7'),CH,rs=[4,4,4,4]),
    sec('instru','Instrument',bs('G','G','Em','Em','C','C','D7','D7'),CS,rs=[4,4]),
    sec('outro','Outro',bs('G','G','Em','Em','C','C','D7','D7','G'),CI,rs=[4,4]),
])

# ── 03 ไม่บอกเธอ ─────────────────────────────────────────────────────────────
generate('03-mai-bok-thoe','ไม่บอกเธอ','Bedroom studio','D','110','4/4',[
    sec('intro','Intro',bs('D','D','Bm','Bm','G','G','A','A'),CI,rs=[4,4]),
    sec('verse1','Verse 1',bs('D','D','G','G','Bm','A','G','G','D','D','G','G','Bm','A','G','G'),CV,rs=[4,4,4,4]),
    sec('prechorus1','Pre-Chorus',bs('Em','Em','G','G','Em','Em','G','A'),CP,rs=[4,4]),
    sec('chorus1','Chorus',bs('D','D','Bm','Bm','G','G','A','A','D','D','Bm','Bm','G','G','A','A'),CH,rs=[4,4,4,4]),
    sec('solo','Solo',bs('D','D','G','G','Bm','A','G','G'),CS,rs=[4,4]),
    sec('verse2','Verse 2',bs('D','D','G','G','Bm','A','G','G','D','D','G','G','Bm','A','G','G'),CV,rs=[4,4,4,4]),
    sec('prechorus2','Pre-Chorus 2',bs('Em','Em','G','G','Em','Em','G','A'),CP,rs=[4,4]),
    sec('chorus2','Chorus 2',bs('D','D','Bm','Bm','G','G','A','A','D','D','Bm','Bm','G','G','A','A'),CH,rs=[4,4,4,4]),
    sec('bridge','Bridge',bs('D','D','Bm','Bm','G','G','A','A','D','D','Bm','Bm','G','G','A','A'),CB,rs=[4,4,4,4]),
    sec('outro','Outro',bs('D','D','G','G','Bm','A','G','G','A'),CI,rs=[4,4]),
])

# ── 04 It's My Life ──────────────────────────────────────────────────────────
generate('04-its-my-life',"It's My Life",'Bon Jovi','Bbm','120','4/4',[
    sec('intro','Intro — Tony Koon',bs('Bbm','Gb|F','Bbm','Gb|F'),CI,rs=[4]),
    sec('verse1','Verse 1',bs('Bbm','Bbm','Bbm','Gb|F','Bbm','Bbm','Bbm','Gb|F','Bbm','Bbm','Eb','Eb'),CV,rs=[4,4,4]),
    nsec('n-v1','Lyric — Verse 1','<p>This ain\'t a song for the broken-hearted<br>No silent prayer for the faith-departed<br>I ain\'t gonna be just a face in the crowd<br>You\'re gonna hear my voice / When I shout it out loud</p>','',CV),
    sec('chorus1','Chorus',bs('Bbm','Gb','Db','Ab/C','Bbm','Gb','Ab','Ab|A','Bbm','Gb','Db','Ab/C','Bbm','Gb','Ab','Ab|A'),CH,rs=[8,8]),
    nsec('n-ch1','Lyric — Chorus','<p>It\'s my life / It\'s now or never<br>I ain\'t gonna live forever<br>I just want to live while I\'m alive</p><p>It\'s my life / My heart is like the open highway<br>Like Frankie said, "I did it my way"<br>I just want to live while I\'m alive / It\'s my life</p>','',CH),
    sec('instru','Instrument Break — Tony Koon',bs('Bbm','Gb|F','Bbm','Gb|F'),CS,rs=[4]),
    sec('verse2','Verse 2',bs('Bbm','Bbm','Bbm','Gb|F','Bbm','Bbm','Bbm','Gb|F','Bbm','Bbm','Eb','Eb'),CV,rs=[4,4,4]),
    nsec('n-v2','Lyric — Verse 2','<p>This is for the ones who stood their ground<br>It\'s for Tommy and Gina who never backed down<br>Tomorrow\'s getting harder, make no mistake<br>Luck ain\'t enough, you\'ve got to make your own breaks</p>','',CV),
    sec('chorus2','Chorus 2',bs('Bbm','Gb','Db','Ab/C','Bbm','Gb','Ab','Ab|A','Bbm','Gb','Db','Ab/C','Bbm','Gb','Ab','Ab|A'),CH,rs=[8,8]),
    sec('solo','Solo — NEWWT',bs('Gb','Gb','Ab','Ab','Bbm','Bbm','Eb','Eb'),CS,rs=[4,4]),
    sec('bridge','Bridge',bs('Bbm','Bbm','Bbm','Bbm','Bbm'),CB,rs=[5]),
    nsec('n-bridge','Lyric — Bridge','<p>You better stand tall when they\'re calling you out<br>Don\'t bend, don\'t break, baby, don\'t back down</p>','',CB),
    sec('chorus3','Chorus 3',bs('Bbm','Gb','Db','Ab/C','Bbm','Gb','Ab','Ab|A','Bbm','Gb','Db','Ab/C','Bbm','Gb','Ab','Ab|A'),CH,rs=[8,8]),
    sec('chorus4','Chorus 4',bs('Bbm','Gb','Db','Ab/C','Bbm','Gb','Ab','Ab|A','Bbm','Gb','Db','Ab/C','Bbm','Gb','Ab','Ab|A'),CH,rs=[8,8]),
    sec('chorus5','Chorus 5',bs('Bbm','Gb','Db','Ab/C','Bbm','Gb','Ab','Ab|A','Bbm','Gb','Db','Ab/C','Bbm','Gb','Ab','Ab|A'),CH,rs=[8,8]),
    sec('chorus6','Chorus 6',bs('Bbm','Gb','Db','Ab/C','Bbm','Gb','Ab','Ab|A','Bbm','Gb','Db','Ab/C','Bbm','Gb','Ab','Ab|A'),CH,rs=[8,8]),
])

# ── 05 เกือบ ──────────────────────────────────────────────────────────────────
generate('05-keuab','เกือบ','Groove riders','E','85','4/4',[
    sec('intro','Intro',bs('E','A'),CI,rs=[2]),
    sec('verse1','Verse 1',bs('E','A','E','A','E','A','E','A','E','A','E','A','G#m|F#m','E'),CV,rs=[4,4,4,2]),
    sec('chorus1','Chorus',bs('A','G#m','F#m','E','A','G#m','F#m','B'),CH,rs=[4,4]),
    sec('instru','Instrument Break',bs('E','A','E','A'),CS,rs=[4]),
    sec('verse2','Verse 2',bs('E','A','E','A','E','A','G#m|F#m','E'),CV,rs=[4,4]),
    sec('chorus2','Chorus 2',bs('A','G#m','F#m','E','A','G#m','F#m','B'),CH,rs=[4,4]),
    sec('riff','Riff + Drum',bs('B','B','B','B'),CR,rs=[4]),
    sec('solo','Solo',bs('E','A','E','A','E','A','G#m|F#m','E'),CS,rs=[4,4]),
    sec('chorus3','Chorus 3',bs('A','G#m','F#m','E','A','G#m','F#m','B'),CH,rs=[4,4]),
    sec('chorus4','Chorus 4',bs('A','G#m','F#m','E','A','G#m','F#m','B'),CH,rs=[4,4]),
    sec('outro','Outro',bs('A','G#m','F#m','E','A','G#m','F#m','B','E'),CI,rs=[4,4]),
])

# ── 06 Birds Of A Feather ────────────────────────────────────────────────────
generate('06-birds-of-a-feather','Birds Of A Feather','Billie Eilish','D','105','4/4',[
    sec('intro','Intro',bs('D','D'),CI,rs=[2]),
    sec('verse1','Verse 1',bs('D','D','Bm','Bm','Em','Em','A','A','D','D','Bm','Bm','Em','Em','A','A'),CV,rs=[4,4,4,4]),
    sec('refrain','Refrain',bs('D','D','Bm','Bm','Em','Em','A','A'),CP,rs=[4,4]),
    sec('prechorus1','Pre-Chorus',bs('D','D','Bm','Bm','Em','Em','A','A'),CP,rs=[4,4]),
    sec('chorus1','Chorus',bs('D','D','Bm','Bm','Em','Em','A','A'),CH,rs=[4,4]),
    sec('verse2','Verse 2',bs('D','D','Bm','Bm','Em','Em','A','A','D','D','Bm','Bm','Em','Em','A','A'),CV,rs=[4,4,4,4]),
    sec('prechorus2','Pre-Chorus 2',bs('D','D','Bm','Bm','Em','Em','A','A'),CP,rs=[4,4]),
    sec('chorus2','Chorus 2',bs('D','D','Bm','Bm','Em','Em','A','A'),CH,rs=[4,4]),
    sec('postchor','Post-Chorus',bs('D','D','Bm','Bm','Em','Em','A','A'),CH,rs=[4,4]),
    sec('outro','Outro',bs('D','D','Bm','Bm','Em','Em','A','A'),CI,rs=[4,4]),
])

# ── 07 She Will Be Loved ─────────────────────────────────────────────────────
generate('07-she-will-be-loved','She Will Be Loved','Maroon 5','Cm','105','4/4',[
    sec('intro','Intro',bs('Cm','Bb','Cm','Bb'),CI,rs=[4]),
    sec('verse1','Verse 1',bs('Cm','Bb','Cm','Bb','Cm','Bb','Cm','Bb','Cm','Bb','Cm','Bb','Cm','Bb','Cm','Bb'),CV,rs=[4,4,4,4]),
    sec('chorus1','Chorus',bs('Eb','Bb','Cm','Bb','Eb','Bb','Cm','Ab','Eb','Bb','Cm','Bb'),CH,rs=[4,4,4]),
    sec('verse2','Verse 2',bs('Cm','Bb','Cm','Bb','Cm','Bb','Cm','Bb','Cm','Bb','Cm','Bb','Cm','Bb','Cm','Bb'),CV,rs=[4,4,4,4]),
    sec('chorus2','Chorus 2',bs('Eb','Bb','Cm','Bb','Eb','Bb','Cm','Ab','Eb','Bb','Cm','Bb'),CH,rs=[4,4,4]),
    sec('bridge','Bridge',bs('Cm','Bb','Cm','Bb','Cm','Bb','Cm','Bb','Cm','Bb','Ab','Ab'),CB,rs=[4,4,4]),
    sec('chorus3','Chorus 3',bs('Eb','Bb','Cm','Bb','Eb','Bb','Cm','Ab','Eb','Bb','Cm','Bb'),CH,rs=[4,4,4]),
    sec('outro','Outro',bs('Eb','Bb','Cm','Bb','Eb','Bb','Cm','Ab','Abmaj7','Ab'),CI,rs=[4,4,2]),
])

# ── 08 Shallow ───────────────────────────────────────────────────────────────
generate('08-shallow','Shallow','Lady Gaga, Bradley Cooper','Em','96','4/4',[
    sec('intro','Intro',bs('Em7','D/F#','G','G','C','G','D'),CI,rs=[4,3]),
    sec('verse1','Verse 1',bs('Em7','D/F#','G','C','G','D','Em7','D/F#','G','C','G','D'),CV,rs=[4,4,4]),
    sec('prechorus1','Pre-Chorus',bs('Em7','D/F#','G','C','G','D','Em7','D/F#','G','C','G','D'),CP,rs=[4,4,4]),
    sec('instru','Instrument Break',bs('Em7','D/F#','G','G','Em7','D/F#','G','G'),CS,rs=[4,4]),
    sec('verse2','Verse 2',bs('Em7','D/F#','G','C','G','D','Em7','D/F#','G','C','G','D'),CV,rs=[4,4,4]),
    sec('prechorus2','Pre-Chorus 2',bs('Em7','D/F#','G','C','G','D','Em7','D/F#','G','C','G','D'),CP,rs=[4,4,4]),
    sec('chorus1','Chorus',bs('Am','D/F#','G','D','Em','Am','D/F#','G','D','Em'),CH,rs=[5,5]),
    sec('postchor1','Post-Chorus',bs('Am','D/F#','G','D','Em','Am','D/F#','G','D','Em'),CH,rs=[5,5]),
    sec('bridge','Bridge',bs('Em','Bm','D','A','Em','Bm','D','A'),CB,rs=[4,4]),
    sec('chorus2','Chorus 2',bs('Am','D/F#','G','D','Em','Am','D/F#','G','D','Em'),CH,rs=[5,5]),
    sec('postchor2','Post-Chorus 2',bs('Am','D/F#','G','D','Em','Am','D/F#','G','D','Em'),CH,rs=[5,5]),
    sec('outro','Outro',bs('Em7','D/F#','G','Em7','D/F#','G'),CI,rs=[3,3]),
])

# ── 09 Ride ──────────────────────────────────────────────────────────────────
generate('09-ride','Ride','HYBS','Eb','78','4/4',[
    sec('intro-drum','Intro — กลอง',bs('Eb','Eb'),CI,rs=[2]),
    sec('intro','Intro',bs('Fm7','Bb7','Ebmaj7','C9','Fm7','Bb7','Ebmaj7','C9'),CI,rs=[4,4]),
    sec('verse1','Verse 1',bs('Fm7','Bb7','Ebmaj7','C9','Fm7','Bb7','Ebmaj7','C9'),CV,rs=[4,4]),
    sec('leadin1','Lead-in',bs('Fm7','Bb7'),CV,rs=[2]),
    sec('chorus1','Chorus',bs('Fm7','Bb7','Ebmaj7','C9','Fm7','Bb7','Ebmaj7','C9'),CH,rs=[4,4]),
    sec('verse2','Verse 2',bs('Fm7','Bb7','Ebmaj7','C9','Fm7','Bb7','Ebmaj7','C9'),CV,rs=[4,4]),
    sec('leadin2','Lead-in 2',bs('Fm7','Bb7'),CV,rs=[2]),
    sec('chorus2','Chorus 2',bs('Fm7','Bb7','Ebmaj7','C9','Fm7','Bb7','Ebmaj7','C9'),CH,rs=[4,4]),
    sec('outro','Outro',bs('Fm7','Bb7','Ebmaj7','C9','Fm7','Bb7','Ebmaj7','C9'),CI,rs=[4,4]),
])

# ── 10 If I Ain't Got You ────────────────────────────────────────────────────
generate('10-if-i-aint-got-you',"If I Ain't Got You",'Alicia Keys','G','118','3/4',[
    sec('intro','Intro',bs('Cmaj7','Bm7','Am7','Gmaj7','Cmaj7','Bm7','Am7','Gmaj7'),CI,rs=[4,4]),
    sec('verse1','Verse 1',bs('Gmaj7','Em','Am7','D9','Gmaj7','Abdim','Am7','D9'),CV,rs=[4,4]),
    nsec('n-v1','Lyric — Verse 1','<p>Some people live for the fortune<br>Some people live just for the fame<br>Some people live for the power, yeah<br>Some people live just to play the game</p>','',CV),
    sec('prechorus1','Pre-Chorus',bs('Gmaj7|Am7','Bm7|Am7','Gmaj7|Am7','Bm7','Gmaj7|Am7','Bm7|Am7','Gmaj7|Am7','Bm7'),CP,rs=[4,4]),
    nsec('n-pc1','Lyric — Pre-Chorus','<p>Some people think that the physical things / Define what\'s within<br>And I\'ve been there before, but that life\'s a bore / So full of the superficial</p>','',CP),
    sec('chorus1','Chorus',bs('Cmaj7','Bm7','Am7','Gmaj7','Cmaj7','Bm7','Am7','Gmaj7'),CH,rs=[4,4]),
    nsec('n-ch1','Lyric — Chorus','<p>want it all / But I don\'t want nothin\' at all<br>If it ain\'t you, baby / If I ain\'t got you, baby</p><p>Some people want diamond rings / Some just want everything<br>But everything means nothin\' / If I ain\'t got you, yeah</p>','',CH),
    sec('verse2','Verse 2',bs('Gmaj7','Em','Am7','D9','Gmaj7','Abdim','Am7','D9'),CV,rs=[4,4]),
    nsec('n-v2','Lyric — Verse 2','<p>Some people search for a fountain / That promises forever young<br>Some people need three dozen roses<br>And that\'s the only way to prove you love them</p>','',CV),
    sec('prechorus2','Pre-Chorus 2',bs('Gmaj7|Am7','Bm7|Am7','Gmaj7|Am7','Bm7','Gmaj7|Am7','Bm7|Am7','Gmaj7|Am7','Bm7'),CP,rs=[4,4]),
    nsec('n-pc2','Lyric — Pre-Chorus 2','<p>Hand me the world on a silver platter / And what good would it be?<br>With no one to share / With no one who truly cares for me</p>','',CP),
    sec('chorus2','Chorus 2',bs('Cmaj7','Bm7','Am7','Gmaj7','Cmaj7','Bm7','Am7','Gmaj7'),CH,rs=[4,4]),
    sec('chorus3','Chorus 3',bs('Cmaj7','Bm7','Am7','Gmaj7','Cmaj7','Bm7','Am7','Gmaj7'),CH,rs=[4,4]),
    sec('chorus4','Chorus 4',bs('Cmaj7','Bm7','Am7','Gmaj7','Cmaj7','Bm7','Am7','Gmaj7'),CH,rs=[4,4]),
    sec('chorus5','Chorus 5',bs('Cmaj7','Bm7','Am7','Gmaj7','Cmaj7','Bm7','Am7','Gmaj7'),CH,rs=[4,4]),
    sec('outro','Outro',bs('Cmaj7','Bm7','Am7','Gmaj7','Cmaj7','Bm7','Am7','Gmaj7','Gmaj7'),CI,rs=[4,4]),
])

# ── 11 Saving All My Love For You ────────────────────────────────────────────
generate('11-saving-all-my-love','Saving All My Love For You','Whitney Houston','A','99','4/4',[
    sec('intro','Intro',bs('A','F#m7','Bm7','E7sus4'),CI,rs=[4]),
    sec('verse1','Verse 1',bs('A','F#m7','Bm7','E7sus4','A','E/G#','F#m7','E','Gm7','C#7','D','C#m7','Bm'),CV,rs=[4,5,4]),
    sec('instru','Instrument Break',bs('A','F#m7','Bm7','E7sus4'),CS,rs=[4]),
    sec('verse2','Verse 2',bs('A','F#m7','Bm7','E7sus4','A','F#m7','B7/D','F#m7','B7/D','A','E/G#','F#m7','E','Gm7','C#7','D','C#m7','Bm'),CV,rs=[4,5,4,4]),
    sec('bridge','Bridge',bs('G#m7b5','C#7','D#m7','G#7','A','F#m7','Bm7','E7sus4','Amaj7'),CB,rs=[2,2,2,2]),
    sec('solo','Solo',bs('A','F#m7','Bm7','E7sus4'),CS,rs=[4]),
    sec('verse3','Verse 3',bs('A','F#m7','Bm7','E7sus4','A','F#m7','B7/D','F#m7','B7/D','A','E/G#','F#m7','E','Gm7','C#7','D','C#m7','Bm'),CV,rs=[4,5,4,4]),
    sec('outro','Outro',bs('A','F#m7','Bm7','E7','A','F#m7','Bm7','E7'),CI,rs=[4,4]),
])

# ── 12 Versace On The Floor ──────────────────────────────────────────────────
generate('12-versace-on-the-floor','Versace On The Floor','Bruno Mars','D','87','4/4',[
    sec('verse1','Verse 1',bs('D','F#m','Gmaj7','A','D','F#m','Gmaj7','A','Am7','B','Gmaj7','Gm','Em7','Bm','Asus4','A'),CV,rs=[4,4,4,4]),
    sec('prechorus1','Pre-Chorus',bs('Gmaj7','Aadd9','Gmaj7','Am7','D7','Gmaj7','F#m7','B7','Em7','F#m','Gmaj7','D'),CP,rs=[5,5,2]),
    sec('chorus1','Chorus',bs('D','F#m','Gmaj7','Gmaj7','A','D','F#m','Gmaj7','Gmaj7','A'),CH,rs=[5,5]),
    sec('verse2','Verse 2',bs('D','F#m','Gmaj7','A','D','F#m','Gmaj7','A','Am7','B','Gmaj7','Gm','Em7','Bm','Asus4','A'),CV,rs=[4,4,4,4]),
    sec('prechorus2','Pre-Chorus 2',bs('Gmaj7','Aadd9','Gmaj7','Am7','D7','Gmaj7','F#m7','B7','Em7','F#m','Gmaj7','D'),CP,rs=[5,5,2]),
    sec('chorus2','Chorus 2',bs('D','F#m','Gmaj7','Gmaj7','A','D','F#m','Gmaj7','Gmaj7','A'),CH,rs=[5,5]),
    sec('solo','Solo',bs('Gmaj7','A','Bm','Em','A','Em','A','D','F#m','Em','A'),CS,rs=[4,4,3]),
    sec('bridge','Bridge',bs('Ab','Bb','Ab','Bb','Fm','Cm','Ab','Ab'),CB,rs=[4,4]),
    sec('chorus3','Chorus 3 (Eb)',bs('Eb','Gm','Ab','Abmaj7','Bb','Eb','Gm','Ab','Abmaj7','Bb'),CH,rs=[5,5]),
    sec('outro','Outro',bs('B','Ebm','Emaj7','Emaj7'),CI,rs=[4]),
])

# ── 13 Get Lucky ─────────────────────────────────────────────────────────────
generate('13-get-lucky','Get Lucky','Daft Punk','Am','116','4/4',[
    sec('intro','Intro',bs('Am','C','Em','D','Am','C','Em','D'),CI,rs=[4,4]),
    sec('verse1','Verse 1',bs('Am','C','Em','D','Am','C','Em','D'),CV,rs=[4,4]),
    sec('prechorus1','Pre-Chorus',bs('Am','C','Em','D','Am','C','Em','D'),CP,rs=[4,4]),
    sec('chorus1','Chorus',bs('Am','C','Em','D','Am','C','Em','D','Am','C','Em','D'),CH,rs=[4,4,4]),
    sec('riff','Riff',bs('Am','C','Em','D'),CR,rs=[4]),
    sec('verse2','Verse 2',bs('Am','C','Em','D','Am','C','Em','D'),CV,rs=[4,4]),
    sec('prechorus2','Pre-Chorus 2',bs('Am','C','Em','D','Am','C','Em','D'),CP,rs=[4,4]),
    sec('chorus2','Chorus 2',bs('Am','C','Em','D','Am','C','Em','D'),CH,rs=[4,4]),
    sec('bridge','Bridge — Sync Vocal',bs('Am','C','Em','D','Am','C','Em','D','Am','C','Em','D','Am','C','Em','D'),CB,rs=[4,4,4,4]),
    sec('prechorus3','Pre-Chorus 3',bs('Am','C','Em','D','Am','C','Em','D'),CP,rs=[4,4]),
    sec('chorus3','Chorus 3',bs('Am','C','Em','D','Am','C','Em','D','Am','C','Em','D','Am','C','Em','D'),CH,rs=[4,4,4,4]),
    sec('outro','Outro',bs('Am','C','Em','D','Am','C','Em','D','Am','C','Em','D'),CI,rs=[4,4,4]),
])

# ── 14 Love Story ────────────────────────────────────────────────────────────
generate('14-love-story','Love Story','Taylor Swift','D','119','4/4',[
    sec('intro','Intro',bs('D','D','A','A','Bm','Bm','G','G'),CI,rs=[4,4]),
    sec('verse1','Verse 1',bs('D','D','G','G','Bm','Bm','G','G','D','D','G','G','Bm','Bm','G','G'),CV,rs=[4,4,4,4]),
    sec('prechorus1','Pre-Chorus',bs('G','A','Bm','D','G','A','Bm','G','A'),CP,rs=[4,4]),
    sec('chorus1','Chorus',bs('D','D','A','A','Bm','Bm','G','A'),CH,rs=[4,4]),
    sec('instru','Instrument',bs('D','D'),CS,rs=[2]),
    sec('verse2','Verse 2',bs('D','D','G','G','Bm','Bm','A','A'),CV,rs=[4,4]),
    sec('prechorus2','Pre-Chorus 2',bs('G','A','Bm','D','G','A','Bm','G','A'),CP,rs=[4,4]),
    sec('chorus2','Chorus 2',bs('D','D','A','A','Bm','Bm','G','A'),CH,rs=[4,4]),
    sec('chorus3','Chorus 3',bs('D','D','A','A','Bm','Bm','G','A'),CH,rs=[4,4]),
    sec('instru2','Instrument 2',bs('D','D','A','A','Bm','Bm','G','A'),CS,rs=[4,4]),
    sec('bridge','Bridge',bs('Bm','D','G','A','Bm','D','G','A'),CB,rs=[4,4]),
    sec('chorus4','Chorus 4',bs('D','D','A','A','Bm','Bm','G','A'),CH,rs=[4,4]),
    sec('chorus5','Chorus 5 (E)',bs('E','E','B','B','C#m','C#m','A','B'),CH,rs=[4,4]),
    sec('outro','Outro',bs('E','E','B','B','C#m','C#m','A','B','E'),CI,rs=[4,4]),
])

# ── 15 Just The Two Of Us ────────────────────────────────────────────────────
generate('15-just-the-two-of-us','Just The Two Of Us','Grover Washington Jr. feat. Bill Withers','E','87','4/4',[
    sec('intro','Instrument',bs('Emaj7','D#7','G#m7','F#m7|B7','Emaj7','D#7','G#m7','F#m7|B7'),CS,rs=[4,4]),
    sec('verse1','Verse 1',bs('Emaj7','D#7','G#m7','F#m7|B7','Emaj7','D#7','G#m7','F#m7|B7','Emaj7','D#7','G#m7','F#m7|B7','Emaj7','D#7','G#m7','F#m7|B7'),CV,rs=[4,4,4,4]),
    sec('chorus1','Chorus',bs('Emaj7','D#7','G#m7|Gm7','F#m7|B7','Emaj7','D#7','G#m7|Gm7','F#m7|B7'),CH,rs=[4,4]),
    sec('verse2','Verse 2',bs('Emaj7','D#7','G#m7','F#m7|B7','Emaj7','D#7','G#m7','F#m7|B7'),CV,rs=[4,4]),
    sec('chorus2','Chorus 2',bs('Emaj7','D#7','G#m7|Gm7','F#m7|B7','Emaj7','D#7','G#m7|Gm7','F#m7|B7'),CH,rs=[4,4]),
    sec('solo','Solo',bs('Emaj7','D#7','Dmaj7','C#sus4','Cmaj7','B7','Emaj7','A'),CS,rs=[4,4]),
    sec('bass-solo','Bass Solo',bs('G#m7'),CS,rs=[1]),
    sec('verse3','Verse 3',bs('Emaj7','D#7','G#m7','F#m7|B7','Emaj7','D#7','G#m7','F#m7|B7'),CV,rs=[4,4]),
    sec('chorus3','Chorus 3',bs('Emaj7','D#7','G#m7|Gm7','F#m7|B7','Emaj7','D#7','G#m7|Gm7','F#m7|B7'),CH,rs=[4,4]),
    sec('interlude','Interlude',bs('Emaj7','D#7','G#m7|Gm7','F#m7|B7','Emaj7','D#7','Dmaj7','C#sus4'),CI,rs=[4,4]),
    sec('outro','Outro — Solo',bs('Emaj7','D#7','Dmaj7','C#sus4','Cmaj7','B7','Emaj7','A','Emaj7','D#7','Dmaj7','C#sus4','Cmaj7','B7','Emaj7','A'),CS,rs=[4,4,4,4]),
])

# ── 17 ลุ่มหลง ───────────────────────────────────────────────────────────────
generate('17-lum-long','ลุ่มหลง','PARKHAUS108','C','90','4/4',[
    sec('intro-drum','Intro — กลอง',bs('Dm9','G9'),CI,rs=[2]),
    sec('intro','Intro',bs('Dm9','G9','Cmaj7','A7b9','Dm9','G9','Cmaj7','A7b9'),CI,rs=[4,4]),
    sec('verse1','Verse 1',bs('Dm9','G9','Cmaj7','A7b9','Dm9','G9','Cmaj7','A7b9'),CV,rs=[4,4]),
    sec('prechorus1','Pre-Chorus',bs('Dm9','G9','Cmaj7','A7b9','Dm9','Em7','Fmaj7','A7b9'),CP,rs=[4,4]),
    sec('chorus1','Chorus',bs('Dm9','G9','Cmaj7','A7b9','Dm9','G9','Cmaj7','A7b9'),CH,rs=[4,4]),
    sec('instru','Instrument',bs('Dm9','G9','Cmaj7','A7b9'),CS,rs=[4]),
    sec('verse2','Verse 2',bs('Dm9','G9','Cmaj7','A7b9','Dm9','G9','Cmaj7','A7b9'),CV,rs=[4,4]),
    sec('prechorus2','Pre-Chorus 2',bs('Dm9','G9','Cmaj7','A7b9','Dm9','Em7','Fmaj7','A7b9'),CP,rs=[4,4]),
    sec('chorus2','Chorus 2',bs('Dm9','G9','Cmaj7','A7b9','Dm9','G9','Cmaj7','A7b9'),CH,rs=[4,4]),
    sec('postchor1','Post-Chorus',bs('Dm9','G9','Cmaj7','A7b9'),CH,rs=[4]),
    sec('solo','Solo',bs('Dm9','G9','Cmaj7','A7b9','Dm9','G9','Cmaj7','A7b9'),CS,rs=[4,4]),
    sec('prechorus3','Pre-Chorus 3',bs('Dm9','G9','Cmaj7','A7b9','Dm9','Em7','Fmaj7','A7b9'),CP,rs=[4,4]),
    sec('chorus3','Chorus 3',bs('Dm9','G9','Cmaj7','A7b9','Dm9','G9','Cmaj7','A7b9'),CH,rs=[4,4]),
    sec('postchor2','Post-Chorus 2',bs('Dm9','G9','Cmaj7','A7b9'),CH,rs=[4]),
    sec('outro','Outro',bs('Dm9','G9','Cmaj7','A7b9','Dm9'),CI,rs=[4]),
])

# ── 18 เคย ───────────────────────────────────────────────────────────────────
generate('18-koey','เคย','ออดี้','C','90','4/4',[
    sec('intro','Intro',bs('C','C','Am','Am','F','F','C','C'),CI,rs=[4,4]),
    sec('verse1','Verse 1',bs('C','C','Am','Am','F','F','C','C','C','C','Am','Am','F','F','C','C'),CV,rs=[4,4,4,4]),
    sec('chorus1','Chorus',bs('C','C','Am','Am','F','F','C','F','G'),CH,rs=[4,4]),
    sec('instru','Instrument',bs('C','C','Am','Am','F','F','C','C'),CS,rs=[4,4]),
    sec('verse2','Verse 2',bs('C','C','Am','Am','F','F','C','C','C','C','Am','Am','F','F','C','C'),CV,rs=[4,4,4,4]),
    sec('chorus2','Chorus 2',bs('C','C','Am','Am','F','F','C','F','G'),CH,rs=[4,4]),
    sec('chorus3','Chorus 3',bs('C','C','Am','Am','F','F','C','F','G'),CH,rs=[4,4]),
    sec('pre-solo','Pre-Solo',bs('G','G','G','G','G','G','G','G','G','G'),CS,rs=[4,4]),
    sec('solo','Solo',bs('C','C','Am','Am','F','F','C','C','C','C','Am','Am','F','F','C','C'),CS,rs=[4,4,4,4]),
    sec('bridge','Bridge',bs('C','C','Am','Am','F','F','C','C'),CB,rs=[4,4]),
    sec('chorus4','Chorus 4',bs('C','C','Am','Am','F','F','C','F','G'),CH,rs=[4,4]),
    sec('chorus5','Chorus 5',bs('C','C','Am','Am','F','F','C','F','G'),CH,rs=[4,4]),
    sec('outro','Outro',bs('C','C','Am','Am','F','F','C','C','C'),CI,rs=[4,4]),
])

# ── 19 โกหก ──────────────────────────────────────────────────────────────────
generate('19-gohok','โกหก','Tatoo Color','A','120','4/4',[
    sec('intro','Intro',bs('Bm','E','A','Bm','E','A','Bm','E','A'),CI,rs=[3,3,3]),
    sec('verse1','Verse 1',bs('Bm','E','A','C#m-Cm','Bm','E','A','C#m-Cm'),CV,rs=[4,4]),
    sec('chorus1','Chorus',bs('D','C#m','Bm','F#','D','C#m','Bm','B','E','E','C#m','Cm'),CH,rs=[4,4,4]),
    sec('verse2','Verse 2',bs('Bm','E','A','C#m-Cm','Bm','E','A','C#m-Cm'),CV,rs=[4,4]),
    sec('riff','Riff',bs('Bm','E','A','Bm','E','A','Bm','E','A'),CR,rs=[3,3,3]),
    sec('solo','Solo',bs('D','C#m','Bm','F#','D','C#m','Bm','A'),CS,rs=[4,4]),
    sec('chorus2','Chorus 2',bs('D','C#m','Bm','F#','D','C#m','Bm','B','E','E','C#m','Cm'),CH,rs=[4,4,4]),
    sec('verse3','Verse 3',bs('Bm','E','A','C#m-Cm','Bm','E','A','C#m-Cm'),CV,rs=[4,4]),
    sec('chorus3','Chorus 3',bs('D','C#m','Bm','F#','D','C#m','Bm','B','Bm','C#m','Bm','E'),CH,rs=[4,4,4]),
    sec('outro','Outro',bs('D','C#m','Bm','A','A'),CI,rs=[4]),
])

# ── 20 สบายดี ─────────────────────────────────────────────────────────────────
generate('20-sabai-dee','สบายดี','ป้าง','A','122','4/4',[
    sec('intro','Intro',bs('A','A','F#m','F#m','A','A','F#m','F#m'),CI,rs=[4,4]),
    sec('verse1','Verse 1',bs('A','A','F#m','F#m','A','A','F#m','F#m','D','D','E','E','D','D','E','E'),CV,rs=[4,4,4,4]),
    sec('chorus1','Chorus',bs('A','A','F#m','F#m','D','D','E','E','A','A','F#m','F#m','D','D','E','E'),CH,rs=[4,4,4,4]),
    sec('interlude','Interlude',bs('A','A','F#m','F#m','A','A','F#m','F#m'),CI,rs=[4,4]),
    sec('verse2','Verse 2',bs('A','A','F#m','F#m','A','A','F#m','F#m','D','D','E','E','D','D','E','E'),CV,rs=[4,4,4,4]),
    sec('chorus2','Chorus 2',bs('A','A','F#m','F#m','D','D','E','E','A','A','F#m','F#m','D','D','E','E'),CH,rs=[4,4,4,4]),
    sec('instru','Instrument',bs('A','A','F#m','F#m','D','D','E','E','A','A','F#m','F#m','D','D','E','E'),CS,rs=[4,4,4,4]),
    sec('outro','Outro',bs('A','A','F#m','F#m'),CI,rs=[4]),
])

# ── 21 บุษบา ──────────────────────────────────────────────────────────────────
generate('21-busbaa','บุษบา','โมเดิร์นด็อก','Bm','116','4/4',[
    sec('riff','Riff — Guitar',bs('Bm','D','G','F#','Bm','D','G','F#','Bm','D','G','F#','Bm','D','G','F#'),CR,rs=[4,4,4,4]),
    sec('intro','Intro',bs('Bm','D','G','F#','Bm','D','G','F#','Bm','D','G','F#','Bm','D','G','F#'),CI,rs=[4,4,4,4]),
    sec('verse1','Verse 1',bs('Bm','D','G','F#','Bm','D','F#','E','Bm','D','F#','E','Bm','D','G','F#'),CV,rs=[4,4,4,4]),
    sec('instru1','Instrument',bs('Bm','D','G','F#','Bm','D','G','F#','Bm','D','G','F#','Bm','D','G','F#'),CS,rs=[4,4,4,4]),
    sec('chorus1','Chorus',bs('Bm','D','G','F#','Bm','D','G','F#','Bm','D','G','F#','Bm','D','G','F#'),CH,rs=[4,4,4,4]),
    sec('instru2','Instrument 2',bs('Bm','D','G','F#','Bm','D','G','F#','Bm','D','G','F#','Bm','D','G','F#'),CS,rs=[4,4,4,4]),
    sec('verse2','Verse 2',bs('Bm','D','G','F#','Bm','D','F#','E','Bm','D','F#','E','Bm','D','G','F#'),CV,rs=[4,4,4,4]),
    sec('chorus2','Chorus 2',bs('Bm','D','G','F#','Bm','D','G','F#','Bm','D','G','F#','Bm','D','G','F#'),CH,rs=[4,4,4,4]),
    sec('solo','Solo',bs('Bm','D','G','F#','Bm','D','G','F#','Bm','D','G','F#','Bm','D','G','F#'),CS,rs=[4,4,4,4]),
    sec('riff-bass','Riff — Bass',bs('Bm','F#','G','A','Bm','F#','G','A'),CR,rs=[4,4]),
    sec('riff-gtr','Riff — Guitar 2',bs('Bm','F#','G','A','Bm','F#','G','A'),CR,rs=[4,4]),
    sec('verse3','Verse 3',bs('Bm','D','G','F#','Bm','D','G','F#','Bm','D','G','F#','Bm','D','G','F#'),CV,rs=[4,4,4,4]),
    sec('chorus3','Chorus 3',bs('Bm','D','G','F#','Bm','D','G','F#','Bm','D','G','F#','Bm','D','G','F#'),CH,rs=[4,4,4,4]),
    sec('outro','Outro',bs('Bm','D','G','F#','Bm','D','G','F#','Bm','D','G','G','G','G','F#'),CI,rs=[4,4,4,3]),
])

print('\n✅ Done! All parkhaus108 bandsheets created.')
