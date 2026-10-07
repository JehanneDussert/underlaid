# Second calcul des durées — rapport du 7 octobre 2026

Calcul terminé le 7 octobre à 1 h 25. Enchaînement automatique (agrégation, contrôles, sensibilités, croisement de contrôle, fichiers du site) terminé sans erreur à 3 h 35. Seuils appliqués tels qu'écrits le 6 octobre à 22 h 17 (`2026-10-06-second-routing-run-blocking-thresholds.md`). Sorties : `data/interim/analysis/` du dossier principal (`v2_blocking_thresholds.txt`, `v2_inversions.txt`, `v2_compare.txt`, `v2_speed_sensitivity*.txt`, `routes_*controls_v2.txt`, `routes_means_v2.txt`).

## Verdict des seuils : publication bloquée (seuil 3)

| Seuil | Résultat | Statut |
|---|---|---|
| 1. Fauteuil roulant plus court que sans contrainte (> 0,5 %) | 11 couples sur 62 744 (0,018 %), dans les deux variantes ; 0,8 % avant correction | passe |
| 2. Ancien / nouveau sans contrainte (moyenne > 1 min, ou > 5 % des quartiers à ± 5 min) | moyennes de − 0,34 à + 0,16 min ; au plus 3,1 % des quartiers à ± 5 min (CAF) | passe |
| 3a. Quartier habité sans durée | 2 quartiers : Aulnay-sous-Bois Nord 1 (445 hab.), Épinay-sur-Seine Iris 2 (1 683 hab.) | **bloque** |
| 3b. Population non atteinte en 90 min (> 1 %, tous profils, mardi 10 h) | CAF en fauteuil roulant, inconnu = non accessible : 1,1 % (inconnu = accessible : 0,5 %) ; tous les autres lieux ≤ 0,6 % | **bloque** |
| 3c. Hausse du nombre de quartiers « plus de 90 min » (> 10), sans contrainte ou marche lente | aucune | passe |
| 4. Verdicts du croisement « services publics » | inchangés : (a) infirmée, nettement inversée dans 92, 93, 94 ; (b) infirmée, nettement inversée dans les 4 départements, dans les deux variantes | passe |

### 3a — deux quartiers sans durée

Les deux quartiers manquaient déjà au premier calcul, celui qui est en ligne (2 747 quartiers sur 2 752 dans les deux). Aucun carreau habité de 200 m n'a son centre dans ces quartiers. Le 3 octobre, une règle avait été notée : leur attribuer le carreau qui contient leur point représentatif, comme le fait le script 32. Elle n'a jamais été appliquée au script 36. Ce n'est donc pas une régression, mais le seuil est franchi tel qu'il a été écrit.

### 3b — CAF en fauteuil roulant, 1,1 % de la population

20 quartiers habités (60 228 habitants) perdent au moins un lieu atteignable en 90 minutes en fauteuil roulant entre le premier et le second calcul. La perte porte surtout sur la CAF. Deux causes distinctes apparaissent :

1. **Trajets déjà longs, rendus plus longs par la vitesse de 0,8 m/s** : Villecresnes (4 quartiers), Mandres-les-Roses, Marolles-en-Brie, Périgny, Santeny, Tremblay-en-France, Villepinte. La CAF y est déjà à 45-70 minutes sans contrainte. C'est l'effet attendu du nouveau profil.
2. **Îlots créés par le retrait des pentes** : Paris 18e (Grandes Carrières 9, Clignancourt 5), Chaville (Iris 0101), probablement Montfermeil et Coubron.
   - À Grandes Carrières 9, le médecin le plus proche reste à 4 minutes, mais aucun autre lieu n'est atteint en 90 minutes. Au premier calcul, les durées étaient de 16 à 33 minutes.
   - À Chaville, aucun lieu clé n'est atteint en fauteuil roulant (inconnu = non). Au premier calcul, ils l'étaient tous, en 10 à 30 minutes.
   - Sur le plan IGN :
     - autour de la butte Montmartre, la plupart des rues retirées montent réellement ;
     - quelques tronçons retirés sur des axes plats, près des voies ferrées du nord, ressemblent à des artefacts du modèle de terrain près des ponts ;
     - à Chaville, versant de vallée, une grande partie des rues résidentielles est retirée, et le réseau se fragmente en de nombreux morceaux.
   - Images : scratchpad de session, `island_*.jpg`.

**Lecture** : le seuil de 8 % appliqué au réseau entier rend certains quartiers en pente « injoignables ». C'est en partie vrai : beaucoup de rues de Montmartre et de Chaville dépassent 8 %. C'est aussi en partie un effet de construction : de courts tronçons retirés coupent des liaisons qui existent, et R5 rattache les points de départ à un fragment isolé.

## Contrôles non bloquants

