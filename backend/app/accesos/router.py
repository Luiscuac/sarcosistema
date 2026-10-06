"""Endpoints de autenticacion y permisos."""
from fastapi import APIRouter

router = APIRouter(prefix="/accesos", tags=["accesos"])

# TODO: POST /accesos/login, gestion de roles y permisos
