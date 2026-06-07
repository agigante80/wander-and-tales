# European Portuguese (pt-PT) quality guide

The single source of truth for writing and reviewing Wander & Tales content in
**European Portuguese (Portugal)**. The goal is prose that sounds natural to a
family in Portugal and never drifts into **Brazilian Portuguese (pt-BR)**, which
the project treats as a separate language added later (like en-GB versus en-US).

This grew out of a native-speaker review that found the whole pt-PT corpus had
been written in the archaic "vós" register with Brazilian gerunds. Those are the
two biggest traps; everything below is ordered by how often it bites.

(Full accents are mandatory in all content; this guide uses them so the example
forms can be copied directly.)

## 1. Register: how you address people

- **One child (singular): use "tu".** "Qual é o **teu** nome?", "Que magia
  **escolhes**?" Avoid "você" for a single child (it reads formal or Brazilian).
- **The group of players (plural): use "vocês" with 3rd person plural verbs.**
  "O que é que **vocês fazem**?", "**Leiam** em voz alta."
- **The grown-up / Game Master in the guides: "tu"** (singular), matching the
  shared Guide ("Imprime", "Lê", "Tem à mão"). Setup lists that address everyone
  doing it together may use "vocês" plural, but pick one and stay consistent
  inside a file.

**Negative commands to one child use the subjunctive, not the indicative.** The
affirmative "tu" imperative is "faz", "corre", "olha"; the negative is the present
subjunctive: "não **faças**", "não **corras**", "não **tenhas** medo", "não **te
preocupes**". Avoid the Brazilian colloquial "não faz", "não corre". For the group
the negative is the same "vocês" form: "não **façam**", "não **tenham** medo".

### Never use "vós"

"Vós" (and its 2nd person plural verbs) is archaic or regional in Portugal. This
is the single most common mistake. Convert every "vós" form to the "vocês"
(3rd person plural) form. The conjugations are **irregular**, so never do a blind
find and replace. Use this table:

| vós form (wrong) | vocês form (right) | kind |
|---|---|---|
| sois | são | present |
| estais | estão | present |
| ides | vão | present |
| dais | dão | present |
| tendes | têm | present |
| vindes | vêm | present |
| fazeis | fazem | present |
| dizeis | dizem | present |
| vedes | veem | present |
| podeis | podem | present |
| quereis | querem | present |
| sabeis | sabem | present |
| ouvis | ouvem | present |
| encontrais | encontram | present |
| chegais | chegam | present |
| falais | falam | present |
| olhais | olham | present |
| trocais | trocam | present |
| estendeis | estendem | present |
| arregaçais | arregaçam | present |
| escolheis | escolhem | present |
| Lede | Leiam | imperative |
| Vede | Vejam | imperative |
| Ouvi | Ouçam | imperative |
| Pedi | Peçam | imperative |
| Fazei | Façam | imperative |
| Dizei | Digam | imperative |
| Ide | Vão | imperative |
| Vinde | Venham | imperative |
| Tende | Tenham | imperative |
| Sede | Sejam | imperative |
| Dai | Deem | imperative |
| Parai | Parem | imperative |
| Olhai | Olhem | imperative |
| Deixai | Deixem | imperative |
| Trazei | Tragam | imperative |
| Tomai | Tomem | imperative |
| Tentai | Tentem | imperative |
| Procurai | Procurem | imperative |
| Cantai | Cantem | imperative |
| Brincai | Brinquem | imperative |
| Ajudai | Ajudem | imperative |
| Esperai | Esperem | imperative |
| fostes | foram | preterite |
| fizestes | fizeram | preterite |
| encontrastes | encontraram | preterite |
| vistes | viram | preterite |
| dissestes | disseram | preterite |
| tivestes | tiveram | preterite |
| estivestes | estiveram | preterite |
| estáveis | estavam | imperfect |
| éreis | eram | imperfect |
| fazíeis | faziam | imperfect |
| tínheis | tinham | imperfect |
| íeis | iam | imperfect |
| seguirdes | seguirem | inflected infinitive |
| pedirdes | pedirem | inflected infinitive |
| enfrentardes | enfrentarem | inflected infinitive |
| fizerdes | fizerem | future subjunctive |
| estivésseis | estivessem | imperfect subjunctive |
| fôsseis | fossem | imperfect subjunctive |

**Pronoun and possessive.** "vós" becomes "vocês". The possessives "vosso" and
"vossa" **may stay**, and the clitic "-vos" is natural ("a vossa magia",
"deixa-vos atravessar" = lets you all cross), so keep them where they read well.
This is accepted, dominant usage in Portugal (it avoids the ambiguity of "seu"),
but it is a contested area: some grammarians prescribe "seu/sua" and "os/as/lhes"
with "vocês". For warm kid prose the natural "vosso" and "-vos" win; just do not
mistake the kept "-vos" clitic for a "vós" verb form you should be converting.

## 2. Gerund versus "a + infinitivo" (Brazilianism)

In Portugal the gerund (`-ando`, `-endo`, `-indo`) is rarely used for an ongoing
action. Use **"a + infinitivo"**.

- "As crianças estão **a brincar**." (not "estão brincando")
- "O dragão está **a dormir**." (not "está dormindo")
- In instructions: "**Ao ajudar** o amigo" or "**a ajudar** o amigo" (not
  "ajudando o amigo").

Watch for false friends when scanning: "quando", "lindo", "brando", "comando"
end in those letters but are not gerunds.

