#!/usr/bin/env python3
import json, re, os

TEMPLATE_PATH = '/Users/ti_am1/Desktop/Vaults/Vault_ti.muse/Bandsheet/_template.html'
OUT_DIR = '/Users/ti_am1/Desktop/Vaults/Vault_ti.muse/Bandsheet/the-maewjons'

with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f:
    TMPL = f.read()

def make_file(title, artist, slug, key, bpm, time_sig, sections):
    html = TMPL
    html = html.replace('<title>New Song · Band Sheet</title>', f'<title>{title} · Band Sheet</title>')
    html = re.sub(r'(id="tb-filename"[^>]*value=")[^"]*(")', rf'\g<1>{title}\g<2>', html)
    html = re.sub(r'(id="tb-artist"[^>]*value=")[^"]*(")', rf'\g<1>— {artist}\g<2>', html)
    html = re.sub(r'(id="meta-key"[^>]*value=")[^"]*(")', rf'\g<1>{key}\g<2>', html)
    html = re.sub(r'(id="meta-bpm"[^>]*value=")[^"]*(")', rf'\g<1>{bpm}\g<2>', html)
    html = re.sub(r'(id="meta-time"[^>]*value=")[^"]*(")', rf'\g<1>{time_sig}\g<2>', html)
    sj = json.dumps(sections, ensure_ascii=False)
    s = html.index('var SECTIONS = ')
    e = html.index('// ── END DATA ──')
    html = html[:s] + 'var SECTIONS = ' + sj + ';\n' + html[e:]
    out = os.path.join(OUT_DIR, f'{slug}.html')
    with open(out, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f'✓ {slug}.html')

def b(c, a='', h=False): return {'c': c, 'a': a, 'h': h}
def bs(*chords): return [b(c) for c in chords]
def sec(id, lbl, bars, col, note='', nh=True, rs=[]):
    return {'id': id, 'label': lbl, 'note': note, 'noteHidden': nh, 'lyric': '', 'color': col, 'bars': bars, 'rowSizes': rs}
def nsec(id, lbl, c1, c2='', col=None):
    if col is None: col = CV
    return {'id': id, 'type': 'note', 'label': lbl, 'cols': [c1, c2], 'color': col}

CI = {'bar': '#ff3b30', 'bg': '#fff1f0', 'lbl': '#b00008'}
CV = {'bar': '#3b82f6', 'bg': '#eef4fd', 'lbl': '#1e40af'}
CP = {'bar': '#f59e0b', 'bg': '#fffbeb', 'lbl': '#78350f'}
CH = {'bar': '#ffcc00', 'bg': '#fffbe6', 'lbl': '#7a5e00'}
CB = {'bar': '#059669', 'bg': '#eafaf4', 'lbl': '#064e3b'}
CS = {'bar': '#8b5cf6', 'bg': '#f5f3ff', 'lbl': '#4c1d95'}
CR = {'bar': '#ff6b30', 'bg': '#fff3ed', 'lbl': '#8a2e00'}

# ── 01 Black Hole Sun ──
make_file('Black Hole Sun', 'Soundgarden', '01-black-hole-sun', 'G', '105', '4/4', [
    sec('intro', 'Intro', bs('G','Bb','F','E','Eb','D','...'), CI),
    sec('verse1', 'Verse 1', bs(
        'G','Bb','F','E','Eb','D','—','Ab',
        'G','Bb','F','E','Eb','D','—','Ab','...'), CV, rs=[8,8,1]),
    nsec('nl-v1', 'Lyric — Verse 1',
         '<p>In my eyes / Indisposed / In disguises no one knows<br>Hides the face / Lies the snake / And the sun in my disgrace</p>',
         '<p>Boiling heat / Summer stench / Neath the black, the sky looks dead<br>Call my name / Through the cream / And I\'ll hear you scream again</p>', CV),
    sec('chorus1', 'Chorus 1', bs('Eb','D','G|F','Bb','Eb','D','C','D','...'), CH),
    nsec('nl-ch1', 'Lyric — Chorus 1',
         '<p>Black hole sun / Won\'t you come / And wash away the rain?<br>Black hole sun / Won\'t you come / Won\'t you come / Won\'t you come</p>', '', CH),
    sec('verse2', 'Verse 2', bs(
        'G','Bb','F','E','Eb','D','—','Ab',
        'G','Bb','F','E','Eb','D','—','Ab','...'), CV, rs=[8,8,1]),
    nsec('nl-v2', 'Lyric — Verse 2',
         '<p>Stuttering / Cold and damp / Steal the warm wind, tired friend<br>Times are gone / For honest men / Sometimes, far too long for snakes</p>',
         '<p>In my shoes / Walking sleep / In my youth, I pray to keep<br>Heaven send / Hell away / No one sings like you anymore</p>', CV),
    sec('chorus2', 'Chorus 2', bs(
        'Eb','D','G|F','Bb','Eb','D','C','Bb',
        'Eb','D','G|F','Bb','Eb','D'), CH, rs=[8,6]),
    nsec('nl-ch2', 'Lyric — Chorus 2',
         '<p>Black hole sun / Won\'t you come / And wash away the rain? (×3)<br>Won\'t you come.... / Oh Won\'t you come / Won\'t you come....</p>', '', CH),
    sec('bridge1', 'Bridge', bs(
        'C','Bb','D','C','Bb','D',
        'C','Bb','D','C','Bb','D'), CB, rs=[6,6]),
    nsec('nl-br1', 'Lyric — Bridge', '<p>(Black hole sun, black hole sun) ×4</p>', '', CB),
    sec('riff1', 'Riff', bs(
        'C','B','A','C','G','F#|F',
        'C','B','A','C','G','F#|F','F','G','...'), CR, note='4/4 + 5/4 alternating — pattern repeats ×6', rs=[6,6,3]),
    sec('verse3', 'Verse 3', bs('G','Bb','F','E','...'), CV),
    nsec('nl-v3', 'Lyric — Verse 3',
         '<p>Hang my head, drown my fear<br>\'Til you all just disappear</p>', '', CV),
    sec('chorus3', 'Chorus 3', bs(
        'Eb','D','G|F','Bb','Eb','D','C','Bb',
        'Eb','D','G|F','Bb','Eb','D'), CH, rs=[8,6]),
    nsec('nl-ch3', 'Lyric — Chorus 3',
         '<p>Black hole sun / Won\'t you come / And wash away the rain? (×8)</p>', '', CH),
    sec('bridge2', 'Bridge', bs(
        'C','Bb','D','C','Bb','D',
        'C','Bb','D','C','Bb','D',
        'C','Bb','D','C','Bb','D',
        'C','Bb','D','C','Bb','D'), CB, rs=[6,6,6,6]),
    sec('riff2', 'Riff (Outro)', bs('Bm','Am','G','F#','F','F','G'), CR),
])

# ── 02 Starlight ──
make_file('Starlight', 'Muse', '02-starlight', 'E', '122', '4/4', [
    sec('intro', 'Intro', bs(
        'B','B','B','B',
        'B','C#m','G#m','E','B','C#m','G#m','E'), CI, note='Row 1: Bass only', rs=[4,8]),
    sec('verse1', 'Verse 1', bs(
        'B','C#m','G#m','E','B','C#m','G#m','E',
        'B','C#m','G#m','E','B','C#m','G#m','E'), CV, rs=[8,8]),
    nsec('nl-v1', 'Lyric — Verse 1',
         '<p>Far away / This ship is taking me far away<br>Far away from the memories / Of the people who care if I live or die</p>',
         '<p>Starlight / I will be chasing a starlight<br>Until the end of my life / I don\'t know if it\'s worth it anymore</p>', CV),
    sec('interlude1', 'Interlude', bs(
        'B','C#m','G#m','E','B','C#m','G#m','E'), CB),
    nsec('nl-int1', 'Lyric — Interlude',
         '<p>Hold you in my arms<br>I just wanted to hold / You in my arms</p>', '', CB),
    sec('verse2', 'Verse 2', bs(
        'B','C#m','G#m','E','B','C#m','G#m','E'), CV),
    nsec('nl-v2', 'Lyric — Verse 2',
         '<p>My life / You electrify my life<br>Let\'s conspire to ignite / All the souls that would die just to feel alive</p>', '', CV),
    sec('prechorus1', 'Pre-Chorus', bs('C#m','F#','D#','G#m','A','E','A','D#'), CP),
    nsec('nl-pc1', 'Lyric — Pre-Chorus',
         '<p>I\'ll never let you go<br>If you promise not to fade away<br>Never fade away</p>', '', CP),
    sec('chorus1', 'Chorus', bs(
        'G#m','D#','E','B','G#m','D#','E','B',
        'G#m','D#','E','B','G#m','D#','E','F#'), CH, rs=[8,8]),
    nsec('nl-ch1', 'Lyric — Chorus',
         '<p>Our hopes and expectations<br>Black holes and revelations<br>Our hopes and expectations<br>Black holes and revelations</p>', '', CH),
    sec('break1', 'Break', bs('B','B','B','B'), CR),
    sec('interlude2', 'Interlude', bs(
        'B','C#m','G#m','E','B','C#m','G#m','E'), CB),
    sec('verse3', 'Verse 3', bs(
        'B','C#m','G#m','E','B','C#m','G#m','E'), CV),
    nsec('nl-v3', 'Lyric — Verse 3',
         '<p>Far away / This ship is taking me far away<br>Far away from the memories / Of the people who care if I live or die</p>', '', CV),
    sec('prechorus2', 'Pre-Chorus', bs('C#m','F#','D#','G#m','A','E','A','D#'), CP),
    sec('chorus2', 'Chorus', bs(
        'G#m','D#','E','B','G#m','D#','E','B',
        'G#m','D#','E','B','G#m','D#','E','F#'), CH, rs=[8,8]),
    sec('outro', 'Outro', bs(
        'B','C#m','G#m','E','B','C#m','G#m','E'), CI),
    nsec('nl-outro', 'Lyric — Outro',
         '<p>Hold you in my arms<br>I just wanted to hold / You in my arms</p>', '', CI),
])

