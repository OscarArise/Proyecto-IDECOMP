import os
from tkinter import filedialog, messagebox

_DEFAULT_EXT = ".caos"
_FILE_TYPES = [("Archivos Caos", "*.caos"), ("Todos los archivos", "*.*")]


class FileManager:
    """
    Gestiona las operaciones de archivo del IDE.

    Parámetros
    ----------
    root         : tk.Tk | tk.Toplevel  – ventana raíz (padre de diálogos)
    state        : AppState             – estado compartido del IDE
    get_content  : callable() -> str    – obtiene el texto del editor
    set_content  : callable(str)        – reemplaza el texto del editor
    update_title : callable(path, modified) – actualiza título de ventana
    """

    def __init__(self, root, state, get_content, set_content, update_title):
        self.root = root
        self.state = state
        self._get_content = get_content
        self._set_content = set_content
        self._update_title = update_title


    def new_file(self):
        """
        Nuevo archivo: limpia el editor, resetea la ruta y el flag de modificación.
        Pregunta si hay cambios sin guardar antes de proceder.
        """
        if not self._confirm_discard():
            return

        self._set_content("")
        self.state.reset()
        self._update_title(None, False)

    def open_file(self):
        """
        Abre un archivo: muestra diálogo, lee el contenido y lo carga en el editor.
        Pregunta si hay cambios sin guardar antes de proceder.
        """
        if not self._confirm_discard():
            return

        path = filedialog.askopenfilename(
            parent=self.root,
            title="Abrir archivo",
            filetypes=_FILE_TYPES,
        )
        if not path:
            return  # El usuario canceló

        try:
            with open(path, "r", encoding="utf-8") as fh:
                content = fh.read()
        except OSError as exc:
            messagebox.showerror(
                "Error al abrir",
                f"No se pudo leer el archivo:\n{exc}",
                parent=self.root,
            )
            return

        self._set_content(content)
        self.state.mark_saved(path)
        self._update_title(path, False)

    def save_file(self):
        """
        Guarda el archivo actual.
        Si aún no tiene ruta asignada, delega a save_as().
        """
        if self.state.current_file:
            self._write_to_disk(self.state.current_file)
        else:
            self.save_as()

    def save_as(self):
        """
        Guarda como: muestra el diálogo de guardado, escribe el archivo y
        actualiza la ruta en el estado.
        """
        path = filedialog.asksaveasfilename(
            parent=self.root,
            title="Guardar como",
            defaultextension=_DEFAULT_EXT,
            filetypes=_FILE_TYPES,
        )
        if not path:
            return  # El usuario canceló

        self._write_to_disk(path)

    def close_file(self):
        """
        Cierra el archivo activo.
        Pregunta si hay cambios sin guardar antes de limpiar el editor.
        """
        if not self._confirm_discard():
            return

        self._set_content("")
        self.state.reset()
        self._update_title(None, False)

    def exit_app(self):
        """
        Sale de la aplicación.
        Llama a close_file() para verificar cambios pendientes; si el usuario
        cancela esa verificación, no se cierra la ventana.
        """
        if self.state.has_unsaved_changes():
            # Reutiliza _confirm_discard que ya pregunta al usuario
            if not self._confirm_discard():
                return
        self.root.quit()



    def _write_to_disk(self, path: str):
        """Escribe el contenido del editor en `path` y actualiza el estado."""
        content = self._get_content()
        try:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(content)
        except OSError as exc:
            messagebox.showerror(
                "Error al guardar",
                f"No se pudo guardar el archivo:\n{exc}",
                parent=self.root,
            )
            return

        self.state.mark_saved(path)
        self._update_title(path, False)

    def _confirm_discard(self) -> bool:
        """
        Si hay cambios sin guardar, pregunta al usuario qué hacer.

        Retorna
        -------
        True  – puede proceder (guardó, o eligió descartar)
        False – el usuario canceló la operación
        """
        if not self.state.has_unsaved_changes():
            return True

        filename = (
            os.path.basename(self.state.current_file)
            if self.state.current_file
            else "Nuevo archivo"
        )

        answer = messagebox.askyesnocancel(
            "Cambios sin guardar",
            f'"{filename}" tiene cambios sin guardar.\n\n'
            "¿Deseas guardar antes de continuar?",
            parent=self.root,
        )

        if answer is None:
            # El usuario presionó Cancelar
            return False
        if answer:
            # El usuario eligió Sí → guardar
            self.save_file()
            # Si save_file falló (p. ej. el diálogo fue cancelado), no proceder
            return not self.state.has_unsaved_changes()
        # answer == False → Descartar cambios
        return True
