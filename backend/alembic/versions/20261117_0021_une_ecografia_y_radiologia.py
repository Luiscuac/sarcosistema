"""Une las ramas de migración de ecografía estructurada (main) y radiología convencional.

Merge sin DDL: 20261114_0017 (datos_ecografia en informe_imagen) y 20261117_0020 (sin rol radiologo)
se desarrollaron en paralelo y no tocan los mismos objetos.
"""

revision = '20261117_0021'
down_revision = ('20261114_0017', '20261117_0020')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    raise RuntimeError('Revertir el merge exige decidir qué rama conservar; hazlo manualmente.')
