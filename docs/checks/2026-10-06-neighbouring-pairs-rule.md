# Paires de quartiers voisins au cadre de vie le plus différent — règle

Écrit le 6 octobre 2026 à 22 h 17, **avant tout calcul de paires**, à la demande de la porteuse du projet. Le résultat sert à choisir un exemple pour la publication de lancement. Ce n'est pas un résultat de méthode et il n'est pas publié sur le site.

## Quartiers retenus

1. **Population** : au moins 500 habitants (recensement 2022, valeur publiée).
2. **Type de quartier** : seulement les quartiers d'habitat, `TYP_IRIS` = H dans le découpage de l'Insee. Les quartiers d'activité (A) et divers (D, souvent de grands parcs, bois ou cimetières) sont écartés.
3. **Occupation du sol** : sont aussi écartés les quartiers dont plus de la moitié de la surface est un espace vert ou boisé ouvert au public ou un cimetière (inventaire régional des espaces verts déjà utilisé par le site, et cimetières de la base d'occupation du sol de L'Institut Paris Region si disponible), ou une zone d'activité.
4. **Données complètes** : les quatre thèmes connus (chaleur, air et bruit, performance énergétique des logements, accès aux soins).

## Voisins

Deux quartiers sont voisins s'ils **se touchent**, c'est-à-dire si leurs contours partagent une frontière de plus de 0 m (un simple point de contact ne suffit pas), **ou** s'ils sont à **15 minutes à pied ou moins**.

**Distance à pied**, donnée pour chaque paire, même quand les quartiers se touchent :
- durée de marche sur le réseau de rues complet, avec le même moteur que le site (R5, réseau OpenStreetMap complet, 4,5 km/h) ;
- calculée entre les **centres habités** des deux quartiers : le centre des carreaux habités de 200 m, pondéré par leur population, rattaché comme les points du second calcul (script 42) ;
- paires candidates : celles qui se touchent, ou à 1,5 km ou moins à vol d'oiseau.

## Écart de cadre de vie

- Pour chaque thème k, le rang r_k du quartier parmi les quartiers habités : la valeur utilisée par la phrase du site « Sur 10 quartiers, N sont moins exposés que le vôtre », avant arrondi. Plus haut = plus exposé, ou accès aux soins plus difficile.
- Pour une paire (A, B), A est le quartier dont la somme des rangs est la plus haute.
- **Écart = Σ_k (r_k(A) − r_k(B))**, sur les 4 thèmes, de 0 à 4. Un écart élevé exige donc que A soit nettement plus exposé que B sur la plupart des thèmes. Des écarts opposés se compensent.
- En cas d'égalité, on retient d'abord la paire où A est plus exposé sur le plus grand nombre de thèmes.
- Les durées sont exclues.

## Liste rendue

- Les 10 paires d'écart le plus élevé, **chaque quartier n'apparaissant qu'une fois**, pour éviter dix variantes autour d'un même quartier.
- Les paires situées dans une même commune sont signalées.
- Pour chaque paire :
  - noms lisibles (« un quartier du Blanc-Mesnil » si le nom Insee n'est pas parlant, comme pour la question « Lequel de ces quartiers ? ») et commune ;
  - distance à pied ;
  - population de chaque quartier ;
  - pour chaque quartier, les 4 thèmes, avec la phrase du site : N = arrondi de r × 10, entre 0 et 9 ;
  - écart de la paire.
- Chacune des 10 paires est vérifiée à la photographie aérienne de l'IGN : un quartier dont l'essentiel serait un parc, un cimetière ou une zone d'activité malgré les critères 2 et 3 est écarté et remplacé par la paire suivante, ce qui est signalé.

## Calendrier

Après la fin du grand calcul, pour ne pas le gêner : la durée de marche demande de charger le réseau de rues complet, environ 9 Go de mémoire.
