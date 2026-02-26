class AppState:

    def __init__(self):
        # Ruta absoluta del archivo actualmente abierto (None si no hay ninguno)
        self.current_file: str | None = None

        # True cuando el contenido del editor difiere del archivo en disco
        self.is_modified: bool = False


    # Helpers de conveniencia

    def mark_modified(self):
        """Marca el estado actual como modificado (cambios sin guardar)."""
        self.is_modified = True

    def mark_saved(self, path: str):
        """Actualiza la ruta y limpia el flag de modificación después de guardar."""
        self.current_file = path
        self.is_modified = False

    def reset(self):
        """Reinicia el estado a 'sin archivo abierto'."""
        self.current_file = None
        self.is_modified = False

    def has_unsaved_changes(self) -> bool:
        """Devuelve True si hay cambios no guardados."""
        return self.is_modified

    def __repr__(self):
        return (
            f"AppState(current_file={self.current_file!r}, "
            f"is_modified={self.is_modified})"
        )
