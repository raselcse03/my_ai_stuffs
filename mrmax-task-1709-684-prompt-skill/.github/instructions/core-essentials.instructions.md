---
applyTo: "app/Customize/**,app/Plugin/**,app/config/**,app/template/**"
---

# EC-Cube Core Essentials (Auto-Loaded)

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
✅ app/Customize/       → Custom business logic
✅ app/Plugin/          → Plugin system
✅ app/config/          → Configuration
✅ app/template/        → Frontend templates (Twig)
❌ src/Eccube/          → Core (NEVER modify)
❌ app/DoctrineMigrations/ → Migrations (NEVER generate)
```

## Naming Conventions

- **Services:** `{Entity}Service` → `OrderService`
- **Repositories:** `{Entity}Repository` → `OrderRepository`
- **Controllers:** `{Feature}Controller` → `CheckoutController`
- **Forms:** `{Entity}Type` → `ProductType`
- **Namespacing:** `Customize\{Layer}\{Feature}`
