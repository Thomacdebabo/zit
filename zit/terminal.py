import click

def print_string(string):
    click.echo(string)

def prompt_for_index():
    return click.prompt("Enter index", type=int)



    