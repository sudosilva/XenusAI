"""
XenusAI — Interactive CLI
Rich command-line interface for ingesting knowledge and asking questions.

Usage:
    python -m interface.cli
"""

import sys
import logging
from typing import Optional

# ─── Setup logging before imports ──────────────────────────────
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown
from rich.text import Text
from rich.prompt import Prompt
from rich import box

console = Console()

# ─── Banner ────────────────────────────────────────────────────

BANNER = r"""
[bold cyan]
 ██╗  ██╗███████╗███╗   ██╗██╗   ██╗███████╗     █████╗ ██╗
 ╚██╗██╔╝██╔════╝████╗  ██║██║   ██║██╔════╝    ██╔══██╗██║
  ╚███╔╝ █████╗  ██╔██╗ ██║██║   ██║███████╗    ███████║██║
  ██╔██╗ ██╔══╝  ██║╚██╗██║██║   ██║╚════██║    ██╔══██║██║
 ██╔╝ ██╗███████╗██║ ╚████║╚██████╔╝███████║    ██║  ██║██║
 ╚═╝  ╚═╝╚══════╝╚═╝  ╚═══╝ ╚═════╝ ╚══════╝    ╚═╝  ╚═╝╚═╝
[/bold cyan]
[dim]  Private Local Knowledge System — v1.0[/dim]
"""

HELP_TEXT = """
[bold]Commands:[/bold]

  [cyan]/ingest <url_or_path>[/cyan]    Ingest a URL, file, or folder into the knowledge base
  [cyan]/search <query>[/cyan]          Search the knowledge base (raw results)
  [cyan]/ask <question>[/cyan]          Ask a question (retrieval + LLM)
  [cyan]/stats[/cyan]                   Show knowledge base statistics
  [cyan]/sources[/cyan]                 List all ingested sources
  [cyan]/delete <source>[/cyan]         Delete a source from the knowledge base
  [cyan]/reset[/cyan]                   Reset the entire knowledge base (⚠️ destructive)
  [cyan]/model <name>[/cyan]            Switch LLM model (e.g., /model llama3)
  [cyan]/models[/cyan]                  List available Ollama models
  [cyan]/help[/cyan]                    Show this help message
  [cyan]/quit[/cyan]                    Exit XenusAI

[dim]Or just type a question directly to ask with retrieval.[/dim]
"""


def cmd_ingest(args: str):
    """Handle /ingest command."""
    if not args.strip():
        console.print("[yellow]Usage: /ingest <url_or_path>[/yellow]")
        return

    from pipelines.ingest import ingest

    try:
        with console.status("[bold green]Ingesting...[/bold green]"):
            result = ingest(args.strip(), verbose=False)

        if result.get("status") == "success":
            table = Table(title="Ingestion Complete ✅", box=box.ROUNDED)
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")
            table.add_row("Source", str(result.get("source", "")))
            table.add_row("Documents", str(result.get("documents_processed", 0)))
            table.add_row("Tokens", f"{result.get('total_tokens', 0):,}")
            table.add_row("Chunks Stored", str(result.get("chunks_stored", 0)))
            table.add_row("Time", f"{result.get('elapsed_seconds', 0):.1f}s")
            table.add_row("KB Total", str(result.get("knowledge_base_total", 0)))
            console.print(table)
        else:
            console.print(f"[red]❌ Error: {result.get('message', 'Unknown error')}[/red]")

    except Exception as e:
        console.print(f"[red]❌ Ingestion failed: {e}[/red]")


def cmd_search(args: str):
    """Handle /search command."""
    if not args.strip():
        console.print("[yellow]Usage: /search <query>[/yellow]")
        return

    from retrieval.search import search

    try:
        with console.status("[bold green]Searching...[/bold green]"):
            results = search(args.strip())

        if not results:
            console.print("[yellow]No results found. Try ingesting some data first![/yellow]")
            return

        for i, result in enumerate(results, 1):
            score = result["score"]
            source = result["source"]
            title = result.get("title", "")
            text = result["document"]

            # Color-code by relevance
            if score >= 0.7:
                score_color = "green"
            elif score >= 0.4:
                score_color = "yellow"
            else:
                score_color = "red"

            header = f"[bold]Result {i}[/bold] [{score_color}]({score:.0%} match)[/{score_color}]"
            if title:
                header += f" — {title}"

            panel = Panel(
                Text(text[:500] + ("..." if len(text) > 500 else ""), style="white"),
                title=header,
                subtitle=f"[dim]{source}[/dim]",
                border_style="cyan",
                box=box.ROUNDED,
            )
            console.print(panel)

    except Exception as e:
        console.print(f"[red]❌ Search failed: {e}[/red]")


def cmd_ask(args: str):
    """Handle /ask command or direct questions."""
    if not args.strip():
        console.print("[yellow]Usage: /ask <question>[/yellow]")
        return

    from retrieval.search import search, get_context
    from retrieval.llm import ask, _check_ollama_available

    question = args.strip()

    # Step 1: Retrieve context
    with console.status("[bold green]Searching knowledge base...[/bold green]"):
        results = search(question)
        context = get_context(question)

    if results:
        console.print(f"[dim]Found {len(results)} relevant chunks. Generating answer...[/dim]\n")

        # Show sources
        sources = list(set(r["source"] for r in results))
        source_list = ", ".join(f"[cyan]{s}[/cyan]" for s in sources[:3])
        console.print(f"[dim]Sources: {source_list}[/dim]\n")
    else:
        console.print("[yellow]No knowledge base results. Asking LLM directly...[/yellow]\n")
        context = None

    # Step 2: Generate answer
    if _check_ollama_available():
        console.print("[bold green]XenusAI:[/bold green] ", end="")
        answer = ask(question, context=context, stream=True)
        console.print()  # newline after streaming
    else:
        console.print(
            Panel(
                "[yellow]Ollama is not running.[/yellow]\n\n"
                "Install: [cyan]https://ollama.com/download[/cyan]\n"
                "Start:   [cyan]ollama serve[/cyan]\n"
                "Pull:    [cyan]ollama pull mistral[/cyan]\n\n"
                "[dim]Showing raw search results instead:[/dim]",
                title="⚠️ LLM Not Available",
                border_style="yellow",
            )
        )
        # Fall back to showing search results
        if results:
            for r in results[:3]:
                console.print(f"\n[cyan]{r.get('title', r['source'])}[/cyan]")
                console.print(r["document"][:300])


