"""Une los historiales de Laboratorio e IA sin modificar objetos ni datos.

Una base cuyo esquema ya materializo ambas ramas pero solo registra una
requiere reconciliacion verificada de su historial antes de este upgrade.
No ejecutar stamp sin comparar previamente el esquema y tener respaldo.
"""

revision = '20261109_0012'
down_revision = ('20261103_0011', '20261103_0009')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    raise RuntimeError(
        'La reconciliacion requiere restauracion verificada; downgrade bloqueado.'
    )
