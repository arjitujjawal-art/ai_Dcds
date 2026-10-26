"""
Deterministic AST Governance & Dynamic Role-Based Access Control (RBAC) Gateway
Enforces zero-trust query security via Abstract Syntax Tree (AST) validation using sqlglot.
Rejects non-SELECT expressions, validates physical table entitlements by role,
and injects deterministic row ceilings to prevent resource-depletion denial of service.
"""

from typing import Dict, List, Set, Tuple, Optional
import re
import sqlglot
from sqlglot import exp


class AccessControlViolation(Exception):
    """Raised when an unapproved table, column, or statement type occurs within the AST."""
    pass


# Default role-based entity entitlements
ROLE_ENTITLEMENTS: Dict[str, Dict[str, List[str]]] = {
    "student": {
        "students": ["student_id", "name", "division", "email"],
        "subjects": ["subject_id", "subject_name", "credits"],
        "marks": ["mark_id", "student_id", "subject_id", "marks"],
        "attendance": ["attendance_id", "student_id", "subject_id", "attendance_percentage"],
    },
    "teacher": {
        "students": ["*"],
        "subjects": ["*"],
        "marks": ["*"],
        "attendance": ["*"],
        # Custom dataset tables are dynamically permitted for teachers and admins
    },
    "admin": {
        "*": ["*"],  # Full access to enterprise schemas
    }
}

FORBIDDEN_COLUMNS: Set[str] = {"password_hash", "password", "secret", "token", "auth_token"}


class DeterministicSQLGateway:
    def __init__(self, dialect: str = "sqlite"):
        self.dialect = dialect

    def parse_and_enforce(
        self,
        candidate_sql: str,
        user_role: str,
        custom_allowed_tables: Optional[Set[str]] = None,
        row_ceiling: int = 50
    ) -> Tuple[bool, str, str]:
        """
        Parses SQL statements into syntax trees to enforce deterministic RBAC.
        Validates statement types, confirms entity entitlements, and injects row limits.

        Returns: (is_valid: bool, sanitized_sql_or_candidate: str, reason: str)
        """
        if not candidate_sql or not candidate_sql.strip():
            return False, candidate_sql, "Empty query received."

        # Pre-check for raw disallowed characters/multi-statements
        if ";" in candidate_sql.strip().rstrip(";"):
            return False, candidate_sql, "Policy Violation: Multiple statements or batch execution blocked."

        if "--" in candidate_sql or "/*" in candidate_sql or "*/" in candidate_sql:
            return False, candidate_sql, "Policy Violation: SQL comments are blocked."

        # 1. Parse AST with sqlglot
        try:
            parsed_statements = sqlglot.parse(candidate_sql, read=self.dialect)
        except Exception as exc:
            return False, candidate_sql, f"AST Syntax Parse Failure: {str(exc)}"

        if len(parsed_statements) != 1 or parsed_statements[0] is None:
            return False, candidate_sql, "Policy Violation: Multiple statements or batch execution blocked."

        syntax_tree = parsed_statements[0]

        # 2. Verify root expression is strictly SELECT
        if not isinstance(syntax_tree, exp.Select):
            stmt_type = getattr(syntax_tree, "key", "UNKNOWN").upper()
            return False, candidate_sql, f"Policy Violation: Statement type '{stmt_type}' unauthorized. Only SELECT permitted."

        # 3. Enumerate physical tables and validate against role entitlements
        queried_tables: Set[str] = {
            tbl.name.lower() for tbl in syntax_tree.find_all(exp.Table) if tbl.name
        }

        # Determine permitted tables for user role
        role_rules = ROLE_ENTITLEMENTS.get(user_role, {})
        if "*" in role_rules:
            permitted_tables = None  # Admin has wildcard access to all tables
        else:
            permitted_tables = set(role_rules.keys())
            if custom_allowed_tables:
                permitted_tables.update(tbl.lower() for tbl in custom_allowed_tables)

        if permitted_tables is not None:
            unauthorized_tables = queried_tables - permitted_tables
            if unauthorized_tables:
                return (
                    False,
                    candidate_sql,
                    f"RBAC Rejection: Role '{user_role}' denied access to table(s): {', '.join(sorted(unauthorized_tables))}."
                )

        # 4. Enforce column-level restrictions (e.g. passwords/tokens)
        queried_columns = {col.name.lower() for col in syntax_tree.find_all(exp.Column) if col.name}
        blocked_cols = queried_columns & FORBIDDEN_COLUMNS
        if blocked_cols:
            return (
                False,
                candidate_sql,
                f"Data Masking Violation: Access to confidential column(s) '{', '.join(sorted(blocked_cols))}' is forbidden."
            )

        # 5. Deterministic row ceiling injection
        # If no LIMIT clause exists in the AST, inject a safe ceiling
        if not syntax_tree.args.get("limit"):
            syntax_tree = syntax_tree.limit(row_ceiling)

        sanitized_sql = syntax_tree.sql(dialect=self.dialect)
        return True, sanitized_sql, "OK"


# Global gateway instance
_gateway = DeterministicSQLGateway(dialect="sqlite")


def validate_sql(
    sql: str,
    user_role: str = "student",
    custom_allowed_tables: Optional[Set[str]] = None,
    row_ceiling: int = 50
) -> dict:
    """
    Standard interface wrapping DeterministicSQLGateway.
    Maintains compatibility with existing app handlers while providing
    full AST inspection and automatic LIMIT injection.
    """
    is_valid, sanitized_sql, reason = _gateway.parse_and_enforce(
        candidate_sql=sql,
        user_role=user_role,
        custom_allowed_tables=custom_allowed_tables,
        row_ceiling=row_ceiling
    )
    return {
        "valid": is_valid,
        "reason": reason,
        "sanitized_sql": sanitized_sql if is_valid else None
    }
