# Indicador Diário de Dolarização

Projeto independente para acompanhar a queda do dólar em relação à maior cotação diária de venda divulgada pelo Banco Central nos últimos 12 meses.

## Cálculo

`Queda (%) = (1 - fechamento semanal / maior fechamento diário dos últimos 12 meses) * 100`

- Referência: Banco Central do Brasil, SGS série 1 — taxa de câmbio livre, dólar americano (venda), periodicidade diária.
- Observação diária: cada registro diário publicado pelo Banco Central. Em fins de semana e feriados, permanece exibida a última observação disponível.
- Máxima de referência: maior valor diário dentro dos 12 meses anteriores ao fechamento semanal, incluindo o próprio dia.
- Gatilho visual inicial: queda igual ou superior a 5%.
- Atualização automática: dias úteis às 18:30 (horário de Brasília), com execução manual disponível em GitHub Actions.

Fonte e metadados: https://dadosabertos.bcb.gov.br/dataset/1-taxa-de-cambio---livre---dolar-americano-venda---diario

## Publicação gratuita no GitHub

1. Repositório público: `rams10/indicador-dolarizacao`.
2. Os arquivos do projeto estão organizados na raiz, incluindo `.github/workflows/update.yml` e `docs/`.
3. Em **Settings → Actions → General → Workflow permissions**, selecione **Read and write permissions** e salve.
4. Em **Settings → Pages**, configure **Deploy from a branch**, branch `main`, pasta `/docs`, e salve.
5. Em **Actions**, selecione **Atualização semanal do dólar** e clique em **Run workflow** para a primeira coleta.
6. Não são necessárias chaves de API, tokens da brapi, Telegram ou variáveis secretas.

## Testes locais

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python monitor.py
```

## Limitações

O valor usado é uma referência cambial diária de venda do BCB, não necessariamente o preço final de compra oferecido por banco, corretora, espécie, cartão, remessa ou ETF. Spread, IOF, tarifas e custos de cada instrumento não estão incluídos. A execução agendada pelo GitHub Actions pode atrasar; a coleta usa a última observação efetivamente publicada pelo BCB.
