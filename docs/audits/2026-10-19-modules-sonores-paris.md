# Audit : traversées sonorisées pour les personnes aveugles et malvoyantes à Paris

Note du 19 octobre 2026. **Audit de sources seulement** : aucun indicateur, aucune couche sur le site, aucun croisement avec un autre indicateur. Objectif envisagé : une couche d'information pour Paris seulement (part des traversées à feux sonorisées autour du quartier), **pas avant la réponse de la Ville de Paris** sur la mise à jour du fichier (partie 4).

Script : `scripts/analysis/sound_modules_paris.py` (image Docker du projet), sur les deux jeux téléchargés le 19 octobre 2026.

## 1. Sources

| Jeu | Éditeur | Licence | Mise à jour | Contenu |
|---|---|---|---|---|
| « Modules sonores passages piétons » (opendata.paris.fr, `modules-sonores-passages-pietons` ; copie sur data.gouv.fr) | Ville de Paris, Direction de la Voirie et des Déplacements | ODbL | 1er octobre 2026 | 10 431 modules équipant la signalisation lumineuse tricolore pour les personnes aveugles ou malvoyantes (extraction de la base EVESA) : code de l'ouvrage, date de pose, secteur, carrefour, position |
| « Signalisation lumineuse tricolore » (`signalisation-tricolore`) | Ville de Paris | ODbL | 1er octobre 2026 | 139 336 lampes de feux, rattachées à 27 510 « ouvrages » ; type de lampe, dont 42 673 têtes de feux piétons (« Caisson Piéton ») |

La clé commune est le code de l'ouvrage. **Un ouvrage correspond très probablement à une traversée à feux** : il est situé en un seul point, et 86 % des ouvrages qui ont des feux piétons en ont exactement deux têtes (une de chaque côté). À faire confirmer par la Ville de Paris. Chaque module est rattaché à un ouvrage différent.

## 2. Premiers chiffres (descriptifs)

- **19 673 traversées à feux** (ouvrages avec au moins une tête de feu piéton), dont **10 412 avec un module sonore, soit 52,9 %** (19 autres modules sont rattachés à des ouvrages sans feu piéton).
- Par arrondissement, de 36,4 % (17e) et 37,8 % (16e) à 73,0 % (4e) et 75,6 % (6e).
- Par quartier (900 quartiers parisiens avec au moins 5 traversées à feux) : médiane 60 %, de 25 % (10e centile) à 92 % (90e centile) ; quelques quartiers à 0 % et à 100 %.

## 3. Écarts avec ce qu'annonce la Ville

- **Taux** : un article de Handicap.fr (17 juillet 2024) cite 12 900 feux piétons équipés d'un module sonore sur 20 700, soit **60 %** ; le fichier donne **52,9 %** (10 412 sur 19 673). Aucune source officielle de la Ville confirmant le chiffre de 2024 et son périmètre n'a été trouvée.
- **Nombre de modules** : 12 900 annoncés contre 10 431 dans le fichier, soit environ 2 470 de moins ; un article d'À Nous Paris (5 mars 2024) annonçait « l'ajout de 2 500 nouveaux modules sonores d'ici les Jeux Olympiques et Paralympiques » (source primaire non citée).
- **Dénominateur** : 20 700 « feux piétons » annoncés contre 19 673 traversées à feux dans le fichier ; les deux ne mesurent peut-être pas la même chose (feux, traversées, carrefours).
- **Dates de pose** : la quasi-totalité des modules du fichier a été posée de 2015 à 2019 (2 068 en 2016, 2 923 en 2017, 2 834 en 2018, 1 541 en 2019) ; 186 en 2020, 81 en 2021, **aucun après 2021**, et 43 sans date. Soit le programme s'est arrêté en 2021, ce qui contredit l'annonce de 2024, soit **le fichier n'enregistre plus les poses récentes**.

L'hypothèse la plus simple, à confirmer, est que le fichier ne contient pas les poses postérieures à 2021, dont celles de 2024 : la part réelle serait alors plus élevée que 52,9 % et la répartition par quartier différente.

## 4. Question à la Ville de Paris avant toute couche

1. Le fichier « Modules sonores passages piétons » contient-il toutes les poses, y compris celles de 2022 à 2026, notamment les 2 500 modules annoncés en 2024 avant les Jeux ?
2. Un « ouvrage » du jeu « Signalisation lumineuse tricolore » correspond-il à une traversée piétonne à feux ?
3. Quel est le périmètre du chiffre de 60 % (12 900 sur 20 700) cité en 2024 ?

## 5. Limites, quelle que soit la réponse

- Seules les traversées **à feux** sont concernées ; les passages piétons sans feux ne figurent dans aucun des deux jeux.
- Un module posé n'est pas un module qui fonctionne, et il ne s'entend qu'avec la télécommande, distribuée gratuitement par la Ville.
- Ces jeux ne disent rien des bandes d'éveil de vigilance ni des annonces sonores dans les stations et les véhicules.
- **Paris seulement** : aucune source équivalente n'a été cherchée pour la petite couronne ; une éventuelle couche porterait la même mention que les toilettes publiques (donnée absente hors de Paris, pas équipement absent).

## Sources

- Ville de Paris, « Modules sonores passages piétons » : https://opendata.paris.fr/explore/dataset/modules-sonores-passages-pietons/ (copie : https://www.data.gouv.fr/datasets/modules-sonores-passages-pietons)
- Ville de Paris, « Signalisation lumineuse tricolore » : https://opendata.paris.fr/explore/dataset/signalisation-tricolore/
- Handicap.fr, « Aveugle : Paris, télécommande gratuite pour les feux sonores » (17 juillet 2024) : https://informations.handicap.fr/a-aveugle-paris-telecommande-gratuite-pour-les-feux-sonores-37013.php
- À Nous Paris, « Paris Innovant : Télécommandes Sonores pour l'Autonomie des Malvoyants » (5 mars 2024) : https://anousparis.fr/immobilier-paris/paris-telecommandes-sonores-malvoyants-35525
- Ville de Paris, MDPH, « Télécommande gratuite pour les feux sonores » : https://handicap.paris.fr/telecommande-gratuite-pour-les-feux-sonores/