# ── 03 Somebody Told Me ──
make_file('Somebody Told Me', 'The Killers', '03-somebody-told-me', 'Bbm', '138', '4/4', [
    sec('intro', 'Intro', bs(
        'Bbm','Bbm','Bbm','Bbm','Bbm','Bbm','Bbm','Bbm',
        'Gb','Gb','Bbm','Bbm'), CI, rs=[8,4]),
    sec('verse1', 'Verse 1', bs(
        'Bbm','Bbm','Bbm','Bbm','Ebm','Gb',
        'Bbm','Bbm','Bbm','Bbm',
        'Bbm','Bbm','Bbm','Bbm','Ebm','Gb',
        'Bbm','Bbm','Bbm','Bbm'), CV, rs=[6,4,6,4]),
    nsec('nl-v1', 'Lyric — Verse 1',
         '<p>Breakin\' my back just to know your name<br>Seventeen tracks and I\'ve had it with this game</p>',
         '<p>I\'m breakin\' my back just to know your name<br>But heaven ain\'t close in a place like this<br>Anything goes, but don\'t blink, you might miss<br>\'Cause heaven ain\'t close in a place like this</p>', CV),
    sec('prechorus1', 'Pre-Chorus', bs('Gb','Ab','Bbm','Bbm','Gb','Gb','Ab','Ab'), CP),
    nsec('nl-pc1', 'Lyric — Pre-Chorus',
         '<p>Bring it back down, bring it back down tonight<br>Never thought I\'d let a rumor ruin my moonlight</p>', '', CP),
    sec('chorus1', 'Chorus 1', bs('Bbm','Gb','Ab','F','Bbm','Gb','Ab','Ab'), CH),
    nsec('nl-ch1', 'Lyric — Chorus 1',
         '<p>Well, somebody told me you had a boyfriend<br>Who looked like a girlfriend that I had in February of last year<br>It\'s not confidential, I\'ve got potential</p>', '', CH),
    sec('verse2', 'Verse 2', bs(
        'Bbm','Bbm','Bbm','Bbm','Ebm','Gb',
        'Bbm','Bbm','Bbm','Bbm'), CV, rs=[6,4]),
    nsec('nl-v2', 'Lyric — Verse 2',
         '<p>Ready, let\'s roll onto somethin\' new<br>Takin\' its toll then I\'m leaving without you<br>\'Cause heaven ain\'t close in a place like this</p>', '', CV),
    sec('prechorus2', 'Pre-Chorus', bs('Gb','Ab','Bbm','Bbm','Gb','Gb','Ab','Ab'), CP),
    sec('chorus2', 'Chorus 2', bs('Bbm','Gb','Ab','F','Bbm','Gb','Ab','F'), CH),
    nsec('nl-ch2', 'Lyric — Chorus 2',
         '<p>Well, somebody told me you had a boyfriend<br>A-rushin\', a-rushin\' around</p>', '', CH),
    sec('bridge', 'Bridge', bs(
        'Gb','Ab','Ebm','Ebm','Db','Ebm','Gb','Gb',
        'Bbm','Ab','Gb','Gb','F','Ab','Ab'), CB, rs=[8,7]),
    nsec('nl-br', 'Lyric — Bridge',
         '<p>Pace yourself for me<br>I said maybe, baby, please<br>But I just don\'t know now<br>When all I wanna do is try</p>', '', CB),
    sec('chorus3', 'Chorus 3', bs(
        'Bbm','Gb','Ab','F','Bbm','Gb','Ab','F',
        'Bbm','Gb','Ab','F','Bbm','Gb','Ab','F',
        'Bbm','Gb','Ab','F','Bbm','Gb','Ab','F',
        'Bbm'), CH, rs=[8,8,8,1]),
    nsec('nl-ch3', 'Lyric — Chorus 3',
         '<p>Well, somebody told me you had a boyfriend<br>Who looked like a girlfriend... (×3)</p>', '', CH),
])

# ── 04 I Put A Spell On You ──
make_file('I Put A Spell On You', 'Annie Lennox', '04-i-put-a-spell-on-you', 'E', '58', '4/4', [
    sec('intro', 'Intro', bs('Dm','Dm'), CI),
    sec('verse1', 'Verse 1', bs(
        'Dm','Gm','Dm','D7','Gm','Gm','A','A|A7',
        'Dm','D7','Gm','Bb','Dm','A7','Dm','A|A7'), CV, rs=[8,8]),
    nsec('nl-v1', 'Lyric — Verse 1',
         '<p>I put a spell on you / Because you\'re mine<br>You better stop the things you do / I tell you I ain\'t lyin\'</p>',
         '<p>You know I can\'t stand it / You\'re runnin\' around, you know better, daddy<br>I cannot stand it \'cause you put me down / Oh, no<br>I put a spell on you / Because you\'re mine</p>', CV),
    sec('solo', 'Solo', bs('Dm7','Gm7','Dm7','D7','Gm','Gm','A','A|A7'), CS),
    sec('verse2', 'Verse 2', bs(
        'Dm','D7','Gm','Bb','Dm','A7','Dm','A|A7'), CV),
    nsec('nl-v2', 'Lyric — Verse 2',
         '<p>You know I love you, I love you / I love you, I love you anyhow<br>And I don\'t care if you don\'t want me / I\'m yours right now<br>I put a spell on you / Because you\'re mine</p>', '', CV),
    sec('riff', 'Riff', bs('Dm','Dm'), CR),
    sec('verse3', 'Verse 3', bs(
        'Dm','D7','Gm','Bb','Dm','A7','Dm','A|A7',
        'Dm','A'), CV, note='Bar 46: หยดท / Beat 3 ...Gm Dm', rs=[8,2]),
    nsec('nl-v3', 'Lyric — Verse 3',
         '<p>You know I can\'t stand it / You\'re runnin\' around, you know better, daddy<br>I can\'t stand it \'cause you put me down / Ooh</p>',
         '<p>I put a spell on you / Because you\'re mine<br>Because you\'re <strong>mine</strong> / Because you\'re mine / Oh, yeah</p>', CV),
])

# ── 05 The Man Who Can't Be Moved ──
make_file("The Man Who Can't Be Moved", 'The Script', '05-the-man-who-cant-be-moved', 'Bb', '100', '4/4', [
    sec('intro', 'Intro', bs('Bb','Dm','Eb','Eb'), CI),
    sec('verse1', 'Verse 1', bs(
        'Bb','Dm','Eb','Eb','Bb','Dm','Eb','Eb',
        'Bb','Dm','Eb','Eb','Bb','Dm','Eb','Eb'), CV, rs=[8,8]),
    nsec('nl-v1', 'Lyric — Verse 1',
         '<p>Going back to the corner where I first saw you<br>Gonna camp in my sleeping bag, I\'m not gonna move<br>Got some words on cardboard, got your picture in my hand<br>Saying, "If you see this girl, can you tell her where I am?"</p>',
         '<p>Some try to hand me money, they don\'t understand<br>I\'m not broke, I\'m just a broken-hearted man<br>I know it makes no sense, what else can I do?<br>And how can I move on when I\'m still in love with you?</p>', CV),
    sec('chorus1', 'Chorus 1', bs(
        'Bb','F','Cm','Eb','Bb','F','Cm','Eb',
        'Bb','F','Cm','Eb'), CH, rs=[8,4]),
    nsec('nl-ch1', 'Lyric — Chorus 1',
         '<p>\'Cause if one day you wake up, and find that you\'re missing me<br>And your heart starts to wonder where on this Earth I could be<br>Thinking maybe you\'ll come back here to the place that we\'d meet<br>And you\'ll see me waiting for you, on the corner of the street<br>So I\'m not moving / I\'m not moving</p>', '', CH),
    sec('break', 'Instrument Break', bs('Bb','F','Eb','Eb'), CR),
    sec('verse2', 'Verse 2', bs(
        'Bb','Dm','Eb','Eb','Bb','Dm','Eb','Eb'), CV),
    nsec('nl-v2', 'Lyric — Verse 2',
         '<p>Policeman says, "Son, you can\'t stay here"<br>I say, "There\'s someone I\'m waiting for / If it\'s a day, a month, a year"<br>Gotta stand my ground, even if it rains or snows<br>If she changes her mind, this is the first place she will go</p>', '', CV),
    sec('chorus2', 'Chorus 2', bs(
        'Bb','F','Cm','Eb','Bb','F','Cm','Eb',
        'Bb','F','Cm','Eb'), CH, rs=[8,4]),
    sec('bridge', 'Bridge', bs(
        'Gm','Eb','F','Cm','Gm','Eb','F','Cm',
        'Eb','F','Eb','F','Eb','F',
        'Cm','Cm','Cm','Cm'), CB, rs=[8,6,4]),
    nsec('nl-br', 'Lyric — Bridge',
         '<p>People talk about the guy who\'s waiting on a girl<br>There are no holes in his shoes, but a big hole in his world<br>Maybe I\'ll get famous as the man who can\'t be moved</p>',
         '<p>And maybe you won\'t mean to, but you\'ll see me on the news<br>And you\'ll come running to the corner \'cause you know it\'s just for you<br>I\'m the man who can\'t be moved</p>', CB),
    sec('chorus3', 'Chorus 3', bs(
        'Bb','F','Cm','Eb','Bb','F','Cm','Eb',
        'Bb','F','Cm','Eb','Bb','F','Cm','Eb'), CH, rs=[8,8]),
    sec('outro', 'Outro', bs('Bb','F','Cm','Eb'), CI),
    nsec('nl-outro', 'Lyric — Outro',
         '<p>Going back to the corner / Where I first saw you<br>Gonna camp in my sleeping bag / I\'m not gonna move</p>', '', CI),
])

