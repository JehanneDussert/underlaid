# Archive des ascenseurs — trous et limites (note du 15 octobre 2026)

Note factuelle, écrite pour la Méthode et pour le futur pré-enregistrement du taux de disponibilité des ascenseurs. Aucun taux de disponibilité n'a été calculé. Source : Île-de-France Mobilités, « État des ascenseurs » (Licence Mobilités).

## Deux archives

- **Archive locale** : le conteneur `underlaid-elevators` interroge le flux toutes les heures (`data/raw/elevators/`, non versionné ; journal `log.csv`, trous de plus de 90 minutes dans `gaps.csv`, réponses vides dans `empty_responses.csv`). Elle tourne depuis le 6 octobre 2026.
- **Archive GitHub** : dépôt privé `underlaid-ascenseurs`, GitHub Actions programmé toutes les heures (`cron: "17 * * * *"`) depuis le 8 octobre 2026 à 8 h 12 UTC.

## Premier trou de l'archive locale (8-15 octobre)

- Dernier relevé avant l'arrêt : **8 octobre 2026 à 19 h 09 UTC** (21 h 09 à Paris). Cause établie le 18 octobre dans le journal de Windows : arrêt du PC depuis le menu Démarrer (« se mettre hors tension », événement 1074) le 8 octobre à 22 h 05, heure de Paris ; Docker et le conteneur se sont arrêtés avec lui.
- Reprise : **15 octobre 2026 à 16 h 59 UTC**, après le redémarrage de Docker et du conteneur.
- Trou : **165,8 heures** (près de 7 jours), inscrit automatiquement dans `data/raw/elevators/gaps.csv`.
- Relevés perdus : rien ne permet de récupérer après coup l'état des ascenseurs pendant cette période. Seule l'archive GitHub la couvre, avec la limite ci-dessous.

## Second trou de l'archive locale (17-19 octobre)

Ajouté le 19 octobre 2026.

- Dernier relevé réussi : **17 octobre 2026 à 21 h 00 UTC**. Premier relevé réussi ensuite : **19 octobre à 6 h 58 UTC**. Trou : **34,0 heures**, inscrit automatiquement dans `gaps.csv`.
- **Première cause, l'arrêt du PC** : arrêt depuis le menu Démarrer le 17 octobre à 21 h 47 UTC (événement 1074) ; le moteur de Docker est arrêté de force deux secondes plus tard (journal de Docker Desktop : `backend process exited: exit status 0x40010004`). Le PC est ensuite en veille du 17 octobre à 21 h 59 au 18 octobre à 17 h 15 UTC. Docker est relancé le 18 octobre vers 17 h 20 UTC.
- **Seconde cause, l'antivirus** : à partir du redémarrage, chaque relevé échoue (14 tentatives, du 18 octobre à 17 h 20 au 19 octobre à 6 h 20 UTC) avec une erreur de certificat. L'antivirus du PC (Norton, « Web/Mail Shield ») intercepte les connexions chiffrées et présente son propre certificat, que le PC approuve mais pas le conteneur. Correction le 19 octobre : le conteneur reçoit, en plus des autorités habituelles, la racine de l'antivirus (déjà approuvée par Windows, valable jusqu'en 2040) ; le premier relevé suivant réussit.
- **Surveillance** : le watchdog local a signalé le problème à chaque passage où le PC était allumé, et l'a notifié par téléphone (ntfy) le 18 octobre à 23 h 48 et le 19 octobre à 5 h 48 UTC, une fois les notifications en place (18 octobre à 17 h 38).
- **Couverture par l'archive GitHub** : 13 relevés pendant le trou (du 17 octobre à 22 h 20 au 19 octobre à 5 h 23 UTC), lancés par la seule planification de GitHub (l'appel horaire externe n'était pas encore actif).

## Limite de l'archive GitHub

- Du 8 octobre à 8 h 12 UTC au 15 octobre à 15 h 02 UTC (174,9 heures), GitHub a exécuté **32 relevés pour environ 175 programmés**, soit **environ 1 relevé horaire sur 5**. L'écart entre deux relevés va de 3,1 à 10,6 heures (médiane 5,3 heures). Les 31 intervalles sont tous inscrits dans le `gaps.csv` de ce dépôt. Les exécutions programmées de GitHub Actions ne sont pas garanties : GitHub en saute une partie.
- Effet mesuré sur l'archive locale (script `scripts/analysis/lift_archive_sampling.py`, voir les règles dans le script) :
  - pris en compte : relevés de journée seulement (4 h à 22 h UTC), car vers 23 h-4 h UTC environ 270 ascenseurs sont signalés indisponibles ensemble pendant la fermeture du réseau ; et seulement la plus longue période sans trou de plus de 90 minutes (du 6 octobre à 6 h 28 au 8 octobre à 3 h 15 UTC, 36 relevés de journée, 124 débuts de panne) ;
  - **46 % des pannes de journée qui se terminent dans la période ne durent qu'un relevé (environ une heure)** ;
  - part des débuts de panne encore vus avec un relevé toutes les *k* heures (minimum / moyenne / maximum selon l'heure de départ) : *k* = 5 : 43 / 49 / 54 % ; *k* = 6 : 34 / 44 / 48 %.
  - Avec l'écart médian de l'archive GitHub (5,3 heures), **une archive de ce rythme ne capte qu'environ 35 à 55 % des pannes de journée** (environ 45 à 50 % en moyenne).
- Lecture : cette période ne couvre que deux jours, avec deux nuits ; les chiffres donnent un ordre de grandeur, pas une estimation précise.

## Conséquences pour le futur pré-enregistrement

- **Les deux trous ont la même cause première : l'arrêt du PC.** D'où la décision du 18 octobre 2026 : deux archives horaires indépendantes (l'archive GitHub lancée toutes les heures par un appel externe), une heure comptée comme couverte si l'une des deux y a un relevé, et, pendant la période d'étude, un PC qui reste allumé, des mises à jour de Windows suspendues et un watchdog qui relance Docker Desktop et prévient par téléphone (pré-enregistrement du 15 octobre, complété le 18).

- L'archive GitHub seule ne suffit pas pour un taux de disponibilité : elle sous-estime le nombre de pannes, surtout les pannes courtes. Elle sert de secours quand l'archive locale s'arrête.
- Les périodes sans relevé (archive locale et GitHub) seront exclues ou traitées par une règle écrite à l'avance, et non comblées.
- La fermeture nocturne du réseau sera séparée des pannes avant tout calcul.
- Le flux change à presque chaque relevé horaire (contenu différent 18 fois le 6 octobre et 24 fois le 7 octobre) : il n'est pas mis à jour seulement trois fois par jour, contrairement à ce que laisse penser la description des tournées des agents.
