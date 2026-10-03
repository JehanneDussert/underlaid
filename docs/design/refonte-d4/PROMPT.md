# Refonte du site : nouveau parcours et identité « D4 »

Lis d'abord `docs/design/refonte-d4/README.md`, puis toutes les images de `docs/design/refonte-d4/png/`. Elles sont la référence visuelle. Les fichiers `sources/*.dc.html` donnent les valeurs exactes (couleurs, tailles, textes, durées d'animation) : lis-les comme une spécification, ne les copie pas dans le site.

Travaille sur la branche `refonte`, avec la prévisualisation Vercel non indexée. Ne fusionne rien dans `main`. Avant d'écrire du code, propose-moi un plan par étapes (pages, composants, ordre, tests) et attends ma validation. Ensuite, des commits petits et lisibles, et à chaque étape une capture d'écran comparée à la maquette.

Les règles de ton de CLAUDE.md s'appliquent à tous les textes : sobre, journalistique, pas de « on », jamais « discrimination ». Mets à jour CLAUDE.md (section « Refonte du site ») avec les décisions ci-dessous, datées.

## 1. Parcours et pages

- **Accueil** : titre, une seule barre d'adresse, choix du mode **facultatif**, plan de réseau animé avec 6 destinations, bouton « Tous les lieux du quotidien », bandeau du bas, puis une question au hasard et le pied de page.
- **Votre quartier** (nouvelle page, URL partageable, remplace « Par adresse » et « Itinéraires ») : barre collante (adresse avec bouton × qui ramène à l'accueil, trois modes), fil d'Ariane, titre-résumé, puis trois parties : 1. Le cadre de vie de votre quartier ; 2. Ce qui est à portée ; 3. Les deux à la fois.
- **Explorer la carte** : panneau de gauche (adresse, « Que voulez-vous voir ? » avec 6 thèmes, encadré de filtres), carte, légende, fiche du quartier.
- **Méthode** et **À propos** : sommaire fixe à gauche, parties numérotées.
- **Pied de page partout** : Sources et méthode, Classement des communes, Citer et réutiliser, Presse, Contact. Le classement existant est gardé et restylé.
- **Supprimés** : la page Quiz (remplacée par la question au hasard), la matrice 3×3, la seconde barre de recherche.
- **Navigation** : le nom « underlaid » ramène à l'accueil ; l'entrée active du menu est en gras et soulignée ; « Votre quartier » est grisé dans le menu tant qu'aucune adresse n'est saisie.
- **À concevoir simplement, sans maquette** : la cible du bouton « Tous les lieux du quotidien » (liste des besoins et des lieux, qui invite à saisir une adresse), les pages Classement, Corrections, Accessibilité, 404, la version anglaise, Méthode et À propos sur téléphone. Reste dans le même style et montre-moi une capture avant de finaliser.

## 2. Identité

- **Police** : Atkinson Hyperlegible (400 et 700), auto-hébergée (pas d'appel à Google Fonts en production).
- **Couleurs** : texte #101010, texte secondaire #3C3C3C, gris #6A6A6A, bordures #D6D6D6 / #E2E2E2, bouton principal #0057B8, rose d'alerte #E4007C (le « quart le plus touché »). Lignes du plan : #0057B8, #E4007C, #00A06B, #FF7A00, #7B3FA0, #00A3E0.
- **Modes** : sans contrainte #00A06B (fond actif #E3F5EC), marche lente #FF7A00 (#FFEEDD), fauteuil roulant #0057B8 (#E2ECF8). Le bouton actif a un contour et un fond pâle de sa couleur, jamais de fond noir.
- **Thèmes de la carte**, une rampe en 5 classes chacun : cumul rose, chaleur orangé, air et bruit violet, logement vert, accès aux soins bleu ciel (#00A3E0), ressources jaune doré (#E0A800). Valeurs exactes dans `sources/ExplorerD4.dc.html`.
- **Formes** : boutons et champs en pilule, cartes à coins arrondis de 16 à 18 px, filets fins. Pastille « vous êtes ici » : cercle blanc à bord noir épais avec un point noir.

## 3. Comportements à respecter

- **Aucun mode par défaut**, nulle part. Sur l'accueil, sans mode choisi, le plan n'affiche aucune durée ; un clic sur un mode les fait apparaître, un second clic le désélectionne. Sur « Votre quartier » sans mode : tous les besoins sont dépliés et chaque lieu affiche les trois durées côte à côte avec leur rond de couleur, plus l'encadré « Aucun mode choisi ». « Comparer avec » n'apparaît qu'une fois un mode choisi.
- **Comparer** : tous les besoins se déplient ; chaque lieu montre la durée du mode choisi, celle de l'autre mode et l'écart en minutes (pastille grise jusqu'à 2 min, rose à partir de 3). Le rappel sur l'accès au réseau (arrêt accessible le plus proche) reste visible.
- **Ce qui est à portée** : accordéon en deux colonnes indépendantes ; chaque besoin fermé montre « le plus proche : X min ». Ordre et libellés : Se soigner, Faire ses démarches administratives, Se nourrir, Faire garder et scolariser ses enfants, Courrier et argent, Porter plainte, signaler, Voir du monde, Se rafraîchir. Le marché est abandonné. Lieux non encore calculés : étiquette « pas encore calculé ».
- **Barres** : barre avec le quart le plus touché en rose et légende « Sur 10 quartiers, N sont moins exposés que le vôtre » (arrondi du rang à la dizaine ; pour les soins : « … ont un accès aux soins plus facile que le vôtre »).
- **Titre de la page quartier** : généré à partir des données avec quelques modèles de phrases sobres. Propose-moi les modèles avant de les coder.
- **Filtres d'Explorer** : trois cases combinées en ET (très exposés = 2 thèmes sur 4 ou plus ; ressources dans le quart le plus faible ; accès aux soins dans le quart le plus difficile), nombre de quartiers retenus, lien « Définitions » vers la Méthode. Le bouton de la partie 3 de « Votre quartier » ouvre la carte avec les bonnes cases cochées.
- **Fiche du quartier sur ordinateur** : elle s'affiche du côté opposé au quartier sélectionné. Sur téléphone : panneau qui monte du bas, refermable, qu'on tire vers le haut pour le détail.
- **Carte** : style B, vrais contours IRIS, limites de communes à l'intérieur seulement, Paris souligné, Seine bordée de blanc, pas de fond gris ni de contour extérieur.

## 4. Animations

Belles mais discrètes, en CSS ou SVG uniquement (pas de bibliothèque lourde), en n'animant que `transform` et `opacity` (et `stroke-dashoffset` pour les lignes).
- **Plan de l'accueil** : chaque ligne se dessine en 2 s (ease-out), avec un décalage de 200 ms entre lignes ; les stations apparaissent ensuite avec un léger rebond (échelle 0 → 1,15 → 1, 400 ms) ; les étiquettes en fondu (500 ms).
- **Titre, sous-titre, formulaire** : montée de 12 px et fondu, 700 ms, décalés de 150 ms.
- **Changement de mode** : les durées changent en fondu croisé (≈ 250 ms), sans saut de mise en page.
- **Accordéons** : ouverture en 200 ms ; le chevron pivote.
- **Carte** : changement de thème en transition de couleur (300 ms) ; filtres en fondu d'opacité (250 ms).
- **Accueil → Votre quartier** : le plan zoome vers la pastille « vous êtes ici » (≈ 600 ms) puis la page du quartier apparaît.
- **Pastille qui pulse** : elle s'arrête après environ 5 secondes (trois battements), pour respecter le critère « mettre en pause, arrêter, masquer » (WCAG 2.2.2). Une seule pastille animée à la fois par écran, en plus du point du bandeau, qui suit la même règle.
- **`prefers-reduced-motion: reduce`** : aucune animation ; tout s'affiche directement dans son état final.

## 5. Accessibilité, au cœur du projet

Objectif : conformité **RGAA 4.1, niveau AA (WCAG 2.1 AA)**, vérifiée et documentée, avec une page « Accessibilité » qui contient la déclaration (état de conformité, résultats des tests, contact).
- **Structure** : `lang="fr"` (et `en` sur la version anglaise), un seul `h1` par page, titres dans l'ordre, repères (`header`, `nav`, `main`, `footer`), lien d'évitement « Aller au contenu », titre de page unique et explicite.
- **Clavier** : tout est utilisable au clavier, focus toujours visible (contour épais bleu), ordre logique. Le panneau du bas sur téléphone et les listes déroulantes se ferment avec Échap ; à l'ouverture d'un panneau, le focus y entre, puis revient au bouton d'origine. Au changement de page, le focus va au `h1`.
- **Composants** : boutons de mode avec `aria-pressed` ; accordéons avec `aria-expanded` et `aria-controls` ; cases de filtres en vraies cases à cocher ; saisie d'adresse en liste de suggestions conforme au motif « combobox » ARIA 1.2 ; nombre de quartiers filtrés et changements de mode annoncés dans une région `aria-live="polite"`.
- **Couleur** : jamais seule porteuse d'information (texte « Sur 10 quartiers… », légendes écrites, contour noir pour les quartiers filtrés). Contraste du texte ≥ 4,5:1 et des éléments d'interface ≥ 3:1 ; l'orangé et le jaune ne servent jamais de couleur de texte.
- **Carte** : une alternative textuelle complète, sous forme de liste ou de tableau des quartiers triable et filtrable avec les mêmes filtres, liée depuis la carte. Les quartiers de la carte ne doivent pas piéger le focus.
- **Zoom et adaptation** : lisible à 200 % et en reflow à 320 px de large sans défilement horizontal ; cibles tactiles d'au moins 44 × 44 px.
- **Tests automatisés en intégration continue** : `@axe-core/playwright` sur chaque page et chaque état important (mode choisi, comparaison, filtres, panneau ouvert), sur ordinateur et téléphone ; le build échoue en cas de violation sérieuse ou critique. Ajoute aussi un test de navigation au clavier par page (Playwright).
- **Tests manuels**, liste à tenir dans `docs/accessibilite.md` : NVDA + Firefox, VoiceOver sur macOS et iOS, TalkBack sur Android, navigation au clavier seul, zoom 200 % et 400 %, mode contraste élevé de Windows, animations réduites. Note les résultats datés.
- **Rapport** : à la fin de chaque étape, liste des critères RGAA vérifiés, résultats d'axe, et problèmes restants.

## 6. Contenus et données

- **Ne jamais inventer un chiffre.** Tout ce qui est entre crochets dans les maquettes doit venir des données, ou rester visiblement « à compléter ». Les chiffres provisoires portent la mention « données provisoires ».
- **Phrase de méthode sur les crèches** : celle notée dans CLAUDE.md, avec le décalage d'environ deux ans.
- **À vérifier dans le code, puis me rapporter avant publication** : la partie « Vos données » d'À propos (l'adresse est-elle conservée ? cookies ? mesure d'audience ?) et la 2e question du quiz (la part de 3,7 % / 30 % porte-t-elle sur le métro seul ? reformule-la exactement).
- **Méthode** : remplis les crochets (indicateurs et sources de la chaleur, de l'air et du bruit, du logement ; sources des médecins et pharmacies ; millésimes ; dates des hypothèses) à partir de CLAUDE.md et du code.
- **Licences et contact** : me demander les licences ; le contact passe par « Écrire à la porteuse du projet » sans afficher l'adresse en clair.
- **Hors périmètre de cette refonte** : le calcul des nouvelles destinations (prévu après la fin du calcul en cours) et le passage de la suroccupation au RP 2022. Prévois simplement l'affichage « pas encore calculé ».

Quand tu as lu tout cela et les maquettes, réponds-moi en langage clair avec ton plan, tes questions et ce qui te paraît impossible ou risqué.
