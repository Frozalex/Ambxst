# Ambxst pour Lenovo LOQ

Fork de [Axenide/Ambxst](https://github.com/Axenide/Ambxst), adapté au Lenovo LOQ 15AHP10 avec Ryzen 7 250, Radeon 780M intégrée et RTX 5060. L’interface et les composants natifs d’Ambxst sont conservés. Un profil facultatif reprend les raccourcis de Hyprland. Ce profil remplace le prototype CHACAL ; il ne recrée pas son interface.

## Adaptations

- Palette **LOQ Monochrome** pour le bureau (barre, dock, menus, widgets, bordures), profil **Lenovo LOQ**, fond statique teinté par le mécanisme natif Ambxst. Les icônes des applications conservent leurs couleurs (`tintIcons=false`) ; les palettes des applications ne sont pas exportées depuis le thème du bureau.
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

Le Lenovo utilise le profil **Hyprland**, appliqué à la demande de son utilisateur. Il reprend les combinaisons de la [configuration officielle](https://github.com/hyprwm/Hyprland/blob/main/example/hyprland.lua), en ouvrant le lanceur Ambxst avec Super+R. Les fonctions supplémentaires Ambxst restent accessibles sans conflit. La rubrique Clavier d’Ambxst permet de consulter et modifier ces préférences.

| Raccourci | Action |
|---|---|
| Super+Q / Super+E | Terminal Kitty / fichiers Dolphin |
| Super+R | Lanceur Ambxst |
| Super+C / Super+V | Fermer / basculer en fenêtre flottante |
| Super+flèche | Sélectionner une fenêtre |
| Super+1…0 / Super+Maj+1…0 | Bureau 1…10 / y déplacer la fenêtre |
| Super+molette | Bureau occupé suivant ou précédent |
| Super+S / Super+Maj+S | Bureau spécial / y déplacer la fenêtre |
| Super+P / Super+J | Pseudo-tiling / changer la séparation (disposition dwindle) |
| Super+M | Quitter la session via hyprshutdown |
| Super+clic gauche / droit maintenu | Déplacer / redimensionner une fenêtre |
| Super+D / Super+Maj+C | Tableau de bord / paramètres Ambxst |
| Super+Ctrl+V / Super+Ctrl+S | Presse-papiers / outils Ambxst |
| Impr. écran / Super+Maj+R | Capture / enregistrement d’écran |
| Super+L / Super+Échap | Verrouiller / menu d’alimentation |

Sur le clavier français AZERTY de ce profil, les bureaux utilisent les symboles non décalés de la rangée 1–0 (`& é " ' ( - è _ ç à`) : Super+& sélectionne le bureau 1, et Super+Maj+& y déplace la fenêtre. Les raccourcis supplémentaires sans conflit, notamment Super+F pour le plein écran, sont conservés. Le bureau spécial Ambxst reste celui déjà utilisé, sans renommage.

Pour appliquer ce choix après un premier lancement d’Ambxst :

```bash
python3 loq/keybindings.py
```

Kitty, Dolphin et hyprshutdown doivent être installés (ils sont présents sur ce Lenovo). Le script sauvegarde `binds.json` dans `~/.local/state/ambxst-loq/keybindings/`, refuse les liens symboliques et les conflits, puis remplace le fichier atomiquement. Ambxst régénère sa configuration à partir de ces préférences. Le script n’est pas exécuté au démarrage : les modifications ultérieures dans l’interface restent libres. Aucun fichier généré Hyprland n’est modifié à la main.

Pour revenir à une sauvegarde précise : `python3 loq/keybindings.py --restore CHEMIN_SAUVEGARDE`. Le fichier courant est également sauvegardé avant ce retour.

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
- 21 tests Python : dispositions HDMI, erreur de mode, retour indépendant, débranchement, protection des préférences symboliques, restauration après une erreur d’écriture injectée, conflits de raccourcis, AZERTY, conservation des préférences et retour exact à une sauvegarde.
- Chargement réel Quickshell 0.3.2 sur Hyprland 0.56.2 en Lua, configuration générée et intégration acceptées avec `config ok`.
- Vérification des notifications, du lanceur et de la disponibilité des trois profils natifs dans la session.
- Profil de raccourcis : 126 entrées chargées, aucun doublon, aucune erreur de configuration et validation isolée `config ok`. L’injection de touches virtuelles n’a pas déclenché les actions dans cette session ; les frappes au clavier physique restent à confirmer. La déconnexion Super+M n’a pas été déclenchée pour le test.

Commandes reproductibles :

```bash
cd backend && go test ./... && cd ..
python3 -m unittest discover -s loq -v
bash -n loq/launch
```

Le verrouillage et le cycle de veille complet demandent un essai manuel. Aucun gain de RAM, de watts ou d’autonomie n’est présenté comme mesuré : Ambxst fournit davantage de fonctions que le prototype, avec une empreinte mémoire différente. Les optimisations ci-dessus réduisent des activités précises sans garantir une baisse de la mémoire totale de la session.

## Mémoire du shell

Le profil LOQ désactive le préchargement invisible du lanceur et du presse-papiers. Les vues du presse-papiers et des emojis sont déchargées lorsqu’elles sont cachées ; leurs données restent gérées par les services existants. Les vues de notes et de sessions terminal restent inchangées pour préserver leur état. Le style et les raccourcis ne sont pas modifiés. La première ouverture peut demander un peu plus de temps.

Mesure ponctuelle sur ce Lenovo, huit secondes après chaque redémarrage de Quickshell : PSS de 457004 à 411915 Kio, soit environ 446 à 402 Mio (44 Mio, 9,9 %). Cette comparaison concerne le processus Quickshell, pas la mémoire totale du PC. Les ouvertures/fermetures du lanceur, presse-papiers, emojis et tableau de bord ont été demandées dans la session ; aucune nouvelle erreur QML n’a été relevée dans le journal consulté. La stabilité de la consommation sur une longue session reste à mesurer.

## Licence et suivi

La licence AGPL-3.0 et les crédits d’Ambxst sont conservés. Le contrôleur HDMI réutilisé comporte sa notice MIT dans `loq/HDMI-LICENSE`. Le dépôt amont reste configuré comme distant `upstream` ; les adaptations peuvent être comparées et fusionnées lors des mises à jour.
