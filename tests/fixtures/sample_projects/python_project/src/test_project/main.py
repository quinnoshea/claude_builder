"""Main module for test project."""
import click
import requests


def fetch_data(url: str) -> dict:
    """Fetch data from URL."""
    response = requests.get(url)
    response.raise_for_status()
    return response.json()


@click.command()
@click.option('--url', required=True, help='URL to fetch data from')
def main(url: str) -> None:
    """Main CLI function."""
    try:
        data = fetch_data(url)
        print(f"Fetched {len(data)} items")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)


if __name__ == '__main__':
    main()