# ── 06 Supersonic ──
make_file('Supersonic', 'Oasis', '06-supersonic', 'A', '104', '4/4', [
    sec('intro', 'Intro', bs(
        'F#m','A','B','F#m','A','B','F#m','A','B','F#m','A','B'), CI, note='Bars 1-4: Drum only', rs=[6,6]),
    sec('verse1', 'Verse 1', bs(
        'F#m','A','B','F#m','A','B','F#m','A','B','F#m','A','B',
        'F#m','A','B','F#m','A','B','F#m','A','B','F#m','A','B'), CV, rs=[6,6,6,6]),
    nsec('nl-v1', 'Lyric — Verse 1',
         '<p>I need to be myself / I can\'t be no one else<br>I\'m feeling supersonic, give me gin and tonic<br>You can have it all, but how much do you want it?</p>',
         '<p>You make me laugh / Give me your autograph<br>Can I ride with you in your BMW?<br>You can sail with me in my yellow submarine</p>', CV),
    sec('prechorus1', 'Pre-Chorus', bs('E','E','F#m','F#m','E','E','C#','C#'), CP),
    nsec('nl-pc1', 'Lyric — Pre-Chorus',
         '<p>You need to find out<br>\'Cause no one\'s gonna tell you what I\'m on about<br>You need to find a way for what you want to say<br>But before tomorrow</p>', '', CP),
    sec('chorus1', 'Chorus', bs(
        'D','A','E','F#m','D','A','E','F#m',
        'D','A','E','F#m','D','A','E','F#m'), CH, rs=[8,8]),
    nsec('nl-ch1', 'Lyric — Chorus',
         '<p>\'Cause my friend said he\'d take you home<br>He sits in a corner all alone<br>He lives under a waterfall<br>Nobody can see him<br>Nobody can ever hear him call</p>', '', CH),
    sec('solo1', 'Solo', bs(
        'D','A','E','F#m','D','A','E','F#m',
        'D','A','E','F#m','D','A','E','F#m'), CS, rs=[8,8]),
    sec('break', 'Instrument Break', bs('E','E','C#','C#'), CR),
    sec('verse2', 'Verse 2', bs(
        'F#m','A','B','F#m','A','B','F#m','A','B','F#m','A','B',
        'F#m','A','B','F#m','A','B','F#m','A','B','F#m','A','B'), CV, rs=[6,6,6,6]),
    nsec('nl-v2', 'Lyric — Verse 2',
         '<p>You need to be yourself / You can\'t be no one else<br>I know a girl called Elsa, she\'s into Alka-Seltzer<br>She sniffs it through a cane on a supersonic train</p>',
         '<p>And she makes me laugh / I got her autograph<br>She done it with a doctor on a helicopter<br>She\'s sniffing in a tissue selling the Big Issue</p>', CV),
    sec('prechorus2', 'Pre-Chorus', bs('E','E','F#m','F#m','E','E','C#','C#'), CP),
    sec('chorus2', 'Chorus', bs(
        'D','A','E','F#m','D','A','E','F#m',
        'D','A','E','F#m','D','A','E','F#m'), CH, rs=[8,8]),
    sec('solo2', 'Solo', bs(
        'D','A','E','F#m','D','A','E','F#m',
        'D','A','E','F#m','D','A','E','F#m'), CS, rs=[8,8]),
    sec('outro', 'Solo — Outro', bs(
        'D','A','E','F#m','D','A','E','F#m',
        'D','A','E','F#m','D','A','E','F#m',
        'D','A','E','F#m','D','A','E','F#m',
        'D','A','E','F#m','D','A','E','F#m'), CI, rs=[8,8,8,8]),
])

# ── 07 Live Forever ──
make_file('Live Forever', 'Oasis', '07-live-forever', 'Am', '91', '4/4', [
    sec('intro', 'Intro', [b('x'),b('x'),b('x'),b('x')], CI, note='Drum only'),
    sec('verse1', 'Verse 1', bs(
        'G','D','Am','C','D','G','D','Am','C','D'), CV, rs=[5,5]),
    nsec('nl-v1', 'Lyric — Verse 1',
         '<p>Maybe, I don\'t really wanna know<br>How your garden grows<br>\'Cause I just wanna fly<br>Lately, did you ever feel the pain<br>In the morning rain<br>As it soaks you to the bone?</p>', '', CV),
    sec('chorus1', 'Chorus 1', bs(
        'Em','D','Am','C','D','Em','D','Am','F'), CH, rs=[4,5]),
    nsec('nl-ch1', 'Lyric — Chorus 1',
         '<p>Maybe I just wanna fly / Wanna live, I don\'t wanna die<br>Maybe I just wanna breathe / Maybe I just don\'t believe<br>Maybe you\'re the same as me / We see things they\'ll never see<br>You and I are gonna live forever</p>', '', CH),
    sec('break1', 'Instrument Break', bs('F'), CR),
    sec('verse2', 'Verse 2', bs(
        'G','D','Am','C','D','G','D','Am','C','D'), CV, rs=[5,5]),
    nsec('nl-v2', 'Lyric — Verse 2',
         '<p>I said maybe, I don\'t really wanna know<br>How your garden grows<br>\'Cause I just wanna fly<br>Lately, did you ever feel the pain<br>In the morning rain<br>As it soaks you to the bone?</p>', '', CV),
    sec('chorus2', 'Chorus 2', bs(
        'Em','D','Am','C','D','Em','D','Am','F'), CH, rs=[4,5]),
    nsec('nl-ch2', 'Lyric — Chorus 2',
         '<p>Maybe I will never be / All the things that I wanna be<br>Now is not the time to cry / Now\'s the time to find out why<br>I think you\'re the same as me / We see things they\'ll never see<br>You and I are gonna live forever</p>', '', CH),
    sec('break2', 'Instrument Break', bs('F'), CR),
    sec('solo', 'Solo', bs(
        'G','D','Am','C','D','G','D','Am','C','D',
        'Em','D','Am','C','D','Em','D','Am','F','F'), CS, rs=[5,5,5,5]),
    sec('verse3', 'Verse 3', bs(
        'G','D','Am','C','D','G','D','Am','C','D'), CV, rs=[5,5]),
    sec('chorus3', 'Chorus 3', bs(
        'Em','D','Am','C','D','Em','D','Am','F',
        'Am','F','Am','F','Am','F','Am','F',
        'Am','F','Am','F'), CH, rs=[4,5,8,4]),
    nsec('nl-ch3', 'Lyric — Chorus 3',
         '<p>You and I are gonna live forever<br>Gonna live forever (×4)</p>', '', CH),
    sec('outro', 'Outro / Solo', bs(
        'Am','F','Am','F','Am','F','Am','F',
        'Am','F','Am','F','Am','F','Am','F'), CI, rs=[8,8]),
])

# ── 08 Sweet Disposition ──
make_file('Sweet Disposition', 'The Temper Trap', '08-sweet-disposition', 'G', '129', '4/4', [
    sec('intro', 'Intro', bs('D','D','D','D'), CI),
    sec('verse1', 'Verse 1', bs(
        'D','D','Bm','Bm','D','D','Bm','Bm',
        'D','D','Bm','Bm','D','D','Bm','Bm',
        'D','D','Bm','G','D','D','Bm','G',
        'D','D','Bm','G','D','D','Bm','G'), CV, rs=[8,8,8,8]),
    nsec('nl-v1', 'Lyric — Verse 1',
         '<p>Sweet disposition / Never too soon<br>Oh, reckless abandon / Like no one\'s watching you</p>', '', CV),
    sec('prechorus1', 'Pre-Chorus', bs('D','D','Bm','G','D','D','D','D'), CP),
    nsec('nl-pc1', 'Lyric — Pre-Chorus',
         '<p>A moment, a love, a dream, aloud<br>A kiss, a cry, our rights, our wrongs<br>A moment, a love, a dream, aloud<br>A moment, a love, a dream, aloud</p>',
         '<p>(A moment, a love)<br>(A moment, a love)</p>', CP),
    sec('chorus1', 'Chorus 1', bs(
        'D','Bm','G','Em','D','Bm','G','Em',
        'D','Bm','G','Em','D','Bm','G','Em'), CH, rs=[8,8]),
    nsec('nl-ch1', 'Lyric — Chorus 1',
         '<p>So stay there<br>\'Cause I\'ll be comin\' over<br>And while our blood\'s still young<br>It\'s so young, it runs<br>And won\'t stop \'til it\'s over<br>Won\'t stop to surrender</p>', '', CH),
    sec('riff1', 'Riff', bs('D','D','D','D'), CR),
    sec('verse2', 'Verse 2', bs(
        'D','D','Bm','G','D','D','Bm','G',
        'D','D','Bm','G','D','D','Bm','G'), CV, rs=[8,8]),
    nsec('nl-v2', 'Lyric — Verse 2',
         '<p>Songs of desperation / I played them for you</p>', '', CV),
    sec('prechorus2', 'Pre-Chorus', bs('D','D','D','D','D','D','D','D'), CP),
    sec('chorus2', 'Chorus 2', bs(
        'D','Bm','G','Em','D','Bm','G','Em',
        'D','Bm','G','Em','D','Bm','G','Em'), CH, rs=[8,8]),
    sec('outro', 'Outro', bs(
        'D','Bm','G','Em','D','Bm','G','Em',
        'D','Bm','G','Em','D','Bm','G','Em'), CI, rs=[8,8]),
    nsec('nl-outro', 'Lyric — Outro',
         '<p>Won\'t stop \'til it\'s over (×3)<br>Won\'t stop to surrender</p>',
         '<p>(A moment, a love, a dream, aloud A kiss, a cry, our rights, our wrongs) ×4</p>', CI),
    sec('riff2', 'Riff (End)', bs('D','D','D','D','D'), CR),
])

