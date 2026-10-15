# Pré-enregistrement — taux de disponibilité des ascenseurs (analyse descriptive)

**Brouillon du 15 octobre 2026, à relire par la porteuse du projet.** Il ne vaut pré-enregistrement qu'une fois sa version finale commitée, avant le début de la période d'étude (2 novembre 2026) et avant tout calcul de taux. Analyse **descriptive, sans hypothèse ni verdict**. Aucun croisement avec les ressources des habitants : s'il est envisagé, il sera pré-enregistré à part.

Source : Île-de-France Mobilités, « État des ascenseurs » (API PRIM), Licence Mobilités. Mention obligatoire sur tout résultat : « Contient des informations de État des ascenseurs, disponible sous la Licence Mobilités ».

## Questions

1. Pour chaque ascenseur, quelle part du temps de service est-il signalé disponible ?
2. Pour chaque station ou gare (`zdcid`), quelle part du temps de service tous ses ascenseurs sont-ils signalés disponibles en même temps ?
3. Combien de pannes signalées, et de quelle durée ?
4. Comment ces taux se répartissent-ils par mode (`liftmode`) et par département (stations de Paris, Hauts-de-Seine, Seine-Saint-Denis et Val-de-Marne ; les autres stations d'Île-de-France sont décrites à part) ?

## Ce qui a déjà été vu des données (transparence)

Avant l'écriture de ce brouillon, les données suivantes ont été examinées. Aucun taux par ascenseur, par station, par mode ni par département n'a été calculé.

- **Archive locale** (relevé horaire, `data/raw/elevators/`) :
  - du 6 octobre à 6 h 28 au 8 octobre 2026 à 19 h 09 UTC, puis à partir du 15 octobre à 16 h 59 UTC ;
  - comptes de statuts pour l'ensemble du réseau à chaque relevé : 990 ascenseurs ; en journée, 874 à 892 signalés disponibles, 56 à 68 indisponibles, 44 à 48 inconnus ;
  - la nuit, entre environ 1 h et 6 h (heure de Paris), environ 270 ascenseurs de plus passent ensemble « indisponible » : c'est la fermeture du réseau ;
  - sur la plus longue période sans trou (du 6 octobre à 6 h 28 au 8 octobre à 3 h 15 UTC) : 124 débuts de panne en journée, et 46 % des pannes terminées dans la période ne durent qu'un relevé (environ une heure). Note `docs/checks/2026-10-15-lift-archive-gaps.md` et script `scripts/analysis/lift_archive_sampling.py` (PR #22) ;
  - relevé du 15 octobre à 17 h 59 UTC : 310 stations ; modes `RapidTransit` 483 ascenseurs, `LocalTrain` 251, `Metro` 152, `Tramway` 104 ; statuts 887 disponibles, 56 indisponibles, 47 inconnus.
- **Archive GitHub** (dépôt privé `underlaid-ascenseurs`) : rythme des relevés (32 relevés pour environ 175 programmés du 8 au 15 octobre), en-têtes et premières lignes de `changes.csv` et de `state.json`.
- Un enregistrement complet du flux (champs : `liftid`, `zdcid`, `zdcname`, `liftmode`, `liftsituation`, `liftstatus`, `liftstateupdate`, `liftreason`, `severity`, coordonnées).

## Données et période

- **Source** : l'archive locale seulement (relevé toutes les heures, conteneur `underlaid-elevators`). L'archive GitHub n'est pas utilisée pour les taux : elle ne relève qu'environ une heure sur cinq et ne capte qu'environ 35 à 55 % des pannes de journée (PR #22).
- **Période d'étude** : du lundi 2 novembre 2026 à 0 h au dimanche 13 décembre 2026 à 24 h (heure de Paris), six semaines entières, hors vacances scolaires de la zone C. Le mercredi 11 novembre (férié) est inclus et signalé.
- **Données antérieures au 2 novembre** (dont le trou du 8 au 15 octobre) : hors période. Elles servent seulement à écrire et tester le code ; aucun résultat calculé sur elles n'est publié ni utilisé pour choisir un paramètre. **Le trou du 8 octobre 19 h 09 UTC au 15 octobre 16 h 59 UTC n'a donc aucun effet sur les résultats.**

## Règles de calcul

- **Heures de service** : relevés dont l'heure de Paris est entre 6 h 30 et 0 h 30. Les autres (fermeture nocturne) sont ignorés.
- **Événement d'ensemble** : un relevé où au moins 150 ascenseurs passent de « disponible » à « indisponible » par rapport au relevé précédent est signalé comme événement d'ensemble (fermeture, grève, panne du flux). Principal : relevé exclu et listé. Sensibilité : relevé gardé.
- **Statut « inconnu »** : jamais compté comme disponible ni comme indisponible. Au niveau de l'ascenseur, ses relevés « inconnu » sont exclus du dénominateur et leur part est publiée. Un ascenseur dont plus de la moitié des relevés de service sont « inconnu » n'a pas de taux ; il est listé.
- **Taux d'un ascenseur** = relevés « disponible » / relevés « disponible » ou « indisponible », sur les heures de service retenues.
- **Taux d'une station** = part des relevés de service où tous ses ascenseurs sont « disponible ». Un relevé où l'un d'eux est « inconnu » est exclu pour cette station ; la part exclue est publiée.
- **Panne** : suite de relevés de service consécutifs où l'ascenseur est « indisponible ». La fermeture nocturne ne coupe pas une panne (indisponible au dernier relevé avant la nuit et au premier après : même panne). Durée comptée en heures de service seulement.
- **Département** : selon la commune où se trouvent les coordonnées de la station (`zdcxepsg2154`, `zdcyepsg2154`).

## Trous dans la période d'étude

- Aucune valeur n'est comblée ni imputée.
- Chaque intervalle de plus de 90 minutes sans relevé réussi est listé (`gaps.csv`), avec sa durée totale en heures de service.
- Si plus de 10 % des relevés horaires attendus en heures de service manquent sur la période, la période est prolongée semaine par semaine, au plus jusqu'au dimanche 3 janvier 2027, et la prolongation est publiée avec son motif.
- Le taux d'un ascenseur ou d'une station n'est publié que si ses relevés couvrent au moins 80 % des heures de service de la période.

## Résultats publiés

- Distribution des taux par ascenseur et par station (médiane, quartiles, part sous 90 % et sous 75 %) ; par mode et par département.
- Nombre de stations où au moins un ascenseur est signalé indisponible plus de 10 % des heures de service.
- Distribution des durées de panne ; part des pannes d'un seul relevé.
- Part des relevés « inconnu », relevés exclus (événements d'ensemble), trous.

## Limites à publier

- Le flux donne l'état **signalé** par Île-de-France Mobilités à partir des tournées des agents RATP et SNCF (`liftstateupdate`), pas l'état physique en continu : une panne peut être signalée en retard, une remise en service aussi.
- Une panne de moins d'une heure peut échapper au relevé horaire.
- Le taux d'une station ne dit pas quel ascenseur est nécessaire pour quel trajet : un ascenseur en panne n'empêche pas toujours le passage.
- Les taux ne sont pas reliés aux durées de trajet publiées ; la simulation d'une durée habituelle et d'une durée défavorable fera l'objet d'un pré-enregistrement séparé.
