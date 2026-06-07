# Peninsular Spanish (es-ES) quality guide

The single source of truth for writing and reviewing Wander & Tales content in
**Spanish from Spain (es-ES)**. The goal is prose that sounds natural to a family
in Spain and never drifts into Latin American Spanish, which the project treats as
a separate language added later (like en-GB versus en-US, or pt-PT versus pt-BR).

The two traps that bite most often are addressing the players as "ustedes" instead
of "vosotros", and Latin American vocabulary. Everything below is ordered by how
often it matters.

(Full accents are mandatory in all content; this guide uses them so the example
forms can be copied directly.)

## 1. Register: how you address people

- **One child (singular): use "tú".** "¿Cómo te llamas?", "¿Qué magia
  **eliges**?" Use "tu" and "ti" for the possessive and object.
- **The group of players (plural): use "vosotros" with its 2nd person plural
  verbs.** "¿Qué **hacéis**?", "**Leed** en voz alta.", "¿Estáis **listos**?"
  The pronoun is "vosotros/vosotras", the object and reflexive is "os", the
  possessive is "vuestro/vuestra".
- **The grown-up in the guides: "tú"** (singular), matching the shared Guide
  ("Imprime", "Lee", "Ten a mano"). Setup lists that address everyone doing it
  together may use "vosotros", but pick one and stay consistent inside a file.

### Address the players as "vosotros", not "ustedes"

In standard peninsular Spanish, "vosotros" is the familiar plural and "ustedes" is
the formal one, so addressing a warm family game with "ustedes" reads cold. Use
"vosotros". (Note: "ustedes" for the informal plural is not only Latin American; it
is also the everyday form in the Canary Islands and western Andalusia, where it
takes 3rd person plural verbs. But the project's standard written register is the
"vosotros" one, so convert "ustedes" address to "vosotros".)

| ustedes form (wrong here) | vosotros form (right) |
|---|---|
| ustedes hacen | vosotros hacéis |
| ustedes tienen | vosotros tenéis |
| ustedes pueden | vosotros podéis |
| ustedes van | vosotros vais |
| ustedes son | vosotros sois |
| ustedes eligen | vosotros elegís |
| miren | mirad |
| lean | leed |
| escuchen | escuchad |
| ayúdense | ayudaos |
| siéntense | sentaos |

Note the reflexive imperative drops the final "-d": "sentaos" (not "sentados"),
"callaos", "ayudaos". The verb "irse" is the exception: "idos" is the traditional
form, and the RAE now also accepts the colloquial "iros", which sounds more
natural in a warm voice.

### Never use voseo

"Vos" with forms like "tenés", "querés", "sos", "podés", "hacés" is River Plate
Spanish. Use the standard "tú" forms: "tienes", "quieres", "eres", "puedes",
"haces".

### Leísmo de persona: "le" for a male person is fine in Spain

Using "le" for a masculine singular person as a direct object is accepted and
natural in Spain: "¿Has visto a Pook? Sí, **le** vi en el jardín." Do not let a
Latin-American ear "correct" it to "lo". Keep the limits, though: "la dije"
(laísmo) is wrong, "les" as a plural direct object is rejected, and for things use
"lo/la", never "le" ("el mapa, **lo** guardo").

## 2. Vocabulary: peninsular versus Latin American

| meaning | es-ES (use) | Latin American (avoid) |
|---|---|---|
| car | coche | carro, auto |
| computer | ordenador | computadora |
| mobile phone | móvil | celular |
| juice | zumo | jugo |
| potato | patata | papa |
| peas | guisantes | arvejas, chícharos |
| beans | judías, alubias | frijoles, porotos |
| peach | melocotón | durazno |
| strawberry | fresa | frutilla |
| pavement | acera | vereda |
| grass, lawn | césped, hierba | pasto, grama |
| glasses | gafas | lentes, anteojos |
| socks | calcetines | medias |
| ticket | billete, entrada | boleto |
| to drive | conducir | manejar |
| to chat | charlar, hablar | platicar |
| to get angry | enfadarse | enojarse |
| to grab, take | coger | agarrar |
| cool, great | guay, chulo, mola | chévere, padre, bacán |
| okay | vale | okay, ok |
| right now | ahora mismo | ahorita |
| cake | tarta | torta, queque |
| sticker | pegatina | calcomanía |
| marble (toy) | canica | bolita |

"Coger" is completely normal and frequent in Spain (coger la pelota, coger una
pista); do not replace it with "agarrar" or "tomar". Use "vale" for agreement.
For recent past, Spain favours the present perfect: "hoy **hemos jugado**", "ya lo
**he encontrado**" (Latin American often uses the simple preterite here).

"Canica" (a marble) and "pegatina" (a sticker) are worth knowing because these
kits are played with household objects.

## 3. Spelling and accents

Full accents are mandatory: "qué", "más", "está", "magía" only where it carries an
accent (it does not; "magia" has none), "ratón", "jardín", "pequeño". Distinguish
the pairs by meaning: "qué/que", "cómo/como", "más/mas", "sí/si", "tú/tu",
"él/el", "sé/se", "dé/de". The LanguageTool check (`build check-lang --locale
es-ES`) catches most missing accents and misspellings; this guide carries the
register and vocabulary, which LanguageTool does not know.

## 4. Project rules (Wander & Tales)

- **No losing.** Never "derrota", "fracaso", or "perder" as failure. A failed try
  is "otro camino" or "un desvío". Keep the no-lose promise intact.
- **Warmth.** The voice is a kind grown-up, not a textbook. Reach for "cariño",
  "ternura", "mimos", "dulzura", "calorcito", "achuchón", "cielo", and the very
  Spanish "peques" (the little ones), "majo/maja" (lovely), and "venga" (come on).
- **No dashes.** Never an em dash or en dash, anywhere. Use commas, colons,
  parentheses, or separate sentences. Number ranges are "3 a 5", never with a dash.
- **Canon names.** Every character, place, creature, and item name must match the
  world `canon/` and the repo lexicon for es-ES. Prose follows canon.
- **Plain words a parent can relay.** Lead with the fun; avoid jargon.

## 5. Soft, associational claims (the Why page and any grown-up copy)

Claims about children are associational, never causal: "se asocia con", "una forma
de practicar", not "hace a los niños más inteligentes" or "mejora las notas". The
study about media use is about a parent and child together ("un padre o una madre
y su hijo o hija"), not adults in general.

## 6. Reviewer checklist

1. [ ] Players addressed as "vosotros" (hacéis, leed, vuestro, os), never
   "ustedes" or 3rd person plural?
2. [ ] No voseo (vos, tenés, querés, sos, podés)?
3. [ ] "le" for a male person kept (not "corrected" to "lo"); but no laísmo
   ("la dije") and no "les" as a plural direct object?
4. [ ] No Latin American vocabulary (coche not carro, ordenador not computadora,
   zumo not jugo, móvil not celular, patata not papa)?
5. [ ] "vale" for okay, "guay/mola" for cool, "coger" used naturally?
6. [ ] Full accents, and the accented pairs correct (qué/que, más/mas, sí/si)?
7. [ ] No em or en dashes; ranges as "3 a 5"?
8. [ ] No-lose tone: no "derrota", "fracaso", "perder" as failure?
9. [ ] Names match the es-ES canon and lexicon?
10. [ ] Grown-up claims associational, never causal?
