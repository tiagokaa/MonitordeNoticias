"""
Neutramol BI Pipeline — CLI entry point.

Usage:
  python main.py init                  # seed device registry
  python main.py sync-latest           # fetch current values
  python main.py sync-history          # fetch history (incremental)
  python main.py sync-alarms           # fetch alarms
  python main.py sync-all              # run all three syncs
  python main.py schedule --interval 5 # run sync-all every N minutes
"""

import logging
import os
import sys
import time
from pathlib import Path

import click
import schedule
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger("main")


def _get_client():
    from tb_client import ThingsBoardClient

    url = os.environ.get("TB_URL", "https://mhocloud.com")
    username = os.environ.get("TB_USERNAME", "")
    password = os.environ.get("TB_PASSWORD", "")

    if not username or not password:
        click.echo("❌  TB_USERNAME e TB_PASSWORD devem estar definidos no .env", err=True)
        sys.exit(1)

    return ThingsBoardClient(url, username, password)


def _get_conn():
    from database import connect

    db_path = Path(os.environ.get("DB_PATH", "neutramol.db"))
    return connect(db_path)


@click.group()
def cli():
    """Neutramol BI Pipeline — sincroniza dados do ThingsBoard para SQLite."""


@cli.command()
def init():
    """Cria o banco e registra dispositivos e chaves."""
    conn = _get_conn()
    from pipeline import seed_registry
    seed_registry(conn)
    conn.close()
    click.echo("✅  Banco inicializado e registry carregado.")


@cli.command("sync-latest")
def sync_latest():
    """Busca os valores mais recentes de todos os dispositivos."""
    client = _get_client()
    conn = _get_conn()
    from pipeline import sync_latest as _sync
    _sync(client, conn)
    conn.close()
    click.echo("✅  Latest values sincronizados.")


@cli.command("sync-history")
@click.option("--days", default=None, type=int, help="Dias de histórico na 1ª execução (padrão: HISTORY_DAYS do .env ou 30)")
def sync_history(days):
    """Busca o histórico de telemetria (incremental)."""
    client = _get_client()
    conn = _get_conn()
    history_days = days or int(os.environ.get("HISTORY_DAYS", 30))
    from pipeline import sync_history as _sync
    _sync(client, conn, history_days=history_days)
    conn.close()
    click.echo("✅  Histórico sincronizado.")


@cli.command("sync-alarms")
def sync_alarms():
    """Busca todos os alarmes de todos os dispositivos."""
    client = _get_client()
    conn = _get_conn()
    from pipeline import sync_alarms as _sync
    _sync(client, conn)
    conn.close()
    click.echo("✅  Alarmes sincronizados.")


@cli.command("sync-all")
@click.option("--days", default=None, type=int, help="Dias de histórico na 1ª execução")
def sync_all(days):
    """Executa todos os syncs: latest, history e alarms."""
    client = _get_client()
    conn = _get_conn()
    history_days = days or int(os.environ.get("HISTORY_DAYS", 30))

    from pipeline import seed_registry, sync_alarms, sync_history, sync_latest
    seed_registry(conn)
    sync_latest(client, conn)
    sync_history(client, conn, history_days=history_days)
    sync_alarms(client, conn)
    conn.close()
    click.echo("✅  Sync completo.")


@cli.command()
@click.option("--interval", default=5, show_default=True, help="Intervalo entre sincronizações (minutos)")
@click.option("--days", default=None, type=int, help="Dias de histórico na 1ª execução")
def scheduler(interval, days):
    """Executa sync-all repetidamente em loop (ideal para rodar como serviço)."""
    click.echo(f"⏰  Scheduler iniciado — sync a cada {interval} minuto(s). Ctrl+C para parar.")

    def _run():
        client = _get_client()
        conn = _get_conn()
        history_days = days or int(os.environ.get("HISTORY_DAYS", 30))
        from pipeline import sync_alarms, sync_history, sync_latest
        sync_latest(client, conn)
        sync_history(client, conn, history_days=history_days)
        sync_alarms(client, conn)
        conn.close()

    # Run immediately on start, then on schedule
    _run()
    schedule.every(interval).minutes.do(_run)

    try:
        while True:
            schedule.run_pending()
            time.sleep(10)
    except KeyboardInterrupt:
        click.echo("\n🛑  Scheduler encerrado.")


if __name__ == "__main__":
    cli()