# ── 09 Crazy ──
make_file('Crazy', 'Gnarls Barkley', '09-crazy', 'Dm', '112', '4/4', [
    sec('intro', 'Intro', bs('Dm'), CI),
    sec('verse1', 'Verse 1', bs(
        'Dm','Dm','F','F','Bb','Bb','A','A',
        'Dm','Dm','F','F','Bb','Bb','A','A'), CV, rs=[8,8]),
    nsec('nl-v1', 'Lyric — Verse 1',
         '<p>I remember when / I remember, I remember when I lost my mind<br>There was something so pleasant about that place<br>Even your emotions have an echo in so much space</p>',
         '<p>And when you\'re out there, without care<br>Yeah I was out of touch<br>But it wasn\'t because I didn\'t know enough<br>I just knew too much</p>', CV),
    sec('chorus1', 'Chorus', bs('Dm','Dm','F','F','Bb','Bb','A','A'), CH),
    nsec('nl-ch1', 'Lyric — Chorus',
         '<p>Does that make me craazy?<br>Does that make me craazy?<br><strong>Possibly</strong></p>', '', CH),
    sec('bridge1', 'Bridge', bs('D','D','Bb','Bb','F','F','A','A'), CB),
    nsec('nl-br1', 'Lyric — Bridge',
         '<p>And I hope that you are having the time of your life<br>But think twice, that\'s my only advice, mm</p>', '', CB),
    sec('verse2', 'Verse 2', bs('Dm','Dm','F','F','Bb','Bb','A','A'), CV),
    nsec('nl-v2', 'Lyric — Verse 2',
         '<p>Come on now, who do you, who do you, who do you<br>Who do you think you are?<br>Ha-ha-ha, bless your soul<br>You really think you\'re in control, well</p>', '', CV),
    sec('chorus2', 'Chorus', bs('Dm','Dm','F','F','Bb','Bb','A','A'), CH),
    nsec('nl-ch2', 'Lyric — Chorus',
         '<p>I think you\'re crazy<br>I think you\'re crazy<br>I think you\'re crazy<br><strong>Just like me</strong></p>', '', CH),
    sec('bridge2', 'Bridge', bs('D','D','Bb','Bb','F','F','A','A'), CB, note='Beat 3,4 Stop on last bar'),
    nsec('nl-br2', 'Lyric — Bridge',
         '<p>My heroes had the heart to lose their lives out on the limb<br>And all I remember is thinking "I want to be like them"</p>', '', CB),
    sec('verse3', 'Verse 3', bs('Dm','Dm','F','F','Bb','Bb','A','A'), CV),
    nsec('nl-v3', 'Lyric — Verse 3',
         '<p>Ever since I was little<br>Ever since I was little, it looked like fun<br>And it\'s no coincidence I\'ve come<br>And I can die when I\'m done</p>', '', CV),
    sec('chorus3', 'Chorus', bs('Dm','Dm','F','F','Bb','Bb','A','A'), CH),
    nsec('nl-ch3', 'Lyric — Chorus',
         '<p>But maybe I\'m crazy<br>Maybe you\'re crazy<br>Maybe we\'re crazy<br><strong>Probably</strong></p>', '', CH),
    sec('outro', 'Outro', bs('D','D','Bb','Bb','F','F','A','A','D'), CI, note='Beat 3,4 Stop on bar 81; bar 82 = D'),
    nsec('nl-outro', 'Lyric — Outro', '<p>Ooh, Hmm</p>', '', CI),
])

# ── 10 Vampire ──
make_file('Vampire', 'Olivia Rodrigo', '10-vampire', 'F', '138', '4/4', [
    sec('intro', 'Intro', bs('F','F','A','A','Bb','Bb','Bbm','Bbm'), CI),
    sec('verse1', 'Verse 1', bs(
        'F','F','A','A','Bb','Bb','Bbm','Bbm',
        'F','F','A','A','Bb','Bb','Bbm','Bbm'), CV, rs=[8,8]),
    nsec('nl-v1', 'Lyric — Verse 1',
         '<p>Hate to give the satisfaction asking how you\'re doing now<br>How\'s the castle built off people you pretend to care about?<br>Just what you wanted / Look at you, cool guy, you got it</p>',
         '<p>I see the parties and the diamonds sometimes when I close my eyes<br>Six months of torture you sold as some forbidden paradise<br>I loved you truly / You gotta laugh at the stupidity</p>', CV),
    sec('chorus1', 'Chorus 1', bs(
        'Gm','Gm','C','C','F','F','A','A',
        'Bb','Bb','Bbm','Bbm','F','F','A','A',
        'Bb','Bbm'), CH, rs=[8,8,2]),
    nsec('nl-ch1', 'Lyric — Chorus 1',
         '<p>\'Cause I\'ve made some real big mistakes<br>But you make the worst one look fine<br>I should\'ve known it was strange / You only come out at night<br>I used to think I was smart / But you made me look so naive</p>',
         '<p>The way you sold me for parts / As you sunk your teeth into me<br>Bloodsucker, fame fucker / Bleedin\' me dry like a goddamn vampire</p>', CH),
    sec('verse2', 'Verse 2', bs(
        'F','F','A','A','Bb','Bb','Bbm','Bbm',
        'F','F','A','A','Bb','Bb','Bbm','Bbm'), CV, rs=[8,8]),
    nsec('nl-v2', 'Lyric — Verse 2',
         '<p>And every girl I ever talked to told me you were bad, bad news<br>You called them crazy, god, I hate the way I called them crazy too</p>',
         '<p>Ooh, what a mesmerizin\', paralyzin\', fucked-up little thrill<br>Went for me, and not her / \'Cause girls your age know better</p>', CV),
    sec('chorus2', 'Chorus 2', bs(
        'Gm','Gm','C7','C7','F','F','A','A',
        'Bb','Bb','Bbm','Bbm','F','F','A','A',
        'Bb','Bbm'), CH, rs=[8,8,2]),
    sec('riff1', 'Riff', bs('F','F','F','F'), CR, note='Rhythmic riff — 1/8 1/8 1/2 1/4'),
    sec('bridge', 'Bridge', bs(
        'Bb','Bbm','F','C','Bb','Bbm','F','C',
        'Bb','Bbm','F','C'), CB, rs=[8,4]),
    nsec('nl-br', 'Lyric — Bridge',
         '<p>You said it was true love, but wouldn\'t that be hard?<br>You can\'t love anyone, \'cause that would mean you had a heart<br>I tried you help you out, now I know that I can\'t<br>\'Cause how you think\'s the kind of thing I\'ll never understand</p>', '', CB),
    sec('chorus3', 'Chorus 3', bs(
        'Gm','Gm','C7','C7','F','F','A','A',
        'Bb','Bb','Bbm','Bbm','F','F','A','A',
        'Bb','Bbm'), CH, rs=[8,8,2]),
    sec('riff2', 'Riff (End)', bs('F','F','F','F','F','F','F'), CR, note='1/2 1/2 1/4 1/8 1/8 1/8'),
])

# ── 11 Yellow ──
make_file('Yellow', 'Coldplay', '11-yellow', 'B', '87', '4/4', [
    sec('intro', 'Intro', bs(
        'B','B','B','B',
        'B','B','F#','F#','E','E','B','B'), CI, note='Row 1: Drum/Gt only', rs=[4,8]),
    sec('verse1', 'Verse 1', bs(
        'B','B','F#','F#','E','E',
        'B','B','F#','F#','E','E',
        'B','B','F#','F#','E','E'), CV, rs=[6,6,6]),
    nsec('nl-v1', 'Lyric — Verse 1',
         '<p>Look at the stars / Look how they shine for you<br>And everything you do / Yeah, they were all yellow</p>',
         '<p>I came along / I wrote a song for you<br>And it was called "Yellow"<br>So then I took my turn / Oh, what a thing to have done<br>And it was all yellow</p>', CV),
    sec('instru1', 'Instrument', bs('B','B'), CR),
    sec('chorus1', 'Chorus', bs(
        'E','G#m|F#','E','G#m|F#','E','G#m|F#','E','E'), CH),
    nsec('nl-ch1', 'Lyric — Chorus',
         '<p>(Ah) Your skin, oh, yeah, your skin and bones<br>(Ooh) Turn into something beautiful<br>(Ah) And you know, you know I love you so<br>You know I love you so</p>', '', CH),
    sec('riff1', 'Riff', bs('B','B','F#','F#','E','E','B','B'), CR),
    sec('verse2', 'Verse 2', bs(
        'B','B','F#','F#','E','E',
        'B','B','F#','F#','E','E'), CV, rs=[6,6]),
    nsec('nl-v2', 'Lyric — Verse 2',
         '<p>I swam across / I jumped across for you<br>Oh, what a thing to do / \'Cause you were all yellow</p>',
         '<p>I drew a line / I drew a line for you<br>Oh, what a thing to do / And it was all yellow</p>', CV),
    sec('instru2', 'INSTRU', bs('B','B'), CR),
    sec('chorus2', 'Chorus', bs(
        'E','G#m|F#','E','G#m|F#','E','G#m|F#','E','E'), CH),
    nsec('nl-ch2', 'Lyric — Chorus',
         '<p>(Ah) And your skin, oh, yeah, your skin and bones<br>(Ooh) Turn into something beautiful<br>(Ah) And you know, for you, I\'d bleed myself dry<br>For you, I\'d bleed myself dry</p>', '', CH),
    sec('riff2', 'Riff', bs('B','B','F#','F#','E','E','B','B'), CR),
    sec('bridge', 'Bridge', bs(
        'B','B','F#','F#','E','E','B','B',
        'B','B','F#','F#'), CB, rs=[8,4]),
    nsec('nl-br', 'Lyric — Bridge',
         '<p>It\'s true / Look how they shine for you / Look how they shine for you<br>Look how they shine for... / Look how they shine for you / Look how they shine</p>', '', CB),
    sec('outro', 'Outro', bs('B','B','F#m','F#m','E'), CI),
    nsec('nl-outro', 'Lyric — Outro',
         '<p>Look at the stars / Look how they shine for you<br>And all the things that you do</p>', '', CI),
])

