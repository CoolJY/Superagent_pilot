"""Keep local deployment secrets/settings out of tests and their subprocesses."""
import os

os.environ["PYTHON_DOTENV_DISABLED"] = "1"
