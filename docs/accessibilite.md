# Accessibilité — tests

Objectif : RGAA 4.1, niveau AA (WCAG 2.1 AA). Tant que les tests manuels ci-dessous ne sont pas faits et datés, la déclaration d'accessibilité du site indique « **partiellement conforme** » (décision du 3 octobre 2026).

## Tests automatiques

Ils sont lancés à chaque push sur la branche `refonte` (workflow `.github/workflows/frontend-checks.yml`) et à la main :

```
cd frontend
npm run build
npm run test:a11y    # axe-core et clavier
npm run test:smoke   # parcours complet, sans erreur console
```

- **axe-core** (règles WCAG 2.0/2.1 A et AA) sur chaque page, en français et en anglais, à largeur d'ordinateur (1280 px) et de téléphone (390 px). Le test échoue en cas de violation « grave » ou « critique ». Les violations « modérées » ou « mineures » sont listées.
- **Clavier** :
  - le lien d'évitement est le premier arrêt ;
  - chaque arrêt de l'en-tête a un contour de focus visible ;
  - après un changement de page, le focus est sur le titre `h1` ;
  - le menu téléphone s'ouvre avec Entrée et se ferme avec Échap, et le focus revient alors au bouton.
- **Redistribution** : aucun défilement horizontal à 320 px de large.

Ces tests automatiques ne détectent qu'une partie des problèmes, à peu près le tiers à la moitié des critères. Ils ne remplacent pas les tests manuels.

## Tests manuels (à faire par une personne, sur le site prévisualisé)

À chaque test, noter la date, la personne, l'appareil, la version du navigateur et du lecteur d'écran, et les problèmes trouvés.

| Test | Pages | Date | Résultat |
|---|---|---|---|
| NVDA + Firefox (Windows) | toutes | — | à faire |
| VoiceOver + Safari (macOS) | toutes | — | à faire |
| VoiceOver + Safari (iOS, vrai téléphone) | toutes | — | à faire |
| TalkBack + Chrome (Android, vrai téléphone) | toutes | — | à faire |
| Clavier seul, sans souris (parcours complet : adresse → quartier → carte → méthode) | toutes | — | à faire |
| Zoom du navigateur à 200 % puis 400 % | toutes | — | à faire |
| Contraste élevé de Windows | toutes | — | à faire |
| Animations réduites (réglage du système) | accueil, quartier, carte | — | à faire |

Points à vérifier en particulier :
- chaque page annonce son titre à l'arrivée ;
- les boutons de mode annoncent leur état (« enfoncé ») et le mode choisi est annoncé ;
- les accordéons annoncent « développé » ou « réduit » ;
- la carte a une alternative textuelle complète (liste des quartiers triable et filtrable) ;
- les filtres annoncent le nombre de quartiers retenus ;
- aucune information n'est donnée par la seule couleur.

## Choix faits pour l'accessibilité (identité D4)

- Police **Atkinson Hyperlegible** (Braille Institute), conçue pour les personnes malvoyantes.
- Contrastes calculés sur fond blanc :
  - texte #101010 : 19,0:1 ;
  - texte secondaire #3C3C3C : 11,0:1 ;
  - gris #6A6A6A : 5,4:1 ;
  - bleu #0057B8 : 6,9:1 ;
  - rose #E4007C : 4,6:1, jamais en texte sur fond rose pâle (4,0:1).
- Contours des champs et des boutons non sélectionnés : #8A8A8A (3,5:1, critère 1.4.11). Les filets #D6D6D6 et #E2E2E2 ne servent qu'à la décoration.
- **Mode actif** : couleur du mode, plus une coche et un texte en gras. Les contours orangé et vert seuls sont sous 3:1 sur leur fond pâle.
- Orangé et jaune jamais en texte.
- **Rampes de la carte** : premier cran légèrement foncé pour rester visible sur fond blanc. La valeur est toujours donnée aussi en texte (légende, fiche, liste).
- **Animations** : uniquement `transform`, `opacity` et `stroke-dashoffset`. Aucune animation avec « animations réduites ». La pastille qui pulse s'arrête après trois battements (critère 2.2.2).
- **Passage de l'accueil au quartier** : sur ordinateur, le plan zoome vers « vous êtes ici » en 600 ms avant le changement de page. Pas d'attente ni de zoom avec « animations réduites » ou sur téléphone.
- **Tableaux qui défilent** (méthode, lieux du quotidien) : la zone de défilement reçoit le focus et porte un nom (« Tableau (faites défiler horizontalement si besoin) »), pour être parcourue au clavier.

## Journal des contrôles automatiques

| Date | Résultat |
|---|---|
| 04/10/2026 | axe-core : aucune violation grave ou critique (toutes pages, FR/EN, ordinateur et téléphone) ; clavier OK ; parcours complet 60/60 ; redistribution OK (9 tailles d'écran). Un tableau défilant de la méthode détaillée n'était pas accessible au clavier sur téléphone : corrigé. |
