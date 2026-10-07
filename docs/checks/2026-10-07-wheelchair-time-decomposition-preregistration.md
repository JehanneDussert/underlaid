# Pré-enregistrement — décomposition des durées en fauteuil roulant (analyse descriptive)

Écrit le 7 octobre 2026 à 7 h 28, **avant tout calcul de cette analyse**. Accord de la porteuse du projet donné le même jour. Analyse **descriptive, sans hypothèse ni verdict**. Elle ne modifie aucune durée publiée.

## Questions

1. Pour chaque mode (sans contrainte, marche lente, fauteuil roulant), quelle part des trajets quartier × lieu utilise les transports en commun, et quelle part se fait entièrement à pied ?
2. En fauteuil roulant, comment se décompose le temps en plus par rapport au trajet sans contrainte :
   - la part due à la vitesse (0,8 m/s) et aux pentes (rues de plus de 8 % évitées) ;
   - la part due aux arrêts et stations inaccessibles ?

## Ce qui est déjà connu à l'écriture (transparence)

- Les durées publiées du second calcul : médianes par lieu et par département, quartiers « plus de 90 min », îlots.
- La sensibilité sans retrait des pentes, pour 18 quartiers.
- **Rien n'a été calculé** sur la part de trajets à pied ni sur la décomposition.

## Calculs supplémentaires

Mêmes carreaux d'origine, mêmes points d'arrivée (script 42), même jour (mardi 13 octobre 2026, départ entre 10 h et 11 h), temps maximal de 90 minutes, médiane de R5, comme le second calcul. Lieux clés et lieux du quotidien (les toilettes et fontaines de Paris ne sont pas incluses).

| Tâche | Réseau de rues | Transports | Vitesse |
|---|---|---|---|
| `standard_places_walk` | complet | aucun (marche seule) | 4,5 km/h |
| `slow_places_walk` | complet | aucun | 3,4 km/h |
| `step_free_no_places_walk` | sans escaliers ni pentes > 8 % | aucun | 0,8 m/s |
| `wc_allstops_tue10` | sans escaliers ni pentes > 8 % | **tous** les arrêts et courses (GTFS complet) | 0,8 m/s |

Les tâches publiées réutilisées sont `standard_tue10`, `slow_tue10` et `step_free_no_tue10` (variante principale, inconnu = non accessible).

## Indicateurs (calculés au carreau, puis rapportés comme dans le site)

1. **Trajet entièrement à pied** : un couple carreau × lieu est « à pied » si la durée combinée (marche et transports) est égale à la durée en marche seule, au même rythme, et « avec transports » si elle est plus courte. Part pondérée par la population, par mode, par lieu et par département.
2. **Décomposition**, par couple carreau × lieu atteint dans les trois calculs :
   - écart total = fauteuil roulant publié − sans contrainte ;
   - **vitesse et pentes** = `wc_allstops` − sans contrainte (même vitesse et mêmes rues que le fauteuil roulant, mais tous les arrêts) ;
   - **arrêts inaccessibles** = fauteuil roulant publié − `wc_allstops`.

   Les deux parts s'additionnent exactement à l'écart total. Rapportés : médiane et moyenne de chaque part, par lieu et par département, pondérées par la population ; part des couples où chaque composante est nulle.
   - Repère complémentaire : marche seule à 0,8 m/s sur le réseau sans pentes − marche seule à 4,5 km/h sur le réseau complet (effet de la vitesse et des pentes sans transports).
   - Couples non atteints en 90 minutes dans l'un des calculs : comptés à part, jamais traités comme 0 ou comme 90.

## Limites, écrites d'avance

- L'ordre de la décomposition est un choix : la vitesse et les pentes d'abord, les arrêts ensuite. Avec l'autre ordre, les parts peuvent différer ; ce n'est pas calculé ici.
- Une seule variante (inconnu = non accessible) ; un seul créneau (mardi 10 h).
- La durée combinée de R5 est une médiane sur une heure de départs : « à pied » veut dire que la marche seule est au moins aussi rapide que la médiane des départs.

## Statut

Analyse descriptive : aucun verdict, aucun changement des durées publiées, aucune nouvelle règle. Les résultats seront rapportés à la porteuse du projet, qui décidera s'ils sont publiés (Méthode) et sous quelle forme.

## Calcul

Après la fusion de la PR n° 7 (fait le 7 octobre 2026), la nuit (à partir de 22 h), 3 processus. Durée estimée : 7 à 9 h. Scripts figés dans une copie dédiée, pour ne pas dépendre des branches de travail.
