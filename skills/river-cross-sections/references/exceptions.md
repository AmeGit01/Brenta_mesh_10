# Exceptions

A violation of a rule that cannot be removed without breaking a more important rule can be accepted by the **user** as an exception. Claude never accepts an exception on its own.

## Procedure

1. **Report the violation.** Name the section or pair, the measured value, the cause, and what fixing it would break. For example: "N16000: crossings 3.13 m from those of nodestring `check_portata`, which must not move".
2. **Propose a fix** if one exists, for example moving the section or editing a line. Propose the exception only as an alternative.
3. **Ask the user.** Exceptions can be grouped in one question, but each needs its own yes.
4. **Record each accepted exception** in `rcs_config.json` → `exceptions`, with the section or pair, the reason and the date. The configuration is the **only** place where exceptions are defined, and every check reads them from there.
5. **Copy the list** into the exceptions table of `docs/rules.md`, and log the decision in `docs/workflow.md`.
6. **Run the checks again.** The violations must coincide exactly with the exceptions, and the checks must say `OK`.

## Categories

| Key | Rule | Typical cause |
|---|---|---|
| `near_node` | Near-node rule: a breakline vertex within R of a crossing | Another nodestring that cannot move is close to the section; a node shared by several lines; a manual edit by the user |
| `locked_line` | Near-node rule where the near vertex belongs to a locked line (wall) | Sections among buildings or walls |
| `spacing` | Spacing outside `spacing ± tol` between two consecutive sections (along the centerline or straight) | A tight bend (the chord is shorter); a section moved by hand; a few millimetres over the limit after a manual edit |
| `angle` | An angle sharper than `min_angle_deg` created by an edit | A section that must cross an oblique line, a constrained junction |

A spacing pair is excluded from the spacing checks when either of its two sections is listed.

## When an exception expires

An exception expires when its violation disappears, for example after the user fixes the line. Remove it, because an exception without a violation hides nothing and confuses the record. The checks report exceptions that no longer match a violation.

Even violations of a few millimetres must be reported and proposed. Never round them away.
