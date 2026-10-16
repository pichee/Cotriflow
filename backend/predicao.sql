-- -- ========================================================
-- -- PREDIÇÕES COTRIFLOW (Estrutura atualizada)
-- -- ========================================================
-- -- Colunas: cliente, animal, quantidade_kg, data_compra, dias_previstos, data_previsao, data_real, observacao

-- -- 1. Consultar as predições (iguais à imagem de Resultados):
-- SELECT 
--     cliente AS "Cliente",
--     animal AS "Animal",
--     quantidade_kg AS "Qtd (Kg)",
--     strftime('%Y-%m-%d', data_compra) AS "Data Compra",
--     dias_previstos AS "Prev. Dias",
--     strftime('%Y-%m-%d', data_previsao) AS "Data Prevista",
--     strftime('%Y-%m-%d', data_real) AS "Data Real"
-- FROM predicoes
-- WHERE data_compra >= '2025-08-08'
-- ORDER BY data_compra ASC
-- LIMIT 22;

-- -- 2. Inserir manualmente uma nova predição:
-- INSERT INTO predicoes (cliente, animal, quantidade_kg, data_compra, dias_previstos, data_previsao, data_real, observacao)
-- VALUES ('C004', 'Suinos', 5650, '2025-08-08 00:00:00', 29, '2025-09-06 00:00:00', '2025-09-08 00:00:00', 'Previsão calculada');


SELECT * from predicoes
ORDER BY data_compra DESC;


.tables