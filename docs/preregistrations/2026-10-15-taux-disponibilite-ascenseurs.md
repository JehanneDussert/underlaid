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
  - du 6 octobre à 6 h 28 au 8 octobre 2026 à 19 h 09 UTC, du 15 octobre à 16 h 59 UTC au 17 octobre à 21 h 00 UTC, puis à partir du 18 octobre (deux trous, tous deux dus à un arrêt du PC : note `docs/checks/2026-10-15-lift-archive-gaps.md`) ;
  - comptes de statuts pour l'ensemble du réseau à chaque relevé : 990 ascenseurs ; en journée, 874 à 892 signalés disponibles, 56 à 68 indisponibles, 44 à 48 inconnus ;
  - la nuit, entre environ 1 h et 6 h (heure de Paris), environ 270 ascenseurs de plus passent ensemble « indisponible » : c'est la fermeture du réseau ;
  - sur la plus longue période sans trou (du 6 octobre à 6 h 28 au 8 octobre à 3 h 15 UTC) : 124 débuts de panne en journée, et 46 % des pannes terminées dans la période ne durent qu'un relevé (environ une heure). Note `docs/checks/2026-10-15-lift-archive-gaps.md` et script `scripts/analysis/lift_archive_sampling.py` (PR #22) ;
  - relevé du 15 octobre à 17 h 59 UTC : 310 stations ; modes `RapidTransit` 483 ascenseurs, `LocalTrain` 251, `Metro` 152, `Tramway` 104 ; statuts 887 disponibles, 56 indisponibles, 47 inconnus.
- **Archive GitHub** (dépôt privé `underlaid-ascenseurs`) : rythme des relevés (32 relevés pour environ 175 programmés du 8 au 15 octobre ; 5 relevés pendant le trou local du 17 au 18 octobre), en-têtes et premières lignes de `changes.csv` et de `state.json`.
- Un enregistrement complet du flux (champs : `liftid`, `zdcid`, `zdcname`, `liftmode`, `liftsituation`, `liftstatus`, `liftstateupdate`, `liftreason`, `severity`, coordonnées).

## Données et période

- **Sources : deux archives indépendantes, toutes deux horaires** (décision du 18 octobre 2026) :
  - l'archive locale (conteneur `underlaid-elevators`, relevé toutes les heures, réponse complète du flux gardée à chaque changement, `log.csv` pour chaque tentative) ;
  - l'archive GitHub (dépôt `underlaid-ascenseurs`), lancée toutes les heures par un appel externe (cron-job.org, minute 47) en plus de la planification de GitHub (minute 17) ; chaque relevé réussi est inscrit dans `checks.csv`, et l'état de chaque ascenseur à ce relevé se reconstruit à partir de `changes.csv`.
- **Essai préalable** : les deux archives fonctionnent ensemble pendant au moins 48 heures avant le 31 octobre ; le nombre d'heures couvertes par chacune et par l'une ou l'autre est publié avec les résultats. Ces données d'essai ne servent qu'à vérifier le fonctionnement.
- **Période d'étude** : du lundi 2 novembre 2026 à 0 h au dimanche 13 décembre 2026 à 24 h (heure de Paris), six semaines entières, hors vacances scolaires de la zone C. Le mercredi 11 novembre (férié) est inclus et signalé.
- **Données antérieures au 2 novembre** (dont le trou du 8 au 15 octobre) : hors période. Elles servent seulement à écrire et tester le code ; aucun résultat calculé sur elles n'est publié ni utilisé pour choisir un paramètre. **Le trou du 8 octobre 19 h 09 UTC au 15 octobre 16 h 59 UTC n'a donc aucun effet sur les résultats.**

## Règles de calcul