# ── 12 Use Somebody ──
make_file('Use Somebody', 'Kings Of Leon', '12-use-somebody', 'C', '137', '4/4', [
    sec('intro', 'Intro', bs(
        'G',
        'C','C/E','F','F','C','C/E','F','F',
        'Am','C','F','F','Am','C','F','F'), CI, note='Bar 1: G pickup', rs=[1,8,8]),
    nsec('nl-intro', 'Lyric — Intro',
         '<p>Oh o oh Oh o oh o (×4)<br>I\'ve been roamin\'</p>', '', CI),
    sec('verse1', 'Verse 1', bs(
        'C','C/E','F','F','C','C/E','F','F',
        'Am','C','F','F','Am','C','F','F',
        'C','C/E','F','F','C','C/E','F','F',
        'Am','C','F','F','Am','C','F','F'), CV, rs=[8,8,8,8]),
    nsec('nl-v1', 'Lyric — Verse 1',
         '<p>around, always lookin\' down at all I see<br>Painted faces fill the places I can\'t reach<br>You know that I could use somebody</p>',
         '<p>Someone like you and all you know and how you speak<br>Countless lovers under cover of the street<br>You know that I could use somebody / Someone like</p>', CV),
    sec('chorus1', 'Chorus 1', bs(
        'C','C/E','F','F','C','C/E','F','F',
        'Am','C','F','F','Am','C','F','F'), CH, rs=[8,8]),
    nsec('nl-ch1', 'Lyric — Chorus 1',
         '<p>you / Oh o oh Oh o oh o (×4)<br>Off in the</p>', '', CH),
    sec('verse2', 'Verse 2', bs(
        'C','C/E','F','F','C','C/E','F','F',
        'Am','C','F','F','Am','C','F','F'), CV, rs=[8,8]),
    nsec('nl-v2', 'Lyric — Verse 2',
         '<p>night, while you live it up, I\'m off to sleep<br>Wagin\' wars to shape the poet and the beat<br>I hope it\'s gonna make you notice</p>', '', CV),
    sec('chorus2', 'Chorus 2', bs(
        'C','C/E','F','F','C','C/E','F','F',
        'Am','C','F','F','Am','C','F','F'), CH, rs=[8,8]),
    nsec('nl-ch2', 'Lyric — Chorus 2',
         '<p>Someone like me / Someone like me<br>Someone like me Somebody<br>Oh o oh Oh o oh o (×4)</p>', '', CH),
    sec('bridge', 'Bridge', bs('D','D','Gb','Gb','D','D','Gb','Bm'), CB),
    nsec('nl-br', 'Lyric — Bridge',
         '<p>....I\'m ready now<br>I\'m ready now (×7)</p>', '', CB),
    sec('solo', 'Solo', bs('C','C/E','F','F','Am','C','F','F'), CS),
    sec('chorus3', 'Chorus 3', bs(
        'Am','C','F','F','Am','C','F','F',
        'Am','C','F','F','Am','C','F','F',
        'Am','C','F','F'), CH, rs=[8,8,4]),
    nsec('nl-ch3', 'Lyric — Chorus 3',
         '<p>you / Somebody / Someone like you<br>Somebody / Someone like you / Somebody<br>I\'ve been roamin\' around, always lookin\' down at all I see<br>Oh o oh Oh o oh o (×4)</p>', '', CH),
    sec('outro', 'Outro', bs('C','C/E','F','F'), CI),
])

# ── 13 Beautiful Ones ──
make_file('Beautiful Ones', 'Suede', '13-beautiful-ones', 'C', '99', '4/4', [
    sec('intro', 'Intro', bs('C','D7','Fmaj7','Esus4','C','D7','Fmaj7','Esus4'), CI),
    sec('verse1', 'Verse 1', bs(
        'C','D7','Fmaj7','Esus4','C','D7','Fmaj7','Esus4',
        'C','D7','Fmaj7','Esus4','C','D7','Fmaj7','Esus4'), CV, rs=[8,8]),
    nsec('nl-v1', 'Lyric — Verse 1',
         '<p>Oh, high on diesel and gasoline / Psycho for drum machine<br>Shaking their bits to the hits / Oh, drag acts, drug acts, suicides<br>In your dad\'s suits, you hide / Staining his name again</p>',
         '<p>Oh, cracked up, stacked up, twenty-two / Psycho for sex and glue<br>Lost it to Bostik, yeah / Oh, shaved heads, rave heads, on the pill<br>Got too much time to kill / Get into bands and gangs, oh</p>', CV),
    sec('chorus1', 'Chorus 1', bs(
        'C','Em','F','Dm','C','Em','F','Dm',
        'Am','—'), CH, rs=[8,2]),
    nsec('nl-ch1', 'Lyric — Chorus 1',
         '<p>Here they come / The beautiful ones / The beautiful ones / La, la, la, la<br>Here they come / The beautiful ones / The beautiful ones / La, la, la, la, la / ..La, La</p>', '', CH),
    sec('verse2', 'Verse 2', bs('C','D7','Fmaj7','Esus4','C','D7','Fmaj7','Esus4'), CV),
    nsec('nl-v2', 'Lyric — Verse 2',
         '<p>loved up, doved up, hung around / Stoned in a lonely town<br>Shaking their meat to the beat / Oh, high on diesel and gasoline<br>Psycho for drum machine / Shaking their bits to the hits, oh</p>', '', CV),
    sec('chorus2', 'Chorus 2', bs('C','Em','F','Dm','C','Em','F','Dm|Bb'), CH),
    nsec('nl-ch2', 'Lyric — Chorus 2',
         '<p>Here they come / The beautiful ones / The beautiful ones / La, la, la, la<br>Here they come / The beautiful ones / The beautiful ones / Oh...</p>', '', CH),
    sec('bridge', 'Bridge', bs(
        'C','Em','F','Dm|Bb','C','Em','F','Dm|Bb',
        'C','Em','F','Dm|Bb','C','Em','F','Dm|Bb',
        'Am','—'), CB, rs=[8,8,2]),
    nsec('nl-br', 'Lyric — Bridge',
         '<p>Oh, oh, you don\'t think about it / You don\'t do without it<br>Because you\'re beautiful, yeah, yeah</p>',
         '<p>And if your babies are going crazy / That\'s how you made me, la, la (×3)</p>', CB),
    sec('outro', 'Outro', bs(
        'C','D7','Fmaj7','Esus4','C','D7','Fmaj7','Esus4',
        'C','D7','Fmaj7','Esus4','C','D7','Fmaj7','Esus4'), CI, rs=[8,8]),
    nsec('nl-outro', 'Lyric — Outro',
         '<p>La, la, la-la, la, la-la / La-la-la, la, la-la / La-la-la-la, la-la-la, oh (×4)</p>', '', CI),
])

# ── 14 Forever Young ──
make_file('Forever Young', 'Youth Group', '14-forever-young', 'B', '113', '4/4', [
    sec('intro', 'Intro', bs('B','B','G#m','E','F#','G#m','E','E'), CI),
    sec('verse1', 'Verse 1', bs(
        'B','B','G#m','E','F#','G#m','E','E',
        'B','B','G#m','E','F#','G#m','E','E',
        'B','B','G#m','E','F#','G#m','E','E'), CV, rs=[8,8,8]),
    nsec('nl-v1', 'Lyric — Verse 1',
         '<p>Let\'s dance in style, let\'s dance for a while<br>Heaven can wait, we\'re only watching the skies<br>Hopin\' for the best but expecting the worst<br>Are you gonna drop the bomb or not?</p>',
         '<p>Let us die young, or let us live forever<br>We don\'t have the power, but we never say never<br>Sittin\' in a sandpit, life is a short trip / Music\'s for the sad men<br>Can you imagine when this race is run?<br>Turn our golden faces into the sun<br>Praisin\' our leaders, gettin\' in tune / The music\'s played by the madmen</p>', CV),
    sec('chorus1', 'Chorus 1', bs('B','B/A#','G#m','E','F#','G#m','E','E'), CH),
    nsec('nl-ch1', 'Lyric — Chorus 1',
         '<p>Forever young, I wanna be forever young<br>Do you really want to live forever, forever, forever?</p>', '', CH),
    sec('riff1', 'Riff', bs('B','B','G#m','E','F#','G#m','E','E'), CR),
    sec('verse2', 'Verse 2', bs(
        'B','B','G#m','E','F#','G#m','E','E',
        'B','B','G#m','E','F#','G#m','E','E'), CV, rs=[8,8]),
    nsec('nl-v2', 'Lyric — Verse 2',
         '<p>Some are like water, some are like the heat<br>Some are a melody, some are the beat<br>Sooner or later they\'ll all be gone / Why don\'t they stay young?</p>',
         '<p>It\'s hard to get old without a cause<br>I don\'t wanna perish like a fadin\' horse<br>Youth is like diamonds in the sun / And diamonds are forever</p>', CV),
    sec('chorus2', 'Chorus 2', bs(
        'B','B/A#','G#m','E','F#','G#m','E','E',
        'B','B/A#','G#m','E','F#','G#m','E','E'), CH, rs=[8,8]),
    nsec('nl-ch2', 'Lyric — Chorus 2',
         '<p>Forever young, I wanna be forever young (×2)<br>Do you really want to live forever, forever, forever?</p>', '', CH),
    sec('riff2', 'Riff', bs(
        'B','B/A#','G#m','E','F#','G#m','E','E',
        'B','B/A#','G#m','E','F#','G#m','E','E'), CR, rs=[8,8]),
    sec('chorus3', 'Chorus 3', bs(
        'B','B/A#','G#m','E','F#','G#m','E','E',
        'B','B/A#','G#m','E','F#','G#m','E','E',
        'B','B/A#','G#m','E','F#','G#m'), CH, rs=[8,8,6]),
    nsec('nl-ch3', 'Lyric — Chorus 3',
         '<p>Forever young, I wanna be forever young (×2)<br>Do you really want to live forever, forever, ...<br>(Fade out)</p>', '', CH),
])

