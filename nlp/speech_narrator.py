"""
DataToSpeechNarrator — Tabular-to-Verbal Synthesis Pipeline
Converts structured database results and security evaluation outcomes into concise,
executive-level spoken narratives for zero-cost Text-to-Speech (TTS) streaming.
Prevents cognitive auditory overload by distilling key metrics and dimensions.
"""

from typing import List, Dict, Any, Optional
import re


class DataToSpeechNarrator:
    @staticmethod
    def construct_verbal_summary(
        intent_prompt: str,
        columns: List[str],
        records: List[Dict[str, Any]],
        error: Optional[str] = None
    ) -> str:
        """
        Transforms relational datasets or security violations into concise
        executive summaries suitable for voice output.
        """
        if error:
            # Spoken security / error notification
            clean_err = error.replace("Query blocked:", "").replace("Policy Violation:", "").strip()
            return f"Access Notice: The database engine halted query execution. Reason: {clean_err}"

        if not records or len(records) == 0:
            return "The database query executed successfully, but identified zero matching records."

        record_count = len(records)
        primary_col = columns[0] if columns else "item"
        lowered_intent = (intent_prompt or "").lower()

        # 1. Ranking, ordering, top / lowest intents
        ranking_keywords = ["top", "worst", "underperforming", "highest", "lowest", "best", "rank", "max", "min", "leader"]
        if any(term in lowered_intent for term in ranking_keywords):
            top_records = records[:3]
            formatted_points = []
            for item in top_records:
                entity_label = str(item.get(primary_col, "Record"))
                # Find the primary numeric metric for context
                metric_val = None
                for col in columns[1:]:
                    val = item.get(col)
                    if isinstance(val, (int, float)) or (isinstance(val, str) and re.match(r"^-?\d+(\.\d+)?$", val)):
                        metric_val = f"{col.replace('_', ' ')} of {val}"
                        break
                if metric_val:
                    formatted_points.append(f"{entity_label} with {metric_val}")
                else:
                    formatted_points.append(entity_label)

            joined_points = "; ".join(formatted_points)
            return (
                f"Retrieved {record_count} records. The primary findings indicate: {joined_points}."
            )

        # 2. Averages, aggregates, metrics
        if any(term in lowered_intent for term in ["average", "avg", "mean", "total", "sum", "rate", "percentage", "count"]):
            first_row = records[0]
            entity = first_row.get(primary_col, "All entities")
            numeric_metrics = []
            for col in columns:
                val = first_row.get(col)
                if isinstance(val, (int, float)) or (isinstance(val, str) and re.match(r"^-?\d+(\.\d+)?$", val)):
                    numeric_metrics.append(f"{col.replace('_', ' ')} is {val}")

            if numeric_metrics:
                metric_str = ", ".join(numeric_metrics[:2])
                if record_count == 1:
                    return f"The analytical result for {entity} shows: {metric_str}."
                return (
                    f"Analyzed {record_count} records. The primary aggregate indicates: "
                    f"{entity} with {metric_str}."
                )

        # 3. Defaulter or attendance queries
        if any(term in lowered_intent for term in ["defaulter", "attendance", "absent", "threshold"]):
            names = [str(r.get(primary_col, "student")) for r in records[:4]]
            joined_names = ", ".join(names)
            return (
                f"Identified {record_count} records meeting the attendance criteria. "
                f"Flagged records include: {joined_names}."
            )

        # 4. Standard listing / exploratory query
        first_entry = records[0].get(primary_col, "Record")
        if record_count == 1:
            return f"Query returned 1 record: {first_entry}."
        elif record_count <= 5:
            all_labels = ", ".join(str(r.get(primary_col, "Record")) for r in records)
            return f"Found {record_count} records: {all_labels}."
        else:
            return (
                f"Query completed successfully. Retrieved {record_count} records. "
                f"The lead entry is {first_entry}."
            )