- **Unité d'observation : l'heure.** Une heure (heure de Paris, de hh:00 à hh:59) est **couverte** si l'une des deux archives y a au moins un relevé réussi. Pour une heure couverte, l'état de chaque ascenseur est celui du premier relevé réussi de l'heure, pris dans l'archive locale s'il y en a un, sinon dans l'archive GitHub. Les taux se calculent sur les heures couvertes, jamais sur le nombre de relevés (une heure relevée deux fois compte une fois).
- **Contrôle de cohérence** : pour les heures couvertes par les deux archives, la part des ascenseurs dont le statut diffère entre les deux relevés est publiée ; au-delà de 1 %, la cause est recherchée et décrite avant toute publication des taux, sans changer les règles.
- **Heures de service** : les 17 heures qui commencent de 7 h à 23 h (heure de Paris), soit de 7 h 00 à 23 h 59. Les autres (fermeture nocturne, environ de 1 h à 6 h) sont ignorées.
- **Événement d'ensemble** : une heure où au moins 150 ascenseurs passent de « disponible » à « indisponible » par rapport à l'heure couverte précédente est signalée comme événement d'ensemble (fermeture, grève, panne du flux). Principal : heure exclue et listée. Sensibilité : heure gardée.
- **Statut « inconnu »** : jamais compté comme disponible ni comme indisponible. Au niveau de l'ascenseur, ses heures « inconnu » sont exclues du dénominateur et leur part est publiée. Un ascenseur dont plus de la moitié des heures de service couvertes sont « inconnu » n'a pas de taux ; il est listé.
- **Taux d'un ascenseur** = heures « disponible » / heures « disponible » ou « indisponible », sur les heures de service couvertes et retenues.
- **Taux d'une station** = part des heures de service couvertes où tous ses ascenseurs sont « disponible ». Une heure où l'un d'eux est « inconnu » est exclue pour cette station ; la part exclue est publiée.
- **Panne** : suite d'heures de service couvertes consécutives où l'ascenseur est « indisponible ». La fermeture nocturne ne coupe pas une panne (indisponible à la dernière heure avant la nuit et à la première après : même panne). Durée comptée en heures de service seulement.
- **Département** : selon la commune où se trouvent les coordonnées de la station (`zdcxepsg2154`, `zdcyepsg2154`).

## Trous dans la période d'étude

- **Heure sans aucun relevé** (ni dans l'une ni dans l'autre archive) : aucune valeur n'est comblée ni imputée ; l'heure est exclue des numérateurs et des dénominateurs de tous les taux.
- Chaque suite d'heures de service sans aucun relevé est listée (début, fin, nombre d'heures, cause si elle est connue), avec le total par semaine.
- **Pannes et trous** : si un ascenseur est « indisponible » juste avant et juste après une suite d'au plus 3 heures de service sans relevé, c'est la même panne, et sa durée compte ces heures. Au-delà de 3 heures, la panne est coupée en deux, chacune marquée « interrompue par un trou » ; leur durée est une borne basse, et la distribution des durées est publiée avec et sans elles.
- Si plus de 10 % des heures de service de la période ne sont pas couvertes, la période est prolongée semaine par semaine, au plus jusqu'au dimanche 3 janvier 2027, et la prolongation est publiée avec son motif.
- Le taux d'un ascenseur ou d'une station n'est publié que si ses heures couvertes représentent au moins 80 % des heures de service de la période.

## Résultats publiés

- Distribution des taux par ascenseur et par station (médiane, quartiles, part sous 90 % et sous 75 %) ; par mode et par département.
- Nombre de stations où au moins un ascenseur est signalé indisponible plus de 10 % des heures de service.
- Distribution des durées de panne ; part des pannes d'un seul relevé.
- Part des heures « inconnu », heures exclues (événements d'ensemble), heures sans aucun relevé ; heures couvertes par chaque archive et par l'une ou l'autre.

## Limites à publier

- Le flux donne l'état **signalé** par Île-de-France Mobilités à partir des tournées des agents RATP et SNCF (`liftstateupdate`), pas l'état physique en continu : une panne peut être signalée en retard, une remise en service aussi.
- Une panne de moins d'une heure peut échapper au relevé horaire.
- Le taux d'une station ne dit pas quel ascenseur est nécessaire pour quel trajet : un ascenseur en panne n'empêche pas toujours le passage.
- Les taux ne sont pas reliés aux durées de trajet publiées ; la simulation d'une durée habituelle et d'une durée défavorable fera l'objet d'un pré-enregistrement séparé.
