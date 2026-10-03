# Note préparatoire — carte « Services pour les personnes sans domicile »

*Rédigée le 03/10/2026 pour la porteuse du projet. Recherche documentaire seulement : **aucun calcul, aucun temps de trajet, aucun croisement** avec les ressources ou un autre indicateur. Point 5 bis de la feuille de route (CLAUDE.md), à reprendre après le lancement.*

Chaque fait ci-dessous vient d'une page ou d'une API ouverte le 03/10/2026 (date de vérification indiquée « vérifié le 03/10/2026 » sauf mention contraire). « Non vérifié » signale ce qui n'a pas pu être confirmé.

---

## 0. Trois règles, avant tout le reste

**Règle absolue n° 1 — aucun lieu d'hébergement sur la carte.** Aucun centre d'hébergement, hôtel social, halte de nuit, place d'urgence, ni aucun autre lieu où des personnes dorment ne figure sur la carte, sous aucune forme (point, zone, compte par quartier, info-bulle). **Les lieux destinés aux femmes victimes de violences n'apparaissent jamais**, ni directement, ni par déduction (par exemple un « trou » dans une couche, ou un compte qui changerait d'une version à l'autre).

Comment la règle serait appliquée (à la source, pas par masquage à l'affichage) :
- **Liste d'autorisation, pas liste d'exclusion** : le pipeline ne télécharge que des jeux de données nommés un par un dans une liste fermée (identifiant du jeu + catégories retenues). Tout jeu de données ou toute catégorie absente de la liste n'est jamais téléchargé, donc jamais stocké, jamais publié.
- **Jeux de données repérés et exclus d'emblée** (ils ne doivent jamais entrer dans le dépôt, même dans `data/raw/`) : Paris `hebergements-casvp`, Paris `exclusion-sans-domicilisme0` (places d'hébergement, source DRIHL), Montreuil `centres-dhebergement`, le « socle de données » hébergement de la DRIHL, la catégorie « Hébergement & Logement » de Soliguide.
- **Test automatique** (même principe que les garde-fous existants de `tests/`) : échec si un fichier publié provient d'une source hors liste, ou si un champ de type ou de catégorie contient « hébergement », « héberg », « CHRS », « CHU », « halte de nuit », « mise à l'abri », « violences », etc. Le test complète la liste d'autorisation, il ne la remplace pas.
- **Relecture humaine** de toute nouvelle source avant ajout à la liste, avec motif écrit dans SCORING.md.
- **Pas de lieux non mixtes localisés** : même quand il ne s'agit pas d'hébergement (accueils de jour ou espaces d'hygiène réservés aux femmes), leur adresse n'est pas affichée (voir partie 4).

**Règle n° 2 — montrer les manques de couverture, pas faire un annuaire.** La carte sert à voir où l'offre de base (toilettes gratuites, eau potable, douches, hygiène menstruelle) est éloignée ou absente, et où **la donnée elle-même manque**. Pour trouver un lieu, la carte renvoie vers **Soliguide** (https://soliguide.fr), tenu à jour par l'association Solinum avec les structures concernées. Underlaid ne republie pas les données de Soliguide (partie 2, conditions d'usage).

**Règle n° 3 — rien n'est calculé dans cette note.** Les chiffres ci-dessous sont des comptes de lignes dans les jeux de données (métadonnées), pas des indicateurs.

---

## 1. Besoins à couvrir

### 1.1 Ordres de grandeur

- **Paris, Nuit de la Solidarité du 23 au 24/01/2025** : 3 507 personnes sans abri décomptées ; « 14 % de femmes ont été décomptées » ; 200 personnes dans les stations de métro ou de RER. Source : paris.fr, « Nuit de la Solidarité 2025 », mise à jour le 13/02/2025 — https://www.paris.fr/pages/nuit-de-la-solidarite-2025-29561 (vérifié le 03/10/2026).
- **Métropole du Grand Paris** : 768 personnes sans abri dans les 30 communes participantes en janvier 2025 ; 33 communes engagées pour l'édition du 22/01/2026. Source : communiqué Métropole du Grand Paris / Ville de Paris / UNCCAS — https://metropolegrandparis.fr/sites/default/files/media/document/CP_Nuit%20de%20la%20Solidarit%C3%A9%202026%20.pdf (vérifié le 03/10/2026). Résultats 2026 : **non vérifié** (pas trouvés).
- **Les femmes sont sous-représentées dans les décomptes de rue** : selon le Samusocial de Paris, elles « évitent l'espace public ou cherchent à se rendre invisible » ; « en janvier 2025, 60 % des adultes hébergés à l'hôtel en IDF en moyenne par jour sont des femmes » ; 120 femmes par jour ont appelé le 115 de Paris en décembre 2024. Source : Samusocial de Paris, *Manifeste pour répondre dignement aux besoins des femmes sans abri*, mars 2025 — https://www.samusocial.paris/sites/default/files/2025-03/Manifeste%20droit%20des%20femmes_2025.pdf (vérifié le 03/10/2026).
- **France** : « 330 000 [personnes sans domicile] en 2024, dont environ 120 000 femmes » ; « chaque soir, environ 3 000 femmes et près de 3 000 enfants sans abri passent la nuit dans la rue ». Source : Sénat, délégation aux droits des femmes, *Femmes sans abri, la face cachée de la rue*, rapport d'information R24-015-1, 08/10/2024, synthèse — https://www.senat.fr/rap/r24-015-1/r24-015-1-syn.pdf (vérifié le 03/10/2026).
- **Dernière enquête nationale** : Insee-Ined 2012, « les femmes représentent 38 % des sans-domicile » (définition large, hébergement compris) — https://www.ined.fr/fr/tout-savoir-population/memos-demo/focus/les-sans-domicile-en-france/ (vérifié le 03/10/2026). Nouvelle enquête Insee-Drees « Sans Domicile 2025 », collecte du 31/03 au 05/07/2025 — https://www.insee.fr/fr/information/8545597 (vérifié le 03/10/2026). Date de publication des premiers résultats : **non vérifié** (un résultat de recherche indique fin 2026, page non ouverte).

### 1.2 Besoins propres aux femmes, d'après les sources

| Besoin | Ce que disent les sources | Source |
|---|---|---|
| **Sécurité, non-mixité** | « La question de la mixité de nombreux lieux d'accueil, d'hygiène et de soins est un frein majeur » ; plus de 90 % des femmes vivant à la rue ont subi des violences (étude Observatoire du Samusocial, 2016). | Samusocial de Paris, fiche « L'Oasis » (mise en ligne en avril 2026 d'après l'URL) — https://www.samusocial.paris/wp-content/uploads/2026/04/Fiche-projet-LOasis.pdf |
| **Douches** | Projet de 2019 : « Although there are around forty free public shower facilities in Paris, only 10% of women use them », « due to fear and the lack of privacy ». Chiffre ancien, propre au Samusocial, à ne pas reprendre sans date. | Fondation Raja-Danièle Marcovici, page projet — https://www.fondation-raja-marcovici.com/en/projet/a-hygiene-and-care-facility-dedicated-to-homeless-women/ |
| **Hygiène, services du quotidien** | « Segmentation des lieux de l'assistance (place d'hébergement, accueil de jour, distribution alimentaire, bains douches, bagagerie…), la mixité de certains lieux et des difficultés d'accès aux transports, entraînant des phénomènes de non-recours. » Recommandation : accueils de jour réservés aux femmes, centralisant les services. Risques cités : « difficultés d'accès à l'hygiène ». | Sénat, synthèse du 08/10/2024 (lien ci-dessus) |
| **Lieux jugés plus sûrs** | Recours à des « mises à l'abri ciblées jugées plus sécurisantes (hôpitaux, urgences, gares, etc.) ». | Samusocial, Manifeste 2025 |
| **Hygiène menstruelle** | Paris indique des distributions gratuites dans « les centres de santé sexuelle, les bibliothèques, les conservatoires, les bains-douches, ainsi que dans des structures dédiées aux jeunes et aux étudiants », et renvoie à la carte Reglà. | paris.fr, « Hygiène menstruelle… », page datée du 01/10/2026 — https://www.paris.fr/pages/hygiene-menstruelle-en-finir-avec-les-idees-recues-pour-reduire-les-inegalites-31315 |
| **Toilettes la nuit** | Besoin cité par la porteuse du projet (CLAUDE.md, point 5 bis). **Aucune source associative ou institutionnelle ouverte le 03/10/2026 ne le chiffre** : à documenter (non vérifié). Le jeu Paris permet seulement de compter les toilettes ouvertes 24 h/24 (partie 2). | — |
| **Eau potable** | Besoin général (chaleur, hygiène) ; aucune source spécifique aux femmes trouvée (non vérifié). | — |
| **Accueils de jour** | 2025, l'Oasis (accueil de jour, d'hygiène et de soins réservé aux femmes, Samusocial) : 572 nouvelles femmes accueillies, 60 femmes par jour en moyenne, 2 613 douches. Illustration d'un besoin, pas une source cartographiable. | Fiche « L'Oasis » (lien ci-dessus) |

