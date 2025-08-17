import click

def print_string(string, err=False):
    click.echo(string, err=err)

def prompt_for_index():
    return click.prompt("Enter index", type=int)



    