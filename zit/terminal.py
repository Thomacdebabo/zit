import click


def print_string(string: str, err: bool = False) -> None:
    click.echo(string, err=err)


def prompt_for_index() -> int:
    return click.prompt("Enter index", type=int)


def date_options(f):
    """Decorator to add --yesterday and --date options to a command"""
    f = click.option(
        "--date",
        "-d",
        default=None,
        help="Add the event for a specific date (format: YYYY-MM-DD)",
    )(f)
    f = click.option(
        "--yesterday", "-y", is_flag=True, help="Add the event for yesterday"
    )(f)
    return f


def time_argument(f):
    """Decorator to add time argument to a command"""
    f = click.argument(
        "time", required=False, default=None, metavar="TIME (format: HHMM, HMM, HH, H)"
    )(f)
    return f
