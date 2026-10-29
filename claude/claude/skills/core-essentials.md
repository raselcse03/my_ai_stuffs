---
name: "Core Essentials"
role: "Critical rules and key directories — auto-loaded every task"
scope: "app/Customize/"
description: "Critical rules and key directories — auto-loaded every task"
---

# EC-Cube Core Essentials

## Critical Rules (NEVER VIOLATE)

1. ❌ **NEVER modify `src/Eccube/`** → Use `app/Customize/` or Plugin
2. ❌ **NEVER generate or run Doctrine migrations** → Use manual SQL scripts
3. ✅ **ALWAYS use dependency injection** → No `new` keyword for services
4. ✅ **ALWAYS clear cache after config changes** → `bin/console cache:clear`
5. ✅ **ALWAYS use parameterized queries** → No SQL concatenation
6. ✅ **ALWAYS validate user input** → Symfony Form validation
7. ✅ **ALWAYS use transactions** → Multi-step DB operations

## Key Directories

```
✅ app/Customize/       → Custom business logic (Entity, Service, Controller, Form, EventListener)
✅ app/Plugin/          → Plugin system
✅ app/config/          → Configuration (services.yaml, routes/)
✅ app/template/        → Frontend templates (Twig)
❌ src/Eccube/          → Core (NEVER modify)
❌ app/DoctrineMigrations/ → Migrations (NEVER generate)
```

## Request Flow

```
index.php → Kernel → Routing → Controller → Service → Repository → Database
                                    ↓
                                 Twig Template → Response
```

## Naming Conventions

- **Services:** `{Entity}Service` → `OrderService`
- **Repositories:** `{Entity}Repository` → `OrderRepository`
- **Controllers:** `{Feature}Controller` → `CheckoutController`
- **Forms:** `{Entity}Type` → `ProductType`
- **Namespacing:** `Customize\{Layer}\{Feature}`

## Validation Commands

```bash
bin/console cache:clear
bin/phpunit
vendor/bin/phpstan analyze app/Customize/
```

## When You Need More

For AWS architecture, edge cases, business logic patterns, and full coding standards → read `core-full.md`.