def cmd_stats():
    """Handle /stats command."""
    from pipelines.embedder import get_stats

    stats = get_stats()

    table = Table(title="📊 Knowledge Base Statistics", box=box.ROUNDED)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    table.add_row("Total Chunks", str(stats["total_chunks"]))
    table.add_row("Unique Sources", str(stats["unique_sources"]))
    table.add_row("Collection", stats["collection_name"])
    console.print(table)


def cmd_sources():
    """Handle /sources command."""
    from pipelines.embedder import get_stats

    stats = get_stats()

    if not stats["sources"]:
        console.print("[yellow]No sources ingested yet.[/yellow]")
        return

    table = Table(title="📚 Ingested Sources", box=box.ROUNDED)
    table.add_column("#", style="dim")
    table.add_column("Source", style="cyan")

    for i, source in enumerate(stats["sources"], 1):
        table.add_row(str(i), source)

    console.print(table)


def cmd_delete(args: str):
    """Handle /delete command."""
    if not args.strip():
        console.print("[yellow]Usage: /delete <source>[/yellow]")
        return

    from pipelines.embedder import delete_source

    source = args.strip()
    confirm = Prompt.ask(
        f"[red]Delete all chunks from '{source}'?[/red]",
        choices=["y", "n"],
        default="n",
    )

    if confirm == "y":
        count = delete_source(source)
        console.print(f"[green]Deleted {count} chunks from: {source}[/green]")
    else:
        console.print("[dim]Cancelled.[/dim]")


def cmd_reset():
    """Handle /reset command."""
    from pipelines.embedder import reset_collection

    confirm = Prompt.ask(
        "[red bold]⚠️ This will DELETE ALL data in the knowledge base. Continue?[/red bold]",
        choices=["y", "n"],
        default="n",
    )

    if confirm == "y":
        reset_collection()
        console.print("[green]Knowledge base has been reset.[/green]")
    else:
        console.print("[dim]Cancelled.[/dim]")


def cmd_models():
    """Handle /models command."""
    from retrieval.llm import list_models

    models = list_models()

    if not models:
        console.print(
            "[yellow]No models found. Is Ollama running?[/yellow]\n"
            "  Install: [cyan]https://ollama.com/download[/cyan]\n"
            "  Start:   [cyan]ollama serve[/cyan]\n"
            "  Pull:    [cyan]ollama pull mistral[/cyan]"
        )
        return

    table = Table(title="🤖 Available Models", box=box.ROUNDED)
    table.add_column("#", style="dim")
    table.add_column("Model", style="cyan")

    for i, model in enumerate(models, 1):
        table.add_row(str(i), model)

    console.print(table)


def cmd_model(args: str):
    """Handle /model command."""
    if not args.strip():
        from config import LLM_MODEL
        console.print(f"Current model: [cyan]{LLM_MODEL}[/cyan]")
        console.print("Usage: [cyan]/model <name>[/cyan]")
        return

    import config
    config.LLM_MODEL = args.strip()
    console.print(f"[green]Model switched to: {config.LLM_MODEL}[/green]")


# ─── Main Loop ─────────────────────────────────────────────────

def main():
    """Main CLI entry point."""
    console.print(BANNER)
    console.print(
        Panel(
            HELP_TEXT,
            title="[bold]Quick Start[/bold]",
            border_style="cyan",
            box=box.ROUNDED,
        )
    )

    # Command dispatch
    commands = {
        "/ingest": cmd_ingest,
        "/search": cmd_search,
        "/ask": cmd_ask,
        "/stats": lambda _: cmd_stats(),
        "/sources": lambda _: cmd_sources(),
        "/delete": cmd_delete,
        "/reset": lambda _: cmd_reset(),
        "/models": lambda _: cmd_models(),
        "/model": cmd_model,
        "/help": lambda _: console.print(HELP_TEXT),
    }

    while True:
        try:
            user_input = Prompt.ask("\n[bold cyan]xenus[/bold cyan]")

            if not user_input.strip():
                continue

            stripped = user_input.strip()

            # Check for quit
            if stripped.lower() in ("/quit", "/exit", "/q", "quit", "exit"):
                console.print("[dim]Goodbye! 👋[/dim]")
                break

            # Check for commands
            handled = False
            for cmd, handler in commands.items():
                if stripped.lower().startswith(cmd):
                    args = stripped[len(cmd):].strip()
                    handler(args)
                    handled = True
                    break

            # If not a command, treat as a question (ask with retrieval)
            if not handled:
                cmd_ask(stripped)

        except KeyboardInterrupt:
            console.print("\n[dim]Use /quit to exit.[/dim]")
        except EOFError:
            break
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")


if __name__ == "__main__":
    main()
