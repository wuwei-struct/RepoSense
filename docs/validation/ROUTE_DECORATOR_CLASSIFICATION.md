# NestJS Route Decorator Classification

RepoSense classifies TypeScript and NestJS decorators before creating canonical code-route facts. This prevents property, parameter, persistence, validation, and documentation decorators from becoming API endpoints merely because their names share an HTTP verb prefix.

## Why Exact Classification Is Required

A prefix expression such as `@(Delete...)` can truncate `@DeleteDateColumn()` to `Delete`. If that result is treated as a route, the false endpoint can propagate into Permission Auditor, Guard Correlation, inferred AuthZ Matrix output, Repository Review, and Human Review Required.

RepoSense therefore accepts only these exact, case-sensitive NestJS route symbols:

- `Get`
- `Post`
- `Put`
- `Patch`
- `Delete`
- `Options`
- `Head`
- `All`

`Controller` is the only class-level route container decorator recognized by this classifier. Similar names such as `DeleteDateColumn`, `GetUser`, and `PostConstruct` are not routes.

## Syntax Context

Each inspected candidate is classified as one of:

- `class`
- `method`
- `property`
- `parameter`
- `unknown`

A canonical NestJS route requires both:

1. an exact route decorator symbol; and
2. a class-method target.

`Controller` is accepted only on a class and supplies the Controller prefix when present. Some static fixtures and partially extracted sources may expose an exact method decorator without a resolved Controller decorator; these remain class-method route facts with an empty prefix. Property and parameter decorators never become routes. An unresolved target is recorded as `unknown` and does not produce a confirmed route.

The implementation is a conservative lexical classifier. It supports decorator stacks, no-argument decorators, quoted path arguments, multiline decorator arguments, Controller prefixes, and multiple decorators on a method. It is not a complete TypeScript AST or type system.

## Canonical Route Facts

The shared classifier feeds:

- the TypeScript detector and `api_surface.json`;
- Permission Auditor source routes;
- NestJS Guard Correlation;
- Route Intent and inferred AuthZ Matrix through Permission Surface;
- Repository Review and Human Review Required.

OpenAPI-only routes remain separate contract/documentation facts with `openapi_only` correlation status. A rejected TypeScript decorator cannot be recreated as a code route downstream.

## Diagnostic Artifacts

Runs can include:

- `route_decorator_classifications.json`
- `route_decorator_summary.json`

Each classification records a stable ID, repository-relative file, positive source line, exact decorator name, syntax context, classification, reason, evidence references, and limitations.

The summary reports:

- candidates inspected;
- accepted routes;
- Controller decorators;
- rejected non-routes;
- unresolved candidates;
- rejected counts by decorator symbol.

Run Manifest records these files as `route_decorator_classification`. Context Pack copies them to `ARTIFACTS/` and adds MAP entries when present.

## Boundaries

- Classification proves only that a decorator is or is not a canonical route fact under the supported syntax.
- It does not prove route correctness, authentication, authorization, or runtime reachability.
- Aliased, computed, or dynamically constructed decorators may remain unresolved.
- Unknown contexts are not promoted to routes.
- OpenAPI security remains contract evidence, not code Guard proof.
- RepoSense does not execute repository code.
