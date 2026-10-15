# Archive des ascenseurs — trous et limites (note du 15 octobre 2026)

Note factuelle, écrite pour la Méthode et pour le futur pré-enregistrement du taux de disponibilité des ascenseurs. Aucun taux de disponibilité n'a été calculé. Source : Île-de-France Mobilités, « État des ascenseurs » (Licence Mobilités).

## Deux archives

- **Archive locale** : le conteneur `underlaid-elevators` interroge le flux toutes les heures (`data/raw/elevators/`, non versionné ; journal `log.csv`, trous de plus de 90 minutes dans `gaps.csv`, réponses vides dans `empty_responses.csv`). Elle tourne depuis le 6 octobre 2026.
- **Archive GitHub** : dépôt privé `underlaid-ascenseurs`, GitHub Actions programmé toutes les heures (`cron: "17 * * * *"`) depuis le 8 octobre 2026 à 8 h 12 UTC.

## Trou de l'archive locale

- Dernier relevé avant l'arrêt : **8 octobre 2026 à 19 h 09 UTC** (21 h 09 à Paris). Docker ne tournait plus ensuite (cause non établie), et le conteneur non plus.
- Reprise : **15 octobre 2026 à 16 h 59 UTC**, après le redémarrage de Docker et du conteneur.
- Trou : **165,8 heures** (près de 7 jours), inscrit automatiquement dans `data/raw/elevators/gaps.csv`.
- Relevés perdus : rien ne permet de récupérer après coup l'état des ascenseurs pendant cette période. Seule l'archive GitHub la couvre, avec la limite ci-dessous.

## Limite de l'archive GitHub

- Du 8 octobre à 8 h 12 UTC au 15 octobre à 15 h 02 UTC (174,9 heures), GitHub a exécuté **32 relevés pour environ 175 programmés**, soit **environ 1 relevé horaire sur 5**. L'écart entre deux relevés va de 3,1 à 10,6 heures (médiane 5,3 heures). Les 31 intervalles sont tous inscrits dans le `gaps.csv` de ce dépôt. Les exécutions programmées de GitHub Actions ne sont pas garanties : GitHub en saute une partie.
- Effet mesuré sur l'archive locale (script `scripts/analysis/lift_archive_sampling.py`, voir les règles dans le script) :
  - pris en compte : relevés de journée seulement (4 h à 22 h UTC), car vers 23 h-4 h UTC environ 270 ascenseurs sont signalés indisponibles ensemble pendant la fermeture du réseau ; et seulement la plus longue période sans trou de plus de 90 minutes (du 6 octobre à 6 h 28 au 8 octobre à 3 h 15 UTC, 36 relevés de journée, 124 débuts de panne) ;
  - **46 % des pannes de journée qui se terminent dans la période ne durent qu'un relevé (environ une heure)** ;
  - part des débuts de panne encore vus avec un relevé toutes les *k* heures (minimum / moyenne / maximum selon l'heure de départ) : *k* = 5 : 43 / 49 / 54 % ; *k* = 6 : 34 / 44 / 48 %.
  - Avec l'écart médian de l'archive GitHub (5,3 heures), **une archive de ce rythme ne capte qu'environ 35 à 55 % des pannes de journée** (environ 45 à 50 % en moyenne).
- Lecture : cette période ne couvre que deux jours, avec deux nuits ; les chiffres donnent un ordre de grandeur, pas une estimation précise.

## Conséquences pour le futur pré-enregistrement

- L'archive GitHub seule ne suffit pas pour un taux de disponibilité : elle sous-estime le nombre de pannes, surtout les pannes courtes. Elle sert de secours quand l'archive locale s'arrête.
- Les périodes sans relevé (archive locale et GitHub) seront exclues ou traitées par une règle écrite à l'avance, et non comblées.
- La fermeture nocturne du réseau sera séparée des pannes avant tout calcul.
- Le flux change à presque chaque relevé horaire (contenu différent 18 fois le 6 octobre et 24 fois le 7 octobre) : il n'est pas mis à jour seulement trois fois par jour, contrairement à ce que laisse penser la description des tournées des agents.
