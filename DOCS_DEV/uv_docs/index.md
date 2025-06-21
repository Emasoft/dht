# uv

An extremely fast Python package and project manager, written in Rust.

## Highlights

- ЁЯЪА A single tool to replace `pip`, `pip-tools`, `pipx`, `poetry`, `pyenv`, `twine`, `virtualenv`,
  and more.
- тЪбя╕П [10-100x faster](https://github.com/astral-sh/uv/blob/main/BENCHMARKS.md) than `pip`.
- ЁЯЧВя╕П Provides [comprehensive project management](#projects), with a
  [universal lockfile](./concepts/projects/layout.md#the-lockfile).
- тЭЗя╕П [Runs scripts](#scripts), with support for
  [inline dependency metadata](./guides/scripts.md#declaring-script-dependencies).
- ЁЯРН [Installs and manages](#python-versions) Python versions.
- ЁЯЫая╕П [Runs and installs](#tools) tools published as Python packages.
- ЁЯФй Includes a [pip-compatible interface](#the-pip-interface) for a performance boost with a
  familiar CLI.
- ЁЯПв Supports Cargo-style [workspaces](./concepts/projects/workspaces.md) for scalable projects.
- ЁЯТ╛ Disk-space efficient, with a [global cache](./concepts/cache.md) for dependency deduplication.
- тПм Installable without Rust or Python via `curl` or `pip`.
- ЁЯЦея╕П Supports macOS, Linux, and Windows.

uv is backed by [Astral](https://astral.sh), the creators of
[Ruff](https://github.com/astral-sh/ruff).

## Installation

Install uv with our official standalone installer:

=== "macOS and Linux"

    ```console
    $ curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

=== "Windows"

    ```pwsh-session
    PS> powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    ```

Then, check out the [first steps](./getting-started/first-steps.md) or read on for a brief overview.

!!! tip

    uv may also be installed with pip, Homebrew, and more. See all of the methods on the
    [installation page](./getting-started/installation.md).

## Projects

uv manages project dependencies and environments, with support for lockfiles, workspaces, and more,
similar to `rye` or `poetry`:

```console
$ uv init example
Initialized project `example` at `/home/user/example`

$ cd example

$ uv add ruff
Creating virtual environment at: .venv
Resolved 2 packages in 170ms
   Built example @ file:///home/user/example
Prepared 2 packages in 627ms
Installed 2 packages in 1ms
 + example==0.1.0 (from file:///home/user/example)
 + ruff==0.5.4

$ uv run ruff check
All checks passed!

$ uv lock
Resolved 2 packages in 0.33ms

$ uv sync
Resolved 2 packages in 0.70ms
Audited 1 package in 0.02ms
```

See the [project guide](./guides/projects.md) to get started.

uv also supports building and publishing projects, even if they're not managed with uv. See the
[packaging guide](./guides/package.md) to learn more.

## Scripts

uv manages dependencies and environments for single-file scripts.

Create a new script and add inline metadata declaring its dependencies:

```console
$ echo 'import requests; print(requests.get("https://astral.sh"))' > example.py

$ uv add --script example.py requests
Updated `example.py`
```

Then, run the script in an isolated virtual environment:

```console
$ uv run example.py
Reading inline script metadata from: example.py
Installed 5 packages in 12ms
<Response [200]>
```

See the [scripts guide](./guides/scripts.md) to get started.

## Tools

uv executes and installs command-line tools provided by Python packages, similar to `pipx`.

Run a tool in an ephemeral environment using `uvx` (an alias for `uv tool run`):

```console
$ uvx pycowsay 'hello world!'
Resolved 1 package in 167ms
Installed 1 package in 9ms
 + pycowsay==0.0.0.2
  """

  ------------
< hello world! >
  ------------
   \   ^__^
    \  (oo)\_______
       (__)\       )\/\
           ||----w |
           ||     ||
```

Install a tool with `uv tool install`:

```console
$ uv tool install ruff
Resolved 1 package in 6ms
Installed 1 package in 2ms
 + ruff==0.5.4
Installed 1 executable: ruff

$ ruff --version
ruff 0.5.4
```

See the [tools guide](./guides/tools.md) to get started.

## Python versions

uv installs Python and allows quickly switching between versions.

Install multiple Python versions:

```console
$ uv python install 3.10 3.11 3.12
Searching for Python versions matching: Python 3.10
Searching for Python versions matching: Python 3.11
Searching for Python versions matching: Python 3.12
Installed 3 versions in 3.42s
 + cpython-3.10.14-macos-aarch64-none
 + cpython-3.11.9-macos-aarch64-none
 + cpython-3.12.4-macos-aarch64-none
```

Download Python versions as needed:

```console
$ uv venv --python 3.12.0
Using CPython 3.12.0
Creating virtual environment at: .venv
Activate with: source .venv/bin/activate

$ uv run --python pypy@3.8 -- python
Python 3.8.16 (a9dbdca6fc3286b0addd2240f11d97d8e8de187a, Dec 29 2022, 11:45:30)
[PyPy 7.3.11 with GCC Apple LLVM 13.1.6 (clang-1316.0.21.2.5)] on darwin
Type "help", "copyright", "credits" or "license" for more information.
>>>>
```

Use a specific Python version in the current directory:

```console
$ uv python pin 3.11
Pinned `.python-version` to `3.11`
```

See the [installing Python guide](./guides/install-python.md) to get started.

## The pip interface

uv provides a drop-in replacement for common `pip`, `pip-tools`, and `virtualenv` commands.

uv extends their interfaces with advanced features, such as dependency version overrides,
platform-independent resolutions, reproducible resolutions, alternative resolution strategies, and
more.

Migrate to uv without changing your existing workflows тАФ and experience a 10-100x speedup тАФ with the
`uv pip` interface.

Compile requirements into a platform-independent requirements file:

```console
$ uv pip compile docs/requirements.in \
   --universal \
   --output-file docs/requirements.txt
Resolved 43 packages in 12ms
```

Create a virtual environment:

```console
$ uv venv
Using CPython 3.12.3
Creating virtual environment at: .venv
Activate with: source .venv/bin/activate
```

Install the locked requirements:

```console
$ uv pip sync docs/requirements.txt
Resolved 43 packages in 11ms
Installed 43 packages in 208ms
 + babel==2.15.0
 + black==24.4.2
 + certifi==2024.7.4
 ...
```

See the [pip interface documentation](./pip/index.md) to get started.

## Learn more

See the [first steps](./getting-started/first-steps.md) or jump straight to the
[guides](./guides/index.md) to start using uv.

---

## Why UV?


At its core, uv is a blazing-fast Python package manager, built from the ground up in Rust. Think of it like pip, but on steroids—faster, smarter, and designed with today’s developers in mind. If pip, venv, and virtualenv had a brilliant, high-performance child written in Rust, it would be uv.

It comes from the folks at [Astral](https://astral.sh/), the same team behind some of the most exciting modern Python tools. You might’ve heard of [ruff](https://docs.astral.sh/ruff/), the lightning-fast linter that catches code issues almost as fast as you can type. And then there’s [pdm](https://pdm-project.org/en/latest/), a modern Python build and packaging tool that simplifies project setup by using pyproject.toml instead of the older, messier setup.py. Clean, simple, and way easier to work with.

Astral’s whole mission is to fix what’s been broken in Python packaging for years — making installs faster, environments more consistent, and getting rid of all those annoying dependency headaches that slow us down.

### What makes uv stand out?

First, it’s *fast*. Like, *really* fast. Thanks to Rust under the hood, installing packages takes seconds instead of minutes. It also works beautifully with pyrproject.toml, which means it slots right into modern Python workflows without extra setup.

And here’s where it gets even better: uv gives you deterministic installs — kind of like what npm or bun do for JavaScript. That means everyone on your team gets the exact same environment every time. No more “Wait, it worked on my machine…” moments.

Plus, if you’re tired of managing messy requirements.txt files and trying to sync environments across macOS, Windows, and Linux, uv helps clean that up, too. It’s a fresh take on how Python projects should be managed—simple, consistent, and fast.

So no, uv isn’t just a pip alternative. It’s a total rethink of how we handle Python dependencies. If you’ve ever felt like Python packaging was stuck in the past, uv is your glimpse into the future.

## Why uv Is the Fast, Clean Python Package Manager You’ll Actually Enjoy Using

### 1. Blazing Fast Installs & Dependency Resolution

Built with Rust, uv speeds up installs and dependency resolution, making package setup much faster than with pip or poetry.

### 2. No Virtual Environments Needed (PEP 582 Support)

With PEP 582 support, you no longer need to manage or activate virtual environments (venv). Project dependencies stay neatly organized, without extra configuration.

### 3. Drop-in Support for pyproject.toml

uv automatically handles pyproject.toml without any manual configuration. It’s built to work seamlessly with modern Python projects.

### 4. Secure, Deterministic Installs

uv ensures consistent installs for everyone — everyone gets the exact same environment every time, minimizing conflicts.


### 5. Cross-Platform Reliability

**For devs:** Works across macOS, Linux, and Windows without needing special setup or adjustments.


## Why Managing FastAPI Projects with `pip` Is Slower, Messier, and Riskier Than You Think

If you’ve built a FastAPI app any time in the last few years, chances are you followed the “classic” setup: create a virtual environment, activate it, install dependencies with pip, freeze them into a requirements.txt file and then run the application. Something like this:


```bash
# The Traditional pip + venv + requirements.txt Workflow

# Step 1: Create a virtual environment
python -m venv venv

# Step 2: Activate the virtual environment
source venv/bin/activate

# Step 3: Install FastAPI and Uvicorn
pip install fastapi uvicorn

# Step 4: Freeze dependencies
pip freeze > requirements.txt

# Step 5: Later on… install more dependencies
pip install beanie
pip freeze > requirements.txt

# Step 6: Run the app (assuming uvicorn)
uvicorn main:app --reload
```

And hey — it works. But at what cost?

### The Pain Points of the Old Workflow

At first, it seems simple enough. Then you add more packages later:

```bash
pip install twilio
pip freeze > requirements.txt
```

Except...
  - Maybe you forgot to freeze the new dependency.
  - Or your teammate installs something else and forgets to update the file.
  - Or worse, your continuous integration pipeline breaks because the versions installed aren’t exactly the same across systems.
  - Or your virtual environment is bloated.
  - Or versions have drifted, and you’re stuck debugging a “works on my machine” issue at 2 a.m.

**It’s not that pip is bad — it’s just showing its age.** FastAPI is a sleek, modern web framework. Managing it with the old pip + venv flow feels like writing TypeScript in Notepad.


### That “Wait — Why Wasn’t This Always the Way?” Moment

The first time I used uv, it honestly felt like a breath of fresh air.

Suddenly, installs were lightning-fast. Lockfiles were created automatically. Everything just *worked*, and it was reproducible on any machine.

No more juggling between pip, venv, requirements.txt, pyproject.toml, and maybe even poetry if I got desperate.

This wasn’t just about performance — it was about peace of mind. About clarity. uv replaced that whole mess with a single, modern workflow.

### **From Clunky to Clean: The Modern uv Way**

With uv, the entire setup becomes drastically simpler:

```graphql
# The Modern uv Workflow (Cleaner, Faster, Reproducible)

# Step 1: Initialize your FastAPI project
uv init --app

# Step 2: Add dependencies with extras
#(auto creates a virtual environment and auto updates pyproject.toml & lock)
uv add fastapi --extra standard
uv add beanie

# Step 3: Run the app with a built-in FastAPI runner
uv run fastapi dev
```

That’s it — just six steps in three easy-to-remember phases. Dependencies are added and locked automatically. Your project structure stays clean. Everything works out of the box and is fully reproducible. With this one tool, you get speed, simplicity, and confidence — all in one place.

### Lockfiles, Explained (And Why They Matter More Than You Think)

Here’s a big reason why uv shines: it uses lockfiles. In the old setup, if your requirements.txt says:

```python
fastapi>=0.95
```

Then pip will install whatever the latest compatible version is *at that moment*. If a new release drops tomorrow, your teammate could install something totally different than you did — without even realizing it.

With uv, it doesn’t work that way. Every install is recorded in a uv.lock file—a detailed snapshot of the exact versions installed, including all transitive dependencies.

Think of it like this: Your pyproject.toml is the recipe (“Make chocolate cake”), and your uv.lock file is the grocery receipt (“Bought this exact brand of flour, eggs, cocoa…”).

That means anyone who clones your repo and installs with uv will get the exact same environment. No drift. No surprises.



### Why `uv.lock` Beats `requirements.txt` Every Time

Sure, pip freeze > requirements.txt gives you a list—but it’s flawed. It grabs *everything* in your virtual environment, even tools you may have installed for debugging or testing but don’t actually use in production.

It doesn’t separate dev dependencies from core ones. It’s easy to forget to update. And even when you do remember, you’re still flying blind when it comes to version consistency across teams or CI/CD environments.

In contrast, uv.lock is generated automatically, updated cleanly, and gives you a crystal-clear record of what was installed and why. It’s designed for reliability, especially when your code moves from laptop to production server.


## Ready to Dive In?

Getting started with uv is refreshingly simple — installation is quick, and it works beautifully in environments like Visual Studio Code. Their [official website](https://uv.dev) offers a clean, modern interface and clear installation instructions. For FastAPI developers, the [Using uv with FastAPI](https://docs.astral.sh/uv/guides/integration/fastapi/) guide is especially helpful. It walks you through initialising a project, adding dependencies, and running your app — all with minimal setup. Plus, if you’re deploying with Docker, they’ve got you covered with a ready-to-use Dockerfile and deployment steps.

### Getting Started with uv: Install, Use, and Manage Dependencies

uv is available in the core Homebrew packages. To install uvon macOS using [Homebrew](https://brew.sh), run:

```bash
$brew install uv
```

You can verify it’s installed correctly with:

```bash
uv --version
```

On Linux or Windows? Visit [https://astral.sh/uv](https://astral.sh/uv) for platform-specific instructions.

### Using uv in VS Code

Once installed, you can use uv directly in the integrated terminal in Visual Studio Code.

```bash
uv add fastapi
uv run fastapi dev
```

It works just like the regular terminal — but inside your editor, keeping everything in one place.

### Removing Dependencies

Need to remove a package? uv makes that simple too:

```bash
uv remove beanie
```

This command:

*   Deletes the package from your project
*   Updates your pyproject.toml
*   Regenerates the uv.lock file to stay clean and reproducible

Just like installing, this command works instantly in your VS Code terminal or any terminal of your choice.

## Final Thoughts: uv Isn’t Just Faster. It’s a Mindset Shift.

At first glance, you might think **uv** is just about speed — and sure, that’s part of the appeal. It’s built in Rust, and it *flies*. Installs that used to take minutes now finish in seconds. That alone is worth celebrating.

But once you start using it, you realise it’s about more than just performance. It’s about *sanity*. About reducing the mental overhead that comes with every Python project you spin up. About not having to juggle between pip, venv, requirements.txt, pyproject.toml, and wondering if you’ve forgotten a step—or worse, broken your teammate’s build.

uv replaces all of that with one simple, unified workflow. It doesn’t just simplify your toolchain — it makes your whole dev experience cleaner, calmer, and more predictable.

For me, someone who’s committed to mastering the tools I use — not just getting by but going deep enough to teach them — uv has been a revelation. It’s the kind of tool that makes you wonder why things were ever more complicated. It brings the same elegance to Python dependency management that FastAPI brought to building web apps.

If you’re still using the traditional pip-and-venv approach, I get it. It’s familiar. It’s what every tutorial tells you to do. But at some point, you start to feel the friction. You start to question why things are so fragmented, so manual, so… fragile. That’s when you know it’s time for a better way.

uv isn’t just a faster tool — it’s a smarter one. It’s built for the developer you’re becoming, not the one you were when you first installed Python.

So go ahead — shake the table break stuff in a clean environment. Try uv. Build with clarity. And finally, spend less time fixing dependencies and more time shipping what matters.

Here’s to fewer bugs, cleaner builds, and clearer minds.

---