# ── 15 Lovefool ──
make_file('Lovefool', 'The Cardigans', '15-lovefool', 'Am', '112', '4/4', [
    sec('intro', 'Intro', bs('Am','Am'), CI),
    sec('verse1', 'Verse 1', bs(
        'Am7','Dm7','G7','Cmaj7','Am','Dm7','G7','Cmaj7',
        'Am7','Dm7','G7','Cmaj7','Am','Dm7','G7'), CV, rs=[8,7]),
    nsec('nl-v1', 'Lyric — Verse 1',
         '<p>Dear, I fear we\'re facing a problem<br>You love me no longer, I know<br>Maybe there is nothing that I can do / To make you do</p>',
         '<p>Mama tells me I shouldn\'t bother<br>That I ought just stick to another man<br>A man that surely deserves me / But I think you do</p>', CV),
    sec('prechorus1', 'Pre-Chorus', bs('C','C#dim7','Dm','Ebdim','E7'), CP),
    nsec('nl-pc1', 'Lyric — Pre-Chorus', '<p>So I cry, and I pray, and I beg</p>', '', CP),
    sec('chorus1', 'Chorus 1', bs(
        'A','Dmaj7','Bm7','E13','A','Dmaj7','Bm7','E13',
        'A','Dmaj7','Bm7','E13','A','Dmaj7','Bm7','E13',
        'F#m7','Bm7','E13','Amaj7',
        'A','Dmaj7','Bm7','E13','A','Dmaj7','Bm7','E13',
        'A','Dm','Eaddb13','Am','Am'), CH, rs=[8,8,4,8,5]),
    nsec('nl-ch1', 'Lyric — Chorus 1',
         '<p>Love me, love me / Say that you love me<br>Fool me, fool me / Go on and fool me<br>Love me, love me / Pretend that you love me<br>Leave me, leave me / Just say that you need me<br>So I cry and I beg for you to</p>',
         '<p>Love me, love me / Say that you love me<br>Leave me, leave me / Just say that you need me<br>I can\'t care \'bout anything but you</p>', CH),
    sec('verse2', 'Verse 2', bs(
        'Am7','Dm7','G7','Cmaj7','Am','Dm7','G7','Cmaj7',
        'Am7','Dm7','G7','Cmaj7','Am','Dm7','G7'), CV, rs=[8,7]),
    nsec('nl-v2', 'Lyric — Verse 2',
         '<p>Lately I have desperately pondered<br>Spent my nights awake and I wonder<br>What I could have done in another way / To make you stay</p>',
         '<p>Reason will not reach a solution<br>I will end up lost in confusion<br>I don\'t care if you really care<br>As long as you don\'t go</p>', CV),
    sec('prechorus2', 'Pre-Chorus', bs('C','C#dim7','Dm','Ebdim','E7'), CP),
    sec('chorus2', 'Chorus 2', bs(
        'A','Dmaj7','Bm7','E13','A','Dmaj7','Bm7','E13',
        'A','Dmaj7','Bm7','E13','A','Dmaj7','Bm7','E13',
        'F#m7','Bm7','E13','Amaj7',
        'A','Dmaj7','Bm7','E13','A','Dmaj7','Bm7','E13',
        'A','Dm','Eaddb13'), CH, rs=[8,8,4,8,3]),
    sec('outro', 'Outro', bs(
        'A','Dmaj7','Bm7','E13','A','Dmaj7','Bm7','E13',
        'A','Dmaj7','Bm7','E13','A','Dmaj7','Bm7','E13',
        'A','Dmaj7','Bm7','E13',
        'A','Dm','Eaddb13','Am'), CI, rs=[8,8,4,4]),
    nsec('nl-outro', 'Lyric — Outro',
         '<p>Love me, love me / Say that you love me<br>Fool me, fool me / Go on and fool me<br>Love me, love me / I know that you need me<br>I can\'t care \'bout anything but you</p>', '', CI),
])

# ── 16 Toxic ──
make_file('Toxic', 'Britney Spears', '16-toxic', 'Cm', '143', '4/4', [
    sec('intro', 'Intro', bs('Cm','Cm','Cm','Cm','Cm','Cm','Cm','Cm'), CI),
    sec('verse1', 'Verse 1', bs('Cm','Cm','Cm','Cm','Eb','G'), CV),
    nsec('nl-v1', 'Lyric — Verse 1',
         '<p>Baby, can\'t you see I\'m callin\'?<br>A guy like you should wear a warnin\'<br>It\'s dangerous, I\'m fallin\'</p>', '', CV),
    sec('riff1', 'Riff', bs('Cm','Cm'), CR),
    sec('verse2', 'Verse 2', bs('Cm','Cm','Cm','Cm','Eb','G'), CV),
    nsec('nl-v2', 'Lyric — Verse 2',
         '<p>There\'s no escape, I can\'t wait<br>I need a hit, baby, give me it<br>You\'re dangerous, I\'m lovin\' it</p>', '', CV),
    sec('riff2', 'Riff', bs('Cm','Cm'), CR),
    sec('prechorus1', 'Pre-Chorus', bs('Cm','Cm','Cm','Cm','Eb','G'), CP),
    nsec('nl-pc1', 'Lyric — Pre-Chorus',
         '<p>Too high, can\'t come down<br>Losing my head, spinnin\' \'round and \'round<br>Do you feel me now?</p>', '', CP),
    sec('riff3', 'Riff', bs('Cm','Cm','Cm','Cm'), CR),
    sec('chorus1', 'Chorus 1', bs(
        'Cm','Eb7','D7','Db7','Cm','Eb7','Ab','G7|Db7',
        'Cm','Eb7','D7','Db7','Cm','Eb7','Ab','G7|Db7'), CH, rs=[8,8]),
    nsec('nl-ch1', 'Lyric — Chorus 1',
         '<p>With a taste of your lips, I\'m on a ride<br>You\'re toxic, I\'m slippin\' under<br>With a taste of a poison paradise<br>I\'m addicted to you / Don\'t you know that you\'re toxic?</p>',
         '<p>And I love what you do<br>Don\'t you know that you\'re toxic?</p>', CH),
    sec('riff4', 'Riff', bs('Cm','Eb7','D7','Db7','Cm','Eb7','Ab','G7|Db7'), CR),
    sec('verse3', 'Verse 3', bs('Cm','Cm','Cm','Cm','Eb','G'), CV),
    nsec('nl-v3', 'Lyric — Verse 3',
         '<p>It\'s gettin\' late to give you up<br>I took a sip from my devil\'s cup<br>Slowly, it\'s takin\' over me</p>', '', CV),
    sec('riff5', 'Riff', bs('Cm'), CR),
    sec('prechorus2', 'Pre-Chorus', bs('Cm','Cm','Cm','Cm','Eb','G'), CP),
    sec('riff6', 'Riff', bs('Cm','Cm'), CR),
    sec('chorus2', 'Chorus 2', bs(
        'Cm','Eb7','D7','Db7','Cm','Eb7','Ab','G7|Db7',
        'Cm','Eb7','D7','Db7','Cm','Eb7','Ab','G7|Db7'), CH, rs=[8,8]),
    sec('riff7', 'Riff', bs('Cm','Eb7','D7','Db7','Cm','Eb7','Ab','G7|Db7'), CR),
    sec('solo', 'Solo', bs(
        'Cm','Eb7','D7','Db7','Cm','Eb7','Ab','G',
        'G','G'), CS, rs=[8,2]),
    nsec('nl-solo', 'Lyric — Solo', '<p>Ha Haha ha ha.. / Ha Haha ha ha..</p>', '', CS),
    sec('chorus3', 'Chorus 3', bs(
        'Cm','Eb7','D7','Db7','Cm','Eb7','Ab','G',
        'Cm','Eb7','D7','Db7','Cm','Eb7','Ab','G'), CH, note='~ Eb on bar 95-96', rs=[8,8]),
    sec('riff8', 'Riff (End)', bs('Cm','Eb7','D7','Db7','Cm','Eb7','Ab','G'), CI),
    nsec('nl-outro', 'Lyric — Outro',
         '<p>Intoxicate me now with your lovin\' now<br>I think I\'m ready now, I think I\'m ready now (×2)</p>', '', CI),
])

