"""Compatibilidad para imports anteriores del router de laboratorio."""

from app.laboratorio.presentation.routes.router import get_service, router

__all__ = ["get_service", "router"]
