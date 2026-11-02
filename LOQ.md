# Ambxst pour Lenovo LOQ

Fork de [Axenide/Ambxst](https://github.com/Axenide/Ambxst), adapté au Lenovo LOQ 15AHP10 avec Ryzen 7 250, Radeon 780M intégrée et RTX 5060. L’interface, les composants et les raccourcis natifs d’Ambxst sont conservés. Ce profil remplace le prototype CHACAL ; il ne recrée pas son interface.

## Adaptations

- Palette **LOQ Monochrome**, profil **Lenovo LOQ**, fond statique teinté par le mécanisme natif Ambxst.
- Animations courtes ; prévisualisations de fenêtres, ligne ondulée et rotation de pochette désactivées dans le profil.
- Statistiques uniquement lorsque l’onglet matériel est visible, à 2 secondes sur secteur et 5 secondes sur batterie.
- `AMBXST_NVIDIA_METRICS=0` interdit toute exécution de `nvidia-smi` par le moniteur. Une mesure désactivée s’affiche « — », pas comme une utilisation réellement mesurée à zéro.
- La lecture de l’état runtime NVIDIA échoue de manière conservatrice : un état absent, illisible ou différent de `active` n’autorise pas le sondage.
- `AMBXST_EASYEFFECTS_AUTOSTART=0` laisse les effets audio facultatifs ; le profil ne lance pas leur service automatiquement.
- `AMBXST_THEME_EXPORTS=0` conserve les couleurs dans Ambxst et évite d’écrire automatiquement les thèmes des autres applications.
- Le sondage de reconnexion s’arrête lorsque le socket est connecté. La veille suit directement les événements Wayland, sans lancer une commande `axctl` chaque seconde.
- Sélection Économie sur batterie et Équilibré sur secteur, par événements ; choix Performance disponible dans le contrôle natif. Un choix manuel demeure jusqu’à un changement d’alimentation ; le passage sous 15 % sur batterie demande Économie.

Le profil ne modifie pas les pilotes, le BIOS, les limites de charge, les gouverneurs CPU ni les variables globales PRIME. Il ne force pas le GPU intégré comme unique carte disponible : le HDMI peut dépendre du câblage NVIDIA.

## Installation et retour

Le fork doit avoir son moteur compilé avec Go 1.26 ou plus récent :

```bash
make build
python3 loq/install-profile.py prepare
./loq/launch
```

`prepare` sauvegarde et écrit des fichiers de préférences Ambxst précis, avec remplacement atomique et annulation sur échec. Il ajoute le lanceur utilisateur et l’entrée « Écrans HDMI — LOQ ». Les fichiers liés symboliquement sont préservés et refusés comme cibles de préférences. Les données et caches des autres applications ne sont ni supprimés ni remplacés.

La configuration générée se trouve dans `~/.local/share/ambxst/hyprland.lua`. Son inclusion dans la session Hyprland doit être examinée avec les composants de l’ancien bureau pour éviter des barres et des raccourcis en double. Sur le Lenovo utilisé pour cette adaptation, l’intégration est déjà active, avec conservation des fichiers d’origine, du clavier français et du mode réel de l’écran interne. Le démarrage à la connexion utilise le lanceur du fork, afin de conserver ses options d’économie.

Retour au bureau sauvegardé sur cette machine :

```bash
python3 loq/install-profile.py restore
```

Les réglages Ambxst récents sont conservés à part avant restauration. Les sources du fork et les données créées par Ambxst restent disponibles. Les sauvegardes se trouvent dans `~/.local/state/ambxst-loq/`.

## Raccourcis

Les raccourcis proviennent intégralement de la configuration native Ambxst ; aucune réaffectation LOQ n’est appliquée. La rubrique Clavier d’Ambxst reste la source de vérité et permet de les consulter ou modifier.

## HDMI

Chercher **Écrans HDMI — LOQ** dans le lanceur, ou exécuter :

```bash
./loq/launch displays
```

Le menu Fuzzel propose Étendre à droite, Dupliquer, Externe seul et Portable seul. Chaque modification exige une confirmation dans les 20 secondes ; un processus indépendant restaure la géométrie précédente si la confirmation manque. Les réglages sont temporaires pour la session et n’écrivent pas dans la configuration des moniteurs.

Le contrôleur requiert une session Hyprland en Lua pour ce profil. Les tests utilisent un faux compositeur ; la compatibilité du câble, les modes vidéo et le retour après débranchement restent à vérifier avec un écran physique. La duplication ne promet pas un rendu identique sur deux formats différents.

## Vérifications réalisées

- Suite Go du backend : `go test ./...`, réussie localement avec Go 1.27.3 et les dépendances vendues par le projet.
- Tests spécifiques : interdiction d’exécuter un faux `nvidia-smi` lorsque les métriques sont désactivées, traitement des états runtime absents, choix des effets audio, conservation du lanceur du fork dans la configuration générée.
- 17 tests Python : dispositions HDMI, erreur de mode, retour indépendant, débranchement, protection des préférences symboliques et restauration après une erreur d’écriture injectée.
- Chargement réel Quickshell 0.3.2 sur Hyprland 0.56.2 en Lua, configuration générée et intégration acceptées avec `config ok`.
- Vérification des notifications, du lanceur et de la disponibilité des trois profils natifs dans la session.

Commandes reproductibles :

```bash
cd backend && go test ./... && cd ..
python3 -m unittest discover -s loq -v
bash -n loq/launch
```

Le verrouillage et le cycle de veille complet demandent un essai manuel. Aucun gain de RAM, de watts ou d’autonomie n’est présenté comme mesuré : Ambxst fournit davantage de fonctions que le prototype, avec une empreinte mémoire différente. Les optimisations ci-dessus réduisent des activités précises sans garantir une baisse de la mémoire totale de la session.

## Licence et suivi

La licence AGPL-3.0 et les crédits d’Ambxst sont conservés. Le contrôleur HDMI réutilisé comporte sa notice MIT dans `loq/HDMI-LICENSE`. Le dépôt amont reste configuré comme distant `upstream` ; les adaptations peuvent être comparées et fusionnées lors des mises à jour.
