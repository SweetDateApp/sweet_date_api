# Contribuer

## Branches

| Branche   | Rôle                                   | Déploiement                  |
|-----------|----------------------------------------|------------------------------|
| `prod`    | Code en production                     | Render — service de production                     |
| `preprod` | Préparation / recette (branche par défaut) | Render — service de préproduction              |

Aucun push direct sur `prod` ni `preprod` : tout passe par une Pull Request.

## Workflow

1. Partir de `preprod` à jour :
   ```bash
   git switch preprod && git pull
   git switch -c feat/ma-fonctionnalite   # ou fix/..., refactor/..., chore/...
   ```
2. Commiter en suivant [Conventional Commits](https://www.conventionalcommits.org/fr) (`feat: ...`, `fix: ...`).
3. Pousser et ouvrir une PR **vers `preprod`**. La CI doit passer avant le merge.
4. Une fois `preprod` validée, ouvrir une PR **`preprod` → `prod`** (release).
   La CI refuse toute PR vers `prod` qui ne vient pas de `preprod`.

## CI/CD (GitHub Actions)

- `.github/workflows/ci.yml` — sur chaque PR vers `preprod`/`prod` : `manage.py check`, vérification des migrations, tests Django (PostgreSQL)
- `.github/workflows/cd.yml` — sur chaque push (= merge) sur `preprod`/`prod` : relance la CI puis déploie.

### Configuration requise sur GitHub

**Settings → Environments** : créer `preprod` et `production` avec les secrets :
- `RENDER_DEPLOY_HOOK_URL` — Render → service → Settings → Deploy Hook (désactiver l'auto-deploy sur Render)

**Settings → Branches** (ou *Rules → Rulesets*), pour `prod` et `preprod` :
- Require a pull request before merging
- Require status checks to pass : `Branch policy`, `Django checks & tests`
- Block force pushes / deletions
