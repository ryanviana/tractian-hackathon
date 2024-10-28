-- db.sql

CREATE TABLE IF NOT EXISTS pieces (
  sap VARCHAR PRIMARY KEY,
  categoria VARCHAR NOT NULL,
  descricao VARCHAR NOT NULL
);

CREATE TABLE IF NOT EXISTS availability (
  sap VARCHAR REFERENCES pieces(sap),
  data DATE NOT NULL,
  hora INT NOT NULL,
  ocupado BOOLEAN NOT NULL,
  PRIMARY KEY (sap, data, hora)
);

INSERT INTO pieces (sap, categoria, descricao) VALUES
('SAP001', 'Ferramenta', 'Chave de Fenda 5mm'),
('SAP002', 'Ferramenta', 'Martelo de Borracha'),
('SAP003', 'Equipamento', 'Máquina de Solda')
ON CONFLICT (sap) DO NOTHING;

INSERT INTO availability (sap, data, hora, ocupado) VALUES
('SAP001', CURRENT_DATE, 9, FALSE),
('SAP001', CURRENT_DATE, 10, FALSE),
('SAP001', CURRENT_DATE, 11, TRUE),
('SAP002', CURRENT_DATE, 9, FALSE),
('SAP002', CURRENT_DATE, 10, TRUE),
('SAP002', CURRENT_DATE, 11, FALSE),
('SAP003', CURRENT_DATE, 9, FALSE),
('SAP003', CURRENT_DATE, 10, FALSE),
('SAP003', CURRENT_DATE, 11, FALSE)
ON CONFLICT (sap, data, hora) DO NOTHING;
