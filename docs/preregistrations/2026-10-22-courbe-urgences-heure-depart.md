# Pré-enregistrement — durée vers les urgences selon l'heure de départ

Rédigé le 22 octobre 2026, **proposé à la porteuse du projet** ; sensibilité de nuit « inconnu = oui », contrôle du créneau de 10 h et mention publique validés le 23 octobre 2026, relecture complète avant fusion. Il est enregistré dans le dépôt avant tout calcul des nouveaux créneaux ; la date qui fait foi est celle du commit de fusion de sa PR. Aucun calcul ne sera lancé avant cette fusion.

L'indicateur est une **information**, comme toutes les durées des itinéraires : pas de sous-score, pas de verdict, **aucun croisement avec les ressources** (un tel croisement serait pré-enregistré à part).

## Ce qui est déjà connu à l'écriture (transparence)

- **Durées vers les urgences déjà calculées** (second calcul, 7 octobre 2026), pour les profils sans contrainte, marche lente et fauteuil roulant (inconnu = non et inconnu = oui) : mardi 13 octobre 2026 à 10 h, 21 h et 1 h, et dimanche 11 octobre 2026 à 10 h. Les médianes par quartier et les parts de population au-delà de 45 minutes ont été vues, notamment pour le tableau « Urgences selon l'heure de départ » préparé sur la branche `emergency-time-slots` (non fusionnée).
- **Mesure du coût, 19 et 20 octobre 2026** (200 carreaux tirés au hasard, graine 20261019, 90 services d'urgences générales) : temps de calcul par carreau, et nombre de carreaux qui atteignent des urgences en 90 minutes. Sans contrainte : 0,94 s à 10 h (200 carreaux sur 200), 0,55 s à 2 h (197 sur 200). Fauteuil roulant, inconnu = non : 0,48 s à 10 h (194 sur 200), 0,34 s à 2 h (165 sur 200). Ces chiffres ont servi seulement à estimer le coût ; ils ne sont pas un résultat.
- Rien d'autre n'a été calculé pour les créneaux de 0 h, 2 h, 4 h, 6 h, 8 h, 12 h, 14 h, 16 h, 18 h, 20 h et 22 h.

## 1. Destinations

Les mêmes que pour la durée vers les urgences déjà publiée : services d'urgences générales de la BPE 2025 (`D106`) en Île-de-France. Les urgences réservées à une spécialité ou aux enfants sont exclues (addendum du 2 octobre 2026). La durée calculée est celle vers les urgences les plus proches, au sens du temps de trajet.

## 2. Créneaux

- **Jour** : mardi 13 octobre 2026 (même jour et même GTFS IDFM du 1er octobre 2026 que le second calcul).
- **Heures de départ** : toutes les 2 heures, de 0 h à 22 h (12 créneaux). Le créneau de 0 h est celui de la nuit du lundi au mardi.
- **Fenêtre de départ** : 60 minutes après l'heure de départ ; durée retenue = temps médian de R5 sur la fenêtre, comme pour les autres créneaux.
- Les créneaux déjà calculés à 21 h et à 1 h, et le dimanche, restent publiés tels quels ; ils ne sont pas recalculés.

## 3. Profils

- **Sans contrainte** : réseau OSM complet, GTFS complet, 4,5 km/h.
- **Fauteuil roulant, inconnu = non** (profil principal) : réseau sans marches ni pentes de plus de 8 %, points d'arrêt et courses signalés accessibles (inconnu = non accessible), 0,8 m/s, comme le second calcul.
- **Fauteuil roulant, inconnu = oui** (sensibilité, validée le 23 octobre 2026) : seulement aux créneaux de 0 h, 2 h et 4 h. La nuit, une grande part des courses de Noctilien a une accessibilité inconnue : par exemple, 191 courses sur 372 entre 1 h et 2 h (constat fait pour le tableau de la branche `emergency-time-slots`). Le choix « inconnu = non » y pèse donc plus qu'en journée.
- Marche lente : non calculée pour la courbe.

## 4. Origines et agrégation

Les mêmes que dans le second calcul : les 13 752 carreaux habités de la Métropole, aux points de rattachement communs (script 42), temps maximal 90 minutes. Un carreau qui n'atteint pas d'urgences en 90 minutes est compté comme « plus de 90 min », jamais comme 0 ni comme valeur manquante. Valeur du quartier = médiane des carreaux pondérée par la population ; si plus de la moitié de la population n'atteint pas d'urgences en 90 minutes, le quartier est « plus de 90 min ». Les deux quartiers sans carreau calculé prennent le carreau qui les recouvre le plus, comme dans le second calcul.

## 5. Contrôles avant publication (rapportés à la porteuse du projet)

1. **Créneau de 10 h** : avec les mêmes réglages, il doit redonner les durées déjà publiées. Si plus de 1 % des quartiers diffèrent, rien n'est publié avant explication.
2. **Inversions** : part des couples carreau × créneau où la durée en fauteuil roulant est plus courte que sans contrainte. La part est publiée dans la Méthode, comme pour le second calcul.
3. **Complétude** : pour chaque créneau, chaque profil et chaque département, part de la population à « plus de 90 min ».
4. **Cohérence avec les créneaux déjà publiés** : la courbe à 20 h et 22 h encadre-t-elle la valeur de 21 h, et la courbe à 0 h et 2 h celle de 1 h ? Les écarts sont décrits, sans correction.

## 6. Ce qui est publié

- **Page « Votre quartier »** : la courbe du quartier, un point toutes les 2 heures, pour les deux profils. Le texte ne nomme jamais un quartier plus éloigné.
- **Méthode** : un tableau par créneau, avec la médiane des quartiers et la part de la population au-delà de 45 minutes et de 90 minutes, pour la Métropole et par département ; la sensibilité « inconnu = oui » pour la nuit.
- **Mentions obligatoires** : « à pied et en transports en commun » sur toute durée de nuit. Le profil fauteuil roulant reste une limite basse : ni ascenseurs en panne, ni état des trottoirs, ni accessibilité du bâtiment d'arrivée. Mention placée avec la courbe (texte de la porteuse du projet, 23 octobre 2026) : « En cas d'urgence, appelez le 15 (SAMU) ou le 112, ou envoyez un SMS au 114 si vous êtes sourd ou malentendant. Cette courbe mesure uniquement le temps nécessaire pour se rendre aux urgences par ses propres moyens, en transports en commun. »
- **Taille** : environ 66 000 durées (2 752 quartiers × 12 créneaux × 2 profils), moins de 1 Mo au total.

## 7. Coût

Environ 59 heures de calcul avec un seul processus, soit environ 20 heures avec 3 processus, plus environ 1 h 30 pour la sensibilité de nuit. Le calcul est fait par lots, et les lots déjà terminés sont gardés si l'ordinateur s'arrête. L'archive des ascenseurs continue pendant le calcul.
