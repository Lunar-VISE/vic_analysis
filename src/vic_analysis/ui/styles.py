def application_stylesheet() -> str:
    """Return the shared stylesheet so visual decisions stay in one place."""
    return """
        QWidget {
            background: #f4f6f8;
            color: #1f2933;
            font-size: 14px;
        }

        QMainWindow {
            background: #f4f6f8;
        }
    """
