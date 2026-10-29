# PR Review — Tech Stack Detection

Extension→stack lookup and EC-Cube detection — loaded at Step 4 (Detect Tech Stack), once, to set `TECH_STACK` and `IS_ECCUBE`. Do not load earlier.

Auto-detect from changed file extensions:

| Extension | Stack |
|---|---|
| `.php` | PHP |
| `.twig` | Twig templates |
| `.js` / `.ts` | JavaScript / TypeScript |
| `.yaml` / `.yml` | Configuration |
| `.sql` | Database scripts |
| `.css` / `.scss` | Stylesheets |
| `.py` | Python |
| `.java` | Java |
| `.go` | Go |

## EC-Cube Detection

If the PR is from the same repository (`bjit-inc/mrmax` or the current repo's remote):

```
TECH_STACK: PHP 8.0+, Symfony 4/5, EC-Cube 4.x, Doctrine ORM, Twig, MySQL 8.0+
IS_ECCUBE: true
```

Otherwise, build `TECH_STACK` from detected extensions and set `IS_ECCUBE: false`.
When `IS_ECCUBE` is false, omit EC-Cube-specific rules from agent prompts.
