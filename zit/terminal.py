import click


def print_string(string: str, err: bool = False) -> None:
    click.echo(string, err=err)


def prompt_for_index() -> int:
    return click.prompt("Enter index", type=int)