- **Durées en fauteuil roulant** (médiane des quartiers, mardi 10 h) : de + 2 minutes (médecin, pharmacie : 3 → 5) à + 7 minutes (CAF : 29 → 36). Les lieux du quotidien sont à 4-21 minutes, contre 3-14 sans contrainte.
- **Durées sans contrainte** : médianes inchangées ; écart moyen de − 0,3 à + 0,2 minute ; 25 à 38 % des quartiers changent d'au moins une minute, le plus souvent à la baisse.
- **Sensibilité à la vitesse** (lieux clés) :
  - à 0,5 m/s : CAF 44 minutes, mairie 26 ; Spearman 0,95-0,99 avec 0,8 m/s ; 1,5 à 8,6 % des quartiers changent de quart le plus éloigné ;
  - à 1,0 m/s : CAF 32 minutes, mairie 16 ; Spearman 0,98-0,99 ; 2,6 à 7,5 %.
- **Sensibilité à la pente de 6 %** : médianes quasi identiques à celles de 8 % ; Spearman 0,96-0,99 ; 1,7 à 3,6 % des quartiers changent de quart pour les lieux clés, jusqu'à 8,9 % pour la maternelle.
- **Écoles publiques** (médiane, sans contrainte / fauteuil roulant) : élémentaire 4 / 7 minutes, collège 7 / 12, lycée 10 / 16.

## Décision attendue

La publication des nouvelles durées est suspendue. Options :

- **(a) Publier tel quel** : le chiffre de 1,1 % et les quartiers concernés sont décrits comme une limite. Les deux quartiers sans durée restent comme aujourd'hui.
- **(b) Examiner les îlots avant de publier** (recommandé) :
  - compter les carreaux rattachés à un fragment du réseau sans pentes ;
  - vérifier 5 cas à l'imagerie ;
  - décider ensuite d'une règle, qui serait une décision prise après avoir vu les résultats et notée comme telle. Exemple : ne pas retirer un tronçon isolé de moins de N m entre deux tronçons gardés ; ou rattacher les points au plus grand fragment.
  - Dans les deux cas, appliquer aussi la règle déjà décidée le 3 octobre pour les 2 quartiers sans carreau.
- **(c)** Autre choix de la porteuse du projet.

Rien n'est publié. Les fichiers du site régénérés à partir du second calcul ne sont dans aucun commit.

## Décision de la porteuse du projet et suites — 7 octobre 2026

**Décision reçue à 3 h 52** (heure du premier traitement du message) :
- îlots : option (b), sans nouvelle règle de pente ; d'abord vérifier si des tronçons sur ou près de ponts ont été retirés (erreur d'application, à corriger seulement si c'est le cas) ;
- **seuil 3b levé pour la cause « vitesse »** : les communes éloignées qui passent au-delà de 90 minutes à cause de la vitesse de 0,8 m/s sont acceptées comme un résultat ;
- les deux quartiers sans durée : appliquer la règle du 3 octobre.

### Ponts (`scripts/analysis/slope_bridge_check.py`)

- Tronçons retirés portant une balise pont, tunnel ou niveau différent : **0**. L'exclusion pré-enregistrée a été appliquée.
- Tronçons retirés qui croisent une voie ferrée, un cours d'eau ou une voie rapide sans balise de pont : 13, soit 454 m (aires de service, chemins forestiers, aucun dans un quartier habité).
- Tronçons retirés près d'un pont : 109 km à moins de 20 m, 73 km entre 20 et 30 m. Ce sont des rampes d'accès, mesurées sur des points situés à plus de 20 m du pont, comme le prévoit la règle du 5 octobre.
- **Conclusion : pas d'erreur d'application, aucun lot recalculé.** Les retirer serait une nouvelle règle.

### Deux quartiers sans durée

La règle du 3 octobre (carreau qui contient le point représentatif) était déjà dans le script 36, mais le point représentatif de ces deux quartiers tombe dans un carreau sans habitant, absent de la grille. Lecture la plus proche de la règle, appliquée et signalée : **le carreau habité déjà calculé qui recouvre le plus le quartier**. Après cela, plus aucun quartier n'est sans durée (2 752 sur 2 752).

### Îlots et sensibilité sans retrait des pentes (`scripts/analysis/v2_islands_no_slope.py`)

Même profil (0,8 m/s, arrêts accessibles, inconnu = non accessible, mardi 10 h) sur le réseau sans escaliers mais **sans retrait des pentes**, pour les 18 quartiers qui perdent au moins un lieu proche (≤ 45 min sans contrainte) :
- **Îlots complets** (presque aucun lieu atteint ; tout redevient atteignable sans retrait des pentes) :
  - Grandes Carrières 9 (1 628 hab.) : CAF de plus de 90 min à 43 min ;
  - Clignancourt 5 (1 964 hab.) : 42 min ;
  - Chaville Iris 0101 (2 749 hab.) : 34 min.
  - Au total 6 341 habitants (2 quartiers, 3 592 habitants, avec « inconnu = accessible »).