Not every gerund is Brazilian: the **adverbial** gerund is fine in European
Portuguese ("**Mesmo sabendo** que era difícil", "**correndo** o risco de"). It is
only the **progressive** gerund for an action in progress ("estou fazendo") that
is the Brazilianism to fix ("estou a fazer"). The scanner flags every gerund, so
the judgment pass keeps the adverbial ones.

## 3. Clitic pronoun placement

European Portuguese puts the pronoun **after the verb (enclisis)** by default;
Brazilian prefers it before (proclisis).

- Default: "Dá-**lhe** um pão.", "Vou ajudar-**te**.", "Chamaram-**nos**."
  Avoid "Me dá um pão.", "Te vou ajudar."
- After a negative or a subordinating word it moves before the verb (proclisis):
  "**Não lhe** dês o pão.", "Espero **que o** encontres."
- Other words also pull the pronoun before the verb (proclisis): quantifiers
  ("**todos** o sabem"), focalising adverbs ("**só** lhe disse", "**também** te
  ajudo", "**até** me sorriu"), and some adverbs ("**já** te disse", "**sempre**
  me ajuda", "**talvez** o encontres").

Avoid **mesoclisis** in kid prose. Forms like "dar-te-ei" or "encontrar-se-ia"
(the pronoun tucked inside a future or conditional verb) are grammatically
European but sound formal and literary. Rephrase with a periphrasis a child would
hear: "vou dar-te", "ia encontrar-se".

## 4. Vocabulary: pt-PT versus pt-BR

| meaning | pt-PT (use) | pt-BR (avoid) |
|---|---|---|
| screen | ecrã | tela |
| mobile phone | telemóvel | celular |
| bus | autocarro | ónibus |
| train | comboio | trem |
| tram | elétrico | bonde |
| bathroom | casa de banho | banheiro |
| fridge | frigorífico | geladeira |
| juice | sumo | suco |
| cup | chávena | xícara |
| breakfast | pequeno-almoço | café da manhã |
| boy / kid | rapaz, miúdo | garoto, moleque |
| to grab, catch | apanhar | pegar |
| team | equipa | equipe |
| sticker | autocolante | adesivo |
| to plan | planear | planejar |
| cool, great | fixe, giro | legal, bacana |
| wildcard, master key | chave-mestra | coringa |
| girl | rapariga, miúda | garota |
| ice cream | gelado | sorvete |
| sweet (candy) | rebuçado | bala |
| trainers | sapatilhas, ténis | tênis |
| butcher's | talho | açougue |
| marble (toy) | berlinde | bolinha de gude |

Also: "nós" not "a gente" for "we" (note "toda a gente" meaning everyone is
correct pt-PT). "para eu fazer" not "para mim fazer". Movement takes "a" or
"para": "vou ao parque", never "vou no parque".

"Rapariga" is the everyday Portugal word for a girl; keep it, and do not let a
Brazilian ear "correct" it to "menina" or "garota" (in Brazil "rapariga" is
offensive, but in Portugal it is neutral and normal). "Berlinde" (a marble) is
worth knowing because these kits are played with household objects.

## 5. Spelling (Acordo Ortográfico 1990)

pt-PT keeps some consonants that pt-BR drops, where the consonant still shapes the
word. Common pt-PT spellings: "receção", "deteção", "facto" (a fact; "fato" is a
suit in Portugal), "contacto", "aspeto". Portugal also writes "**connosco**" with
two n's (Brazilian "conosco"). When unsure, check a Portugal dictionary; do not
assume the Brazilian spelling.

## 6. Project rules (Wander & Tales)

- **No losing.** Never "derrota", "fracasso", or "perder" as failure. A failed try
  is a "desvio" or "outro caminho". Keep the no-lose promise intact.
- **Warmth.** The voice is a kind grown-up, not a textbook. Reach for "meigo",
  "doçura", "bondade", "calor", "aconchego".
- **No dashes.** Never an em dash or en dash, anywhere. Use commas, colons,
  parentheses, or separate sentences. Number ranges are "3 a 5", never with a dash.
- **Canon names.** Every character, place, creature, and item name must match the
  world `canon/` and the repo lexicon for pt-PT. Prose follows canon.
- **Plain words a parent can relay.** Lead with the fun; avoid jargon.

## 7. Soft, associational claims (the Why page and any grown-up copy)

Claims about children are associational, never causal: "associa-se a", "uma forma
de praticar", not "torna as crianças mais inteligentes" or "melhora as notas". The
study about media use is about a parent and child ("um pai ou mãe e a sua
criança"), not adults in general.

## 8. Reviewer checklist

1. [ ] Any "vós" pronoun or 2nd person plural verb (`-ais`, `-eis`, `-des`,
   `-stes`, `-sseis`, `-rdes`)? Convert to the "vocês" 3rd person plural form.
2. [ ] Any **progressive** gerund (`estou fazendo`) for an action in progress?
   Change to "a + infinitivo". (Adverbial gerunds like "mesmo sabendo" are fine.)
3. [ ] Negative commands to a child in the subjunctive ("não faças", "não
   corras"), not the indicative ("não faz")?
4. [ ] Clitics after the verb (enclisis), except after a negative, subordinating
   word, quantifier, or focalising adverb? No mesoclisis ("dar-te-ei") in kid prose?
5. [ ] Any pt-BR vocabulary (ecrã not tela, sumo not suco, apanhar not pegar,
   rapariga kept not "corrected")?
6. [ ] Portugal spelling (facto, contacto, receção, connosco)?
7. [ ] No em or en dashes; ranges as "3 a 5"?
8. [ ] No-lose tone: no "derrota", "fracasso", "perder" as failure?
9. [ ] Names match the pt-PT canon and lexicon?
10. [ ] Grown-up claims associational, never causal?
