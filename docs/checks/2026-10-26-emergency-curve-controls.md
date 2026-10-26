# Courbe des urgences : contrôles avant publication (26 octobre 2026)

Calcul pré-enregistré dans `docs/preregistrations/2026-10-22-courbe-urgences-heure-depart.md` (PR #38 et #39), lancé le 25 octobre 2026 à 13 h 24 UTC et terminé le 26 octobre 2026 à 15 h 18 UTC (1 242 lots, tous relus sans erreur). Les contrôles de la partie 5 ont été lancés automatiquement à la fin du calcul (`scripts/analysis/curve_controls.py`). Sortie complète : `2026-10-26-emergency-curve-controls.txt`, dans ce dossier.

## Résultats des contrôles

1. **Créneau de 10 h : OK.** Aucun des 2 737 quartiers qui ont au moins un carreau habité de 50 habitants ou plus n'a une durée différente des durées publiées, ni sans contrainte, ni en fauteuil roulant (seuil : 1 %).
2. **Inversions** : la durée en fauteuil roulant ressort plus courte que la durée sans contrainte dans 83 couples carreau × heure sur 158 729 (0,052 %).
3. **Complétude** : la part de la population à plus de 90 minutes est au plus de 0,1 % sans contrainte, à toute heure. En fauteuil roulant, elle est de 0,4 à 0,6 % le jour, et de 3,3 %, 6,6 % et 0,7 % à 0 h, 2 h et 4 h (hypothèse « inconnu = non accessible »).
4. **Cohérence avec les créneaux publiés** : la valeur publiée à 1 h se trouve entre les valeurs de la courbe à 0 h et 2 h pour 97,5 % des quartiers sans contrainte, et pour 96,5 % et 93,9 % en fauteuil roulant (selon l'hypothèse). La valeur publiée à 21 h se trouve entre celles de 20 h et 22 h pour 91,5 % des quartiers sans contrainte, mais seulement pour **81,1 % en fauteuil roulant** (voir ci-dessous).
5. **Sensibilité de nuit** (fauteuil roulant, « inconnu = accessible » au lieu de « inconnu = non accessible ») : la médiane des quartiers change d'une minute au plus ; le nombre de quartiers à plus de 90 minutes passe de 80 à 71 à 0 h, de 167 à 134 à 2 h et de 16 à 8 à 4 h ; corrélation de rang entre les deux hypothèses de 0,985 à 0,993.

Sur les 2 690 quartiers habités du site (au moins 50 habitants), le tableau de la Méthode (script 46) donne les mêmes fourchettes de nuit : 71 à 80, 134 à 167 et 8 à 16 quartiers à plus de 90 minutes.

## Pourquoi 19 % des quartiers sont hors de l'intervalle à 21 h en fauteuil roulant

**Ce n'est pas une différence de version des horaires, de date ni de réglages.** Le créneau de 21 h publié vient du second calcul (7 octobre 2026), avec les mêmes horaires (GTFS IDFM du 1er octobre 2026), le même jour (mardi 13 octobre 2026), les mêmes réseaux et le même code que la courbe. Vérification faite le 26 octobre 2026 (`scripts/analysis/curve_check_21h.py`) : 300 carreaux tirés au hasard parmi ceux dont la durée publiée à 21 h est hors de l'intervalle ont été recalculés à 21 h avec le code de la courbe. **Pour les 300, la durée recalculée est identique à la durée publiée.** Le créneau de 10 h, recalculé de la même façon pour tous les quartiers, est lui aussi identique (contrôle 1).

**L'explication est l'heure de départ elle-même.** Chaque durée est la médiane des durées pour des départs répartis sur une fenêtre de 60 minutes : 20 h-21 h, 21 h-22 h et 22 h-23 h. Ces trois fenêtres ne se recouvrent pas. La durée de 21 h n'est donc pas une moyenne des deux autres : elle dépend des passages qui tombent entre 21 h et 22 h. En soirée, les bus passent moins souvent et l'attente compte davantage, et une course de plus ou de moins dans une fenêtre déplace la médiane d'une minute ou deux. Le fauteuil roulant y est plus sensible, puisqu'il ne peut prendre qu'une partie des courses (arrêts et véhicules signalés accessibles). Les chiffres le confirment (`scripts/analysis/curve_21h_gaps.py`) :

- **Les écarts sont petits** : en fauteuil roulant, sur 524 quartiers hors de l'intervalle, l'écart avec la borne la plus proche est d'une minute pour 381 quartiers et de deux minutes pour 105 ; il ne dépasse 3 minutes que pour 12 quartiers (au plus 7 minutes). Sans contrainte, 212 écarts sur 235 sont d'une minute.
- **Ils vont dans les deux sens** : en fauteuil roulant, 374 quartiers sont en dessous de l'intervalle et 150 au-dessus ; sans contrainte, 171 et 64.
- **En moyenne, 21 h se place bien entre 20 h et 22 h** : sur les carreaux, 32,5 / 33,5 / 34,7 minutes en fauteuil roulant et 22,1 / 22,8 / 23,6 minutes sans contrainte à 20 h, 21 h et 22 h.
- **L'arrondi à la minute joue aussi** : les valeurs des quartiers sont des médianes arrondies, et la courbe est souvent plate le soir ; une différence d'une minute suffit alors à sortir de l'intervalle.

Conformément au pré-enregistrement, ces écarts sont décrits sans correction. Les valeurs déjà publiées à 21 h (soir) restent publiées telles quelles ; la courbe ne les remplace pas.
