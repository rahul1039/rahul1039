name: Update profile README

on:
  schedule:
    - cron: "17 3 * * *"   # daily, 03:17 UTC
  workflow_dispatch:
  push:
    paths:
      - scripts/update_readme.py
      - .github/workflows/update-readme.yml

permissions:
  contents: write

concurrency:
  group: update-readme
  cancel-in-progress: false

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Generate AUTO-GENERATED section
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          GH_USER: ${{ github.repository_owner }}
        run: python scripts/update_readme.py

      - name: Commit if changed
        run: |
          if git diff --quiet -- README.md; then
            echo "Nothing to commit"; exit 0
          fi
          git config user.name  "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
          git add README.md
          git commit -m "chore: update auto-generated profile section"
          git push
