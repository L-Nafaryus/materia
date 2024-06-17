import click


@click.group() 
def client():
    click.echo("Hola!")

@client.command() 
def test():
    pass 

if __name__ == "__main__":
    client()
