# Kobo Book Downloader

Kobo Book Downloader is a command-line tool that downloads books you purchased from Kobo. It can turn Kobo's KEPUB/EPUB download into a DRM-free EPUB that you can read in apps such as [KOReader](https://github.com/koreader/koreader).

It talks directly to Kobo, so you do not need to download each book through a Kobo e-reader or desktop application first.

> Use this tool only for books you are authorized to download, and follow the laws and terms that apply where you live.

![Kobo Book Downloader in a terminal](screenshot.png)

## Quick start with uv

You need [uv](https://docs.astral.sh/uv/getting-started/installation/) and a Kobo account with at least one purchased book.

From the repository directory:

```console
uv sync --locked
mkdir -p books
uv run kobo-book-downloader pick ./books
```

On the first command that contacts Kobo, the tool prints an activation URL and code. Open the URL, enter the code, and sign in to Kobo in your browser. The terminal waits until activation is complete, then remembers the resulting access tokens for later runs.

Run the help at any time:

```console
uv run kobo-book-downloader --help
```

## Common commands

All examples below start with `uv run kobo-book-downloader`.

| Command                         | What it does |
| ------------------------------- | ------------ |
| `list`                          | List unread books and their IDs. |
| `list --all`                    | List both read and unread books. |
| `pick ./books`                  | Interactively select unread books to download. |
| `pick ./books --all`            | Interactively select from all books. |
| `get ./books BOOK_ID`           | Download one book and choose its filename automatically. |
| `get ./books/book.epub BOOK_ID` | Download one book to an exact filename. |
| `get ./books --all`             | Download every available, non-archived book. |
| `wishlist`                      | List books on your Kobo wish list. |
| `info`                          | Print the configuration file location. |
| `--verbose list`                | List books with debug logging enabled. |

The output directory must already exist. Use the ID printed by `list` when running `get` for one book.

## Run with Docker

Build the image and create host directories for books and configuration:

```console
docker build -t kobo-book-downloader .
mkdir -p books kobo-config
```

On Linux or macOS, this one command mounts both directories and starts the interactive book picker:

```console
docker run --rm -it --user "$(id -u):$(id -g)" -v "$PWD/books:/books" -v "$PWD/kobo-config:/config" kobo-book-downloader pick /books
```

- Downloaded EPUB files appear in `./books` on the host.
- Kobo access tokens are stored in `./kobo-config/kobo-book-downloader.json` on the host.
- Reuse both mounts on later Docker runs so the downloads and login survive the temporary container.

For example, replace `pick /books` with `list --all` to list the full library, or with `get /books --all` to download it.

The included Compose file provides the same mounts:

```console
mkdir -p books kobo-config
KBD_UID="$(id -u)" KBD_GID="$(id -g)" docker compose run --rm kobo pick /books
```

## Credentials and privacy

The tool does not store your Kobo password. Kobo authentication happens in your browser.

It does store the device ID, serial number, access token, refresh token, Kobo user ID, and user key needed for later downloads. Treat the configuration file like a password and do not commit or share it. New files are created with owner-only permissions on filesystems that support POSIX permissions.

The configuration file is located at:

- `$XDG_CONFIG_HOME/kobo-book-downloader.json` when `XDG_CONFIG_HOME` is set;
- `~/.config/kobo-book-downloader.json` for a normal local run;
- `/config/kobo-book-downloader.json` inside Docker, which the examples map to `./kobo-config/kobo-book-downloader.json`.

To confirm the exact path for the current environment, run:

```console
uv run kobo-book-downloader info
```

## Troubleshooting

### An archived book will not download

Restore the book on the Kobo website first. Kobo does not return download URLs or content keys for archived books.

### A command fails without enough detail

Put `--verbose` before the command:

```console
uv run kobo-book-downloader --verbose get ./books BOOK_ID
```

### Start authentication again

Move the configuration file to a safe backup location, then run a command that contacts Kobo. A fresh activation flow will start. Keep the backup until the new login works.

## Development

Dependencies are pinned in `pyproject.toml` and fully resolved in `uv.lock`.

```console
make sync       # Install the locked environment
make test       # Run tests
make validate   # Check the lock, run tests, and build distributions
make docker-build
```

The DRM removal code is based on Physisticated's `obok.py` from the [DeDRM tools project](https://github.com/noDRM/DeDRM_tools). Thank you to its contributors.
