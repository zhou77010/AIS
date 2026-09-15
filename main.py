"""
AIS - Adaptive Investment System

Entry Point

Author : AIS Project
"""

from app.application import Application


def main() -> None:
    """Application entry point."""
    app = Application()
    app.run()


if __name__ == "__main__":
    main()
