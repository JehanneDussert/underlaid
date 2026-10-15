# Pré-enregistrement — accès aux places en crèche, pondéré par le nombre de places (E2SFCA)

**Brouillon du 15 octobre 2026, à relire par la porteuse du projet.** Il ne vaut pré-enregistrement qu'une fois sa version finale commitée, avant tout calcul de temps de trajet depuis les crèches, de l'indicateur et de tout croisement avec les ressources. Les choix marqués **[à valider]** sont des propositions.

L'indicateur reste une **information**, hors du score de cumul (décision du 3 octobre 2026). Le croisement avec les ressources (partie 6) est le seul test, avec une règle de verdict fixée ici.

## Ce qui est déjà connu à l'écriture (transparence)

- **Offre** (BPE 2025, code `D502`, établissements qui perçoivent une prestation de service de la CAF) : Île-de-France 3 297 établissements et 138 275 places ; Métropole du Grand Paris 2 183 et 96 991 (Paris 833 / 39 654, Hauts-de-Seine 583 / 25 480, Seine-Saint-Denis 362 / 15 527, Val-de-Marne 405 / 16 330). Capacité renseignée pour toutes les fiches.
- **Concordance avec la CAF** (places au barème CAF, décembre 2023) : totaux par département presque identiques à la BPE (vérifié le 3 octobre 2026). Les micro-crèches à tarif libre sont en grande partie absentes de la BPE.
- **Durée vers la crèche la plus proche** (publiée, second calcul, mardi 10 h) : médiane métropolitaine 4 min sans contrainte, 5 en marche lente, 6 en fauteuil roulant.
- **Aucun** indicateur pondéré par les places n'a été calculé, et l'accès aux crèches n'a jamais été croisé avec les ressources des habitants.
- Méthode et résultats de l'accès aux soins (même méthode, autre service) : connus.

## 1. Offre

- Toutes les fiches `D502` de la BPE 2025 en Île-de-France (y compris hors de la Métropole, pour l'effet de bord), capacité = champ `CAPACITE` (places).
- Pas de tri par le nom ni par le gestionnaire (décision du 3 octobre 2026). Étiquette « Crèche (publique ou privée) » et phrase de méthode sur les crèches déjà publiée.

## 2. Demande

- Grille Filosofi 2021 de 200 m, tranche `ind_0_3` (enfants de 0 à 3 ans), comme le reste de l'E2SFCA.
- Limite : la tranche compte les enfants de 3 ans, dont la plupart sont à l'école maternelle ; elle surestime la demande de façon à peu près proportionnelle partout.
- Carreaux imputés (`i_est_200`) : gardés, comme pour l'accès aux soins.

## 3. Temps de trajet

- Mêmes réseaux que l'accès aux soins (OSM Île-de-France du 30 septembre 2026, GTFS IDFM du 1er octobre 2026), mêmes règles R5, temps médian sur une fenêtre de 60 minutes, calculés de chaque crèche vers les carreaux.
- **Départ : mardi 13 octobre 2026, de 8 h à 9 h [à valider]** (heure du trajet vers la crèche). Sensibilité : de 10 h à 11 h.
- **Profil principal : sans contrainte** (4,5 km/h, réseau complet).
- **Profil descriptif « poussette » [à valider]** : réseau sans escaliers, arrêts et courses signalés accessibles (inconnu = non accessible ; variante inconnu = accessible), 4,5 km/h, sans retrait des pentes. Il n'entre pas dans le test.
- Temps maximal calculé : 25 minutes.

## 4. Décroissance et indicateur

- **Décroissance [à valider]** : celle de l'APL de la DREES, déjà utilisée pour les médecins : moins de 10 min : 1 ; 10 à 15 : 2/3 ; 15 à 20 : 1/3 ; au-delà : 0. Sensibilité : bornes décalées de −5 et +5 minutes.
- Indicateur du carreau = places accessibles pour 100 enfants de 0 à 3 ans (E2SFCA, Luo et Qi 2009). Valeur du quartier = moyenne des carreaux pondérée par le nombre d'enfants de 0 à 3 ans.
- Quartiers concernés : quartiers habités (au moins 50 habitants) ; un quartier sans enfant de 0 à 3 ans dans la grille n'a pas de valeur.

## 5. Contrôles avant tout croisement (rapportés à la porteuse du projet)

- Distribution : part des quartiers au plancher et au plafond, asymétrie, |z| maximal (critère de l'ancien `access_time`).
- Complétude de l'offre par département ; nombre de crèches dans le tampon hors Métropole.
- Stabilité : part des quartiers qui entrent ou sortent du quart le moins bien doté avec les bornes à −5 et +5 minutes, et avec le départ de 10 h.
- Comparaison avec les places au barème CAF par commune (data.caf.fr, communes de plus de 10 000 habitants, Paris par arrondissement) rapportées aux enfants de moins de 3 ans : corrélation de Spearman, et explication des plus gros écarts.
- Si la distribution est écrasée contre une borne (même critère que pour `access_time`), le croisement n'est pas fait et l'indicateur reste une information.

## 6. Croisement avec les ressources (test)

**Hypothèse** : les quartiers où les habitants ont le moins de ressources ont un accès plus faible aux places en crèche.

- Indice de ressources publié (revenu Filosofi 2021, suroccupation et résidences secondaires du recensement 2022) ; **tiers calculés à l'intérieur de chaque département** (leçon de l'étape 4 : la Seine-Saint-Denis non évaluable avec les tiers de la Métropole).
- Quart le moins bien doté défini sur les quartiers habités de la Métropole.
- Pour chaque département d : écart_d = part au quart le moins bien doté dans le tiers aux ressources les plus faibles − part dans le tiers aux ressources les plus élevées ; ρ_d = Spearman(indice de ressources, indicateur orienté « plus haut = plus défavorable »).
- **Défavorable de façon nette** dans d si écart_d ≥ +10 points et ρ_d ≤ −0,10.
- **Soutenue** si c'est le cas dans au moins 2 départements, dont au moins un autre que la Seine-Saint-Denis ; **infirmée** si au moins 2 départements sont nettement inversés (écart_d ≤ −10 et ρ_d ≥ +0,10) ; **nuancée** dans les autres cas.
- Contrôle complémentaire, rapporté sans changer le verdict : même calcul à densité égale (quintiles de densité).
- Aucun indicateur, profil, horaire ou paramètre ajouté, retiré ou modifié après ce croisement ; toute décision prise ensuite sera notée comme telle.

## Limites à publier

- Places au barème CAF seulement : les micro-crèches à tarif libre manquent en grande partie.
- La BPE recense les établissements avec un décalage d'environ deux ans.
- Une place n'est pas forcément attribuable : priorités communales, critères d'attribution et listes d'attente ne sont pas connus.
- Les assistantes maternelles, les crèches d'entreprise hors CAF et la garde à domicile ne sont pas comptées.
- Les enfants de 3 ans gonflent la demande (partie 2).
