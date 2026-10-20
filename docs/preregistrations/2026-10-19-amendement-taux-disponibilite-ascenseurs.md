# Amendement au pré-enregistrement « taux de disponibilité des ascenseurs »

Rédigé le 19 octobre 2026. Il complète le pré-enregistrement `2026-10-15-taux-disponibilite-ascenseurs.md`, fusionné le 19 octobre 2026 à 10 h 55 UTC (commit `db0ef9e`, PR #24), **sans le remplacer** : les règles de ce texte restent valables, sauf là où cet amendement les précise. Il est enregistré dans le dépôt **avant le début de la période d'étude (2 novembre 2026) et avant tout calcul de taux** ; la date qui fait foi est celle du commit de fusion de sa PR. La copie horodatée déposée hors du dépôt (OSF ou Zenodo) porte sur le pré-enregistrement ainsi amendé.

## 1. Ce que mesure l'archive

- **Formulation** : la mesure est l'état **« hors service » signalé dans le flux d'Île-de-France Mobilités (alimenté en continu par la RATP et Gare & Connexions, publié toutes les 15 minutes)**. Ce n'est pas l'état physique de l'ascenseur à chaque instant. Cette formulation remplace « état signalé par Île-de-France Mobilités à partir des tournées des agents RATP et SNCF » dans les limites du pré-enregistrement.
- **Source de la fréquence** : documentation d'Île-de-France Mobilités « Données état des ascenseurs » (septembre 2026) : données « transmises à Île-de-France Mobilités en continu », jeu « mis à jour toutes les 15 min ». La fiche du jeu sur le portail d'IDFM et sur data.gouv.fr indique encore « collectées et publiées 3 fois par jour » ; l'archive (partie 3) confirme la documentation.
- **Gares SNCF** : pour les ascenseurs des trains SNCF (`LocalTrain`) et une partie des gares RER, les dates de mise à jour se concentrent vers 5-6 h, 11 h, 15 h et 20 h, alors que les changements de statut se répartissent sur toute la journée : l'état y est en partie confirmé lors des tours de gare. Un changement survenu entre deux tours peut n'apparaître qu'au tour suivant. Phrase à publier avec les résultats : « Pour les gares SNCF, l'état de l'ascenseur est en partie confirmé lors des tours de gare ; un ascenseur tombé en panne entre deux tours peut n'être signalé qu'au tour suivant. »

## 2. Fréquence des relevés

- **Archive locale** : un relevé **toutes les 15 minutes**, calé sur les quarts d'heure UTC (minutes 0, 15, 30 et 45), depuis le 19 octobre 2026 vers 19 h 10 UTC (toutes les heures auparavant).
- **Archive GitHub** : inchangée, horaire (appel externe à la minute 32, planification de GitHub aux minutes 17 et 47), en secours.
- **Unité d'observation : inchangée**, l'heure. Une heure est couverte si l'une des deux archives y a au moins un relevé réussi ; l'état d'un ascenseur pour une heure couverte est celui du premier relevé réussi de l'heure, pris dans l'archive locale s'il y en a un, sinon dans l'archive GitHub. Les taux principaux se calculent comme prévu.
- **Ajouts permis par la nouvelle fréquence** (fixés ici, avant tout calcul) :
  - **Durée des pannes** : mesurée au quart d'heure à partir de tous les relevés de l'archive locale ; les heures sans relevé local mais couvertes par l'archive GitHub comptent à l'heure. La règle de continuité à travers les trous (au plus 3 heures de service sans relevé) est inchangée.
  - **Sensibilité** : taux de disponibilité calculé sur tous les relevés locaux de service (part des relevés « disponible » parmi les relevés « disponible » ou « indisponible »), publié à côté du taux principal.
- **Trous** : `gaps.csv` garde son seuil de 90 minutes sans relevé réussi ; le watchdog local alerte après une heure sans relevé (quatre relevés manqués).

## 3. Ce qui a déjà été regardé dans l'archive (transparence)

En plus de ce que liste le pré-enregistrement du 15 octobre, une **analyse de fréquence** a été faite le 19 octobre 2026, **sans aucun calcul de taux** (ni par ascenseur, ni par station, ni par mode, ni par département) : script `scripts/analysis/lift_update_frequency.py`, sur les 127 relevés horaires réussis de l'archive locale du 6 octobre à 6 h 28 au 19 octobre à 18 h 58 UTC. Résultats :

- changements de statut entre deux relevés consécutifs, entre 7 h et 23 h (heure de Paris) : 4 à 12 en moyenne par relevé pour l'ensemble du réseau ; à l'ouverture et à la fermeture du réseau (de 0 h à 6 h), jusqu'à 178 ;
- dates de mise à jour attachées par la source à chaque état : sur une journée complète, 1 150 à 1 200 mises à jour d'ascenseur, à 444-480 heures différentes ; pics à 4-5 h et 0-1 h, et à 11 h, 15 h et 20 h ;
- par mode, les dates de mise à jour se concentrent vers 5-6 h, 11 h, 15 h et 20 h pour les trains SNCF, et en continu, avec des pics à l'ouverture et à la fermeture du réseau, pour le métro et le tram ;
- part des changements de statut de 7 h à 23 h vus aux relevés qui suivent 11 h, 15 h et 20 h (35 % si la répartition était uniforme) : métro 39 %, RER 30 %, trains SNCF 41 %, tram 38 % ;
- 71 % des changements de statut vus par un relevé portent une date de mise à jour comprise entre ce relevé et le précédent ; délai médian entre cette date et le relevé : 53 minutes.

## 4. Limites (précisions)

- Une panne qui ne dure qu'un relevé horaire dure **au plus une heure** (et non « environ une heure ») ; à partir du 19 octobre, la résolution est le quart d'heure pour l'archive locale.
- La phrase « Le flux donne l'état signalé par Île-de-France Mobilités à partir des tournées des agents RATP et SNCF » est remplacée par la formulation de la partie 1 et par la phrase sur les gares SNCF.