**Ce que la carte peut couvrir** : toilettes gratuites (dont la nuit et en fauteuil roulant), eau potable, douches et bains-douches gratuits, et, si une source le permet, points de distribution de protections périodiques. **Ce qu'elle ne couvre pas** : l'hébergement (règle n° 1), l'aide alimentaire et les accueils de jour en tant que points (partie 4), la sécurité ressentie (aucune donnée).

---

## 2. Sources possibles

Licences et dates lues dans les métadonnées des portails (API Opendatasoft ou API data.gouv.fr), le 03/10/2026. « Comptes » = nombre de lignes du jeu, pas un indicateur.

| Source | Éditeur | Licence | Couverture | Mise à jour | Champs utiles | Réutilisation | Constat |
|---|---|---|---|---|---|---|---|
| Toilettes publiques `sanisettesparis` — https://opendata.paris.fr/explore/dataset/sanisettesparis/ | Ville de Paris | ODbL | Paris | 03/10/2026 (quotidienne) | `type`, `statut`, `horaire`, `acces_pmr`, `relais_bebe` | Oui (ODbL, attribution, partage à l'identique) | 610 lignes : sanisettes 422, WC de parcs 172, lavatories 6 (payants), urinoirs 9, urinoir femme 1 ; 581 en service ; accès PMR 504 (488 en service) ; 153 sanisettes en service ouvertes « 24/24h », toutes PMR ; relais bébé 14. Pas de champ « gratuit » (lavatory = payant selon la description). **25 horaires incohérents** (« 00h01 - 00h02 », « 21h59 - 22h00 »…), à signaler à l'éditeur. Les urinoirs ne répondent pas au besoin des femmes. |
| Fontaines à boire `fontaines-a-boire` — https://opendata.paris.fr/explore/dataset/fontaines-a-boire/ | Eau de Paris | ODbL | Paris + cimetières parisiens hors Paris | 28/09/2026 | `type_objet`, `modele`, `dispo`, `motif_ind`, dates d'indisponibilité | Oui (ODbL) | 1 323 lignes, 1 238 disponibles. Pas de champ d'accessibilité. Copie régionale `fontaines-a-boire-5` (Région IDF). |
| Bains-douches, jeu `ilots-de-fraicheur-equipements-activites` (type « Bains-douches ») — https://opendata.paris.fr/explore/dataset/ilots-de-fraicheur-equipements-activites/ | Ville de Paris (DTEC) | ODbL | Paris | 03/10/2026 | `payant`, horaires par jour | Oui (ODbL) | 17 bains-douches, tous « payant = Non ». Pas de champ PMR ni de créneau femmes. **Écart** : la page paris.fr « Les bains-douches municipaux » (mise à jour le 16/02/2026, https://www.paris.fr/pages/les-bains-douches-municipaux-138) en liste 16, dont 8 « accessibles aux personnes à mobilité réduite », sans créneau réservé aux femmes mentionné. À rapprocher avant usage. |
| Maisons des Solidarités `coordonnees-ssp-et-casvp` | Ville de Paris (DSOL) | ODbL | Paris | 28/11/2025 | horaires, accessibilité | Oui | 17 lieux (services sociaux d'arrondissement, pas des lieux d'hygiène). Contexte possible. |
| Restaurants du CASVP `restaurants-casvp` | Ville de Paris (DSOL) | ODbL | Paris | 23/07/2019 | type (E / S) | Oui | 43 lignes dont 8 « restaurants solidaires ». Données de 2019 : périmées. |
| Points de distribution de protections périodiques | — | — | — | — | — | — | **Aucun jeu ouvert trouvé** (catalogue Paris : 0 résultat pour « protections périodiques » et « précarité menstruelle » ; data.gouv.fr : 0). |
| Reglà (carte des distributions gratuites de protections périodiques) — https://www.regla-app.fr | Règles Élémentaires | **Non vérifié** (aucune mention lisible sur le site) | France, contributive | Non vérifié | — | Non vérifié : à demander | Lancée le 28/04/2025 selon diplomeo.com (article du 24/04/2025, https://diplomeo.com/actualite-regla_application_localiser_protections_periodiques_gratuites). Paris y renvoie. |
| Toilettes dans le réseau RATP `sanitaires-reseau-ratp` — https://www.data.gouv.fr/datasets/toilettes-publiques-dans-le-reseau-ratp | RATP | ODbL | Stations RATP (Paris et petite couronne, ex. Créteil-Préfecture, Rosny-Bois-Perrier) | 02/09/2026 | gratuit/payant, zone contrôlée, accès avec titre de transport, PMR | Oui (ODbL) | 87 toilettes ; 86 gratuites ; 54 en zone contrôlée (titre de transport nécessaire) ; PMR « oui » 67. « Localisation approximative ». Pas d'horaires. Copie IDFM de 2023 (`toilettes-publiques-dans-le-reseau-ratp-2`) : périmée. |
| Fontaines dans le réseau RATP `fontaines-a-eau-dans-le-reseau-ratp` — https://www.data.gouv.fr/datasets/fontaines-a-eau-dans-le-reseau-ratp | RATP | Licence Ouverte | Stations RATP | 22/09/2026 | commune, zone contrôlée | Oui | 115 fontaines : Paris 79, le reste dans une vingtaine de communes de petite couronne (Saint-Denis 3, Vincennes 3, Montreuil 2…) et 2 en Seine-et-Marne. « Localisation approximative ». Noms de communes non normalisés. |
| Fontaines à proximité des arrêts `fontaines-a-proximite-des-arrets-de-transport-en-commun-d-ile-de-france` | Île-de-France Mobilités | Licence Ouverte 2.0 | Île-de-France | 14/08/2026 | `accessible_pmr`, `remplissage_contenant_possible`, `indisponible`, gestionnaire | Oui | 179 lignes. Codes commune et gestionnaire mal renseignés (gestionnaire vide partout) : à examiner. |
| Toilettes publiques en Île-de-France — https://www.data.gouv.fr/datasets/toilettes-publiques-en-ile-de-france | Région Île-de-France | ODbL | IDF, « non exhaustive » | 18/05/2024 | tarif, PMR, horaires, type | Oui (ODbL) | 3 217 lignes, consolidées depuis Paris, RATP, OSM et quelques communes. Lignes hors OSM : 75 : 627 ; **92 : 10 ; 93 : 3 ; 94 : 6** ; le reste vient d'OSM. Non mis à jour depuis mai 2024. |
| Points d'eau potable en IDF (OpenStreetMap) | Région Île-de-France | ODbL | IDF | 21/09/2026 (hebdomadaire) | `fee`, `opening_hours`, `wheelchair`, `bottle` | Oui | 3 377 lignes. Extraction OSM : mêmes limites qu'OSM. |
| Bornes-fontaines `bornes-fontaines` — https://data.seineouest.fr | Grand Paris Seine Ouest (92) | Licence Ouverte | 7 communes : Boulogne-Billancourt 66, Issy-les-Moulineaux 46, Meudon 25, Vanves 13, Ville-d'Avray 9, Sèvres 8, Chaville 6 | 02/10/2026 | `en_service`, type | Oui | 173 bornes, 171 en service. Marnes-la-Coquette n'apparaît pas. |
| Sanitaires `sanitaires` — https://data.seineouest.fr | Grand Paris Seine Ouest (92) | Licence Ouverte | Boulogne 19, Meudon 4, Vanves 4, Issy 2, Ville-d'Avray 2, Chaville 1 (+1 sans commune) | 02/10/2026 | localisation seulement (`type` vide) | Oui | 33 toilettes, **sans horaires, gratuité ni accessibilité**. |
| Fontaines publiques à Sceaux — portail opendata.hauts-de-seine.fr | Ville de Sceaux | **Non indiquée** dans les métadonnées | Sceaux | 29/09/2026 | adresse | Non vérifié | 21 fontaines. |
| Portail du département des Hauts-de-Seine (opendata.hauts-de-seine.fr) | Département 92 | — | — | — | — | — | Recherches « toilette », « wc », « sanisette », « eau potable », « douche », « bains » : **rien trouvé** de pertinent (hors jeux communaux ci-dessus). |
| Points d'eau potable 93 (données OSM) — https://www.data.gouv.fr/datasets/points-deau-potable-seine-saint-denis-donnees-osm | Département de la Seine-Saint-Denis (portail data.seinesaintdenis.fr) | ODbL | 93 | 31/08/2026 (mensuelle) | gratuit, intérieur | Oui | 271 lignes. **C'est une extraction OpenStreetMap**, pas un inventaire officiel. Recherches « toilettes », « douche », « sans-abri », « hygiène » sur le portail : rien trouvé. |
| Montreuil (data.montreuil.fr) | Ville de Montreuil (93) | Licence Ouverte 2.0 | Montreuil | 2019 | — | Oui | `bornes-fontaines` 22 (10/07/2019) ; `lieux-de-solidarite` 9 (08/05/2019 : Emmaüs, Restos du cœur…) ; `centres-dhebergement` : **exclu (règle n° 1)**. Données de 2019. |
| Saint-Denis (93), Plaine Commune, Est Ensemble | — | — | — | — | — | — | **Rien trouvé.** Correction : le jeu data.gouv.fr « Toilette publique » (https://www.data.gouv.fr/datasets/toilette-publique) est publié par la **Mairie de Saint-Denis (La Réunion)**, pas par Saint-Denis (93). La mention de CLAUDE.md (« Saint-Denis seulement ») est à corriger. |
| Val-de-Marne | — | — | — | — | — | — | **Aucun portail départemental trouvé** (data.valdemarne.fr et opendata.valdemarne.fr ne répondent pas ; aucune organisation « Département du Val-de-Marne » sur data.gouv.fr). Rien trouvé à l'échelle communale non plus (recherche limitée). |
| SEDIF | Syndicat des eaux d'Île-de-France | — | 133 communes | — | — | — | **Aucune liste ouverte des fontaines trouvée** (ni sur data.gouv.fr, ni par recherche web ; le SEDIF évoque des fontaines installées pour les Jeux de 2024). |
| Soliguide / API Solidarité — https://www.data.gouv.fr/dataservices/solidarite | Solinum | Pas de licence ouverte ; convention de partenariat | France | Fiche data.gouv du 07/03/2025 ; « 2 mises à jour minimum par an de toute la base » | Catégories dont « Hygiène », « Accueil », « Alimentation », **« Hébergement & Logement »** ; horaires ; publics ciblés (« genre, âge, situation administrative… ») | **Non** : « interdiction d'en faire des copies », « indiquer la source », « ne pas revendre » ; accès réservé aux « structures publiques et organisations à but non lucratif agissant dans le domaine de l'action sociale » | ~100 000 services. Underlaid, projet personnel ouvert, ne remplit probablement pas le critère d'éligibilité, et l'interdiction de copie est incompatible avec des données publiées et un calcul reproductible. **Usage retenu : un lien, rien d'autre.** Documentation (apisolidarite.soliguide.fr) : page non lisible sans navigateur, **non vérifiée**. |
| DRIHL, 115 / SIAO, Samusocial | — | — | — | — | — | — | Données ouvertes trouvées : seulement des places d'**hébergement** (DRIHL, via Paris `exclusion-sans-domicilisme0`) → **exclues (règle n° 1)**. Aucun jeu ouvert du 115, des SIAO ni du Samusocial trouvé (recherches data.gouv.fr « 115 », « SIAO », « veille sociale », « Samu social »). |
| Décompte Nuit de la Solidarité `exclusion-sans-domicilisme` | Ville de Paris | ODbL | Paris | 06/12/2024 | année, nombre | Oui | 7 lignes (une par année). Chiffres agrégés, pour le texte seulement, **jamais sur la carte**. |
| OpenStreetMap | Contributeurs OSM | ODbL | Partout, inégal | Continue | `amenity=toilets`, `drinking_water`, `shower`, `fee`, `opening_hours`, `wheelchair` | Oui (ODbL) | Vérification du projet du 03/10/2026 (CLAUDE.md, « Toilettes publiques et points d'eau potable ») : même à Paris, OSM ne retrouve que 83 % des toilettes officielles et 73 % des fontaines en service (à 30 m) ; horaires renseignés 20 / 2 / 2 / 5 % (75 / 92 / 93 / 94) ; douches 17 / 1 / 4 / 2. **Écarté comme source principale** (même leçon que les trottoirs). |
| FINESS, BPE | DREES / INSEE | Licence Ouverte | France | — | — | — | **Non examinés** pour cette note. FINESS recense surtout des établissements d'hébergement (à exclure) ; codes BPE pertinents éventuels : non vérifié. |

---

## 3. Couverture en petite couronne

### 3.1 Où la donnée manque (au 03/10/2026)

| Besoin | Paris | Hauts-de-Seine | Seine-Saint-Denis | Val-de-Marne |
|---|---|---|---|---|
| Toilettes publiques | Officielle, complète, quotidienne (horaires, PMR) | GPSO seulement (7 communes, sans horaires ni PMR) + 10 lignes communales (Région, 2024) | 3 lignes communales (Région, 2024) | 6 lignes communales (Région, 2024) |
| Eau potable | Officielle (Eau de Paris) | GPSO (7 communes), Sceaux | Montreuil (2019) ; extraction OSM du Département | Rien d'officiel |
| Douches / bains-douches | Officielle (17 ou 16) | Rien | Rien | Rien |
| Protections périodiques | Pas de jeu ouvert | Rien | Rien | Rien |
| Réseau RATP (toilettes, fontaines) | Oui | Stations RATP seulement | Stations RATP seulement | Stations RATP seulement |

Hors Paris, la donnée officielle couvre une poignée de communes. La phrase prévue dans CLAUDE.md (« Les communes de petite couronne ne publient pas de liste ouverte de leurs toilettes publiques et points d'eau. ») est trop générale : proposer « La plupart des communes de petite couronne ne publient pas de liste ouverte de leurs toilettes publiques et points d'eau ; quelques-unes le font (Grand Paris Seine Ouest, Sceaux, Montreuil). »

### 3.2 Montrer que la donnée manque, sans laisser croire que le service manque

- **Trois états distincts, jamais confondus** : (1) donnée officielle disponible → durée ou distance affichée ; (2) donnée partielle (OSM seul, ou liste sans horaires) → affichée en hachures avec la mention « donnée incomplète » ; (3) aucune donnée → **gris hachuré « donnée non publiée »**, jamais une couleur de l'échelle et jamais « 0 ».
- **Aucun calcul de distance là où la donnée manque** : une commune sans liste officielle n'a pas de valeur, même si OSM y place des toilettes (même règle que les trottoirs).
- **Légende et phrase de méthode** : « Une zone grise signifie que la commune ne publie pas de liste ouverte, pas qu'il n'existe aucune toilette ou fontaine. »
- **Carte de couverture des sources en premier**, avant toute carte de durées : quelles communes publient quoi, avec la date de mise à jour.
- **Appel aux communes** : la carte de couverture sert aussi à demander la publication des listes (partie 5).

---

## 4. Ce que la carte montrerait, et ce qu'elle ne montrerait jamais

**Montrerait (Paris d'abord, petite couronne seulement là où la donnée existe)**
- Durée à pied vers les toilettes gratuites en service les plus proches, le jour et **la nuit** (sanisettes « 24/24h »), avec le profil fauteuil roulant (sous-ensemble « accès PMR »). Urinoirs et lavatories payants exclus de la mesure.
- Durée à pied vers le point d'eau potable disponible le plus proche.
- Durée vers le bain-douche gratuit le plus proche, avec ses jours d'ouverture.
- Zones « donnée non publiée » (partie 3).
- Toujours en **information**, jamais dans le score d'exposition, jamais en sous-score (même règle que les Itinéraires).

**Ne montrerait jamais**
- Aucun lieu d'hébergement, de mise à l'abri ou de nuit ; aucun lieu pour femmes victimes de violences (règle n° 1).
- Aucune adresse d'accueil de jour, d'espace d'hygiène ou de soins **réservé aux femmes** : ces lieux sont connus des maraudes et de Soliguide ; les rendre visibles sur une carte publique peut exposer les personnes qui les fréquentent. Au plus, une phrase de contexte sans localisation.
- Aucun décompte de personnes à la rue par quartier (la Nuit de la Solidarité reste en chiffres agrégés, dans le texte).
- Aucune donnée copiée de Soliguide.

**Renvoi vers Soliguide** : sur chaque fiche de quartier, un lien du type « Trouver un lieu (douche, repas, accueil, soins) : Soliguide », vers la recherche Soliguide de la commune. Format exact des liens de recherche : **non vérifié** (le site ne se lit pas sans navigateur) ; à confirmer avec Solinum.

**Vie privée et sécurité**
- Aucun suivi individuel : pas de géolocalisation enregistrée, pas de journal des adresses recherchées, pas de mesure d'audience par adresse. La recherche d'adresse du site actuel passe par l'API Adresse côté navigateur : vérifier qu'aucune adresse n'est stockée côté projet (non vérifié pour cette note).
- Pas d'emplacement exact des services sensibles (voir ci-dessus) ; pas de couche « signalement » de personnes ou de campements.
- Vocabulaire : « personnes sans domicile », « personnes sans abri » ; ni « SDF » ni formulations qui désignent un responsable.

---

## 5. Prochaines étapes proposées (aucun calcul lancé)

1. **Solinum** (api@solinum.org, formulaire indiqué sur la fiche data.gouv.fr) : présenter le projet, demander (a) si un simple lien vers Soliguide par commune leur convient et sous quelle forme, (b) s'ils accepteraient de relire la liste des catégories affichées et la règle d'exclusion, (c) éventuellement un chiffre agrégé de couverture par commune, sans copie de leurs données. Ne pas demander l'accès à l'API tant que les conditions (pas de copie) sont incompatibles avec un calcul publié.
2. **Ville de Paris** : signaler les 25 horaires incohérents de `sanisettesparis` et l'écart 17 / 16 bains-douches ; demander s'il existe une liste ouverte des points de distribution de protections périodiques.
3. **Règles Élémentaires** : demander la licence de la carte Reglà et si une réutilisation agrégée (compte par commune, sans adresse) est possible.
4. **Départements et territoires** : Hauts-de-Seine, Seine-Saint-Denis, Val-de-Marne, Plaine Commune, Est Ensemble, Paris Terres d'Envol, Grand-Orly Seine Bièvre : demander s'ils disposent d'un inventaire des toilettes publiques, fontaines et douches (souvent tenu par les services de voirie ou de propreté) et s'ils peuvent le publier.
5. **SEDIF** : demander la liste des fontaines publiques gérées ou installées (dont celles des Jeux de 2024).
6. **RATP / IDFM** : vérifier les codes commune et le gestionnaire du jeu IDFM des fontaines ; confirmer que les toilettes en zone contrôlée exigent un titre de transport (à ne pas compter comme accès libre).
7. **Associations** (Samusocial de Paris, Fondation des femmes, Règles Élémentaires) : faire relire la liste « montrerait / ne montrerait jamais » avant tout calcul.
8. **Ensuite seulement** : pré-enregistrement daté dans CLAUDE.md (sources retenues, règles d'exclusion, mesures, créneaux jour / nuit, profils), puis calcul. Aucun croisement avec les ressources n'est prévu ; s'il est envisagé, il sera pré-enregistré à part.

---

## Annexe — ce qui n'a pas pu être vérifié

- Résultats 2026 de la Nuit de la Solidarité (Paris et Métropole).
- Date de publication des résultats de l'enquête Sans Domicile 2025.
- Licence, éditeur légal et conditions de réutilisation de la carte Reglà.
- Documentation de l'API Solidarité (catégories détaillées, sous-catégories hygiène, champs « genre »), format des liens de recherche Soliguide.
- Existence d'un portail ouvert du Val-de-Marne et de données communales en Val-de-Marne et Seine-Saint-Denis (hors Montreuil).
- Une source chiffrée sur le besoin de toilettes la nuit pour les femmes sans abri.
- Codes BPE et FINESS éventuellement pertinents.