- **Lieux perdus à cause des pentes, ailleurs** (atteints sans retrait des pentes) : Montfermeil Les Arbres (CAF 66 min), Villepinte Nord-Est Mousseaux (CAF 88 min), Marolles-en-Brie Vieux Village (lycée public 89 min), Villecresnes, 4 quartiers (centre social 34 à 54 min).
- **Cause « vitesse »** (toujours au-delà de 90 min sans retrait des pentes) : Coubron, Montfermeil Les Coudreaux, Mandres-les-Roses, Périgny, Santeny, Sucy-en-Brie Notre-Dame-Bruyères, Marolles-en-Brie La Butte du Berger, Tremblay-en-France Centre Activités, pour certains lieux (CAF surtout).
- **CAF en fauteuil roulant au-delà de 90 min à cause des pentes** : 15 187 habitants (0,22 % de la population), sous le seuil de 1 %. Avec la levée pour la cause « vitesse », **le seuil 3b ne bloque plus**.
- Quartiers où au moins un lieu n'est plus atteint à cause des pentes : environ 29 000 habitants (0,4 %).

### Cinq cas vérifiés à l'imagerie (IGN, réseau sans pentes superposé)

1. **Grandes Carrières 9** (flanc ouest de la butte Montmartre, secteur rue Lepic) : quartier entouré de rues retirées qui montent réellement. Les carreaux se rattachent à des fragments de réseau isolés (103, 26, 24 nœuds), alors que le réseau principal compte 15 834 nœuds.
2. **Clignancourt 5** (flanc sud de la butte, vers le Sacré-Cœur) : même situation, fragments de 103 et 63 nœuds.
3. **Chaville Iris 0101** (coteau boisé de la vallée) : une grande partie des rues résidentielles descend à plus de 8 %. Le réseau se fragmente en 241 morceaux dans un carré de 2 km ; les rues du centre forment un fragment isolé de 46 nœuds.
4. **Coubron** (plateau) : le réseau reste relié (composante principale de 2 247 nœuds). L'allongement vient de la vitesse et des détours imposés par les pentes : arrêt accessible le plus proche 68 min au lieu de 27 en 1er calcul ; urgences 81 min, 51 sans retrait des pentes.
5. **Montfermeil Les Coudreaux** : relié (2 014 nœuds) ; même effet de détour (arrêt accessible 65 min, urgences 73 min, 36 sans retrait des pentes).

**Lecture** : Montmartre et Chaville sont de vrais secteurs en forte pente. Le calcul les isole, faute de chemin à 8 % ou moins vers l'extérieur. Conformément à la décision, les rues qui montent vraiment restent retirées.

### Arrêt accessible le plus proche (îlots)

À vol d'oiseau depuis le centre habité du quartier ; atteignable en fauteuil roulant, d'après le calcul (marche à 0,8 m/s sur le réseau sans pentes, 90 min au plus) :

| Quartier | Arrêt accessible le plus proche | Distance | Atteint par la rue (2e calcul) |
|---|---|---|---|
| Grandes Carrières 9 | Angélique Compoint - Porte de Montmartre (tram) | 1,25 km | non (1er calcul : 24 min) |
| Clignancourt 5 | Gare du Nord | 1,12 km | non (1er calcul : 22 min) |
| Chaville Iris 0101 | Chaville Rive Droite | 0,40 km | non (1er calcul : 8 min) |
| Coubron | Hôpital de Montfermeil (tram T4) | 1,50 km | oui, 68 min |
| Montfermeil Les Coudreaux | Hôpital de Montfermeil (tram T4) | 1,22 km | oui, 65 min |
| Montfermeil Les Arbres | Arboretum (tram T4) | 1,03 km | oui, 27 min |

### Contrôles refaits après ces corrections

- Seuil 1 : 11 couples sur 62 788 (0,018 %) ; 10 d'une minute, 1 de 4 minutes.
- Seuil 2 : inchangé, il passe.
- Seuil 3a : 0 quartier sans durée.
- Seuil 3b : levé pour la cause « vitesse » ; cause « pentes » à 0,22 % (CAF).
- Seuil 4 : trois verdicts confirmés.
- **Plus rien ne bloque.**

### Affichage

- Sur la page du quartier, un lieu atteint sans contrainte mais pas en 90 minutes en fauteuil roulant reçoit la mention : « Selon le calcul, non atteignable en fauteuil roulant en moins de 90 minutes (vitesse de 0,8 m/s, rues de plus de 8 % de pente évitées). »
- La formulation proposée (« notamment à cause des pentes ») a été adaptée, parce que la cause est parfois la vitesse seule.
- Deux paragraphes sont ajoutés à la Méthode : « Vitesse et pentes en fauteuil roulant » et « Lieux non atteints en fauteuil roulant ».