# ── 17 Bad Guy ──
make_file('Bad Guy', 'Billie Eilish', '17-bad-guy', 'Gm', '135', '4/4', [
    sec('intro', 'Intro', bs('Gm','Gm','Gm','Gm','Cm','Cm','D','D'), CI),
    sec('verse1', 'Verse 1', bs(
        'Gm','Gm','Gm','Gm','Cm','Cm','D','D',
        'Gm','Gm','Gm','Gm','Cm','Cm','D','D',
        'Gm','Gm','Gm','Gm','Cm','Cm','D','D',
        'Gm','Gm','Gm','Gm','Cm','Cm','D','D'), CV, rs=[8,8,8,8]),
    nsec('nl-v1', 'Lyric — Verse 1',
         '<p>White shirt now red, my bloody nose<br>Sleepin\', you\'re on your tippy toes<br>Creepin\' around like no one knows<br>Think you\'re so criminal</p>',
         '<p>Bruises on both my knees for you<br>Don\'t say thank you or please<br>I do what I want when I\'m wanting to<br>My soul? So cynical</p>', CV),
    nsec('nl-v1b', 'Lyric — Verse 1 (cont.)',
         '<p>So you\'re a tough guy / Like it really rough guy<br>Just can\'t get enough guy / Chest always so puffed guy</p>',
         '<p>I\'m that bad type / Make your mama sad type<br>Make your girlfriend mad tight / Might seduce your dad type</p>', CV),
    sec('stop1', 'x / Stop', [b('Stop'),b('Stop')], CR, note="I'm the bad guy"),
    sec('mainriff1', 'Main Riff', bs('Gm','Gm','Gm','Gm','Cm','Cm','D','D'), CR),
    nsec('nl-riff1', 'Note — Main Riff',
         '<p>35/ Duh<br>39/ I\'m the bad guy</p>', '', CR),
    sec('verse2', 'Verse 2', bs(
        'Gm','Gm','Gm','Gm','Cm','Cm','D','D',
        'Gm','Gm','Gm','Gm','Cm','Cm','D','D',
        'Gm','Gm','Gm','Gm','Cm','Cm','D','D'), CV, rs=[8,8,8]),
    nsec('nl-v2', 'Lyric — Verse 2',
         '<p>I like it when you take control<br>Even if you know that you don\'t<br>Own me, I\'ll let you play the role<br>I\'ll be your animal</p>',
         '<p>My mommy likes to sing along with me<br>But she won\'t sing this song<br>If she reads all the lyrics<br>She\'ll pity the men I know</p>', CV),
    nsec('nl-v2b', 'Lyric — Verse 2 (cont.)',
         '<p>So you\'re a tough guy / Like it really rough guy<br>Just can\'t get enough guy / Chest always so puffed guy<br>I\'m that bad type / Make your mama sad type<br>Make your girlfriend mad tight / Might seduce your dad type</p>', '', CV),
    sec('stop2', 'x / Stop', [b('Stop'),b('Stop')], CR, note="I'm the bad guy"),
    sec('mainriff2', 'Main Riff', bs(
        'Gm','Gm','Gm','Gm','Cm','Cm','D','D',
        'Gm','Gm','Gm','Gm','Cm','Cm','D','D'), CR, rs=[8,8]),
    nsec('nl-riff2', 'Note — Main Riff',
         '<p>69/Duh<br>73/I\'m the bad guy<br>77/Duh<br>81/I\'m only good at bein\' bad, bad</p>', '', CR),
    sec('slow', 'Slow BPM:60', bs(
        'Gm','Gm','Gm','Gm','Gm','Gm','Gm','Gm',
        'Gm','Gm','Gm','Gm','Gm','Gm','Gm','Gm',
        'Gm','Gm','Gm','Gm'), CV, rs=[8,8,4]),
    nsec('nl-slow', 'Lyric — Slow section',
         '<p>I like when you get mad / I guess I\'m pretty glad that you\'re alone<br>You said she\'s scared of me? / I mean, I don\'t see what she sees<br>But maybe it\'s \'cause I\'m wearing your cologne</p>',
         '<p>I\'m a bad guy / I\'m, I\'m a bad guy<br>Bad guy, bad guy / I\'m a bad</p>', CV),
])

# ── 18 When You Were Young ──
make_file('When You Were Young', 'The Killers', '18-when-you-were-young', 'B', '130', '4/4', [
    sec('intro', 'Intro', bs('F#'), CI, note='Key-Syn note: 1=Syn1 main melody, 2=Syn2, 3=Syn+Bell, 4=Bell, 5=String, 6=หวานๆ (Focus เสียง 1-4)'),
    sec('riff1', 'Riff', bs('E','F#|G#m','B','E','E','F#|G#m','B','E'), CR),
    sec('verse1', 'Verse 1', bs('E','F#|G#m','B','E','E','F#|G#m','B','E'), CV),
    nsec('nl-v1', 'Lyric — Verse 1',
         '<p>You sit there in your heartache<br>Waiting on some beautiful boy to<br>To save you from your old ways<br>You play forgiveness<br>Watch it now, here he comes</p>', '', CV),
    sec('chorus1', 'Chorus 1', bs(
        'E','F#|G#m','B','E','E','F#|G#m','B','E',
        'E','F#|G#m','B','E'), CH, rs=[8,4]),
    nsec('nl-ch1', 'Lyric — Chorus 1',
         '<p>He doesn\'t look a thing like Jesus<br>But he talks like a gentleman<br>Like you imagined<br>When you were young</p>', '', CH),
    sec('verse2', 'Verse 2', bs('E','F#|G#m','B','E','E','F#|G#m','B','E'), CV),
    nsec('nl-v2', 'Lyric — Verse 2',
         '<p>Can we climb this mountain? I don\'t know<br>Higher now than ever before<br>I know we can make it if we take it slow<br>Let\'s take it easy / Easy now, watch it go</p>', '', CV),
    sec('chorus2', 'Chorus 2', bs(
        'E','F#|G#m','B','E','E','F#|G#m','B','E',
        'E','F#|G#m','B','E','E'), CH, rs=[8,5]),
    nsec('nl-ch2', 'Lyric — Chorus 2',
         '<p>We\'re burning down the highway skyline<br>On the back of a hurricane that started turning<br>When you were young / When you were young</p>', '', CH),
    sec('bridge1', 'Bridge', bs('E','F#|G#m','B','E','E','F#m'), CB, note='Syn4 Bell'),
    nsec('nl-br1', 'Lyric — Bridge',
         '<p>And sometimes you close your eyes<br>And see the place where you used to live<br>When you were young</p>', '', CB),
    sec('solo1', 'Solo 1', bs('E','F#|G#m','B','E','E','F#|G#m','B','E'), CS, note='Syn1'),
    sec('solo2', 'Solo 2 (Strings)', bs('E','D#m|C#m','B','A#|G#','F#','...'), CS, note='Syn5 String — descending'),
    sec('bridge2', 'Bridge', bs('C#m','C#m','E','G#m','D#m','G#m','F#','F#'), CB, note='Syn6 หวานๆ'),
    nsec('nl-br2', 'Lyric — Bridge',
         '<p>They say the devil\'s water, it ain\'t so sweet<br>You don\'t have to drink right now<br>But you can dip your feet<br>Every once in a little while</p>', '', CB),
    sec('riff2', 'RIFF', bs('E','F#|G#m','B','E'), CR),
    sec('solo3', 'Solo 2 (Reprise)', bs('E','F#|G#m','B','E','E','F#|G#m','B','E'), CS, note='Syn2 / Syn2 8va'),
    sec('verse3', 'Verse 3', bs('E','F#|G#m','B','E','E','F#|G#m','B','E'), CV, note='Syn2 Max'),
    nsec('nl-v3', 'Lyric — Verse 3',
         '<p>You sit there in your heartache<br>Waiting on some beautiful boy to<br>To save you from your old ways<br>You play forgiveness<br>Watch it now, here he comes</p>', '', CV),
    sec('chorus3', 'Chorus 3', bs(
        'F#m','F#m','B','A#|G#m','F#m','E','F#|G#m','B','E',
        'E','F#|G#m','B','E'), CH, note='Syn5 String Pad+Bell', rs=[9,4]),
    nsec('nl-ch3', 'Lyric — Chorus 3',
         '<p>He doesn\'t look a thing like Jesus<br>But he talks like a gentleman<br>Like you imagined / When you were young<br>I Said,</p>',
         '<p>he doesn\'t look a thing like Jesus<br>He doesn\'t look a thing like Jesus<br>But more than you\'ll ever know</p>', CH),
    sec('outro', 'Outro', bs('E','F#|G#m','B','E','E','F#|G#m','B','E'), CI, note='Syn1'),
    sec('riff3', 'Riff (End)', bs('E','D#m|C#m','B','A#|G#','F#','...'), CR),
])

