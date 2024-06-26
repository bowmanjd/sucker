"""Package configuration."""
import setuptools

setuptools.setup(
    author="Jonathan Bowman",
    description="Bulk URL downloader.",
    entry_points={"console_scripts": ["sucker=sucker:run"]},
    name="sucker",
    py_modules=["sucker"],
    install_requires=["rich"],
    version="0.1.0",
)
