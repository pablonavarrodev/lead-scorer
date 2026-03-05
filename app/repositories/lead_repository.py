
import json
import sqlite3
from typing import Any, Dict, List, Optional

from app.core.config import DB_PATH

#MAS ALANTE REVISAR SQLModel PARA EVITAR ESCRIBIR SQL

def get_connection() -> sqlite3.Connection:
    print("DB_PATH =", DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    #row factori para que devuelva diccionarios en vez de tuplas
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:

#with es para que haga commit y rollback automatico
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS leads_enriched (
                id INTEGER PRIMARY KEY,
                nombre TEXT NOT NULL,
                empresa TEXT NOT NULL,
                sector TEXT NOT NULL,
                score INTEGER NOT NULL,
                interes INTEGER NOT NULL,
                enriched_json TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP),
                updated_at TEXT NOT NULL DEFAULT (CURRENT_TIMESTAMP)
            );
        """)
        conn.commit()


def save_enriched_lead(enriched: Dict[str, Any], status: str = "ok") -> None:
    lead = enriched["lead"]

    lead_id = int(lead["id"])
    nombre = str(lead["nombre"])
    empresa = str(lead["empresa"])
    sector = str(lead["sector"])
    score = int(enriched["rule_score"])
    interes = int(lead["interes"])

    enriched_json = json.dumps(enriched, ensure_ascii=False)

    with get_connection() as conn:
        conn.execute("""
            INSERT INTO leads_enriched (
                id, nombre, empresa, sector, score, interes, enriched_json, status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                nombre=excluded.nombre,
                empresa=excluded.empresa,
                sector=excluded.sector,
                score=excluded.score,
                interes=excluded.interes,
                enriched_json=excluded.enriched_json,
                status=excluded.status,
                updated_at=CURRENT_TIMESTAMP;
        """, (lead_id, nombre, empresa, sector, score, interes, enriched_json, status))
        conn.commit()


def get_enriched_lead_by_id(lead_id: int) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        cur = conn.execute("""
            SELECT *
            FROM leads_enriched
            WHERE id = ?;
        """, (lead_id,))
        row = cur.fetchone()

    if row is None:
        return None

    return {
        "id": row["id"],
        "nombre": row["nombre"],
        "empresa": row["empresa"],
        "sector": row["sector"],
        "score": row["score"],
        "interes": row["interes"],
        "status": row["status"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "enriched": json.loads(row["enriched_json"]),
    }


def get_leads_enriched() -> List[Dict[str, Any]]:
    with get_connection() as conn:
        cur = conn.execute("""
            SELECT *
            FROM leads_enriched
            ORDER BY updated_at DESC;
        """)
        rows = cur.fetchall()

    result = []
    for r in rows:
        result.append({
            "id": r["id"],
            "nombre": r["nombre"],
            "empresa": r["empresa"],
            "sector": r["sector"],
            "score": r["score"],
            "interes": r["interes"],
            "status": r["status"],
            "created_at": r["created_at"],
            "updated_at": r["updated_at"],
            "enriched": json.loads(r["enriched_json"]),
        })

    return result