"""Almacenamiento server-side de sesiones para Flask basado en archivos locales.

Mantiene `id_usuario`, `dni` y `access_token` (JWT) en el servidor dentro de
un directorio local con permisos restringidos (`0700` / `0600`), mientras que
la cookie del navegador contiene únicamente un identificador de sesión aleatorio
firmado con `FRONTEND_SECRET_KEY`. No utiliza variables globales mutables en
memoria ni requiere ORM o SQLAlchemy.
"""

from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import re
import secrets
import tempfile
import time
from typing import Any

from flask import Flask, Request, Response
from flask.sessions import SessionInterface, SessionMixin
from itsdangerous import BadSignature, Signer
from werkzeug.datastructures import CallbackDict

_SID_VALIDO_RE = re.compile(r"^[A-Za-z0-9_-]{32,64}$")
DEFAULT_SESSION_LIFETIME_SECONDS = 3600


class ServerSideSession(CallbackDict, SessionMixin):
    """Objeto `session` de Flask respaldado por almacenamiento server-side."""

    def __init__(
        self,
        initial: dict[str, Any] | None = None,
        sid: str | None = None,
        new: bool = False,
    ) -> None:
        def _on_update(self_dict: dict[str, Any]) -> None:
            self.modified = True

        super().__init__(initial or {}, _on_update)
        self.sid = sid or secrets.token_urlsafe(32)
        self.new = new
        self.modified = False
        self.regenerated_from: str | None = None

    def regenerate(self) -> None:
        """Regenera el identificador de sesión (p. ej. tras iniciar sesión)."""
        if self.regenerated_from is None and not self.new:
            self.regenerated_from = self.sid
        self.sid = secrets.token_urlsafe(32)
        self.modified = True


class FileSystemSessionInterface(SessionInterface):
    """Implementación server-side de `SessionInterface` sobre el sistema de archivos."""

    session_class = ServerSideSession

    def __init__(
        self,
        storage_dir: str | Path,
        key_prefix: str = "cmsi_sess:",
        default_ttl: int = DEFAULT_SESSION_LIFETIME_SECONDS,
    ) -> None:
        self.storage_dir = Path(storage_dir).resolve()
        self.key_prefix = key_prefix
        self.default_ttl = max(int(default_ttl), 60)
        self._asegurar_directorio()

    def _asegurar_directorio(self) -> None:
        self.storage_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        try:
            os.chmod(self.storage_dir, 0o700)
        except OSError:
            pass

    def _get_signer(self, app: Flask) -> Signer:
        if not app.secret_key:
            raise RuntimeError(
                "FRONTEND_SECRET_KEY debe estar configurada para firmar la cookie de sesión."
            )
        return Signer(
            app.secret_key,
            salt="centro-medico-frontend-session",
            key_derivation="hmac",
        )

    def _ruta_archivo(self, sid: str) -> Path | None:
        if not isinstance(sid, str) or not _SID_VALIDO_RE.match(sid):
            return None
        ruta = (self.storage_dir / f"{sid}.json").resolve()
        if ruta.parent != self.storage_dir:
            return None
        return ruta

    def _eliminar_archivo(self, sid: str | None) -> None:
        if not sid:
            return
        ruta = self._ruta_archivo(sid)
        if ruta is not None:
            try:
                ruta.unlink(missing_ok=True)
            except OSError:
                pass

    def _limpiar_vencidas(self) -> None:
        ahora = time.time()
        try:
            archivos = list(self.storage_dir.glob("*.json"))
        except OSError:
            return

        for ruta in archivos:
            try:
                contenido = json.loads(ruta.read_text(encoding="utf-8"))
                if float(contenido.get("expires_at", 0)) <= ahora:
                    ruta.unlink(missing_ok=True)
            except (OSError, ValueError, TypeError):
                try:
                    ruta.unlink(missing_ok=True)
                except OSError:
                    pass

    def open_session(self, app: Flask, request: Request) -> ServerSideSession:
        cookie_name = app.config.get("SESSION_COOKIE_NAME", "session")
        raw_cookie = request.cookies.get(cookie_name)
        if not raw_cookie:
            return self.session_class(new=True)

        signer = self._get_signer(app)
        try:
            sid = signer.unsign(raw_cookie).decode("utf-8")
        except BadSignature:
            return self.session_class(new=True)

        ruta = self._ruta_archivo(sid)
        if ruta is None or not ruta.is_file():
            return self.session_class(new=True)

        try:
            registro = json.loads(ruta.read_text(encoding="utf-8"))
            expires_at = float(registro.get("expires_at", 0))
            data = registro.get("data")
            if expires_at <= time.time() or not isinstance(data, dict):
                ruta.unlink(missing_ok=True)
                return self.session_class(new=True)
            return self.session_class(initial=data, sid=sid, new=False)
        except (OSError, ValueError, TypeError):
            self._eliminar_archivo(sid)
            return self.session_class(new=True)

    def save_session(
        self,
        app: Flask,
        session: SessionMixin,
        response: Response,
    ) -> None:
        cookie_name = app.config.get("SESSION_COOKIE_NAME", "session")
        domain = self.get_cookie_domain(app)
        path = self.get_cookie_path(app)
        httponly = self.get_cookie_httponly(app)
        secure = self.get_cookie_secure(app)
        samesite = self.get_cookie_samesite(app)

        sid = getattr(session, "sid", None)
        regenerated_from = getattr(session, "regenerated_from", None)
        if regenerated_from:
            self._eliminar_archivo(regenerated_from)

        if not session:
            if getattr(session, "modified", False):
                self._eliminar_archivo(sid)
                response.delete_cookie(
                    cookie_name,
                    domain=domain,
                    path=path,
                    secure=secure,
                    samesite=samesite,
                    httponly=httponly,
                )
            return

        if not self.should_set_cookie(app, session):
            return

        self._asegurar_directorio()
        self._limpiar_vencidas()

        if not isinstance(sid, str) or not _SID_VALIDO_RE.match(sid):
            sid = secrets.token_urlsafe(32)
            session.sid = sid  # type: ignore[attr-defined]

        ruta = self._ruta_archivo(sid)
        if ruta is None:
            return

        ahora = time.time()
        expires_at = float(session.get("_expires_at", ahora + self.default_ttl))
        if expires_at <= ahora:
            self._eliminar_archivo(sid)
            response.delete_cookie(
                cookie_name,
                domain=domain,
                path=path,
                secure=secure,
                samesite=samesite,
                httponly=httponly,
            )
            return

        payload = {
            "expires_at": expires_at,
            "data": dict(session),
        }

        fd, tmp_path = tempfile.mkstemp(
            dir=str(self.storage_dir),
            prefix=".sess_",
            suffix=".tmp",
        )
        try:
            os.chmod(tmp_path, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8") as tmp_file:
                json.dump(payload, tmp_file, ensure_ascii=False)
            os.replace(tmp_path, ruta)
        except OSError:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise

        signer = self._get_signer(app)
        signed_sid = signer.sign(sid.encode("utf-8")).decode("utf-8")
        expires_dt = datetime.fromtimestamp(expires_at, tz=timezone.utc)
        max_age = max(int(expires_at - ahora), 0)

        response.set_cookie(
            cookie_name,
            signed_sid,
            max_age=max_age,
            expires=expires_dt,
            path=path,
            domain=domain,
            secure=secure,
            httponly=httponly,
            samesite=samesite,
        )
