# Pré-enregistrement — profil « fauteuil roulant » des durées de trajet

Rédigé le 4 octobre 2026, **validé par la porteuse du projet le 4 octobre 2026**, enregistré dans ce commit **avant tout calcul de vitesse ou de pente**. Il complète le pré-enregistrement des Itinéraires du 2 octobre 2026 (CLAUDE.md, « Hypothèse de travail »).

## Ce qui change

### Vitesse

- Profil fauteuil roulant (sans marches, variantes « inconnu = non accessible » et « inconnu = accessible ») : **0,8 m/s (2,88 km/h)** au lieu de 4,5 km/h.
- Sources vérifiées le 4 octobre 2026 :
  - Tolerico et al. 2007 : 52 utilisateurs de fauteuil manuel, enregistreur porté 13 à 20 jours, vitesse moyenne 0,79 ± 0,19 m/s ;
  - Sonenblum, Lopez et Sprigle, RESNA 2011, « 17,000 bouts of mobility » : vitesse moyenne des déplacements 0,46 m/s, 0,63 m/s pour les plus longs ;
  - Slowik et al. 2015, *Clinical Biomechanics* (PMC4631660) : 170 utilisateurs, vitesse spontanée 1,04 ± 0,30 m/s, sur ergomètre (pas en conditions réelles).
- Dans r5py (1.1.7), `speed_walking` (km/h) s'applique à toute la marche : accès, correspondances, sortie.
- **Sensibilité** : 0,5 m/s et 1,0 m/s, mardi 13 octobre 2026 à 10 h, variante « inconnu = non accessible ».
- Limite : fauteuil manuel ; un fauteuil électrique va plus vite (non modélisé).

### Pentes

- Altitude : RGE ALTI 1 m de l'IGN (Licence Ouverte 2.0) : Paris (2020-07-30), Hauts-de-Seine (2020-07-30), Seine-Saint-Denis (2020-02-24), Val-de-Marne (2020-03-05).
- Pente calculée sur des fenêtres d'au moins 10 m le long de chaque chemin praticable, pour lisser le bruit du modèle de terrain.
- **Tronçons retirés du réseau sans marches au-delà de 8 %** (seuil principal : tolérance de l'arrêté du 15 janvier 2007 sur l'accessibilité de la voirie, pente normale ≤ 5 %, jusqu'à 8 % sur 2 m ; proche des 8,3 % d'OpenTripPlanner).
- **Sensibilité** : seuil de 6 % (openrouteservice), mêmes conditions que la sensibilité de vitesse.
- Gardés sans calcul de pente : ponts, tunnels, passages couverts, tronçons en hauteur (`bridge`, `tunnel`, `covered`, `layer` ≠ 0), dont le modèle de terrain ne donne pas l'altitude.
- Hors des quatre départements : pas de pente (limite documentée).
- Le ralentissement selon la pente proposé par r5py (Tobler, Minetti) n'est pas retenu : il s'appliquerait à tous les profils.

### Points de départ et d'arrivée (décision du 4 octobre 2026)

- Mêmes points pour les quatre profils, posés d'avance sur le réseau sans marches (script 42), sans nouveau déplacement par r5py.
- Cette correction est partielle : sur 604 carreaux d'essai, la part de couples où le fauteuil roulant ressort plus rapide passe de 14,2 % à 2,5 %. **Les cas restants sont publiés comme limite, avec le chiffre mesuré sur l'ensemble des quartiers après le calcul ; aucune valeur n'est forcée.**

## Statut des résultats

- Les verdicts déjà publiés (calculés à 4,5 km/h, sans pente, avec l'ancien rattachement) restent les résultats officiels.
- Les nouveaux résultats sont présentés comme des **contrôles**, avec une ligne « Contrôle après correction du rattachement et révision du profil fauteuil roulant : confirmé / non confirmé », sur le modèle « Contrôle avec le recensement 2022 ».
- Aucun indicateur, profil, créneau ni destination n'est ajouté, retiré ou repondéré après avoir vu ces contrôles.