# ── 19 Beggin' ──
make_file("Beggin'", 'Måneskin', '19-beggin', 'Bm', '134', '4/4', [
    sec('intro', 'Intro', [b('—')], CI, note="Put your lovin' hand out, baby / 'Cause I'm beggin'"),
    sec('riff1', 'Riff', bs('Bm','Bm','Bm','Bm'), CR),
    sec('chorus1', 'Chorus 1', bs('Bm','Em','C#m','F#','Bm','Em','C#m','F#'), CH),
    nsec('nl-ch1', 'Lyric — Chorus 1',
         '<p>I\'m beggin\', beggin\' you<br>So put your lovin\' hand out, baby<br>I\'m beggin\', beggin\' you<br>So put your loving hand out, darlin\'</p>', '', CH),
    sec('verse1', 'Verse 1', bs('Bm','G','C#m','F#','Bm','G','C#m','F#'), CV),
    nsec('nl-v1', 'Lyric — Verse 1',
         '<p>Ridin\' high when I was king<br>I played it hard and fast, \'cause I had everything<br>I walked away, you warned me then<br>But easy come and easy go and it would end</p>', '', CV),
    sec('prechorus1', 'Pre-Chorus', bs('Bm','G','C#m','F#','Bm','G','C#m','F#'), CP),
    nsec('nl-pc1', 'Lyric — Pre-Chorus',
         '<p>So anytime I bleed, you let me go<br>Anytime I feed, you get me, no<br>Anytime I seek, you let me know<br>I\'m on my knees when I\'m beggin\'<br>\'Cause I don\'t wanna lose you</p>', '', CP),
    sec('chorus2', 'Chorus 2', bs('Bm','Em','C#m','F#','Bm','Em','C#m','F#'), CH),
    sec('bridge1', 'Bridge 1', bs('—','G','C#m','F#','Bm','G','C#m','F#'), CB),
    nsec('nl-br1', 'Lyric — Bridge 1',
         '<p>I need you to understand<br>Tried so hard to be your man<br>The kind of man you want in the end<br>Only then can I begin to live again</p>', '', CB),
    sec('verse2', 'Verse 2', bs('Bm','G','C#m','F#','Bm','G','C#m','F#'), CV),
    nsec('nl-v2', 'Lyric — Verse 2',
         '<p>An empty shell, I used to be<br>The shadow of my life was hangin\' over me<br>A broken man that I don\'t know<br>Won\'t even stand the devil\'s dance to win my soul</p>', '', CV),
    sec('prechorus2', 'Pre-Chorus', bs(
        'Bm','Em','C#m','F#','Bm','Em','C#m','F#',
        'Bm','Em','C#m','F#','Bm'), CP, rs=[8,5]),
    nsec('nl-pc2', 'Lyric — Pre-Chorus 2',
         '<p>What we doin\'? What we chasin\'?<br>Why the bottom? Why the basement?<br>Why we got good shit, don\'t embrace it?</p>',
         '<p>But I keep walkin\' on, keep openin\' doors<br>\'Cause I don\'t wanna live in a broken home, girl, I\'m beggin\'</p>', CP),
    sec('chorus3', 'Chorus 3', bs('—','Em','C#m','F#','Bm','Em','C#m','F#'), CH),
    nsec('nl-ch3', 'Lyric — Chorus 3',
         '<p>Mmm, yeah, yeah, I\'m beggin\', beggin\' you<br>So put your lovin\' hand out, baby<br>I\'m beggin\', beggin\' you<br>So put your lovin\' hand out, darlin\'</p>', '', CH),
    sec('bridge2', 'Bridge 2', bs('—','G','C#m','F#','Bm','G','C#m','F#'), CB),
    nsec('nl-br2', 'Lyric — Bridge 2',
         '<p>I\'m fightin\' hard to hold my own<br>Just can\'t make it all alone<br>I\'m holdin\' on, I can\'t fall back<br>I\'m just a calm, \'bout to fade to black</p>', '', CB),
    sec('chorus4', 'Chorus Final', bs(
        'Bm','Em','C#m','F#','Bm','Em','C#m','F#',
        'Bm','Em','C#m','F#','Bm','Em','C#m','F#',
        'Bm','Em','C#m','F#','Bm','Em','C#m','F#',
        'Bm'), CH, rs=[8,8,8,1]),
    nsec('nl-ch4', 'Lyric — Chorus Final',
         '<p>I\'m beggin\', beggin\' you / Put your lovin\' hand out, baby (×3+)<br>I\'m beggin\', beggin\' you / So put your lovin\' hand out darlin\'</p>', '', CH),
])

# ── 20 Bring Me To Life ──
make_file('Bring Me To Life', 'Evanescence', '20-bring-me-to-life', 'Em', '95', '4/4', [
    sec('intro', 'Intro', bs('Em','C/E','C/E'), CI, note='Bar 1: Piano intro'),
    sec('verse1', 'Verse 1', bs('Em','Em','C/E','C/E','Em','Em','C/E','C/E'), CV),
    nsec('nl-v1', 'Lyric — Verse 1',
         '<p>How can you see into my eyes / Like open doors?<br>Leading you down into my core<br>Where I\'ve become so numb</p>', '', CV),
    sec('verse2', 'Verse 2', bs(
        'Em','Em','C/E','C/E','Em','Em','C/E','C/E'), CV, note='Gt. Distortion — Stop at bar 21'),
    nsec('nl-v2', 'Lyric — Verse 2',
         '<p>Without a soul (Oh) / My spirit sleeping somewhere cold<br>Until you find it there / And lead it back home</p>', '', CV),
    sec('chorus1', 'Chorus 1', bs('Em','G','D','Am','Em','G','D','Em'), CH),
    nsec('nl-ch1', 'Lyric — Chorus 1',
         '<p>(Wake me up) Wake me up inside<br>(I can\'t wake up) Wake me up inside<br>(Save me) Call my name and save me from the dark<br>(Wake me up) Bid my blood to run<br>(I can\'t wake up) Before I come undone<br>(Save me) Save me from the nothing I\'ve become</p>', '', CH),
    sec('verse3', 'Verse 3', bs('Em','Em','C/E','C/E','Em','Em','C/E','C/E'), CV),
    nsec('nl-v3', 'Lyric — Verse 3',
         '<p>Now that I know what I\'m without<br>You can\'t just leave me (No)<br>Breathe into me and make me real<br>Bring (Bring) me (Me) to life</p>', '', CV),
    sec('chorus2', 'Chorus 2', bs('Em','G','D','Am','Em','G','D','Em'), CH),
    sec('postchorus1', 'Post-Chorus', bs(
        'C','D','Em','Em','Em|F#m|G|Bm',
        'C','D','Em','Em|F#m|G|Bm'), CS, rs=[5,4]),
    nsec('nl-pc1', 'Lyric — Post-Chorus',
         '<p>Bring me to life<br>I\'ve been livin\' a lie / There\'s nothing inside<br>Bring me to life</p>', '', CS),
    sec('bridge', 'Bridge', bs(
        'Am','Em/G','F#','D','Em|F#m|G|Bm',
        'Am','Em/G','Bm','G'), CB, rs=[5,4]),
    nsec('nl-br', 'Lyric — Bridge',
         '<p>(Frozen inside) Frozen inside<br>(Without your love) Without your touch / without your love<br>(Only you) Darling, only you<br>Are the life among the dead</p>', '', CB),
    sec('verse4', 'Verse 4', bs('Em','Em','Em','Em','Em','Em','Em','D'), CV),
    nsec('nl-v4', 'Lyric — Verse 4',
         '<p>All this time, I can\'t believe I couldn\'t see<br>Kept in the dark, but you were there in front of me<br>Without a thought, without a voice, without a soul<br>Don\'t let me die here / There must be something more</p>',
         '<p>I\'ve been sleeping a thousand years, it seems<br>Got to open my eyes to everything<br>Bring me to life</p>', CV),
    sec('chorus3', 'Chorus 3', bs('Em','G','D','Am','Em','G','D','Em'), CH),
    sec('postchorus2', 'Post-Chorus', bs(
        'C','D','Em','Em|F#m|G|Bm',
        'C','D','Em','—'), CS, rs=[4,4]),
    nsec('nl-pc2', 'Lyric — Post-Chorus',
         '<p>Bring me to life<br>I\'ve been livin\' a lie / There\'s nothing inside<br>Bring me to life</p>', '', CS),
])

# ── 21 Hysteria ──
make_file('Hysteria', 'Muse', '21-hysteria', 'Am', '186', '4/4', [
    sec('intro', 'Intro', bs('Am','E7','Dm','Am','Am','E7','Dm','Am'), CI),
    sec('riff1', 'Riff', bs('Am','E7','Dm','Am','Am','E7','Dm','Am'), CR),
    sec('verse1', 'Verse 1', bs('Am','E7','Dm','Am','Am','E7','Dm','Am'), CV),
    nsec('nl-v1', 'Lyric — Verse 1',
         '<p>It\'s bugging me / Grating me<br>And twisting me around<br>Yeah, I\'m endlessly / Caving in<br>And turning inside out</p>', '', CV),
    sec('chorus1', 'Chorus 1', bs('C','G7','D','A','C','G7','D','E7'), CH),
    nsec('nl-ch1', 'Lyric — Chorus 1',
         '<p>\'Cause I want it now / I want it now<br>Give me your heart and your soul<br>And I\'m <strong>breaking out</strong> / I\'m <strong>breaking out</strong><br>Last chance to lose control</p>', '', CH),
    sec('riff2', 'Riff', bs('Am','E7','Dm','Am'), CR),
    sec('verse2', 'Verse 2', bs('Am','E7','Dm','Am','Am','E7','Dm','Am'), CV),
    nsec('nl-v2', 'Lyric — Verse 2',
         '<p>And it\'s holding me / Morphing me<br>And forcing me to strive<br>To be endlessly / Cold within<br>And dreaming I\'m alive</p>', '', CV),
    sec('chorus2', 'Chorus 2', bs('C','G7','D','A','C','G7','D','Am'), CH),
    nsec('nl-ch2', 'Lyric — Chorus 2',
         '<p>\'Cause I want it now / I want it now<br>Give me your heart and your soul<br>I\'m <strong>not breaking down</strong> / I\'m <strong>breaking out</strong><br>Last chance to lose control</p>', '', CH),
    sec('riff3', 'Riff', bs('E7','E7','E7','E7'), CR),
    sec('solo1', 'Solo 1', bs('Am','E7','Dm','Am','Am','E7','Dm','Am'), CS),
    sec('solo2', 'Solo 2', bs('C','G','D','A','C','G','D','A'), CS),
    sec('chorus3', 'Chorus 3', bs('C','G7','D','A','C','G7','D','Am'), CH),
    nsec('nl-ch3', 'Lyric — Chorus 3',
         '<p>And I want you now / I want you now<br>I feel my heart implode<br>And I\'m <strong>breaking out</strong> / <strong>Escaping now</strong><br>Feeling my faith erode</p>', '', CH),
    sec('outro', 'Outro', bs('E7','E7','E7','E7','E7','E7','E7'), CI),
])

print('\n✅ Done! All 21 bandsheets created.')
