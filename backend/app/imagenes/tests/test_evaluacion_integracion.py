import pytest


@pytest.mark.asyncio
async def test_ablacion_empareja_300_y_no_modifica_scores_ni_confirma():
    from scripts.evaluacion_radiologia.integracion import evaluar_ablacion
    from scripts.evaluacion_radiologia.casos import generar_casos
    r = await evaluar_ablacion(generar_casos(), {'estado': 'informacion_insuficiente', 'evidencia': []})
    assert r['n_pares'] == 300
    assert r['scores_identicos'] == r['fusion_identica'] == 300
    assert r['confirmaciones'] == 0
    assert r['vision_synthetic'] is True
    assert len({f['id'] for f in r['rows']}) == 300
