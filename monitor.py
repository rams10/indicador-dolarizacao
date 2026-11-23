"""Atualiza o indicador diário de queda do dólar usando a série SGS 1 do BCB."""
from __future__ import annotations

import datetime as dt
import json
import pathlib
from zoneinfo import ZoneInfo

import httpx

TZ = ZoneInfo("America/Sao_Paulo")
ROOT = pathlib.Path(__file__).resolve().parent
DATA_FILE = ROOT / "docs" / "data.json"
BCB_URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.1/dados"
SERIES_CODE = 1
HISTORY_DAYS = 740
DISPLAY_DAYS = 365
THRESHOLD_PCT = 5.0


def one_year_before(day: dt.date) -> dt.date:
    """Subtrai 12 meses de calendário, preservando o dia quando possível."""
    try:
        return day.replace(year=day.year - 1)
    except ValueError:
        return day.replace(year=day.year - 1, month=2, day=28)


def parse_bcb_rows(payload: list[dict]) -> list[tuple[dt.date, float]]:
    rows: list[tuple[dt.date, float]] = []
    for item in payload:
        day = dt.datetime.strptime(item["data"], "%d/%m/%Y").date()
        value = float(str(item["valor"]).replace(",", "."))
        if value > 0:
            rows.append((day, value))
    by_day = {day: value for day, value in rows}
    return sorted(by_day.items())


def build_payload(rows: list[tuple[dt.date, float]], now: dt.datetime) -> dict:
    if not rows:
        raise RuntimeError("O Banco Central não retornou cotações para o período consultado.")

    rows = sorted(rows)
    display_start = now.date() - dt.timedelta(days=DISPLAY_DAYS)

    # Um ponto por observação diária publicada pelo Banco Central.
    history = []
    for day, daily_close in rows:
        if day < display_start:
            continue
        window_start = one_year_before(day)
        window = [value for obs_day, value in rows if window_start <= obs_day <= day]
        if not window:
            continue
        maximum = max(window)
        decline = max(0.0, (1.0 - daily_close / maximum) * 100.0)
        history.append({
            "date": day.isoformat(),
            "close": round(daily_close, 4),
            "max_12m": round(maximum, 4),
            "drop_pct": round(decline, 4),
        })

    if not history:
        raise RuntimeError("Não foi possível montar o histórico semanal do dólar.")

    latest = history[-1]
    return {
        "updated_at": now.isoformat(),
        "source": {
            "name": "Banco Central do Brasil — SGS série 1",
            "description": "Taxa de câmbio livre: dólar americano (venda), frequência diária",
            "series_code": SERIES_CODE,
            "url": "https://dadosabertos.bcb.gov.br/dataset/1-taxa-de-cambio---livre---dolar-americano-venda---diario",
        },
        "method": {
            "daily_close": "Cada observação diária publicada pelo Banco Central",
            "rolling_max": "Maior fechamento diário nos 12 meses anteriores à data do fechamento semanal, inclusive",
            "formula": "(1 - fechamento_semanal / maior_fechamento_diario_12m) * 100",
            "threshold_pct": THRESHOLD_PCT,
        },
        "latest": latest,
        "history": history[-400:],
    }


def fetch_daily(start: dt.date, end: dt.date) -> list[tuple[dt.date, float]]:
    params = {
        "formato": "json",
        "dataInicial": start.strftime("%d/%m/%Y"),
        "dataFinal": end.strftime("%d/%m/%Y"),
    }
    headers = {"Accept": "application/json", "User-Agent": "indicador-dolarizacao/1.0"}
    with httpx.Client(timeout=40.0, headers=headers, follow_redirects=True) as client:
        response = client.get(BCB_URL, params=params)
        response.raise_for_status()
        payload = response.json()
    if not isinstance(payload, list):
        raise RuntimeError(f"Resposta inesperada do Banco Central: {str(payload)[:250]}")
    return parse_bcb_rows(payload)


def main() -> None:
    now = dt.datetime.now(TZ)
    end = now.date()
    start = end - dt.timedelta(days=HISTORY_DAYS)
    rows = fetch_daily(start, end)
    result = build_payload(rows, now)

    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    temporary = DATA_FILE.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(DATA_FILE)

    latest = result["latest"]
    print(json.dumps({
        "date": latest["date"],
        "daily_close": latest["close"],
        "max_12m": latest["max_12m"],
        "drop_pct": latest["drop_pct"],
        "threshold_reached": latest["drop_pct"] >= THRESHOLD_PCT,
        "history_points": len(result["history"]),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
